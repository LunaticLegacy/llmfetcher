# llmfetcher/context_handlers/linear/ — Linear Context INDEX

Durable linear transcript, split into concern modules. `ContextHandlerLinear`
(`handler.py`) is the only stateful owner: it appends turns, decides when to
compact and persists through the `ContextStorage` port. Every other module in
this package is a pure or narrow helper the handler composes.

| File | Responsibility |
|---|---|
| `handler.py` | `ContextHandlerLinear`: transcript state, compaction orchestration, checkpoint save/load, atomic active-context replacement. |
| `codec.py` | Serialize and rebuild `LLMContext` / `LLMContextCompacted` row payloads. |
| `compaction.py` | `CompactionFetcher`, `CompactionRequestPreview`, the fixed compactor prompt, request planning (`build_request_preview`) and `<context_abstract>` parsing. |
| `rendering.py` | Render stored entries into provider-neutral request messages, including the derived post-compaction resume turn. |
| `paging.py` | `read_persisted_context_page`: bounded reverse-timeline reads over one checkpoint. |
| `__init__.py` | Public exports; preserves the historical `context_handlers.linear` import surface. |

## Boundaries

- Only `handler.py` mutates transcript state; sibling modules take explicit
  arguments and never reach back into the handler.
- Compaction archives raw turns instead of deleting them, matching the
  package-level policy in [`../INDEX.md`](../INDEX.md).
