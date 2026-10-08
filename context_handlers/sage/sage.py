"""``SageContext``: a context handler whose history is indexed as context trees.

Sage's intent is that a session's context involves *a set of context trees*
for previous information, and that the Agent maintains them.  This first cut
keeps those trees as an index over one durable transcript: ``build_messages``
renders the whole active history, so behaviour matches
:class:`~llmfetcher.context_handlers.linear.ContextHandlerLinear`.  Durable
rows, compaction, paging and usage accounting are delegated to a composed
linear handler; only the indexing structure is Sage-specific.

Converging the trees after a compaction (which branch survives, what the
abstract replaces) is therefore still linear: the index is rebuilt from the
compacted transcript.  Changing that is a ``build_messages`` policy decision
layered on top of this structure, not a change to persistence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, override

from ..base import ContextHandler
from ..linear import CompactionFetcher, ContextHandlerLinear
from ..storage import ContextStorage
from ...execution.control import ExecutionController
from ...llm_types import LLMContext, LLMContextCompacted, LLMOutput, TokenUsage
from ...multimodal import UserMessage
from ...usage_ledger import UsageRecord
from .tree import ContextTree


class SageContext(ContextHandler):
    """Index a composed linear transcript as a set of context trees.

    Args:
        compacting_fetcher: LLMFetcher used for context compaction (same
            protocol as :class:`ContextHandlerLinear`).
        max_context_threshold: Character threshold that triggers compaction.
        compaction_output_max_tokens: Completion-token budget for one
            compactor summary request.
        storage: Optional durable row store for the composed linear handler;
            defaults to its SQLite implementation.
    """

    def __init__(
        self,
        compacting_fetcher: CompactionFetcher,
        max_context_threshold: int = 262144,
        compaction_output_max_tokens: int = 8192,
        *,
        storage: ContextStorage | None = None,
    ) -> None:
        super().__init__()
        # Durable rows, compaction, paging and the timeline counter all belong
        # to the composed handler, so Sage inherits that behaviour instead of
        # re-implementing persistence.
        self.linear = ContextHandlerLinear(
            compacting_fetcher,
            max_context_threshold=max_context_threshold,
            compaction_output_max_tokens=compaction_output_max_tokens,
            storage=storage,
        )
        # The tree indexes the composed handler's active transcript.  Its
        # entries are the same objects ``get_prev_messages`` returns, so the
        # index cannot disagree with what a request would render.
        self.tree = ContextTree()

    # -- ContextHandler interface -------------------------------------------

    @override
    def add_user_message(self, message: "str | UserMessage") -> None:
        """Append a user input and index it in the tree.

        Args:
            message: The original user input, plain text or a
                :class:`~llmfetcher.multimodal.UserMessage`.
        """
        previous_length = len(self.linear.messages)
        self.linear.add_user_message(message)
        self._index_appended(previous_length)

    @override
    def add_assistant_message(
        self,
        message: LLMOutput,
        tool_results: Optional[Dict[str, str]] = None,
        *,
        usage: Optional[Dict[str, int]] = None,
        model_duration_ms: Optional[int] = None,
        round_duration_ms: Optional[int] = None,
        created_at: Optional[float] = None,
        controller: ExecutionController | None = None,
    ) -> None:
        """Append an assistant turn and index it in the tree.

        Args:
            message: The output produced by the LLM.
            tool_results: Tool output keyed by provider tool-call ID.
            usage: Primary model-call token usage for this durable turn.
            model_duration_ms: Wall time spent generating this model output.
            round_duration_ms: Whole round wall time, including tools.
            created_at: Unix timestamp when this response completed.
            controller: Optional cancellation source for the compaction this
                call may trigger.
        """
        previous_length = len(self.linear.messages)
        self.linear.add_assistant_message(
            message,
            tool_results,
            usage=usage,
            model_duration_ms=model_duration_ms,
            round_duration_ms=round_duration_ms,
            created_at=created_at,
            controller=controller,
        )
        self._index_appended(previous_length)

    @override
    def build_messages(self) -> List[Dict[str, Any]]:
        """Render the active history exactly as the composed handler does.

        Returns:
            A list of provider-neutral message dicts.
        """
        return self.linear.build_messages()

    @override
    def compact(self, *, controller: ExecutionController | None = None) -> bool:
        """Compact the composed transcript, then re-index what remains.

        Args:
            controller: Optional cancellation source.

        Returns:
            ``True`` when the compaction succeeded and the tree was rebuilt.
        """
        compacted = self.linear.compact(controller=controller)
        if compacted:
            self.tree.rebuild(self.linear.get_prev_messages())
        return compacted

    @override
    def save(
        self,
        path: str | Path,
        *,
        checkpoint_generation: str | None = None,
        graph_checkpoint: str | None = None,
    ) -> bool:
        """Persist the composed checkpoint and mirror its failure cause.

        Args:
            path: Destination file path.
            checkpoint_generation: Optional generation selected by a composing
                handler coordinating multiple durable files.
            graph_checkpoint: Optional companion filename committed by a
                composing handler.

        Returns:
            ``True`` on success, ``False`` on write failure.
        """
        saved = self.linear.save(
            path,
            checkpoint_generation=checkpoint_generation,
            graph_checkpoint=graph_checkpoint,
        )
        # ``Agent`` reads ``last_save_error`` off the handler it holds, so the
        # composed handler's cause has to be visible here too.
        self.last_save_error = self.linear.last_save_error
        return saved

    @override
    def load(self, path: Optional[str | Path]) -> bool:
        """Restore the composed checkpoint and rebuild the tree index.

        Args:
            path: Source file path.

        Returns:
            ``True`` on success; retained state is left untouched on failure.
        """
        loaded = self.linear.load(path)
        if loaded:
            self.tree.rebuild(self.linear.get_prev_messages())
        return loaded

    @override
    def clear_context(self) -> bool:
        """Clear the transcript, the timeline and the tree index.

        Returns:
            ``True`` once the composed handler has reset.
        """
        cleared = bool(self.linear.clear_context())
        self.tree.clear()
        return cleared

    # -- composed surface ---------------------------------------------------

    def replace_active_context(
        self,
        messages: list[Dict[str, Any]],
        *,
        database: Path,
        context_editing: Dict[str, object] | None = None,
    ) -> int:
        """Atomically replace the active transcript and re-index the tree.

        Context editing (the ``*_agent_context`` tools) rewrites the whole
        active window instead of appending, so the index is rebuilt from the
        replacement rows rather than extended.

        Args:
            messages: Serialized active entries in the new display order.
            database: Durable sidecar database for this context pointer.
            context_editing: Optional editing metadata to record.

        Returns:
            The new timeline high-water mark.
        """
        high_water = self.linear.replace_active_context(
            messages,
            database=database,
            context_editing=context_editing,
        )
        self.tree.rebuild(self.linear.get_prev_messages())
        return high_water

    def get_prev_messages(self) -> List[LLMContext | LLMContextCompacted]:
        """Return the composed handler's stored history, abstract first."""
        return self.linear.get_prev_messages()

    def set_compaction_event_hook(self, hook: Any) -> None:
        """Forward the compaction lifecycle observer to the composed handler.

        Args:
            hook: ``(event_type, message, data)`` observer, or ``None``.
        """
        self.linear.set_compaction_event_hook(hook)

    @property
    def extra_usage(self) -> TokenUsage:
        """Token usage accumulated by the composed handler's hidden LLM calls."""
        return self.linear.extra_usage

    @override
    def record_usage(self, usage: Optional[TokenUsage]) -> None:
        """Forward one internal LLM call's usage to the composed handler.

        Args:
            usage: Usage from an internal (non-round) LLM call.
        """
        self.linear.record_usage(usage)

    def drain_usage_records(self) -> list[UsageRecord]:
        """Drain the composed handler's internal-call usage records once."""
        return self.linear.drain_usage_records()

    # -- tree maintenance ---------------------------------------------------

    def _index_appended(self, previous_length: int) -> None:
        """Index whatever the composed handler appended to its transcript.

        A pure append adds exactly one entry, so it extends the chain.  A
        compaction collapses the active transcript instead, so the whole index
        is rebuilt from the new active history.

        Args:
            previous_length: Length of ``linear.messages`` before delegating.
        """
        if len(self.linear.messages) == previous_length + 1:
            self.tree.append(self.linear.messages[-1])
        else:
            self.tree.rebuild(self.linear.get_prev_messages())


__all__ = ["SageContext"]
