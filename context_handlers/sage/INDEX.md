# llmfetcher/context_handlers/sage/ — Sage Context INDEX

Context history indexed as a set of context trees. `SageContext` (`sage.py`)
is the public entry point: it composes `ContextHandlerLinear` for durable
rows, compaction and usage accounting, and keeps one `tree.py` index over the
active transcript.

| File | Responsibility |
|---|---|
| `sage.py` | `SageContext`: create/read/update/delete over the composed transcript plus the tree index, mirroring the linear handler's reads and persistence. |
| `tree.py` | `ContextNode` / `ContextTree`: the chain-shaped index, its append/rebuild/clear operations and root-first traversal. |
| `__init__.py` | Public exports: `SageContext`, `ContextNode`, `ContextTree`, `SageMessage`. |

## Boundaries

- Reads and persistence are delegated: `build_messages` and the checkpoint
  come from the composed linear handler, so Sage cannot drift from it.
- Only `tree.py` defines structure; which nodes a request renders stays a
  `SageContext` policy decision, not a persistence concern.
- No SQL here: durable rows go through `ContextStorage` (`../storage.py`).

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [compaction.py](compaction.py#L20) | `SageCompactionFetcher.fetch` | `msg: str, system_prompt: str \| None, temperature: float, max_tokens: int, context_handler: Any, controller: ExecutionController \| None` | `LLMOutput` | Implement `SageCompactionFetcher.fetch`. |
| [compaction.py](compaction.py#L50) | `SageCompactionRequest.messages` | `None` | `int` | Compatibility name used by Angelus's compaction preview DTO. |
| [compaction.py](compaction.py#L55) | `SageCompactionRequest.omitted` | `None` | `int` | Compatibility name used by Angelus's compaction preview DTO. |
| [compaction.py](compaction.py#L60) | `build_sage_compaction_request` | `messages: Sequence[RequestMessage], branch_path: str, input_char_limit: int, output_max_tokens: int, threshold: int, round: int` | `SageCompactionRequest` | Implement `build_sage_compaction_request`. |
| [compaction.py](compaction.py#L87) | `parse_sage_summary` | `raw: str` | `str \| None` | Implement `parse_sage_summary`. |
| [sage.py](sage.py#L127) | `SageContext.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append a user input to ``raw_contexts_info``. |
| [sage.py](sage.py#L153) | `SageContext.add_assistant_message` | `turn: AssistantTurnInput, tool_results: Sequence[ToolResultInput], controller: ExecutionController \| None` | `None` | Append an assistant turn to ``raw_contexts_info``. |
| [sage.py](sage.py#L241) | `SageContext.resolve_tool_result` | `result_id: ToolResultId` | `ToolResultRecord` | Return the stored result a durable tool call references. |
| [sage.py](sage.py#L261) | `SageContext.build_messages` | `system_prompt: str \| None` | `List[RequestMessage]` | Render the active context of the current worktree position. |
| [sage.py](sage.py#L298) | `SageContext.block_source_catalog` | `None` | `tuple[ContextBlockSource, ...]` | Declare Sage's fixed sections, including the empty current input. |
| [sage.py](sage.py#L312) | `SageContext.build_blocks` | `snapshot: ContextSnapshot` | `list[ContextBlock]` | Expose Sage's history, summaries, worktree, and current input. |
| [sage.py](sage.py#L340) | `SageContext.describe_request_messages` | `messages: List[RequestMessage]` | `list[dict[str, Any]]` | Label Sage's synthetic worktree and summary messages in previews. |
| [sage.py](sage.py#L363) | `SageContext._render_branch_summaries` | `None` | `list[RequestMessage]` | Implement `SageContext._render_branch_summaries`. |
| [sage.py](sage.py#L380) | `SageContext._previous_context_ids` | `None` | `list[int]` | Return active history IDs excluding the latest assistant round. |
| [sage.py](sage.py#L389) | `SageContext._last_round_context_ids` | `None` | `list[int]` | Return the latest committed assistant turn, if one exists. |
| [sage.py](sage.py#L397) | `SageContext._render_context_ids` | `context_ids: list[int], by_timeline: dict[int, ContextItem]` | `list[RequestMessage]` | Render selected context items in stable timeline order. |
| [sage.py](sage.py#L415) | `SageContext._render_worktree_information` | `None` | `RequestMessage \| None` | Render branch descriptions and status for the active stack. |
| [sage.py](sage.py#L440) | `SageContext.compact` | `controller: ExecutionController \| None, keep_recent: Optional[int]` | `bool` | Compact the composed transcript, then re-index what remains. |
| [sage.py](sage.py#L520) | `SageContext.save` | `path: str \| Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Persist the composed checkpoint and mirror its failure cause. |
| [sage.py](sage.py#L589) | `SageContext._estimate_context_size` | `None` | `int` | Implement `SageContext._estimate_context_size`. |
| [sage.py](sage.py#L592) | `SageContext.compaction_request_preview` | `None` | `Any` | Build Sage's local compaction request without provider I/O. |
| [sage.py](sage.py#L611) | `SageContext.queue_branch_command` | `command: SageBranchCommand` | `None` | Implement `SageContext.queue_branch_command`. |
| [sage.py](sage.py#L614) | `SageContext.apply_pending_branch_commands` | `None` | `list[dict[str, str]]` | Implement `SageContext.apply_pending_branch_commands`. |
| [sage.py](sage.py#L648) | `SageContext._checkout` | `branch_id: UUID \| None` | `None` | Implement `SageContext._checkout`. |
| [sage.py](sage.py#L659) | `SageContext.worktree_snapshot` | `None` | `dict[str, Any]` | Implement `SageContext.worktree_snapshot`. |
| [sage.py](sage.py#L670) | `SageContext.load` | `path: Optional[str \| Path]` | `bool` | Restore the composed checkpoint and rebuild the tree index. |
| [sage.py](sage.py#L741) | `SageContext.clear_context` | `None` | `bool` | Clear the transcript, the timeline and the tree index. |
| [sage.py](sage.py#L769) | `SageContext._atomic_json_write` | `path: Path, payload: dict[str, Any]` | `None` | Write one JSON checkpoint using fsync and atomic replacement. |
| [sage.py](sage.py#L786) | `SageContext._state_to_dict` | `None` | `dict[str, Any]` | Serialize branch and projection state as a flat UUID-indexed map. |
| [sage.py](sage.py#L816) | `SageContext._state_from_dict` | `state: dict[str, Any], contexts: list[ContextItem]` | `dict[str, Any]` | Validate and rebuild state before mutating the live handler. |
| [tools.py](tools.py#L25) | `SageToolProvider.tools` | `None` | `list[Tool]` | Implement `SageToolProvider.tools`. |
| [tools.py](tools.py#L44) | `SageToolProvider.get_worktree` | `**_: Any` | `str` | Implement `SageToolProvider.get_worktree`. |
| [tools.py](tools.py#L47) | `SageToolProvider.fork_branch` | `description: str, checkout: bool, **_: Any` | `str` | Implement `SageToolProvider.fork_branch`. |
| [tools.py](tools.py#L55) | `SageToolProvider.checkout_branch` | `branch_id: str, **_: Any` | `str` | Implement `SageToolProvider.checkout_branch`. |
| [tools.py](tools.py#L60) | `SageToolProvider.pause_branch` | `reason: str, **_: Any` | `str` | Implement `SageToolProvider.pause_branch`. |
| [tools.py](tools.py#L64) | `SageToolProvider.resume_branch` | `**_: Any` | `str` | Implement `SageToolProvider.resume_branch`. |
| [tools.py](tools.py#L68) | `SageToolProvider.finish_branch` | `verdict: str, **_: Any` | `str` | Implement `SageToolProvider.finish_branch`. |
| [tools.py](tools.py#L74) | `create_sage_tools` | `context: Any` | `list[Tool]` | Return tools bound to *context* for an Angelus Agent. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [commands.py](commands.py#L11) | `SageBranchCommand` | `kind: str, branch_id: Optional[UUID], description: str, verdict: Optional[str], reason: str` | `object` | One mutation applied at the next completed agent round. |
| [compaction.py](compaction.py#L19) | `SageCompactionFetcher` | `None` | `Protocol` | Provide `SageCompactionFetcher` behavior. |
| [compaction.py](compaction.py#L39) | `SageCompactionRequest` | `text: str, system_prompt: str, max_tokens: int, source_messages: int, omitted_messages: int, temperature: float, threshold: int, round: int` | `object` | Provide `SageCompactionRequest` behavior. |
| [sage.py](sage.py#L49) | `SageContext` | `compacting_fetcher: SageCompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None, graph_store: Any \| None, keep_recent: int, keep_recent_tokens: int` | `ContextHandler` | Index a composed linear transcript as a set of context trees. |
| [status.py](status.py#L11) | `BranchPhase` | `None` | `StrEnum` | Provide `BranchPhase` behavior. |
| [status.py](status.py#L19) | `BranchVerdict` | `None` | `StrEnum` | Provide `BranchVerdict` behavior. |
| [status.py](status.py#L27) | `SageWorkTreeBranch` | `id: UUID, description: str, branches_id: List[UUID], parent_branch_id: Optional[UUID], root_context_id: Optional[int], holding_context_ids: List[int], summary_context_id: Optional[int], phase: BranchPhase, verdict: BranchVerdict` | `object` | The metadata about the branch. A branch can be the root of the subtree. |
| [tools.py](tools.py#L19) | `SageToolProvider` | `context: Any` | `object` | Bind Sage coordination tools to one context handler instance. |

<!-- END GENERATED SYMBOL MAP -->