- Checkpoint persistence stays behind `ContextStorage` (`../storage.py`); this
  package issues no SQL of its own.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [codec.py](codec.py#L17) | `context_to_dict` | `ctx: LLMContext` | `Dict[str, Any]` | Serialize one durable context entry into its persisted row payload. |
| [codec.py](codec.py#L22) | `context_from_dict` | `data: Dict[str, Any]` | `LLMContext` | Rebuild one durable context entry from a persisted row payload. |
| [codec.py](codec.py#L48) | `compacted_to_dict` | `comp: Optional[LLMContextCompacted]` | `Optional[Dict[str, Any]]` | Serialize a compacted abstract, preserving ``None``. |
| [codec.py](codec.py#L57) | `compacted_from_dict` | `data: Optional[Dict[str, Any]]` | `Optional[LLMContextCompacted]` | Rebuild a compacted abstract from its pointer payload. |
| [compaction.py](compaction.py#L58) | `CompactionFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Any, controller: ExecutionController \| None` | `LLMOutput` | Generate one compacted context response. |
| [compaction.py](compaction.py#L112) | `serialize_request_message` | `message: Dict[str, Any]` | `str` | Serialize one request message with the shared size accounting. |
| [compaction.py](compaction.py#L117) | `estimate_context_size` | `messages: Sequence[Dict[str, Any]]` | `int` | Estimate the serialized size of the request built from *messages*. |
| [compaction.py](compaction.py#L126) | `build_request_preview` | `messages: Sequence[Dict[str, Any]], input_char_limit: int, output_max_tokens: int, threshold: int, round: int` | `CompactionRequestPreview` | Build the exact compaction request parameters without sending them. |
| [compaction.py](compaction.py#L178) | `parse_compacted_abstract` | `raw: str` | `Optional[str]` | Extract the contents of the ``<context_abstract>`` tag. |
| [handler.py](handler.py#L153) | `ContextHandlerLinear.clear_context` | `None` | `Any` | Clear all conversation entries and restart timeline numbering. |
| [handler.py](handler.py#L169) | `ContextHandlerLinear.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed internal-call usage records exactly once. |
| [handler.py](handler.py#L174) | `ContextHandlerLinear.set_compaction_event_hook` | `hook: Optional[Callable[[str, str, dict], None]]` | `None` | Attach or detach the compaction lifecycle event observer. |
| [handler.py](handler.py#L189) | `ContextHandlerLinear._emit_compaction_event` | `event_type: str, message: str, data: Dict[str, Any]` | `None` | Notify the attached observer, isolating any observer failure. |
| [handler.py](handler.py#L213) | `ContextHandlerLinear.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [handler.py](handler.py#L240) | `ContextHandlerLinear.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]], usage: Optional[Dict[str, int]], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float], controller: ExecutionController \| None` | `None` | Append an LLM output to the conversation history. |
| [handler.py](handler.py#L291) | `ContextHandlerLinear.compact` | `controller: ExecutionController \| None, keep_recent: int \| None` | `bool` | Compress the conversation history into a single abstract. |
| [handler.py](handler.py#L487) | `ContextHandlerLinear.get_prev_messages` | `None` | `List[LLMContext \| LLMContextCompacted]` | Return the stored conversation history. |
| [handler.py](handler.py#L495) | `ContextHandlerLinear.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [handler.py](handler.py#L513) | `ContextHandlerLinear._estimate_context_size` | `None` | `int` | Estimate the serialized size of this handler's next request. |
| [handler.py](handler.py#L525) | `ContextHandlerLinear._bounded_tool_results` | `tool_results: Optional[Dict[str, str]]` | `Dict[str, str]` | Copy complete tool output into the in-memory conversation history. |
| [handler.py](handler.py#L546) | `ContextHandlerLinear.compaction_request_preview` | `None` | `CompactionRequestPreview` | Build the exact compaction request parameters without sending them. |
| [handler.py](handler.py#L561) | `ContextHandlerLinear._build_compaction_input` | `None` | `str` | Render the bounded transcript one summary request would carry. |
| [handler.py](handler.py#L572) | `ContextHandlerLinear.save` | `path: str \| Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Persist metadata plus only newly-created transcript rows. |
| [handler.py](handler.py#L648) | `ContextHandlerLinear.load` | `path: Optional[str \| Path]` | `bool` | Deserialize conversation history from a JSON file. |
| [handler.py](handler.py#L735) | `ContextHandlerLinear._save_sqlite_rows` | `database: Path` | `None` | Append changed context rows in one SQLite transaction. |
| [handler.py](handler.py#L756) | `ContextHandlerLinear.replace_active_context` | `messages: list[Dict[str, Any]], database: Path, context_editing: Dict[str, object] \| None` | `int` | Replace the active transcript and its durable rows atomically. |
| [handler.py](handler.py#L805) | `ContextHandlerLinear._context_to_dict` | `ctx: LLMContext` | `Dict[str, Any]` | Serialize one context entry for hosts and persistence. |
| [handler.py](handler.py#L810) | `ContextHandlerLinear._context_from_dict` | `data: Dict[str, Any]` | `LLMContext` | Rebuild one context entry from its serialized payload. |
| [paging.py](paging.py#L15) | `read_persisted_context_page` | `path: str \| Path, before_timeline: int \| None, limit: int, include_archive: bool, storage: ContextStorage \| None` | `tuple[list[LLMContext], int \| None, int]` | Read one reverse-timeline page without loading the full checkpoint. |
| [rendering.py](rendering.py#L20) | `append_context_entry` | `messages: List[Dict[str, Any]], item: LLMContext` | `None` | Append backend-neutral messages for a single context entry. |
| [rendering.py](rendering.py#L80) | `render_messages` | `history: List[LLMContext \| LLMContextCompacted], pending_resume: bool` | `List[Dict[str, Any]]` | Render stored history into the message list for one request. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [compaction.py](compaction.py#L55) | `CompactionFetcher` | `None` | `Protocol` | Describe the minimal LLM interface used for context compaction. |
| [compaction.py](compaction.py#L88) | `CompactionRequestPreview` | `text: str, system_prompt: str, temperature: float, max_tokens: int, messages: int, omitted: int, threshold: int, round: int` | `object` | One exact, credential-free compaction request plan. |
| [handler.py](handler.py#L54) | `ContextHandlerLinear` | `compacting_llmfetcher_handler: CompactionFetcher, max_context_threshold: int, compaction_input_char_limit: int, compaction_output_max_tokens: int, event_hook: Optional[Callable[[str, str, dict], None]], storage: ContextStorage \| None, keep_recent: int` | `ContextHandler` | A simple context handler that stores messages in a flat list. |

<!-- END GENERATED SYMBOL MAP -->
