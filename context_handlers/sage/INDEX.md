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
| [sage.py](sage.py#L71) | `SageContext.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append a user input and index it in the tree. |
| [sage.py](sage.py#L83) | `SageContext.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]], usage: Optional[Dict[str, int]], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float], controller: ExecutionController \| None` | `None` | Append an assistant turn and index it in the tree. |
| [sage.py](sage.py#L119) | `SageContext.build_messages` | `None` | `List[Dict[str, Any]]` | Render the active history exactly as the composed handler does. |
| [sage.py](sage.py#L128) | `SageContext.compact` | `controller: ExecutionController \| None` | `bool` | Compact the composed transcript, then re-index what remains. |
| [sage.py](sage.py#L143) | `SageContext.save` | `path: str \| Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Persist the composed checkpoint and mirror its failure cause. |
| [sage.py](sage.py#L173) | `SageContext.load` | `path: Optional[str \| Path]` | `bool` | Restore the composed checkpoint and rebuild the tree index. |
| [sage.py](sage.py#L188) | `SageContext.clear_context` | `None` | `bool` | Clear the transcript, the timeline and the tree index. |
| [sage.py](sage.py#L200) | `SageContext.replace_active_context` | `messages: list[Dict[str, Any]], database: Path, context_editing: Dict[str, object] \| None` | `int` | Atomically replace the active transcript and re-index the tree. |
| [sage.py](sage.py#L229) | `SageContext.get_prev_messages` | `None` | `List[LLMContext \| LLMContextCompacted]` | Return the composed handler's stored history, abstract first. |
| [sage.py](sage.py#L233) | `SageContext.set_compaction_event_hook` | `hook: Any` | `None` | Forward the compaction lifecycle observer to the composed handler. |
| [sage.py](sage.py#L242) | `SageContext.extra_usage` | `None` | `TokenUsage` | Token usage accumulated by the composed handler's hidden LLM calls. |
| [sage.py](sage.py#L247) | `SageContext.record_usage` | `usage: Optional[TokenUsage]` | `None` | Forward one internal LLM call's usage to the composed handler. |
| [sage.py](sage.py#L255) | `SageContext.drain_usage_records` | `None` | `list[UsageRecord]` | Drain the composed handler's internal-call usage records once. |
| [sage.py](sage.py#L261) | `SageContext._index_appended` | `previous_length: int` | `None` | Index whatever the composed handler appended to its transcript. |
| [tree.py](tree.py#L58) | `ContextTree.append` | `message: SageMessage, parent_id: int \| None` | `ContextNode` | Index one message, linked to the current tail by default. |
| [tree.py](tree.py#L87) | `ContextTree.rebuild` | `messages: Sequence[SageMessage]` | `None` | Replace the index with one chain over *messages*, in order. |
| [tree.py](tree.py#L99) | `ContextTree.clear` | `None` | `None` | Drop every indexed node so the tree can be reused. |
| [tree.py](tree.py#L106) | `ContextTree.path_to` | `node_id: int` | `List[ContextNode]` | Return the root-first chain leading to *node_id*. |
| [tree.py](tree.py#L124) | `ContextTree.ordered` | `None` | `List[ContextNode]` | Return every indexed node in insertion order. |
| [tree.py](tree.py#L128) | `ContextTree.__len__` | `None` | `int` | Implement `ContextTree.__len__`. |
| [tree.py](tree.py#L131) | `ContextTree.__iter__` | `None` | `Iterator[ContextNode]` | Implement `ContextTree.__iter__`. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [sage.py](sage.py#L32) | `SageContext` | `compacting_fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None` | `ContextHandler` | Index a composed linear transcript as a set of context trees. |
| [tree.py](tree.py#L22) | `ContextNode` | `node_id: int, message: SageMessage, parent_id: int \| None` | `object` | One indexed entry, linked to the entry it continues. |
| [tree.py](tree.py#L37) | `ContextTree` | `nodes: Dict[int, ContextNode], root_id: int \| None, tail_id: int \| None, next_id: int` | `object` | A chain-shaped index over one context transcript. |

<!-- END GENERATED SYMBOL MAP -->
