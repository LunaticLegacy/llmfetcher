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
| [assembly.py](assembly.py#L105) | `ContextAssembler.assemble` | `items: Sequence[ContextItem], placement: ToolResultPlacement, pending_resume: bool` | `AssembledContext` | Build both projections for one model request. |
| [assembly.py](assembly.py#L280) | `_fold_reasoning` | `reasoning: str, content: str` | `str` | Fold native reasoning into content inside a ``<think>`` block. |
| [assembly.py](assembly.py#L288) | `_deferred_message` | `entries: Sequence[tuple[str, ToolResultRecord]]` | `RequestMessage \| None` | Merge every deferred result into one system message. |
| [assembly.py](assembly.py#L315) | `_validate_interleaved` | `messages: Sequence[RequestMessage]` | `None` | Reject a tool message that does not answer the preceding assistant turn. |
| [codec.py](codec.py#L31) | `_field` | `data: JsonObject, key: str` | `JsonValue` | Return one required payload field. |
| [codec.py](codec.py#L42) | `_text` | `data: JsonObject, key: str` | `str` | Return one required string field. |
| [codec.py](codec.py#L50) | `_number` | `data: JsonObject, key: str` | `int` | Return one required integer field. |
| [codec.py](codec.py#L58) | `_optional_int` | `data: JsonObject, key: str` | `int \| None` | Return an optional integer field, rejecting wrong types. |
| [codec.py](codec.py#L68) | `_optional_float` | `data: JsonObject, key: str` | `float \| None` | Return an optional numeric field, rejecting wrong types. |
| [codec.py](codec.py#L78) | `_objects` | `data: JsonObject, key: str` | `list[JsonObject]` | Return one required list of JSON objects. |
| [codec.py](codec.py#L91) | `_texts` | `data: JsonObject, key: str` | `tuple[str, ...]` | Return one required list of strings. |
| [codec.py](codec.py#L99) | `_as_text` | `value: JsonValue, key: str` | `str` | Return one string list entry. |
| [codec.py](codec.py#L106) | `_images_to_json` | `images: tuple[ImageReference, ...]` | `list[JsonValue]` | Encode durable image references without any image bytes. |
| [codec.py](codec.py#L120) | `_images_from_json` | `value: JsonValue` | `tuple[ImageReference, ...]` | Decode image references through the shared validator. |
| [codec.py](codec.py#L142) | `_usage_to_json` | `usage: TokenUsage` | `JsonObject` | Encode one token-usage snapshot. |
| [codec.py](codec.py#L153) | `_usage_from_json` | `value: JsonValue` | `TokenUsage` | Decode one token-usage snapshot. |
| [codec.py](codec.py#L167) | `_tool_call_to_json` | `call: ToolCallRecord` | `JsonObject` | Encode one tool-call reference. |
| [codec.py](codec.py#L177) | `_tool_call_from_json` | `data: JsonObject` | `ToolCallRecord` | Decode one tool-call reference without inventing an ID. |
| [codec.py](codec.py#L197) | `tool_result_to_dict` | `record: ToolResultRecord` | `JsonObject` | Serialize one complete tool result for its own storage row. |
| [codec.py](codec.py#L211) | `tool_result_from_dict` | `data: JsonObject` | `ToolResultRecord` | Rebuild one complete tool result from its storage row. |
| [codec.py](codec.py#L228) | `context_item_to_dict` | `item: ContextItem` | `JsonObject` | Serialize one ordered context item. |
| [codec.py](codec.py#L279) | `context_item_from_dict` | `data: JsonObject` | `ContextItem` | Rebuild one ordered context item from its storage row. |
| [codec.py](codec.py#L325) | `_field_list` | `data: JsonObject, key: str` | `list[JsonValue]` | Return one required generic list field. |
| [codec.py](codec.py#L333) | `_number_entry` | `value: JsonValue` | `int` | Return one integer list entry. |
| [compaction.py](compaction.py#L58) | `CompactionFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Any, controller: ExecutionController \| None` | `LLMOutput` | Generate one compacted context response. |
| [compaction.py](compaction.py#L112) | `serialize_request_message` | `message: RequestMessage` | `str` | Serialize one request message with the shared size accounting. |
| [compaction.py](compaction.py#L117) | `estimate_context_size` | `messages: Sequence[RequestMessage]` | `int` | Estimate the serialized size of the request built from *messages*. |
| [compaction.py](compaction.py#L126) | `build_request_preview` | `messages: Sequence[RequestMessage], input_char_limit: int, output_max_tokens: int, threshold: int, round: int` | `CompactionRequestPreview` | Build the exact compaction request parameters without sending them. |
| [compaction.py](compaction.py#L178) | `parse_compacted_abstract` | `raw: str` | `Optional[str]` | Extract the contents of the ``<context_abstract>`` tag. |
| [handler.py](handler.py#L176) | `ContextHandlerLinear.clear_context` | `None` | `Any` | Clear all conversation entries and restart timeline numbering. |
| [handler.py](handler.py#L194) | `ContextHandlerLinear.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed internal-call usage records exactly once. |
| [handler.py](handler.py#L199) | `ContextHandlerLinear.set_compaction_event_hook` | `hook: Optional[Callable[[str, str, dict], None]]` | `None` | Attach or detach the compaction lifecycle event observer. |
| [handler.py](handler.py#L214) | `ContextHandlerLinear._emit_compaction_event` | `event_type: str, message: str, data: Dict[str, Any]` | `None` | Notify the attached observer, isolating any observer failure. |
| [handler.py](handler.py#L238) | `ContextHandlerLinear.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [handler.py](handler.py#L265) | `ContextHandlerLinear.add_assistant_message` | `turn: AssistantTurnInput, tool_results: Sequence[ToolResultInput], controller: ExecutionController \| None` | `None` | Append one durable assistant turn to the conversation history. |
| [handler.py](handler.py#L345) | `ContextHandlerLinear.resolve_tool_result` | `result_id: ToolResultId` | `ToolResultRecord` | Return the stored result a durable tool call references. |
| [handler.py](handler.py#L364) | `ContextHandlerLinear.compact` | `controller: ExecutionController \| None, keep_recent: int \| None` | `bool` | Compress the conversation history into a single abstract. |
| [handler.py](handler.py#L576) | `ContextHandlerLinear.get_prev_messages` | `None` | `List[ContextItem]` | Return the stored conversation history. |
| [handler.py](handler.py#L584) | `ContextHandlerLinear.build_messages` | `system_prompt: str \| None` | `List[RequestMessage]` | Build context messages for an LLM request. |
| [handler.py](handler.py#L605) | `ContextHandlerLinear.block_source_catalog` | `None` | `tuple[ContextBlockSource, ...]` | Declare the transcript slots even when a slot has no item. |
| [handler.py](handler.py#L622) | `ContextHandlerLinear.build_blocks` | `snapshot: ContextSnapshot` | `list[ContextBlock]` | Project the linear transcript into Composer ordering slots. |
| [handler.py](handler.py#L684) | `ContextHandlerLinear._estimate_context_size` | `None` | `int` | Estimate the serialized size of this handler's next request. |
| [handler.py](handler.py#L696) | `ContextHandlerLinear.compaction_request_preview` | `None` | `CompactionRequestPreview` | Build the exact compaction request parameters without sending them. |
| [handler.py](handler.py#L711) | `ContextHandlerLinear._build_compaction_input` | `None` | `str` | Render the bounded transcript one summary request would carry. |
| [handler.py](handler.py#L722) | `ContextHandlerLinear.save` | `path: str \| Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Persist metadata plus only newly-created transcript rows. |
| [handler.py](handler.py#L749) | `ContextHandlerLinear._save_locked` | `target: Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Implement `ContextHandlerLinear._save_locked`. |
| [handler.py](handler.py#L806) | `ContextHandlerLinear.load` | `path: Optional[str \| Path]` | `bool` | Deserialize conversation history from a JSON file. |
| [handler.py](handler.py#L916) | `ContextHandlerLinear._save_sqlite_rows` | `database: Path` | `None` | Append changed context rows in one SQLite transaction. |
| [handler.py](handler.py#L948) | `ContextHandlerLinear.replace_active_context` | `messages: list[JsonObject], database: Path, context_editing: Dict[str, object] \| None` | `int` | Replace the active transcript and its durable rows atomically. |
| [paging.py](paging.py#L16) | `read_persisted_context_page` | `path: str \| Path, before_timeline: int \| None, limit: int, include_archive: bool, storage: ContextStorage \| None` | `tuple[list[ContextItem], int \| None, int]` | Read one reverse-timeline page without loading the full checkpoint. |
| [paging.py](paging.py#L63) | `read_persisted_archive_page` | `path: str \| Path, before_timeline: int \| None, limit: int, storage: ContextStorage \| None` | `tuple[list[ContextItem], int \| None, bool]` | Read one archive-only page without loading the active transcript. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [assembly.py](assembly.py#L49) | `ContextAssemblyError` | `None` | `RuntimeError` | Raised when a transcript cannot produce a valid model request. |
| [assembly.py](assembly.py#L54) | `ContextObservation` | `kind: ObservationKind, source: str, item_id: ContextItemId \| None, timeline: int \| None, call_id: str \| None, result_id: ToolResultId \| None, characters: int, truncated: bool, ok: bool \| None, duration_ms: int \| None` | `object` | One source fragment of an assembled request. |
| [assembly.py](assembly.py#L83) | `AssembledContext` | `messages: tuple[RequestMessage, ...], observations: tuple[ContextObservation, ...]` | `object` | The model and observation projections of one request. |
| [assembly.py](assembly.py#L95) | `ContextAssembler` | `store: ContextStore` | `object` | Join ordered context items with the results they reference. |
| [compaction.py](compaction.py#L55) | `CompactionFetcher` | `None` | `Protocol` | Describe the minimal LLM interface used for context compaction. |
| [compaction.py](compaction.py#L88) | `CompactionRequestPreview` | `text: str, system_prompt: str, temperature: float, max_tokens: int, messages: int, omitted: int, threshold: int, round: int` | `object` | One exact, credential-free compaction request plan. |
| [handler.py](handler.py#L70) | `ContextHandlerLinear` | `compacting_llmfetcher_handler: CompactionFetcher, max_context_threshold: int, compaction_input_char_limit: int, compaction_output_max_tokens: int, event_hook: Optional[Callable[[str, str, dict], None]], storage: ContextStorage \| None, keep_recent: int` | `ContextHandler` | A simple context handler that stores messages in a flat list. |

<!-- END GENERATED SYMBOL MAP -->
