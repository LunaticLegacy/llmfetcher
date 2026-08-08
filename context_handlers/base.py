from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..llm_types import LLMOutput, TokenUsage


class ContextHandler(ABC):
    """Manages conversational context and builds API-ready message lists.

    Subclasses decide how context is stored, summarised, or compacted;
    ``build_messages`` serialises the stored state into the message format
    expected by ``LLMFetcher.fetch`` / ``fetch_stream``.
    """

    def __init__(self) -> None:
        """Initialize the base context handler with a usage counter.

        ``extra_usage`` accumulates token usage from internal LLM calls that
        are not part of the main agent round loop (context compaction, graph
        extraction, retrieval seed extraction). ``Agent.run`` merges this
        counter into the agent's reported usage so hidden costs become
        visible.
        """
        self._extra_usage: TokenUsage = TokenUsage()

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

    @abstractmethod
    def add_user_message(
        self,
        message: str,
    ) -> None:
        """
        Append an User input to conversation history.

        Args:
            message: The original user input.
        """

    @abstractmethod
    def add_assistant_message(
        self,
        message: LLMOutput,
        tool_results: Optional[Dict[str, str]] = None,
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
        """

    @abstractmethod
    def build_messages(self) -> List[Dict[str, Any]]:
        """Build context messages for an LLM request.

        Returns the stored conversation history (excluding system prompt
        and the current user message) as a list of API-compatible dicts.
        The caller (``LLMFetcher``) is responsible for prepending the
        system prompt and appending the current user message.

        Returns:
            A list of message dicts (``{"role": ..., "content": ...}``),
            with ``tool_calls`` embedded where applicable.
        """

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
