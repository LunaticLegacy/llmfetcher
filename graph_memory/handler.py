"""GraphContextHandler: linear context + graph long-term memory (P2).

Composes :class:`ContextHandlerLinear` for the current session with a
:class:`GraphStore` memory graph fed incrementally by :class:`GraphBuilder`.

- Every ``graph_update_every`` user/assistant messages (or whenever
  compaction happens) the newest turns are flushed into the graph via
  ``builder.ingest`` — incremental, low-overhead entity extraction.
- On the first user message (or again after compaction when
  ``retrieval_trigger="auto"``) :class:`GraphRetriever` runs the hybrid
  four-channel retrieval and injects a ``<graph_memory>`` block as a
  **user-role** message at the front of ``build_messages`` (low-trust
  historical data never overrides system instructions).
- ``save`` additionally writes the graph to ``<path><graph_save_suffix>``;
  ``load`` restores both files and resets the graph when the companion
  file is missing (so stale long-term data never leaks into a fresh
  session).
- ``clear_context`` clears the session (linear history + per-session
  retrieval state) but keeps the long-term graph, matching the design
  trigger table (docs/graph_context_design.md §4.7).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ..context_handlers.base import ContextHandler
from ..context_handlers.linear import CompactionFetcher, ContextHandlerLinear
from ..llm_types import LLMContext, LLMOutput
from .builder import ExtractionFetcher, GraphBuilder
from .graph_store import GraphStore
from .retriever import GraphRetriever, GraphRetrievalResult, RetrievalConfig


class GraphContextHandler(ContextHandler):
    """A context handler with an entity-relation long-term memory graph.

    Args:
        compacting_fetcher: LLMFetcher used for context compaction (same
            protocol as :class:`ContextHandlerLinear`).
        extraction_fetcher: Optional LLM used to extract entities/relations
            from conversation batches. Absent -> deterministic regex
            fallback keeps the graph building offline-safe.
        query_fetcher: Optional LLM used to extract seed entities from the
            retrieval query. Absent -> regex fallback.
        store: Optional pre-existing :class:`GraphStore` (e.g. a long-term
            store loaded from disk). A fresh empty store is created when
            omitted.
        retriever_config: Optional :class:`RetrievalConfig` for the hybrid
            retrieval weights / limits.
        retrieval_trigger: ``"first_message"`` (default), ``"auto"``
            (re-retrieve after compaction), or ``"manual"`` (explicit
            :meth:`retrieve` calls only).
        graph_update_every: Flush the pending messages into the graph after
            this many user/assistant messages (default 3).
        max_context_threshold: Character threshold that triggers linear
            context compaction (forwarded to the linear handler).
        graph_save_suffix: Suffix appended to the context file path when
            persisting the graph (default ``".graph.json"``).
    """

    def __init__(
        self,
        *,
        compacting_fetcher: CompactionFetcher,
        extraction_fetcher: Optional[ExtractionFetcher] = None,
        query_fetcher: Optional[ExtractionFetcher] = None,
        store: Optional[GraphStore] = None,
        retriever_config: Optional[RetrievalConfig] = None,
        retrieval_trigger: str = "first_message",
        graph_update_every: int = 3,
        max_context_threshold: int = 262144,
        graph_save_suffix: str = ".graph.json",
    ) -> None:
        super().__init__()
        self.linear = ContextHandlerLinear(
            compacting_fetcher,
            max_context_threshold=max_context_threshold,
        )
        self.store = store if store is not None else GraphStore()
        self.builder = GraphBuilder(self.store, fetcher=extraction_fetcher)
        self.retriever = GraphRetriever(
            self.store,
            query_fetcher=query_fetcher,
            config=retriever_config,
        )
        self.retrieval_trigger = retrieval_trigger
        self.graph_update_every = max(1, graph_update_every)
        self.graph_save_suffix = graph_save_suffix
        self._init_session_state()

    # -- session state -----------------------------------------------------

    def _init_session_state(self) -> None:
        """(Re)set all per-session transient state (keeps long-term graph)."""
        self._graph_memory: str = ""                 # last rendered block
        self._has_retrieved = False
        self._message_count = 0
        self._compaction_generation = 0              # incremented on compact()
        self._last_retrieved_gen = 0
        self._pending: list[LLMContext] = []         # messages awaiting ingest

    @property
    def has_retrieved(self) -> bool:
        """True once a retrieval has been performed this session."""
        return self._has_retrieved

    @property
    def graph_memory(self) -> str:
        """Last rendered ``<graph_memory>`` block (empty when none)."""
        return self._graph_memory

    @property
    def compaction_generation(self) -> int:
        """Number of compactions observed since the session started."""
        return self._compaction_generation

    @property
    def compress_threshold(self) -> int:
        """Compaction threshold forwarded from the inner linear handler.

        Kept so external code (e.g. ``Agent.context_handler.
        compress_threshold``) keeps working when this handler replaces
        :class:`ContextHandlerLinear` as a drop-in.
        """
        return self.linear.compress_threshold

    # -- public API --------------------------------------------------------

    def retrieve(self, query: str) -> GraphRetrievalResult:
        """Run hybrid graph retrieval and store the rendered context block.

        The block is injected at the front of ``build_messages`` until the
        next retrieval. ``current_timeline`` is the linear round counter so
        recency weighting stays consistent with the conversation.
        """
        result = self.retriever.retrieve(
            query, current_timeline=self.linear._round,
        )
        self._graph_memory = result.rendered or ""
        self._has_retrieved = True
        self._last_retrieved_gen = self._compaction_generation
        return result

    # -- ContextHandler interface -------------------------------------------

    def add_user_message(self, message: str) -> None:
        """Append a user message and trigger retrieval when due."""
        timeline = self.linear._round + 1
        self._pending.append(LLMContext(
            role="user", timeline=timeline, content=message,
        ))
        self.linear.add_user_message(message)
        self._message_count += 1
        if self._should_retrieve():
            self.retrieve(message)

    def add_assistant_message(
        self,
        message: LLMOutput,
        tool_results: Optional[dict[str, str]] = None,
    ) -> None:
        """Append an assistant output, detect compaction and flush the graph."""
        # Snapshot before the linear handler may compact the history.
        prev = (len(self.linear.messages), self.linear.abstract is not None)
        timeline = self.linear._round + 1
        self._pending.append(LLMContext(
            role=message.role,
            timeline=timeline,
            content=message.content or "",
            content_reasoning=message.reasoning_content or "",
        ))
        self.linear.add_assistant_message(message, tool_results)
        now = (len(self.linear.messages), self.linear.abstract is not None)
        compacted = prev[0] > 0 and now[0] == 0 and now[1]
        if compacted:
            self._compaction_generation += 1
        if compacted or len(self._pending) >= self.graph_update_every:
            self._flush_pending()

    def build_messages(self) -> list[dict[str, Any]]:
        """Build messages: graph memory block (user), then linear history."""
        messages: list[dict[str, Any]] = []
        if self._graph_memory:
            messages.append({"role": "user", "content": self._graph_memory})
        messages.extend(self.linear.build_messages())
        return messages

    def save(self, path: str | Path) -> bool:
        """Save the conversation AND the companion graph file.

        Returns:
            ``True`` only when both the linear context and the graph were
            persisted successfully.
        """
        saved = self.linear.save(path)
        graph_saved = self.store.save(f"{path}{self.graph_save_suffix}")
        return saved and graph_saved

    def load(self, path: str | Path) -> bool:
        """Restore the conversation and its companion graph.

        When the graph file is missing (e.g. an old context file written by
        a linear-only handler), the in-memory graph is reset so stale
        long-term data never mixes with the restored session.
        """
        loaded = self.linear.load(path)
        graph_path = f"{path}{self.graph_save_suffix}"
        if loaded and not self.store.load(graph_path):
            # Old context file written by a linear-only handler: reset the
            # graph so stale long-term data never mixes with this session.
            self.store.clear()
        self._init_session_state()
        if loaded and self.linear.abstract is not None:
            # A restored context that was already compacted counts as one
            # generation so ``auto`` re-retrieval behaves consistently.
            self._compaction_generation = 1
        return loaded

    def clear_context(self) -> bool:
        """Clear the session but keep the long-term memory graph."""
        result = self.linear.clear_context()
        self._init_session_state()
        return result

    # -- internal helpers --------------------------------------------------

    def _should_retrieve(self) -> bool:
        """Decide whether this user message should trigger retrieval."""
        if self.retrieval_trigger == "manual":
            return False
        if self._has_retrieved:
            if self.retrieval_trigger == "auto":
                return self._compaction_generation > self._last_retrieved_gen
            return False
        return self._message_count >= 1

    def _flush_pending(self) -> None:
        """Ingest buffered messages into the graph and clear the buffer."""
        if not self._pending:
            return
        self.builder.ingest(self._pending)
        self._pending = []
