"""Sage's branch-aware context handler.

The durable transcript is indexed by worktree branches. Sage owns its summary
format and compaction policy; branch state remains separate from raw
conversation rows and is persisted with the checkpoint manifest.

This context manager is still WIP, I think, and need to be tested asap.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, override
from uuid import uuid4, UUID

from ..base import ContextHandler
from ..composer import ContextBlock, ContextPosition, ContextSnapshot
from ..linear.assembly import ContextAssembler
from ..linear.codec import (
    context_item_from_dict,
    context_item_to_dict,
    tool_result_from_dict,
    tool_result_to_dict,
)
from .compaction import SageCompactionFetcher, build_sage_compaction_request, parse_sage_summary
from ..storage import ContextStorage, SQLiteContextStorage
from ...execution.control import ExecutionController
from ...llm_types import (
    AssistantContextItem,
    AssistantTurnInput,
    ContextItem,
    ContextItemId,
    ContextSummaryItem,
    RequestMessage,
    ToolCallRecord,
    ToolResultId,
    ToolResultInput,
    ToolResultRecord,
    UserContextItem,
)
from ...multimodal import UserMessage, validate_images

from .status import BranchPhase, BranchVerdict, SageWorkTreeBranch
from .commands import SageBranchCommand

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
        compacting_fetcher: SageCompactionFetcher,
        max_context_threshold: int = 262144,
        compaction_output_max_tokens: int = 8192,
        *,
        storage: ContextStorage | None = None,
        graph_store: Any | None = None,
        keep_recent: int = 0,
        keep_recent_tokens: int = 32768,
    ) -> None:
        super().__init__()

        self.compacting_fetcher = compacting_fetcher
        self.max_context_threshold = max_context_threshold
        self.compacttion_output_max_tokens = compaction_output_max_tokens
        self.storage: ContextStorage = storage or SQLiteContextStorage()
        # Optional graph-memory companion from ``llmfetcher.graph_memory``.
        # Sage owns the worktree state; the graph store only owns long-term
        # entities and relations.
        self.graph_store = graph_store
        self.keep_recent = keep_recent
        self.keep_recent_tokens = keep_recent_tokens

        # storage the raw info.
        self.raw_contexts_info: list[ContextItem] = []
        # Complete tool results addressed by the raw assistant items.  The
        # transcript holds only a ``ToolResultId`` reference; resolution goes
        # through :meth:`resolve_tool_result`, which fails on a dangling id.
        self.tool_results: dict[str, ToolResultRecord] = {}
        self.timeline: int = 0

        # Worktree related, and history related thing.
        self.worktree_root_branch: SageWorkTreeBranch = SageWorkTreeBranch(
            id=uuid4(),
            description="""
                The main context tree line.
            """,
            parent_branch_id=None,
            root_context_id=0,
            holding_context_ids=[]
        )

        # A worktree dict for this.
        self.worktree_dict: Dict[UUID, SageWorkTreeBranch] = {}
        self.worktree_dict[self.worktree_root_branch.id] = self.worktree_root_branch
       
        # worktree. Current branch is the last element of the stack.
        self.current_worktree_stack: List[SageWorkTreeBranch] = []
        self.current_worktree_stack.append(self.worktree_root_branch)

        # But: Based on these infra, how to define the active context?
        self.activate_context_id_list: List[int] = []
        # Inputs remain pending until the next assistant step is committed.
        # This keeps request projection order explicit and prevents the new
        # user/steering turn from being rendered twice as history.
        self._pending_context_id_list: List[int] = []
        self._pending_branch_commands: list[SageBranchCommand] = []
        self.summaries: dict[int, str] = {}
        self._next_summary_id = -1


    # -- ContextHandler interface -------------------------------------------

    @override
    def add_user_message(self, message: "str | UserMessage") -> None:
        """Append a user input to ``raw_contexts_info``.

        Args:
            message: The original user input, plain text or a
                :class:`~llmfetcher.multimodal.UserMessage`.
        """
        # A plain string carries no image references; a UserMessage does, and
        # they are preserved verbatim.
        self.raw_contexts_info.append(UserContextItem(
            item_id=ContextItemId.new(),
            timeline=self.timeline,
            content=str(message),
            images=(
                tuple(validate_images(message.images))
                if isinstance(message, UserMessage)
                else ()
            ),
        ))
        self._pending_context_id_list.append(self.timeline)
        target_worktree: SageWorkTreeBranch = self.current_worktree_stack[-1]
        target_worktree.holding_context_ids.append(self.timeline)
        self.timeline += 1


    @override
    def add_assistant_message(
        self,
        turn: AssistantTurnInput,
        tool_results: Sequence[ToolResultInput] = (),
        *,
        controller: ExecutionController | None = None,
    ) -> None:
        """Append an assistant turn to ``raw_contexts_info``.

        Args:
            turn: The output produced by the LLM, with its calls, usage and
                timing.
            tool_results: Completed results for the calls in *turn*.
            controller: Optional cancellation source for the compaction this
                call may trigger.
        """
        # Pair every requested tool call with the result it produced, so the
        # entry can still render a tool feedback turn later.
        results_by_call: dict[str, ToolResultInput] = {}
        for result in tool_results:
            if result.call_id in results_by_call:
                raise ValueError(
                    f"duplicate tool result for call_id {result.call_id!r}"
                )
            results_by_call[result.call_id] = result
        unmatched = set(results_by_call) - {call.call_id for call in turn.tool_calls}
        if unmatched:
            raise ValueError(
                "tool results answer no call in this turn: "
                f"{sorted(unmatched)!r}"
            )

        # Store every complete result outside the transcript and keep only its
        # reference on the call, so a missing result can never read as empty.
        tool_calls: list[ToolCallRecord] = []
        for call in turn.tool_calls:
            result = results_by_call.get(call.call_id)
            result_id: ToolResultId | None = None
            if result is not None:
                result_id = ToolResultId.new()
                self.tool_results[result_id.value] = ToolResultRecord(
                    result_id=result_id,
                    call_id=result.call_id,
                    tool_name=result.tool_name,
                    output=result.output,
                    images=tuple(result.images),
                    ok=result.ok,
                    duration_ms=result.duration_ms,
                    created_at=result.created_at,
                )
            tool_calls.append(ToolCallRecord(
                call_id=call.call_id,
                name=call.name,
                arguments=call.arguments,
                result_id=result_id,
            ))
        # Maybe I should make the long tool calls became a series of abstracted information,
        # instead of one of ...?

        self.raw_contexts_info.append(AssistantContextItem(
            item_id=ContextItemId.new(),
            timeline=self.timeline,
            content=turn.content,
            reasoning=turn.reasoning,
            tool_calls=tuple(tool_calls),
            usage=turn.usage,
            model_duration_ms=turn.model_duration_ms,
            round_duration_ms=turn.round_duration_ms,
            created_at=turn.created_at,
        ))
        
        # Commit any staged user/steering input before the assistant response.
        for context_id in self._pending_context_id_list:
            if context_id not in self.activate_context_id_list:
                self.activate_context_id_list.append(context_id)
        self._pending_context_id_list.clear()

        # Add the assistant turn to the current worktree and active context.
        target_worktree: SageWorkTreeBranch = self.current_worktree_stack[-1]
        target_worktree.holding_context_ids.append(self.timeline)

        # and make it active.
        self.activate_context_id_list.append(self.timeline)
        self.timeline += 1

        if self._estimate_context_size() > self.max_context_threshold:
            self.compact(controller=controller)

    def resolve_tool_result(self, result_id: ToolResultId) -> ToolResultRecord:
        """Return the stored result a durable tool call references.

        Args:
            result_id: Reference carried by an assistant tool call.

        Returns:
            The complete stored result record.

        Raises:
            KeyError: When no result was stored for this reference.
        """
        try:
            return self.tool_results[result_id.value]
        except KeyError:
            raise KeyError(
                f"no stored tool result for {result_id.value!r}"
            ) from None

    @override
    def build_messages(self, *, system_prompt: str | None = None) -> List[RequestMessage]:
        """Render the active context of the current worktree position.

        Returns:
            The provider-neutral request messages for the active context.
        """
        messages: List[RequestMessage] = []
        if system_prompt:
            messages.append(RequestMessage(role="system", content=system_prompt))
        by_timeline = {
            item.timeline: item
            for item in self.raw_contexts_info
        }

        # ``activate_context_id_list`` is the sole selector for historical
        # messages. The worktree stack contributes structure and status below;
        # it must not render the same transcript entries a second time.
        messages.extend(self._render_context_ids(
            self._previous_context_ids(),
            by_timeline,
        ))
        messages.extend(self._render_branch_summaries())

        worktree_message = self._render_worktree_information()
        if worktree_message is not None:
            messages.append(worktree_message)

        messages.extend(self._render_context_ids(
            self._last_round_context_ids(),
            by_timeline,
        ))
        messages.extend(self._render_context_ids(
            self._pending_context_id_list,
            by_timeline,
        ))
        return messages

    def build_blocks(self, snapshot: ContextSnapshot) -> list[ContextBlock]:
        """Expose Sage's history, summaries, worktree, and current input.

        Each semantic section gets its own Composer position while the
        legacy ``build_messages`` path remains unchanged for compatibility.
        """
        by_timeline = {item.timeline: item for item in self.raw_contexts_info}
        blocks: list[ContextBlock] = []

        def add(messages: list[RequestMessage], position: ContextPosition, source: str) -> None:
            for message in messages:
                blocks.append(ContextBlock(
                    role=message.role,
                    content=message.content or "",
                    source=source,
                    position=position,
                    message=message,
                ))

        add(self._render_context_ids(self._previous_context_ids(), by_timeline), ContextPosition.PREVIOUS, "sage.previous")
        add(self._render_branch_summaries(), ContextPosition.MEMORY, "sage.summary")
        worktree = self._render_worktree_information()
        if worktree is not None:
            add([worktree], ContextPosition.WORKTREE, "sage.worktree")
        add(self._render_context_ids(self._last_round_context_ids(), by_timeline), ContextPosition.LAST_ROUND, "sage.last_round")
        add(self._render_context_ids(self._pending_context_id_list, by_timeline), ContextPosition.CURRENT_INPUT, "sage.current_input")
        return blocks

    def describe_request_messages(self, messages: List[RequestMessage]) -> list[dict[str, Any]]:
        """Label Sage's synthetic worktree and summary messages in previews."""
        result: list[dict[str, Any]] = []
        for index, message in enumerate(messages):
            content = message.content or ""
            if message.role == "system" and index == 0:
                source = "system_prompt"
            elif "<worktree_state>" in content:
                source = "sage_worktree"
            elif "<context_abstract>" in content:
                source = "sage_summary"
            elif index == len(messages) - 1 and message.role == "user" and not content:
                source = "hypothetical_input"
            else:
                source = "sage_context"
            result.append({
                "index": index,
                "role": message.role,
                "source": source,
                "persisted": source == "sage_context",
            })
        return result

    def _render_branch_summaries(self) -> list[RequestMessage]:
        rendered: list[RequestMessage] = []
        seen: set[int] = set()
        for branch in self.current_worktree_stack:
            summary_id = branch.summary_context_id
            if summary_id is not None and summary_id not in seen and summary_id in self.summaries:
                rendered.append(RequestMessage(
                    role="system",
                    content=(
                        f"<context_abstract>\n"
                        f"{self.summaries[summary_id].abstract}\n"
                        f"</context_abstract>"
                    ),
                ))
                seen.add(summary_id)
        return rendered

    def _previous_context_ids(self) -> list[int]:
        """Return active history IDs excluding the latest assistant round."""
        last_round = set(self._last_round_context_ids())
        return [
            context_id
            for context_id in self.activate_context_id_list
            if context_id not in last_round
        ]

    def _last_round_context_ids(self) -> list[int]:
        """Return the latest committed assistant turn, if one exists."""
        active = set(self.activate_context_id_list)
        for item in reversed(self.raw_contexts_info):
            if item.kind == "assistant" and item.timeline in active:
                return [item.timeline]
        return []

    def _render_context_ids(
        self,
        context_ids: list[int],
        by_timeline: dict[int, ContextItem],
    ) -> list[RequestMessage]:
        """Render selected context items in stable timeline order."""
        selected = [
            by_timeline[context_id]
            for context_id in context_ids
            if context_id in by_timeline
        ]
        assembled = ContextAssembler(self).assemble(
            selected,
            placement=self.tool_result_placement,
            pending_resume=False,
        )
        return list(assembled.messages)

    def _render_worktree_information(self) -> RequestMessage | None:
        """Render branch descriptions and status for the active stack."""
        if not self.current_worktree_stack:
            return None

        lines = [
            "<worktree_state>",
            "This is Sage coordination state, not conversation history.",
            "<path>",
        ]
        for index, branch in enumerate(self.current_worktree_stack):
            description = " ".join(str(branch.description).split())
            if not description:
                description = "(no description)"
            lines.append(
                f"{index + 1}. id={branch.id} "
                f"phase={branch.phase.value} "
                f"verdict={branch.verdict.value} "
                f"description={description}"
            )
        lines.extend(["</path>", "</worktree_state>"])
        return RequestMessage(role="user", content="\n".join(lines))


    @override
    def compact(
        self, 
        *, 
        controller: ExecutionController | None = None,
        keep_recent: Optional[int] = None
    ) -> bool:
        """Compact the composed transcript, then re-index what remains.

        Notes:
            The rule of compaction of Sage should be like this:
            - Once the threshold was touched,

        Args:
            controller: Optional cancellation source.

        Returns:
            ``True`` when the compaction succeeded and the tree was rebuilt.
        """
        active = [i for i in self.activate_context_id_list if i not in self._pending_context_id_list]
        if not active:
            return False
        by_timeline = {item.timeline: item for item in self.raw_contexts_info}
        entries = self._render_branch_summaries()
        entries.extend(self._render_context_ids(active, by_timeline))
        if not entries:
            return False
        policy = self.keep_recent if keep_recent is None else max(0, int(keep_recent))
        keep = min(policy, max(0, len(active) - 1))
        archived_ids = active[:-keep] if keep else active
        retained_ids = active[-keep:] if keep else []
        branch_path = "\n".join(
            f"{branch.id} | {branch.phase.value} | {branch.verdict.value} | {branch.description}"
            for branch in self.current_worktree_stack
        )
        preview = build_sage_compaction_request(
            entries,
            branch_path=branch_path,
            input_char_limit=196_608,
            output_max_tokens=self.compacttion_output_max_tokens,
            threshold=self.max_context_threshold,
            round=self.timeline,
        )
        try:
            result = self.compacting_fetcher.fetch(
                msg=preview.text, system_prompt=preview.system_prompt,
                temperature=0.0, max_tokens=preview.max_tokens,
                context_handler=None, controller=controller,
            )
        except Exception:
            return False
        abstract = parse_sage_summary(result.content)
        if not abstract:
            return False
        # The summary references exactly the entries it replaces, so a reader
        # can still audit which transcript range it stands in for.
        archived_items = [by_timeline[context_id] for context_id in archived_ids]
        summary_id = self._next_summary_id
        self._next_summary_id -= 1
        self.summaries[summary_id] = ContextSummaryItem(
            item_id=ContextItemId.new(),
            timeline=summary_id,
            abstract=abstract,
            source_item_ids=tuple(item.item_id for item in archived_items),
            source_timeline=tuple(item.timeline for item in archived_items),
            source_result_ids=tuple(
                call.result_id
                for item in archived_items
                if item.kind == "assistant"
                for call in item.tool_calls
                if call.result_id is not None
            ),
        )
        current = self.current_worktree_stack[-1]
        current.summary_context_id = summary_id
        current.holding_context_ids = [i for i in current.holding_context_ids if i not in archived_ids]
        self.activate_context_id_list = retained_ids
        return True


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
        if not path:
            self.last_save_error = ValueError("Sage checkpoint path is required")
            return False
        try:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            generation = checkpoint_generation or uuid4().hex
            database = target.with_suffix(target.suffix + ".sqlite3")
            state_name = f"{target.name}.sage-state.{generation}.json"
            # Results commit before the transcript that references them: an
            # orphan result is harmless, a dangling reference is not.
            self.storage.append_rows(
                database,
                (),
                (),
                [
                    (
                        result_id,
                        json.dumps(tool_result_to_dict(record), ensure_ascii=False),
                    )
                    for result_id, record in self.tool_results.items()
                ],
            )
            self.storage.replace_active(database, [
                (item.timeline, json.dumps(context_item_to_dict(item), ensure_ascii=False))
                for item in self.raw_contexts_info
            ])
            state = self._state_to_dict()
            state.update({"schema_version": 1, "checkpoint_generation": generation,
                          "database": database.name})
            self._atomic_json_write(target.with_name(state_name), state)
            manifest = {"schema_version": 3, "storage": "sqlite",
                        "database": database.name, "sage_state_checkpoint": state_name,
                        "checkpoint_generation": generation, "timeline": self.timeline,
                        "message_count": self.storage.count(database, "messages"),
                        "archive_count": self.storage.count(database, "archive"),
                        "compress_threshold": self.max_context_threshold}
            graph_name = graph_checkpoint
            if self.graph_store is not None:
                graph_name = graph_name or f"{target.name}.graph.{generation}.json"
                if not self.graph_store.save(target.with_name(graph_name)):
                    raise OSError("could not save Sage graph checkpoint")
            if graph_name:
                manifest["graph_checkpoint"] = graph_name
            self._atomic_json_write(target, manifest)
            self.last_save_error = None
            return True
        except (OSError, TypeError, ValueError) as exc:
            self.last_save_error = exc
            return False
    def _estimate_context_size(self) -> int:
        return sum(len(message.content or "") for message in self.build_messages())

    def compaction_request_preview(self):
        """Build Sage's local compaction request without provider I/O."""
        active = [i for i in self.activate_context_id_list if i not in self._pending_context_id_list]
        by_timeline = {item.timeline: item for item in self.raw_contexts_info}
        entries = self._render_branch_summaries()
        entries.extend(self._render_context_ids(active, by_timeline))
        branch_path = "\n".join(
            f"{branch.id} | {branch.phase.value} | {branch.verdict.value} | {branch.description}"
            for branch in self.current_worktree_stack
        )
        return build_sage_compaction_request(
            entries,
            branch_path=branch_path,
            input_char_limit=196_608,
            output_max_tokens=self.compacttion_output_max_tokens,
            threshold=self.max_context_threshold,
            round=self.timeline,
        )

    def queue_branch_command(self, command: SageBranchCommand) -> None:
        self._pending_branch_commands.append(command)

    def apply_pending_branch_commands(self) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        commands, self._pending_branch_commands = self._pending_branch_commands, []
        for command in commands:
            current = self.current_worktree_stack[-1]
            if command.kind == "fork":
                branch = SageWorkTreeBranch(
                    id=uuid4(), description=command.description,
                    parent_branch_id=current.id,
                    root_context_id=current.holding_context_ids[-1] if current.holding_context_ids else None,
                )
                self.worktree_dict[branch.id] = branch
                current.branches_id.append(branch.id)
                if command.reason == "checkout":
                    self._checkout(branch.id)
                results.append({"operation": "fork", "branch_id": str(branch.id)})
            elif command.kind == "checkout":
                self._checkout(command.branch_id)
                results.append({"operation": "checkout", "branch_id": str(command.branch_id)})
            elif command.kind == "pause":
                current.phase = BranchPhase.PAUSED
                current.summary_context_id = current.summary_context_id
                if command.reason:
                    current.description = f"{current.description} (paused: {command.reason})"
                results.append({"operation": "pause", "branch_id": str(current.id)})
            elif command.kind == "resume":
                current.phase = BranchPhase.RUNNING
                results.append({"operation": "resume", "branch_id": str(current.id)})
            elif command.kind == "finish":
                current.phase = BranchPhase.FINISHED
                current.verdict = BranchVerdict(str(command.verdict))
                results.append({"operation": "finish", "branch_id": str(current.id)})
        return results

    def _checkout(self, branch_id: UUID | None) -> None:
        if branch_id is None or branch_id not in self.worktree_dict:
            raise ValueError(f"unknown Sage branch: {branch_id}")
        path: list[SageWorkTreeBranch] = []
        cursor = self.worktree_dict[branch_id]
        while cursor is not None:
            path.append(cursor)
            cursor = self.worktree_dict.get(cursor.parent_branch_id) if cursor.parent_branch_id else None
        self.current_worktree_stack = list(reversed(path))
        self.current_worktree_stack[-1].phase = BranchPhase.RUNNING

    def worktree_snapshot(self) -> dict[str, Any]:
        return {
            "current_branch_id": str(self.current_worktree_stack[-1].id),
            "path": [{"id": str(b.id), "description": b.description,
                      "phase": b.phase.value, "verdict": b.verdict.value}
                     for b in self.current_worktree_stack],
            "branches": [{"id": str(b.id), "parent_branch_id": str(b.parent_branch_id) if b.parent_branch_id else None,
                          "description": b.description, "phase": b.phase.value, "verdict": b.verdict.value}
                         for b in self.worktree_dict.values()],
        }
    @override
    def load(self, path: Optional[str | Path]) -> bool:
        """Restore the composed checkpoint and rebuild the tree index.

        Args:
            path: Source file path.

        Returns:
            ``True`` on success; retained state is left untouched on failure.
        """
        if not path:
            return False
        try:
            target = Path(path)
            manifest = json.loads(target.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or manifest.get("schema_version") not in {1, 3}:
                raise ValueError("unsupported Sage checkpoint")
            database_name = manifest.get("database")
            state_name = manifest.get("sage_state_checkpoint")
            if not isinstance(database_name, str) or Path(database_name).name != database_name:
                raise ValueError("invalid Sage database reference")
            if not isinstance(state_name, str) or Path(state_name).name != state_name:
                raise ValueError("invalid Sage state reference")
            state = json.loads(target.with_name(state_name).read_text(encoding="utf-8"))
            database = target.with_name(database_name)
            rows = self.storage.read_rows(database)
            contexts = [context_item_from_dict(json.loads(payload)) for _, payload in rows]
            result_ids = [
                call.result_id.value
                for item in contexts
                if item.kind == "assistant"
                for call in item.tool_calls
                if call.result_id is not None
            ]
            stored = self.storage.read_tool_results(database, result_ids)
            tool_results: dict[str, ToolResultRecord] = {}
            for result_id, payload in stored:
                decoded = json.loads(payload)
                if not isinstance(decoded, dict):
                    raise ValueError("Sage tool result payload must be an object")
                tool_results[result_id] = tool_result_from_dict(decoded)
            if set(result_ids) != set(tool_results):
                # A dangling reference is a corrupt checkpoint, never an
                # empty result the model could mistake for real output.
                raise ValueError("Sage checkpoint references a missing tool result")
            restored = self._state_from_dict(state, contexts)
            graph_name = manifest.get("graph_checkpoint")
            if graph_name:
                if self.graph_store is None or not isinstance(graph_name, str):
                    raise ValueError("Sage graph checkpoint has no graph store")
                graph_path = target.with_name(graph_name)
                if not graph_path.exists() or not self.graph_store.load(graph_path):
                    raise ValueError("could not load Sage graph checkpoint")
            elif self.graph_store is not None:
                self.graph_store.clear()
        except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
            return False
        self.raw_contexts_info = restored["contexts"]
        self.tool_results = tool_results
        self.timeline = restored["timeline"]
        self.worktree_dict = restored["worktree_dict"]
        self.worktree_root_branch = restored["root_branch"]
        self.current_worktree_stack = restored["stack"]
        self.activate_context_id_list = restored["active_ids"]
        self._pending_context_id_list = restored["pending_ids"]
        self.summaries = restored["summaries"]
        self._next_summary_id = restored["next_summary_id"]
        self._pending_branch_commands.clear()
        self.last_save_error = None
        return True

    @override
    def clear_context(self) -> bool:
        """Clear the transcript, the timeline and the tree index.

        Returns:
            ``True`` once the composed handler has reset.
        """
        self.raw_contexts_info.clear()
        self.tool_results.clear()
        self.timeline = 0
        self.activate_context_id_list.clear()
        self._pending_context_id_list.clear()
        self._pending_branch_commands.clear()
        self.summaries.clear()
        self._next_summary_id = -1
        root = self.worktree_root_branch
        root.branches_id.clear()
        root.holding_context_ids.clear()
        root.root_context_id = None
        root.summary_context_id = None
        root.phase = root.phase.__class__.NOT_STARTED
        root.verdict = root.verdict.__class__.UNKNOWN
        self.worktree_dict = {root.id: root}
        self.current_worktree_stack = [root]
        return True

    # -- persistence helpers ---------------------------------------------

    @staticmethod
    def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
        """Write one JSON checkpoint using fsync and atomic replacement."""
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def _state_to_dict(self) -> dict[str, Any]:
        """Serialize branch and projection state as a flat UUID-indexed map."""
        branches: dict[str, Any] = {}
        for branch_id, branch in self.worktree_dict.items():
            branches[str(branch_id)] = {
                "id": str(branch.id),
                "description": branch.description,
                "branches_id": [str(value) for value in branch.branches_id],
                "parent_branch_id": str(branch.parent_branch_id) if branch.parent_branch_id else None,
                "root_context_id": branch.root_context_id,
                "holding_context_ids": list(branch.holding_context_ids),
                "summary_context_id": branch.summary_context_id,
                "phase": branch.phase.value,
                "verdict": branch.verdict.value,
            }
        return {
            "root_branch_id": str(self.worktree_root_branch.id),
            "current_worktree_stack": [str(branch.id) for branch in self.current_worktree_stack],
            "branches": branches,
            "active_context_id_list": list(self.activate_context_id_list),
            "pending_context_id_list": list(self._pending_context_id_list),
            "timeline": self.timeline,
            "summaries": {
                str(key): context_item_to_dict(value)
                for key, value in self.summaries.items()
            },
            "next_summary_id": self._next_summary_id,
        }

    @staticmethod
    def _state_from_dict(
        state: dict[str, Any],
        contexts: list[ContextItem],
    ) -> dict[str, Any]:
        """Validate and rebuild state before mutating the live handler."""
        raw_branches = state.get("branches")
        if not isinstance(raw_branches, dict):
            raise ValueError("Sage branches must be an object")
        context_ids = {item.timeline for item in contexts}
        branches: dict[UUID, SageWorkTreeBranch] = {}
        for key, raw in raw_branches.items():
            branch_id = UUID(str(raw.get("id", key)))
            branches[branch_id] = SageWorkTreeBranch(
                id=branch_id,
                description=str(raw.get("description", "")),
                branches_id=[UUID(value) for value in raw.get("branches_id", [])],
                parent_branch_id=(UUID(raw["parent_branch_id"])
                                  if raw.get("parent_branch_id") else None),
                root_context_id=raw.get("root_context_id"),
                holding_context_ids=[int(value) for value in raw.get("holding_context_ids", [])],
                summary_context_id=raw.get("summary_context_id"),
                phase=BranchPhase(raw.get("phase", BranchPhase.NOT_STARTED.value)),
                verdict=BranchVerdict(raw.get("verdict", BranchVerdict.UNKNOWN.value)),
            )
        root_id = UUID(str(state["root_branch_id"]))
        stack_ids = [UUID(value) for value in state.get("current_worktree_stack", [])]
        if root_id not in branches or not stack_ids or any(value not in branches for value in stack_ids):
            raise ValueError("invalid Sage branch references")
        active_ids = [int(value) for value in state.get("active_context_id_list", [])]
        pending_ids = [int(value) for value in state.get("pending_context_id_list", [])]
        if not set(active_ids + pending_ids).issubset(context_ids):
            raise ValueError("invalid Sage context references")
        for branch in branches.values():
            if not set(branch.holding_context_ids).issubset(context_ids):
                raise ValueError("invalid branch context references")
        summaries: dict[int, ContextSummaryItem] = {}
        for key, value in (state.get("summaries") or {}).items():
            if not isinstance(value, dict):
                raise ValueError("Sage summary payload must be an object")
            summary = context_item_from_dict(value)
            if summary.kind != "summary":
                raise ValueError("Sage summary payload must be a summary item")
            summaries[int(key)] = summary
        return {
            "contexts": contexts,
            "timeline": max([int(state.get("timeline", 0)), *(value + 1 for value in context_ids)], default=0),
            "worktree_dict": branches,
            "root_branch": branches[root_id],
            "stack": [branches[value] for value in stack_ids],
            "active_ids": active_ids,
            "pending_ids": pending_ids,
            "summaries": summaries,
            "next_summary_id": int(state.get("next_summary_id", -1)),
        }

__all__ = ["SageContext"]
