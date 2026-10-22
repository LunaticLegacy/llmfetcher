"""Composable, source-aware context blocks for built-in and plugin providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Mapping, Protocol, Sequence

from ..llm_types import JsonObject, JsonValue, MessageRole, RequestMessage


class ContextPosition(IntEnum):
    """Canonical position of a block in the assembled request."""

    PERSISTENT = 10
    PREVIOUS = 20
    MEMORY = 30
    CUSTOM = 35
    WORKTREE = 40
    LAST_ROUND = 50
    CURRENT_INPUT = 60


@dataclass(frozen=True)
class ContextBlock:
    """One bounded semantic contribution to a model request.

    Attributes:
        role: Provider-neutral message role used when rendered.
        content: Text to inject into the next model request.
        source: Stable provider identifier for diagnostics and previews.
        position: Canonical ordering slot selected by the Composer.
        priority: Lower values are rendered first.
        persistent: Whether the block represents durable context.
        enabled: Whether the composer includes this block.
        metadata: Provider-specific diagnostics not sent to the model.
        message: Optional full message preserving tool calls and images.
    """

    role: MessageRole
    content: str
    source: str
    position: "ContextPosition" = ContextPosition.PERSISTENT
    priority: int = 0
    persistent: bool = False
    enabled: bool = True
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    message: RequestMessage | None = None


class ContextSource(Protocol):
    """Source contract consumed by :class:`ContextComposer`."""

    source_id: str

    def build_blocks(self, snapshot: ContextSnapshot) -> Sequence[ContextBlock]:
        """Project source state into request blocks."""
        ...


class ContextHandlerPort(Protocol):
    """Handler capability the composer itself invokes for one request."""

    def limit_tool_result_messages(
        self,
        messages: list[RequestMessage],
    ) -> list[RequestMessage]:
        """Bound tool-result text for the outgoing model request."""
        ...


class HandlerBlockSource(Protocol):
    """Read-only handler surface used by :class:`HandlerContextSource`."""

    def build_messages(
        self,
        *,
        system_prompt: str | None = None,
    ) -> list[RequestMessage]:
        """Return the handler's complete provider-neutral context."""
        ...


@dataclass(frozen=True)
class ContextSnapshot:
    """Read-only information exposed to context providers for one request.

    Attributes:
        handler: Active context handler.
        system_prompt: System prompt selected for the request.
        current_message: Current user input, when available.
        metadata: Host-provided request metadata.
    """

    handler: ContextHandlerPort | None
    system_prompt: str | None = None
    current_message: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


class ContextProvider(ContextSource, Protocol):
    """Plugin contract for adding context without owning conversation state.

    Providers project durable or dynamic plugin state into request blocks;
    they do not append to conversation history.
    """

    provider_id: str

    def build_blocks(self, snapshot: ContextSnapshot) -> Sequence[ContextBlock]:
        """Build blocks for one model request.

        Args:
            snapshot: Read-only request and handler information.

        Returns:
            Blocks to validate, order, and render.
        """
        ...


