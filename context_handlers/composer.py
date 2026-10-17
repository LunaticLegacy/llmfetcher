"""Composable, source-aware context blocks for built-in and plugin providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Protocol, Sequence

from ..llm_types import MessageRole, RequestMessage


class ContextPosition(IntEnum):
    """Canonical position of a block in the assembled request."""

    PERSISTENT = 10
    PREVIOUS = 20
    MEMORY = 30
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
    metadata: dict[str, Any] = field(default_factory=dict)
    message: RequestMessage | None = None


class ContextSource(Protocol):
    """Source contract consumed by :class:`ContextComposer`."""

    source_id: str

    def build_blocks(self, snapshot: ContextSnapshot) -> Sequence[ContextBlock]:
        """Project source state into request blocks."""
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

    handler: Any
    system_prompt: str | None = None
    current_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


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
        providers: Initial providers in declaration order.
    """

    def __init__(self, providers: Sequence[ContextProvider] = ()) -> None:
        """Create a composer with optional initial providers.

        Args:
            providers: Providers to register in declaration order.
        """
        self._providers: list[ContextSource] = list(providers)

    @property
    def providers(self) -> tuple[ContextSource, ...]:
        """Return the currently registered providers in registration order."""
        return tuple(self._providers)

    def register(self, provider: ContextSource) -> None:
        """Register a provider for future requests.

        Args:
            provider: Provider implementing ``provider_id`` and
                ``build_blocks``.

        Raises:
            ValueError: If the provider ID is empty or already registered.
        """
        provider_id = str(getattr(provider, "source_id", getattr(provider, "provider_id", ""))).strip()
        if not provider_id:
            raise ValueError("context provider must define provider_id")
        if any(getattr(item, "source_id", getattr(item, "provider_id", None)) == provider_id for item in self._providers):
            raise ValueError(f"context provider already registered: {provider_id}")
        self._providers.append(provider)

    def blocks(self, snapshot: ContextSnapshot) -> list[ContextBlock]:
        """Collect, filter, and stably sort provider blocks.

        Args:
            snapshot: Request snapshot passed to every provider.

        Returns:
            Enabled, non-empty blocks ordered by priority and declaration
            order.
        """
        result: list[tuple[int, int, ContextBlock]] = []
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
                result.append((int(block.position), block.priority, sequence, block))
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
        return messages

    def describe(
        self,
        *,
        snapshot: ContextSnapshot,
        system_prompt: str | None = None,
    ) -> list[dict[str, Any]]:
        """Describe the exact composed messages with source provenance."""
        effective = ContextSnapshot(
            handler=snapshot.handler,
            system_prompt=system_prompt if system_prompt is not None else snapshot.system_prompt,
            current_message=snapshot.current_message,
            metadata=dict(snapshot.metadata),
        )
        rows: list[dict[str, Any]] = []
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
                "persisted": block.persistent,
            })
            index += 1
        return rows


class HandlerContextSource:
    """Adapter that exposes a context handler as a composer source."""

    source_id = "context_handler"

    def __init__(self, handler: Any) -> None:
        self.handler = handler

    def build_blocks(self, snapshot: ContextSnapshot) -> Sequence[ContextBlock]:
        """Render the handler's durable context without its system prompt."""
        previous = getattr(self.handler, "_composer_source_build", False)
        self.handler._composer_source_build = True
        try:
            messages = self.handler.build_messages(system_prompt=None)
        finally:
            self.handler._composer_source_build = previous
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

