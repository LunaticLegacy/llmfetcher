from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from pathlib import Path
import threading

from ..llm_types import LLMOutput, RequestMessage, TokenUsage
from ..multimodal import UserMessage
from .composer import (
    ContextBlock,
    ContextPosition,
    ContextSnapshot,
)

TOOL_RESULT_OMITTED_PLACEHOLDER = (
    "[Earlier tool result omitted from the active context. "
    "Use the stored artifact reference or artifact_read if needed.]"
)

if TYPE_CHECKING:
    from ..execution.control import ExecutionController


_CHECKPOINT_LOCKS: dict[str, threading.RLock] = {}
_CHECKPOINT_LOCKS_GUARD = threading.Lock()


def checkpoint_lock(path: str | Path) -> threading.RLock:
    """Return the process-local lock shared by all writers of one checkpoint."""
    key = str(Path(path).resolve())
    with _CHECKPOINT_LOCKS_GUARD:
        lock = _CHECKPOINT_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _CHECKPOINT_LOCKS[key] = lock
        return lock


class ContextHandler(ABC):
    """Manages conversational state and exposes it as a context source.

    Subclasses decide how context is stored, summarised, or compacted;
    ``build_blocks`` projects that state into semantic blocks. The legacy
    ``build_messages`` method still serialises a complete request for direct
    callers, while ``ContextComposer`` owns cross-source ordering.
    """

    source_id = "context_handler"

    def __init__(self) -> None:
        """Initialize the base context handler with a usage counter.

        ``extra_usage`` accumulates token usage from internal LLM calls that
        are not part of the main agent round loop (context compaction, graph
        extraction, retrieval seed extraction). ``Agent.run`` merges this
        counter into the agent's reported usage so hidden costs become
        visible.
        """
        self._extra_usage: TokenUsage = TokenUsage()
        # ``save`` remains a boolean compatibility API, but callers need the
        # original OS/serialization failure to diagnose a rejected checkpoint.
        # This is transient diagnostic state and is never persisted alongside
        # conversation content.
        self.last_save_error: Exception | None = None
        self._composer_source_build = False
        self.tool_result_context_limit = 0

    def limit_tool_result_messages(
        self,
        messages: List[RequestMessage],
    ) -> List[RequestMessage]:
        """Replace older tool results for the active model request only.

        Durable context remains untouched; this projection is applied after
        the handler and plugin providers have produced request messages.
        """
        limit = int(getattr(self, "tool_result_context_limit", 0) or 0)
        if limit <= 0:
            return messages
        tool_indexes = [
            index for index, message in enumerate(messages)
            if message.role == "tool" and message.tool_call_id is not None
        ]
        keep = set(tool_indexes[-limit:])
        return [
            message if index in keep or index not in tool_indexes else RequestMessage(
                role="tool",
                content=TOOL_RESULT_OMITTED_PLACEHOLDER,
                tool_call_id=message.tool_call_id,
            )
            for index, message in enumerate(messages)
        ]

    def build_blocks(self, snapshot: ContextSnapshot) -> list[ContextBlock]:
        """Expose durable handler state as a Composer-owned context source.

        The legacy ``build_messages`` method remains the serialization
        implementation, while the Composer controls where these messages
        appear relative to other sources.
        """
        previous = self._composer_source_build
        self._composer_source_build = True
        try:
            messages = self.build_messages(system_prompt=None)
        finally:
            self._composer_source_build = previous
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

    @property
    def extra_usage(self) -> TokenUsage:
        """Token usage accumulated by internal (non-round) LLM calls.

        Subclasses that aggregate usage from multiple internal components
        (e.g. graph builder + retriever + linear compaction) may override
        this property.
        """
        return self._extra_usage

    def record_usage(self, usage: Optional[TokenUsage]) -> None:
        """Accumulate one internal LLM call's usage into ``extra_usage``.

        Args:
            usage: Token usage from an internal (non-round) LLM call, or
                ``None`` when the call provided no usage.
        """
        if usage is None:
            return
        self._extra_usage.input_tokens += usage.input_tokens or 0
        self._extra_usage.output_tokens += usage.output_tokens or 0
        self._extra_usage.total_tokens += usage.total_tokens or 0
        self._extra_usage.cached_tokens += usage.cached_tokens or 0
        self._extra_usage.reasoning_tokens += usage.reasoning_tokens or 0

    def compact(
        self,
        *,
        controller: "ExecutionController | None" = None,
        keep_recent: "int | None" = None,
    ) -> bool:
        """Compact this handler through its linear context implementation.

        Composed handlers may override this hook to flush their own indexes
        after the linear compaction succeeds. Keeping the operation on the
        context-handler interface lets automatic and manual compaction share
        the same implementation and cancellation contract.

        Args:
            controller: Optional cancellation source for the compaction call.
            keep_recent: Number of newest active entries to keep verbatim
                instead of summarising them; ``None`` uses the handler's
                configured default and ``0`` summarises the whole active
                transcript.
        """
        linear = getattr(self, "linear", None)
        if linear is None or linear is self:
            raise NotImplementedError("context handler does not support compaction")
        return bool(linear.compact(controller=controller, keep_recent=keep_recent))

    @abstractmethod
    def add_user_message(
        self,
        message: "str | UserMessage",
    ) -> None:
        """
        Append an User input to conversation history.

        Args:
            message: The original user input. Either plain text or a
                :class:`~llmfetcher.multimodal.UserMessage` carrying image
                references; implementations preserve references when present.
        """

    @abstractmethod
    def add_assistant_message(
        self,
        message: LLMOutput,
        tool_results: Optional[Dict[str, str]] = None,
        *,
        usage: Optional[Dict[str, int]] = None,
        model_duration_ms: Optional[int] = None,
        round_duration_ms: Optional[int] = None,
        created_at: Optional[float] = None,
        controller: "ExecutionController | None" = None,
    ) -> None:
        """Record an LLM response into the conversation history.

        Args:
            message: The output produced by the LLM (includes content,
                     tool calls, usage, etc.).
            tool_results:
                Mapping from ``call_id`` to execution result text.
                When provided, each tool call in *message* is paired
                with its result so that future ``build_messages`` calls
                can emit the ``{"role": "tool", ...}`` feedback turn.
            usage: Primary model-call token usage for this durable turn.
            model_duration_ms: Wall time spent generating this model output.
            round_duration_ms: Whole round wall time, including tools.
            created_at: Unix timestamp when this response completed.
        """

    @abstractmethod
    def build_messages(
        self,
        *,
        system_prompt: str | None = None,
    ) -> List[RequestMessage]:
        """Build context messages for an LLM request.

        Return the complete provider-neutral request context. Context
        handlers own semantic message composition, including the optional
        system prompt and memory projection.
        The caller is responsible only for provider transport and wire
        adaptation after this semantic projection is returned.

        Returns:
            A complete provider-neutral request message sequence.
        """

    def describe_request_messages(
        self,
        messages: List[RequestMessage],
    ) -> list[dict[str, Any]]:
        """Describe the origin of messages in a request preview.

        The message payload remains the exact provider-neutral request. This
        companion projection gives hosts a stable way to explain which part
        came from a context handler without changing provider wire data.
        """
        result: list[dict[str, Any]] = []
        for index, message in enumerate(messages):
            if message.role == "system":
                source = "system_prompt"
            elif index == len(messages) - 1 and message.role == "user" and not message.content:
                source = "hypothetical_input"
            else:
                source = f"{self.__class__.__name__}:context"
            result.append({
                "index": index,
                "role": message.role,
                "source": source,
                "persisted": source.endswith(":context"),
            })
        return result

    @abstractmethod
    def save(self, path: str | Path) -> bool:
        """
        Save context from disk.

        Args:
            path: The path of saving the file.

        Returns:
            A boolean for indicate whether successfully saved or not.
        """

    @abstractmethod
    def load(self, path: str | Path) -> bool:
        """
        Load context from disk.

        Args:
            path: Path to file.

        Returns:
            A boolean for indicate whether successfully loaded or not.
        """

    @abstractmethod
    def clear_context(self) -> bool:
        """
        Clear context.
        
        Returns:
            A boolean for indicate whether successfully clear or not.
        """