class ContextComposer:
    """Validate, order, and render provider-produced blocks.

    Args:
        providers: Complete source collection in declaration order. The Agent
            owns this Composer; sources are never inherited from a handler.
    """

    def __init__(
        self,
        providers: Sequence[ContextSource],
        *,
        priority_overrides: Mapping[str, int] | None = None,
    ) -> None:
        """Create a composer with its complete externally supplied sources.

        Args:
            providers: Providers to register in declaration order.
            priority_overrides: Optional source-id to priority overrides.
                ``source`` is the identity a block already exposes, so an
                override pins a block without inventing a new position.  An
                entry whose source is absent from the current request is
                ignored, letting a saved order survive a removed plugin.
        """
        self._providers: list[ContextSource] = list(providers)
        self._priority_overrides: dict[str, int] = {}
        for source, priority in (priority_overrides or {}).items():
            if not isinstance(source, str) or not source.strip():
                raise ValueError("context priority override sources must be non-empty strings")
            if isinstance(priority, bool) or not isinstance(priority, int):
                raise ValueError("context priority overrides must be integers")
            self._priority_overrides[source] = priority

    @property
    def providers(self) -> tuple[ContextSource, ...]:
        """Return the currently registered providers in registration order."""
        return tuple(self._providers)

    def register(self, provider: ContextSource) -> None:
        """Register a provider for future requests.

        Args:
            provider: Provider implementing ``source_id`` and
                ``build_blocks``.

        Raises:
            ValueError: If the source ID is empty or already registered.
        """
        provider_id = provider.source_id.strip()
        if not provider_id:
            raise ValueError("context provider must define a non-empty source_id")
        if any(item.source_id == provider_id for item in self._providers):
            raise ValueError(f"context provider already registered: {provider_id}")
        self._providers.append(provider)

    def blocks(self, snapshot: ContextSnapshot) -> list[ContextBlock]:
        """Collect, filter, and stably sort provider blocks.

        Args:
            snapshot: Request snapshot passed to every provider.

        Returns:
            Enabled, non-empty blocks ordered by priority, then position,
            then declaration order.
        """
        result: list[tuple[int, int, int, ContextBlock]] = []
        sequence = 0
        for provider in self._providers:
            provider_blocks = provider.build_blocks(snapshot)
            for block in provider_blocks or ():
                if not isinstance(block, ContextBlock) or not block.enabled:
                    continue
                if (
                    (not block.content or not block.content.strip())
                    and not (block.message is not None and block.message.tool_calls)
                ):
                    continue
                priority = self._priority_overrides.get(block.source, block.priority)
                result.append((priority, int(block.position), sequence, block))
                sequence += 1
        result.sort(key=lambda item: (item[0], item[1], item[2]))
        return [item[3] for item in result]

    def render(self, blocks: Sequence[ContextBlock]) -> list[RequestMessage]:
        """Render blocks as provider-neutral request messages.

        Args:
            blocks: Validated blocks to render.

        Returns:
            Request messages containing each block's role and content.
        """
        rendered: list[RequestMessage] = []
        for block in blocks:
            if block.message is not None:
                rendered.append(block.message)
            else:
                rendered.append(RequestMessage(role=block.role, content=block.content))
        return rendered

    def compose(
        self,
        *,
        snapshot: ContextSnapshot,
        system_prompt: str | None = None,
    ) -> list[RequestMessage]:
        """Build the complete request in the canonical context order.

        The composer owns ordering. Sources only describe semantic blocks;
        neither a context handler nor a plugin may reorder another source.
        The system prompt is always emitted first and is not a source block.
        """
        effective = ContextSnapshot(
            handler=snapshot.handler,
            system_prompt=system_prompt if system_prompt is not None else snapshot.system_prompt,
            current_message=snapshot.current_message,
            metadata=dict(snapshot.metadata),
        )
        blocks = self.blocks(effective)
        messages: list[RequestMessage] = []
        if effective.system_prompt:
            messages.append(RequestMessage(role="system", content=effective.system_prompt))
        messages.extend(self.render(blocks))
        if effective.handler is not None:
            messages = effective.handler.limit_tool_result_messages(messages)
        return messages

    def describe(
        self,
        *,
        snapshot: ContextSnapshot,
        system_prompt: str | None = None,
    ) -> list[JsonObject]:
        """Describe the exact composed messages with source provenance.

        Rows stay JSON objects because this is the preview boundary consumed
        by the host API; the values are already typed scalars.
        """
        effective = ContextSnapshot(
            handler=snapshot.handler,
            system_prompt=system_prompt if system_prompt is not None else snapshot.system_prompt,
            current_message=snapshot.current_message,
            metadata=dict(snapshot.metadata),
        )
        rows: list[JsonObject] = []
        index = 0
        if effective.system_prompt:
            rows.append({
                "index": index,
                "source": "system_prompt",
                "type": "system",
                "length": len(effective.system_prompt),
                "persisted": False,
            })
            index += 1
        for block in self.blocks(effective):
            message = block.message
            content = message.content if message is not None else block.content
            rows.append({
                "index": index,
                "source": block.source,
                "type": block.role,
                "length": len(content or ""),
                "position": block.position.name.lower(),
                "position_value": int(block.position),
                "priority": self._priority_overrides.get(block.source, block.priority),
                "default_priority": block.priority,
                "persisted": block.persistent,
            })
            index += 1
        return rows


class HandlerContextSource:
    """Adapter that exposes a context handler as a composer source."""

    source_id = "context_handler"

    def __init__(self, handler: HandlerBlockSource) -> None:
        self.handler = handler

    def build_blocks(self, snapshot: ContextSnapshot) -> Sequence[ContextBlock]:
        """Render the handler's durable context without its system prompt."""
        messages = self.handler.build_messages(system_prompt=None)
        return [
            ContextBlock(
                role=message.role,
                content=message.content or "",
                source=self.source_id,
                position=ContextPosition.PREVIOUS,
                message=message,
            )
            for message in messages
        ]

