"""``ContextHandlerLinear``: a durable flat transcript with compaction.

History is kept verbatim until compaction is triggered (by exceeding
``max_context_threshold``), at which point active messages are replaced with a
single compacted abstract (``LLMContextCompacted``). The raw messages are
retained in ``archive`` as an append-only persistence record.

This module owns only the stateful orchestration. Serialization lives in
``codec.py``, compaction planning in ``compaction.py``, message rendering in
``rendering.py``, durable row access in ``storage.py`` and bounded paging in
``paging.py``.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, override

from ..base import ContextHandler
from ..storage import ContextStorage, SQLiteContextStorage
from ...llm_types import (
    LLMContext,
    LLMContextCompacted,
    LLMOutput,
    TokenUsage,
    ToolInfo,
)
from ...multimodal import UserMessage, ImageToolResult, validate_images
from ...usage_ledger import UsageRecord, copy_usage, drain_records
from ...execution.control import ExecutionController
from .codec import (
    compacted_from_dict,
    compacted_to_dict,
    context_from_dict,
    context_to_dict,
)
from .compaction import (
    _COMPACTION_INPUT_CHAR_LIMIT,
    _COMPACTION_OUTPUT_MAX_TOKENS,
    CompactionFetcher,
    CompactionRequestPreview,
    build_request_preview,
    estimate_context_size,
    parse_compacted_abstract,
)
from .rendering import render_messages


class ContextHandlerLinear(ContextHandler):
    """A simple context handler that stores messages in a flat list.

    History is kept verbatim until compaction is triggered (by exceeding
    *max_context_threshold*), at which point active messages are replaced
    with a single compacted abstract (``LLMContextCompacted``).  The raw
    messages are retained in ``archive`` as an append-only persistence
    record; they are deliberately not sent on normal model requests.

    Timeline (round counter) is managed internally as ``_round``,
    monotonically increasing on every ``add_user_message`` /
    ``add_assistant_message`` call.
    """

    def __init__(
        self,
        compacting_llmfetcher_handler: CompactionFetcher,
        max_context_threshold: int = 262144,
        compaction_input_char_limit: int = _COMPACTION_INPUT_CHAR_LIMIT,
        compaction_output_max_tokens: int = _COMPACTION_OUTPUT_MAX_TOKENS,
        event_hook: Optional[Callable[[str, str, dict], None]] = None,
        storage: ContextStorage | None = None,
        keep_recent: int = 0,
    ) -> None:
        """
        Initiate the context handler.

        Args:
            compacting_llm_handler:
                Instance of LLMFetcher for compacting.
            max_context_threshold:
                When the length of context exceeded this number, compact it.
            compaction_input_char_limit:
                Maximum transcript size sent to the standalone compactor.
            compaction_output_max_tokens:
                Maximum generated tokens requested from the compactor.
            event_hook:
                Optional observer invoked synchronously with
                ``(event_type, message, data)`` for each compaction lifecycle
                stage (started / success / failed / skipped). A raising hook
                is isolated so a broken observer never breaks compaction.
            storage:
                Durable row store; defaults to the SQLite implementation.
            keep_recent:
                Default number of newest active entries compaction keeps
                verbatim instead of summarising. ``0`` summarises the whole
                active transcript. Overridable per call through
                :meth:`compact`.

        Raises:
            ValueError: If either compaction budget is not positive.
        """
        super().__init__()

        self.llm_handler = compacting_llmfetcher_handler
        self.storage: ContextStorage = storage or SQLiteContextStorage()
        self.compress_threshold: int = max_context_threshold
        if compaction_input_char_limit <= 0 or compaction_output_max_tokens <= 0:
            raise ValueError("compaction budgets must be greater than zero")
        self.compaction_input_char_limit = compaction_input_char_limit
        self.compaction_output_max_tokens = compaction_output_max_tokens
        self.keep_recent = max(0, int(keep_recent))

        self.abstract: Optional[LLMContextCompacted] = None
        self.messages: List[LLMContext] = []
        # Raw messages which have left the active model context through a
        # successful compaction.  This is a durable source record for future
        # retrieval / re-compaction, not another prompt buffer.
        self.archive: List[LLMContext] = []
        # Forward-compatible checkpoint metadata survives ordinary Agent
        # load/save cycles so context editing and graph commit state are not
        # silently discarded by the linear serializer.
        self.checkpoint_generation: str | None = None
        self.graph_checkpoint: str | None = None
        self.context_editing: dict[str, object] = {}
        self._usage_records: list[UsageRecord] = []
        # These diagnostics are intentionally transient: applications can
        # report the failed compaction attempt without persisting raw model
        # output in the durable conversation file.
        self.last_compaction_error: Optional[str] = None
        self.last_compaction_raw: Optional[str] = None

        # Optional compaction lifecycle observer (event_type, message, data).
        self.event_hook: Optional[Callable[[str, str, dict], None]] = event_hook

        # Internal round counter — timeline for every added message.
        self._round: int = 0
        # Set by a successful compaction so the next build_messages() appends
        # a derived resume user turn (never stored, never persisted).
        self._pending_resume: bool = False
        # SQLite checkpoint high-water marks mean ordinary saves append only
        # newly created timeline rows instead of rewriting the transcript.
        self._storage_message_high_water = 0
        self._storage_archive_high_water = 0

    # -- public API ---------------------------------------------------------
    # System prompt should NOT be included in this context manager.

    @override
    def clear_context(self):
        """Clear all conversation entries and restart timeline numbering.

        Returns:
            ``True`` after the in-memory context and round counter are reset.
        """
        self.abstract = None
        self.messages = []
        self.archive = []
        self._round = 0
        self._pending_resume = False
        self._usage_records.clear()
        self._storage_message_high_water = 0
        self._storage_archive_high_water = 0
        return True

    def drain_usage_records(self) -> list[UsageRecord]:
        """Return completed internal-call usage records exactly once."""
        return drain_records(self._usage_records)


    def set_compaction_event_hook(
        self,
        hook: Optional[Callable[[str, str, dict], None]],
    ) -> None:
        """Attach or detach the compaction lifecycle event observer.

        The hook receives ``(event_type, message, data)`` synchronously for
        every compaction stage (:data:`context:compact_started`,
        ``context:compact_success``, ``context:compact_failed`` or
        ``context:compact_skipped``). Passing ``None`` detaches it. A raising
        hook is isolated by :meth:`_emit_compaction_event`, so a broken
        observer can never corrupt or conceal a compaction attempt.
        """
        self.event_hook = hook

    def _emit_compaction_event(
        self,
        event_type: str,
        message: str,
        data: Dict[str, Any],
    ) -> None:
        """Notify the attached observer, isolating any observer failure.

        Args:
            event_type: Machine-readable compaction lifecycle event name.
            message: Human-readable compaction status description.
            data: Structured payload for the browser (round, sizes, ratios).
        """
        hook = self.event_hook
        if hook is None:
            return
        try:
            hook(event_type, message, data)
        except Exception:
            # A broken observer must not conceal or corrupt the compaction.
            pass


    @override
    def add_user_message(
        self,
        message: "str | UserMessage",
    ) -> None:
        """
        Append an User input to conversation history.

        The timeline is assigned automatically from the internal
        round counter (``_round``).

        Args:
            message: The original user input; a
                :class:`~llmfetcher.multimodal.UserMessage` also carries
                durable image references that are preserved verbatim.
        """
        self._round += 1
        self.messages.append(LLMContext(
            role="user",
            timeline=self._round,
            content=str(message),
            images=validate_images(message.images) if isinstance(message, UserMessage) else [],
        ))
        # A real user turn supersedes any derived resume prompt left by a
        # previous compaction.
        self._pending_resume = False

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
        """Append an LLM output to the conversation history.

        Each tool call in *message* is paired with its result from
        *tool_results* (keyed by ``call_id``).

        After appending, triggers compaction if the estimated context
        size exceeds ``compress_threshold``.

        Args:
            mesages: The original LLMOutput provided by LLMFetcher.
            tool_results: Tool execution result of this round's llm call.
        """
        self._round += 1
        bounded_tool_results = self._bounded_tool_results(tool_results)
        tool_calls: List[ToolInfo] = []
        for index, tc in enumerate(message.tool_calls):
            call_id = tc.call_id or f"call_{index}"
            result = bounded_tool_results.get(call_id) if bounded_tool_results else None
            tool_calls.append(ToolInfo(
                call=tc, result=str(result) if result is not None else None,
                images=validate_images(result.images) if isinstance(result, ImageToolResult) else [],
            ))

        self.messages.append(LLMContext(
            role=message.role,
            timeline=self._round,
            content=message.content,
            content_reasoning=message.reasoning_content,
            tool_calls=tool_calls,
            usage=dict(usage or {}),
            model_duration_ms=model_duration_ms,
            round_duration_ms=round_duration_ms,
            created_at=created_at,
        ))

        # Auto-trigger compaction when context exceeds threshold.
        context_size: int = self._estimate_context_size()
        if context_size > self.compress_threshold:
            self.compact(controller=controller)

    def compact(
        self,
        *,
        controller: ExecutionController | None = None,
        keep_recent: int | None = None,
    ) -> bool:
        """Compress the conversation history into a single abstract.

        Sends the current messages to the LLM with the compaction
        schema prompt, parses the response, and replaces the summarised
        messages with the compacted ``LLMContextCompacted`` (stored in
        ``self.abstract``).

        Args:
            controller: Optional cancellation source for the compactor call.
            keep_recent: Number of newest active entries to keep verbatim
                instead of summarising them; ``None`` uses this handler's
                configured default. Retained entries stay in the active
                transcript and are excluded from the abstract's
                ``source_timeline``. ``0`` archives the whole active
                transcript (the original behaviour), and so does any value at
                or above its length, because at least one entry is always
                summarised.

        Returns:
            ``True`` on successful compaction, ``False`` otherwise
            (e.g. no messages to compact, or the LLM call / parsing
            failed). On failure, ``last_compaction_error`` describes the
            reason and ``last_compaction_raw`` retains an unparseable model
            content response for the current process only.
        """
        if not self.messages:
            self.last_compaction_error = "No active messages are available to compact."
            self.last_compaction_raw = None
            self._emit_compaction_event(
                "context:compact_skipped",
                f"Context compaction skipped (round {self._round}): no active messages",
                {"round": self._round, "reason": self.last_compaction_error},
            )
            return False

        # Clear stale diagnostics before every independent compaction attempt.
        self.last_compaction_error = None
        self.last_compaction_raw = None
        started_at = time.time()
        round_index = self._round

        # Retaining a verbatim tail moves the summarise/archive boundary: only
        # the entries before it are summarised and archived, so the newest
        # turns stay intact in the active transcript.  At least one entry is
        # always summarised, otherwise compaction would report success while
        # archiving nothing and the next round would compact again forever.
        policy = self.keep_recent if keep_recent is None else int(keep_recent)
        keep = max(0, min(policy, len(self.messages) - 1))
        boundary = len(self.messages) - keep
        archived_messages = self.messages[:boundary]
        retained_messages = self.messages[boundary:]

        # Provenance is owned by the context handler, never by the model.
        # The next abstract includes the preceding abstract in its prompt, so
        # retain its full source range plus the timelines this abstract
        # actually replaces; a retained tail is not part of that range.
        source_timelines: List[int] = []
        if self.abstract is not None:
            source_timelines.extend(self.abstract.source_timeline)
        source_timelines.extend(m.timeline for m in archived_messages)

        request_preview = self.compaction_request_preview()
        compaction_input = request_preview.text
        context_size = self._estimate_context_size()
        self._emit_compaction_event(
            "context:compact_started",
            f"Context compaction started (round {round_index})",
            {
                "round": round_index,
                "context_size": context_size,
                "compaction_input_characters": len(compaction_input),
                "compress_threshold": self.compress_threshold,
                "ratio": round(
                    100.0 * context_size / self.compress_threshold, 1
                ) if self.compress_threshold else 0.0,
            },
        )
        try:
            stream_usage = TokenUsage()
            chunks: list[str] = []
            for chunk in self.llm_handler.fetch_stream(
                msg=request_preview.text,
                system_prompt=request_preview.system_prompt,
                temperature=request_preview.temperature,
                max_tokens=request_preview.max_tokens,
                context_handler=None,
                usage_sink=stream_usage,
                controller=controller,
            ):
                chunks.append(chunk)
                self._emit_compaction_event(
                    "context:compact_delta",
                    "Context compaction model output",
                    {"round": round_index, "channel": "content", "delta": chunk},
                )
            result = LLMOutput(
                content="".join(chunks),
                provider=self.llm_handler.default_backend_config.provider,
                backend_name=self.llm_handler.default_backend_config.name,
                model=self.llm_handler.default_backend_config.model,
                usage=stream_usage,
            )
        except Exception as exc:
            self.last_compaction_error = f"Compaction model request failed: {exc}"
            self._emit_compaction_event(
                "context:compact_failed",
                f"Context compaction failed (round {round_index}): {self.last_compaction_error}",
                {
                    "round": round_index,
                    "error": self.last_compaction_error,
                    "duration_ms": round((time.time() - started_at) * 1000),
                },
            )
            raise
        # Account for the compaction LLM call in the reported usage.
        self.record_usage(result.usage)
        self._usage_records.append(UsageRecord("compaction", copy_usage(result.usage)))
        compacted_raw: str = result.content

        if not compacted_raw.strip():
            self.last_compaction_error = "Compaction model returned an empty content field."
            self._emit_compaction_event(
                "context:compact_failed",
                f"Context compaction failed (round {round_index}): {self.last_compaction_error}",
                {
                    "round": round_index,
                    "error": self.last_compaction_error,
                    "duration_ms": round((time.time() - started_at) * 1000),
                },
            )
            return False

        abstract_msg = parse_compacted_abstract(compacted_raw)
        if not abstract_msg:
            self.last_compaction_error = (
                "Compaction model response did not contain a usable "
                "<context_abstract> element."
            )
            self.last_compaction_raw = compacted_raw
            self._emit_compaction_event(
                "context:compact_failed",
                f"Context compaction failed (round {round_index}): {self.last_compaction_error}",
                {
                    "round": round_index,
                    "error": self.last_compaction_error,
                    "raw_retained": bool(self.last_compaction_raw),
                    "duration_ms": round((time.time() - started_at) * 1000),
                },
            )
            return False

        # Count archived messages from the boundary computed before the
        # compactor ran.
        archived_count = len(archived_messages)
        self.abstract = LLMContextCompacted(
            abstract_msg=abstract_msg,
            source_timeline=source_timelines,
        )
        # Only archive after the compactor response has been parsed.  A
        # failed compaction must leave the active context wholly intact.
        self.archive.extend(archived_messages)
        self.messages = retained_messages

        # Archiving every active message would otherwise leave the next
        # request as system-only (agent prompt + compacted abstract) and some
        # providers return an empty completion for a request with no user turn
        # (rejected as EMPTY_RESPONSE).  Mark the handler so the next
        # build_messages() appends a derived resume user turn - but only when
        # nothing was retained, since a verbatim tail already supplies the
        # user-visible turn.  The resume prompt is intentionally NOT stored in
        # ``messages``: it must not consume a timeline slot, must not be
        # re-archived by a later compaction, and must not be persisted.
        self._pending_resume = not self.messages
        self._emit_compaction_event(
            "context:compact_success",
            f"Context compaction completed (round {round_index}): "
            f"{archived_count} message(s) -> 1 abstract "
            f"({len(retained_messages)} retained)",
            {
                "round": round_index,
                "archived_messages": archived_count,
                "retained_messages": len(retained_messages),
                "abstract_characters": len(abstract_msg),
                "source_timeline": source_timelines,
                "duration_ms": round((time.time() - started_at) * 1000),
            },
        )
        return True

    @override
    def get_prev_messages(self) -> List[LLMContext | LLMContextCompacted]:
        """Return the stored conversation history."""
        result: List[LLMContext | LLMContextCompacted] = list(self.messages)
        if self.abstract is not None:
            result.insert(0, self.abstract)
        return result

    @override
    def build_messages(self) -> List[Dict[str, Any]]:
        """Build context messages for an LLM request.

        Returns stored conversation history only — the caller
        (``LLMFetcher``) prepends the system prompt and appends the
        current user message.

        Returns:
            A list of message dicts, with tool calls and the derived
            post-compaction resume turn included where applicable.
        """
        return render_messages(
            self.get_prev_messages(),
            pending_resume=self._pending_resume,
        )

    # -- compaction helpers ------------------------------------------------

    def _estimate_context_size(self) -> int:
        """Estimate the serialized size of this handler's next request.

        Measures the messages :meth:`build_messages` would send, so trimming
        is reflected and one oversized tool result cannot inflate the estimate
        beyond what the model would actually receive.

        Returns:
            Total serialized character length of the next request messages.
        """
        return estimate_context_size(self.build_messages())

    def _bounded_tool_results(
        self,
        tool_results: Optional[Dict[str, str]],
    ) -> Dict[str, str]:
        """Copy complete tool output into the in-memory conversation history.

        Tool calls may return complete HTML pages, archives, or command output.
        The host can persist a large output and pass a stable reference here;
        this handler does not apply a second limit or mutate that reference.

        Args:
            tool_results: Raw tool output keyed by provider tool-call ID.

        Returns:
            A copied mapping containing every complete tool result.
        """
        if not tool_results:
            return {}
        return {call_id: raw_value if isinstance(raw_value, ImageToolResult) else str(raw_value)
                for call_id, raw_value in tool_results.items()}

    def compaction_request_preview(self) -> CompactionRequestPreview:
        """Build the exact compaction request parameters without sending them.

        Returns:
            Bounded input text and the fixed model parameters that
            :meth:`compact` would use for its next provider request.
        """
        return build_request_preview(
            self.build_messages(),
            input_char_limit=self.compaction_input_char_limit,
            output_max_tokens=self.compaction_output_max_tokens,
            threshold=self.compress_threshold,
            round=self._round,
        )

    def _build_compaction_input(self) -> str:
        """Render the bounded transcript one summary request would carry.

        Returns:
            The exact compaction user-message text for this handler's state.
        """
        return self.compaction_request_preview().text

    # -- persistence -------------------------------------------------------

    @override
    def save(
        self,
        path: str | Path,
        *,
        checkpoint_generation: str | None = None,
        graph_checkpoint: str | None = None,
    ) -> bool:
        """Persist metadata plus only newly-created transcript rows.

        Args:
            path: Destination file path.
            checkpoint_generation: Optional generation selected by a composed
                handler coordinating multiple durable files.
            graph_checkpoint: Optional immutable graph filename committed by
                a composed graph handler.

        Returns:
            ``True`` on success, ``False`` on write failure.
        """
        if not path:
            self.last_save_error = ValueError("context checkpoint path is required")
            return False

        try:
            self.last_save_error = None
            generation = checkpoint_generation or uuid.uuid4().hex
            target = Path(path)
            database = target.with_suffix(target.suffix + ".sqlite3")
            self._save_sqlite_rows(database)
            data: Dict[str, Any] = {
                "schema_version": 3,
                "storage": "sqlite",
                "database": database.name,
                "checkpoint_generation": generation,
                "compress_threshold": self.compress_threshold,
                "round": self._round,
                "abstract": compacted_to_dict(self.abstract),
                "message_count": self.storage.count(database, "messages"),
                "archive_count": self.storage.count(database, "archive"),
            }
            if self.context_editing:
                data["context_editing"] = dict(self.context_editing)
            committed_graph = graph_checkpoint if graph_checkpoint is not None else self.graph_checkpoint
            if committed_graph:
                data["graph_checkpoint"] = committed_graph
            serialized = json.dumps(data, ensure_ascii=False, indent=2)
            temp_path: Optional[Path] = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=target.parent,
                    prefix=f".{target.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                    temp_file.write(serialized)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                os.replace(temp_path, target)
            except OSError:
                if temp_path is not None:
                    try:
                        temp_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                raise
            self.checkpoint_generation = generation
            self.graph_checkpoint = committed_graph
            return True
        except (OSError, TypeError, ValueError) as exc:
            self.last_save_error = exc
            return False

    @override
    def load(self, path: Optional[str | Path]) -> bool:
        """Deserialize conversation history from a JSON file.

        Existing in-memory state is replaced only after the complete payload
        validates; read or parse failures leave retained state untouched.

        Args:
            path: Source file path.

        Returns:
            ``True`` on success, ``False`` on read / parse failure.
        """
        if not path:
            return False

        try:
            target = Path(path)
            raw = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False

        try:
            if not isinstance(raw, dict):
                raise ValueError("checkpoint must be an object")
            compress_threshold = raw.get("compress_threshold", 262144)
            if not isinstance(compress_threshold, int) or isinstance(compress_threshold, bool):
                raise ValueError("compress_threshold must be an integer")
            abstract = compacted_from_dict(raw.get("abstract"))
            sqlite_checkpoint = raw.get("schema_version") == 3 and raw.get("storage") == "sqlite"
            if sqlite_checkpoint:
                page = self.storage.read_page(target)
                messages = [context_from_dict(item) for item in page.rows]
                archive: list[LLMContext] = []
                database_name = raw.get("database")
                if not isinstance(database_name, str):
                    raise ValueError("checkpoint database must be a string")
                database = target.with_name(database_name)
                message_high_water = self.storage.max_timeline(database, "messages")
                archive_high_water = self.storage.max_timeline(database, "archive")
            else:
                messages = [context_from_dict(m) for m in raw.get("messages", [])]
                archive_raw = raw.get("archive", [])
                if not isinstance(archive_raw, list):
                    raise ValueError("archive must be a list")
                archive = [context_from_dict(m) for m in archive_raw]
                message_high_water = 0
                archive_high_water = 0
            # ``archive`` was introduced after the original linear format.
            # Missing it is a valid legacy file, whose already-discarded raw
            # history unfortunately cannot be reconstructed.
            # Old context files do not contain ``round``. Recover their next
            # timeline boundary from both retained and compacted history.
            restored_timelines = [message.timeline for message in messages]
            if abstract is not None:
                restored_timelines.extend(abstract.source_timeline)
            saved_round = raw.get("round", 0)
            if not isinstance(saved_round, int) or isinstance(saved_round, bool):
                raise ValueError("round must be an integer")
            restored_round = max([saved_round, *restored_timelines], default=0)
            generation = raw.get("checkpoint_generation")
            if generation is not None and not isinstance(generation, str):
                raise ValueError("checkpoint_generation must be a string")
            graph_checkpoint = raw.get("graph_checkpoint")
            if graph_checkpoint is not None and not isinstance(graph_checkpoint, str):
                raise ValueError("graph_checkpoint must be a string")
            editing = raw.get("context_editing", {})
            if not isinstance(editing, dict):
                raise ValueError("context_editing must be an object")

            # Commit parsed state only after every field validates. A corrupt
            # checkpoint therefore cannot erase a retained Agent's memory.
            self.compress_threshold = compress_threshold
            self.abstract = abstract
            self.messages = messages
            self.archive = archive
            self._round = restored_round
            self.checkpoint_generation = generation
            self.graph_checkpoint = graph_checkpoint
            self.context_editing = dict(editing)
            self._storage_message_high_water = message_high_water
            self._storage_archive_high_water = archive_high_water
            # The resume prompt is derived state, never persisted.
            self._pending_resume = False
            return True
        except (TypeError, KeyError, ValueError):
            return False

    def _save_sqlite_rows(self, database: Path) -> None:
        """Append changed context rows in one SQLite transaction.

        Args:
            database: Durable sidecar database for this context pointer.

        Returns:
            ``None`` after the transaction commits.
        """
        new_messages = [item for item in self.messages if item.timeline > self._storage_message_high_water]
        new_archive = [item for item in self.archive if item.timeline > self._storage_archive_high_water]
        self.storage.append_rows(
            database,
            [(item.timeline, json.dumps(context_to_dict(item), ensure_ascii=False)) for item in new_messages],
            [(item.timeline, json.dumps(context_to_dict(item), ensure_ascii=False)) for item in new_archive],
        )
        if new_messages:
            self._storage_message_high_water = max(self._storage_message_high_water, max(item.timeline for item in new_messages))
        if new_archive:
            self._storage_archive_high_water = max(self._storage_archive_high_water, max(item.timeline for item in new_archive))

    def replace_active_context(
        self,
        messages: list[Dict[str, Any]],
        *,
        database: Path,
        context_editing: Dict[str, object] | None = None,
    ) -> int:
        """Replace the active transcript and its durable rows atomically.

        Context editing rewrites the whole active window instead of appending.
        Renumbered timelines start above the archived and persisted high-water
        marks so an edited transcript can never collide with compaction
        history, and the in-memory handler is left consistent with the rows
        that were just written.

        Args:
            messages: Serialized active entries in the new display order.
            database: Durable sidecar database for this context pointer.
            context_editing: Optional editing metadata to record on the
                handler; ``None`` keeps the current value.

        Returns:
            The new timeline high-water mark.
        """
        archive_max = self.storage.max_timeline(database, "archive")
        message_max = self.storage.max_timeline(database, "messages")
        start = max(archive_max, message_max, self._round) + 1
        normalized: list[Dict[str, Any]] = []
        for offset, item in enumerate(messages):
            value = dict(item)
            value["timeline"] = start + offset
            normalized.append(value)
        self.storage.replace_active(
            database,
            [
                (item["timeline"], json.dumps(item, ensure_ascii=False))
                for item in normalized
            ],
        )
        self.messages = [context_from_dict(item) for item in normalized]
        self._round = normalized[-1]["timeline"] if normalized else start
        self._storage_message_high_water = self._round
        if context_editing is not None:
            self.context_editing = dict(context_editing)
        return self._round

    # -- serialization helpers ---------------------------------------------

    @staticmethod
    def _context_to_dict(ctx: LLMContext) -> Dict[str, Any]:
        """Serialize one context entry for hosts and persistence."""
        return context_to_dict(ctx)

    @staticmethod
    def _context_from_dict(data: Dict[str, Any]) -> LLMContext:
        """Rebuild one context entry from its serialized payload."""
        return context_from_dict(data)
