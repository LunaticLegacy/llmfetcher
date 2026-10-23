# llmfetcher/context_handlers/ — Durable Context INDEX

Context storage and retrieval contracts used by `Agent` across a session. The
nearest index owns every `context_handlers/*.py` source; the top-level
[`../INDEX.md`](../INDEX.md) owns the package-level modules.

| File | Responsibility |
|---|---|
| `base.py` | `ContextHandler` abstract contract: message assembly, checkpoint save/load, compaction hooks, and an `extra_usage` counter for internal LLM calls. |
| [`linear/`](linear/INDEX.md) | `ContextHandlerLinear` durable linear transcript: state orchestration (`handler.py`), serialization (`codec.py`), compaction planning (`compaction.py`), message rendering (`rendering.py`) and bounded paging (`paging.py`). |
| [`sage/`](sage/INDEX.md) | `SageContext` indexes the active transcript as a set of context trees (`tree.py`); durable rows, compaction and reads are delegated to a composed linear handler. |
| [`storage.py`](storage.py) | `ContextStorage` port plus the schema-3 SQLite row store (`SQLiteContextStorage`) and `is_sqlite_context_pointer`. The only place that knows table names or issues SQL. |
| `retrieved.py` | `RetrievedContextHandler` composes durable linear history with a provider-backed retrieval channel. |
| `archive_retrieval.py` | Bounded lexical retrieval over raw archived `LLMContext` values: `ArchiveRetrievalConfig`, `ArchiveEvidence`, `ArchiveRetrievalResult`, `retrieve_archive`. No file I/O or LLM calls. |
| `tlb.py` | `TLBContextHandler` adapter over `rag_module_tlb`; `PathStatus` / `WorkingStatus` track traversal state. |
| `__init__.py` | Public exports for the package. |

## Boundaries

- Compaction is a prompt-size optimisation, never a deletion policy: archived
  raw turns stay retrievable through `archive_retrieval.py`.
- Only the linear handler owns durable transcript persistence; retrieved, TLB
  and Sage handlers delegate storage to the linear handler.
- Retrieval composition must not leak internal tool/transcript state into the
  primary Agent's visible model rounds.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [archive_retrieval.py](archive_retrieval.py#L36) | `ArchiveRetrievalConfig.__post_init__` | `None` | `None` | Implement `ArchiveRetrievalConfig.__post_init__`. |
| [archive_retrieval.py](archive_retrieval.py#L72) | `retrieve_archive` | `query: str, records: Sequence[ContextItem] \| Iterable[ContextItem], store: ContextStore, config: ArchiveRetrievalConfig \| None` | `ArchiveRetrievalResult` | Lexically retrieve relevant raw archived records without mutation. |
| [archive_retrieval.py](archive_retrieval.py#L153) | `_tokenize` | `text: str` | `list[str]` | Return case-insensitive lexical tokens, with useful CJK fallback. |
| [archive_retrieval.py](archive_retrieval.py#L165) | `_record_role` | `record: ContextItem` | `str` | Return the provider-neutral role label one archived item renders as. |
| [archive_retrieval.py](archive_retrieval.py#L178) | `_resolved_output` | `record: ContextItem, store: ContextStore` | `list[tuple[str, dict[str, object], ToolResultRecord \| None]]` | Return every tool call of one item with its resolved result. |
| [archive_retrieval.py](archive_retrieval.py#L200) | `_record_search_text` | `record: ContextItem, store: ContextStore` | `str` | Construct the local lexical index text for one raw context record. |
| [archive_retrieval.py](archive_retrieval.py#L225) | `_bounded_record_text` | `record: ContextItem, limit: int, store: ContextStore` | `str` | Render a source record with one total character cap. |
| [base.py](base.py#L32) | `checkpoint_lock` | `path: str \| Path` | `threading.RLock` | Return the process-local lock shared by all writers of one checkpoint. |
| [base.py](base.py#L47) | `replace_checkpoint` | `temporary: str \| Path, target: str \| Path` | `None` | Publish ``temporary`` as ``target``, absorbing a transient Windows denial. |
| [base.py](base.py#L105) | `ContextHandler.linear` | `None` | `'ContextHandler'` | Return the linear context surface owned by this handler. |
| [base.py](base.py#L110) | `ContextHandler.linear` | `value: 'ContextHandler'` | `None` | Implement `ContextHandler.linear`. |
| [base.py](base.py#L113) | `ContextHandler.graph_projection` | `None` | `'ContextGraphProjection'` | Return this handler's long-term entity graph for inspection. |
| [base.py](base.py#L129) | `ContextHandler.limit_tool_result_messages` | `messages: List[RequestMessage]` | `List[RequestMessage]` | Replace older tool results for the active model request only. |
| [base.py](base.py#L155) | `ContextHandler.block_source_catalog` | `None` | `tuple[ContextBlockSource, ...]` | Declare the block sources this handler can emit. |
| [base.py](base.py#L167) | `ContextHandler.build_blocks` | `snapshot: ContextSnapshot` | `list[ContextBlock]` | Expose durable handler state as a Composer-owned context source. |
| [base.py](base.py#L192) | `ContextHandler.extra_usage` | `None` | `TokenUsage` | Token usage accumulated by internal (non-round) LLM calls. |
| [base.py](base.py#L201) | `ContextHandler.record_usage` | `usage: Optional[TokenUsage]` | `None` | Accumulate one internal LLM call's usage into ``extra_usage``. |
| [base.py](base.py#L216) | `ContextHandler.compact` | `controller: 'ExecutionController \| None', keep_recent: 'int \| None'` | `bool` | Compact this handler through its linear context implementation. |
| [base.py](base.py#L241) | `ContextHandler._init_session_state` | `None` | `None` | Reset transient composed-handler state when no reset is needed. |
| [base.py](base.py#L245) | `ContextHandler.set_compaction_event_hook` | `hook: object` | `None` | Install a compaction event hook when the handler supports one. |
| [base.py](base.py#L249) | `ContextHandler.drain_usage_records` | `None` | `list[object]` | Return internal usage records accumulated by this handler. |
| [base.py](base.py#L253) | `ContextHandler.apply_pending_branch_commands` | `None` | `list[dict[str, str]]` | Apply pending branch commands when the handler supports them. |
| [base.py](base.py#L258) | `ContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [base.py](base.py#L272) | `ContextHandler.add_assistant_message` | `turn: AssistantTurnInput, tool_results: Sequence[ToolResultInput], controller: 'ExecutionController \| None'` | `None` | Record one completed assistant turn into the conversation history. |
| [base.py](base.py#L292) | `ContextHandler.build_messages` | `system_prompt: str \| None` | `List[RequestMessage]` | Build context messages for an LLM request. |
| [base.py](base.py#L309) | `ContextHandler.describe_request_messages` | `messages: List[RequestMessage]` | `list[dict[str, Any]]` | Describe the origin of messages in a request preview. |
| [base.py](base.py#L336) | `ContextHandler.save` | `path: str \| Path` | `bool` | Save context from disk. |
| [base.py](base.py#L348) | `ContextHandler.load` | `path: str \| Path` | `bool` | Load context from disk. |
| [base.py](base.py#L360) | `ContextHandler.clear_context` | `None` | `bool` | Clear context. |
| [composer.py](composer.py#L77) | `ContextSource.source_id` | `None` | `str` | Return the stable source identity with no setter. |
| [composer.py](composer.py#L85) | `ContextSource.build_blocks` | `snapshot: ContextSnapshot` | `Sequence[ContextBlock]` | Project source state into request blocks. |
| [composer.py](composer.py#L93) | `ContextHandlerPort.limit_tool_result_messages` | `messages: list[RequestMessage]` | `list[RequestMessage]` | Bound tool-result text for the outgoing model request. |
| [composer.py](composer.py#L100) | `ContextHandlerPort.block_source_catalog` | `None` | `tuple[ContextBlockSource, ...]` | Declare every block source this handler can emit. |
| [composer.py](composer.py#L108) | `HandlerBlockSource.build_messages` | `system_prompt: str \| None` | `list[RequestMessage]` | Return the handler's complete provider-neutral context. |
| [composer.py](composer.py#L143) | `ContextProvider.build_blocks` | `snapshot: ContextSnapshot` | `Sequence[ContextBlock]` | Build blocks for one model request. |
| [composer.py](composer.py#L197) | `ContextComposer.effective_priority` | `source: str, default_priority: int` | `int` | Return the priority one block source is ordered by. |
| [composer.py](composer.py#L215) | `ContextComposer.is_ordered` | `source: str` | `bool` | Return whether the saved table gives this source an explicit slot. |
| [composer.py](composer.py#L220) | `ContextComposer.providers` | `None` | `tuple[ContextSource, ...]` | Return the currently registered providers in registration order. |
| [composer.py](composer.py#L224) | `ContextComposer.register` | `provider: ContextSource` | `None` | Register a provider for future requests. |
| [composer.py](composer.py#L241) | `ContextComposer.blocks` | `snapshot: ContextSnapshot` | `list[ContextBlock]` | Collect, filter, and stably sort provider blocks. |
| [composer.py](composer.py#L269) | `ContextComposer.render` | `blocks: Sequence[ContextBlock]` | `list[RequestMessage]` | Render blocks as provider-neutral request messages. |
| [composer.py](composer.py#L286) | `ContextComposer.compose` | `snapshot: ContextSnapshot, system_prompt: str \| None` | `list[RequestMessage]` | Build the complete request in the canonical context order. |
| [composer.py](composer.py#L313) | `ContextComposer.describe` | `snapshot: ContextSnapshot, system_prompt: str \| None` | `list[JsonObject]` | Describe the exact composed messages with source provenance. |
| [composer.py](composer.py#L359) | `ContextComposer.catalog` | `snapshot: ContextSnapshot` | `list[ContextBlockSource]` | List block sources the active handler declares, present or not. |
| [composer.py](composer.py#L387) | `HandlerContextSource.build_blocks` | `snapshot: ContextSnapshot` | `Sequence[ContextBlock]` | Render the handler's durable context without its system prompt. |
| [empty.py](empty.py#L61) | `NullContext.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append a user input and index it in the tree. |
| [empty.py](empty.py#L72) | `NullContext.add_assistant_message` | `turn: AssistantTurnInput, tool_results: Sequence[ToolResultInput], controller: ExecutionController \| None` | `None` | Discard an assistant turn. |
| [empty.py](empty.py#L91) | `NullContext.build_messages` | `system_prompt: str \| None` | `List[RequestMessage]` | Render the active history exactly as the composed handler does. |
| [empty.py](empty.py#L102) | `NullContext.compact` | `controller: ExecutionController \| None, keep_recent: Optional[int]` | `bool` | Compact the composed transcript, then re-index what remains. |
| [empty.py](empty.py#L120) | `NullContext.save` | `path: str \| Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Persist the composed checkpoint and mirror its failure cause. |
| [empty.py](empty.py#L143) | `NullContext.load` | `path: Optional[str \| Path]` | `bool` | Restore the composed checkpoint and rebuild the tree index. |
| [empty.py](empty.py#L155) | `NullContext.clear_context` | `None` | `bool` | Clear the transcript, the timeline and the tree index. |
| [registry.py](registry.py#L25) | `_create_linear` | `fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None, keep_recent: int, settings: Mapping[str, Any] \| None` | `ContextHandler` | Build the flat durable transcript handler. |
| [registry.py](registry.py#L44) | `_create_sage` | `fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None, keep_recent: int, settings: Mapping[str, Any] \| None` | `ContextHandler` | Build the branch-aware Sage handler. |
| [registry.py](registry.py#L64) | `_create_graph` | `fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None, keep_recent: int, settings: Mapping[str, Any] \| None` | `ContextHandler` | Build the transcript plus entity-relation graph handler. |
| [registry.py](registry.py#L178) | `available_context_handlers` | `None` | `tuple[str, ...]` | Return every selectable handler id, sorted. |
| [registry.py](registry.py#L187) | `context_handler_revision` | `None` | `str` | Return a stable revision for host Agent cache fingerprints. |
| [registry.py](registry.py#L192) | `context_handler_specs` | `None` | `tuple[ContextHandlerSpec, ...]` | Return the catalog in the order a host should present it. |
| [registry.py](registry.py#L201) | `create_context_handler` | `name: str, fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None, keep_recent: int, settings: Mapping[str, Any] \| None` | `ContextHandler` | Build one registered context handler. |
| [registry.py](registry.py#L245) | `normalize_context_settings` | `spec: ContextHandlerSpec, values: Mapping[str, Any] \| None` | `dict[str, Any]` | Apply defaults and validate handler-specific settings. |
| [retrieved.py](retrieved.py#L63) | `_index_lock` | `path: Path` | `threading.RLock` | Return the process-local lock protecting one archive INDEX.md. |
| [retrieved.py](retrieved.py#L70) | `_write_text_atomic` | `path: Path, text: str` | `None` | Publish one UTF-8 text file without exposing a partial write. |
| [retrieved.py](retrieved.py#L123) | `_extract_json_from_text` | `text: str` | `dict[str, Any]` | Extract and parse the first valid JSON object from text via raw_decode. |
| [retrieved.py](retrieved.py#L222) | `RetrievedContextHandler._init_session_state` | `None` | `None` | (Re)set all per-session transient state (P0-J). |
| [retrieved.py](retrieved.py#L235) | `RetrievedContextHandler.has_retrieved` | `None` | `bool` | Implement `RetrievedContextHandler.has_retrieved`. |
| [retrieved.py](retrieved.py#L238) | `RetrievedContextHandler.retrieve` | `query: str` | `list[dict[str, Any]]` | Explicitly trigger TLB retrieval. |
| [retrieved.py](retrieved.py#L246) | `RetrievedContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Implement `RetrievedContextHandler.add_user_message`. |
| [retrieved.py](retrieved.py#L252) | `RetrievedContextHandler.add_assistant_message` | `turn: AssistantTurnInput, tool_results: Sequence[ToolResultInput], controller: ExecutionController \| None` | `None` | Implement `RetrievedContextHandler.add_assistant_message`. |
| [retrieved.py](retrieved.py#L265) | `RetrievedContextHandler.build_messages` | `system_prompt: str \| None` | `list[RequestMessage]` | Build messages: retrieved as **user** role (P0-I), then linear. |
| [retrieved.py](retrieved.py#L280) | `RetrievedContextHandler.save` | `path: str \| Path` | `bool` | Implement `RetrievedContextHandler.save`. |
| [retrieved.py](retrieved.py#L288) | `RetrievedContextHandler.load` | `path: str \| Path` | `bool` | Implement `RetrievedContextHandler.load`. |
| [retrieved.py](retrieved.py#L291) | `RetrievedContextHandler.clear_context` | `None` | `bool` | Clear linear context AND reset all per-session state (P0-J). |
| [retrieved.py](retrieved.py#L299) | `RetrievedContextHandler.create_save_tool` | `None` | `Tool` | Return a Tool for LLM-triggered mid-session archival. |
| [retrieved.py](retrieved.py#L341) | `RetrievedContextHandler._should_retrieve` | `None` | `bool` | Return whether the newly added user message requires retrieval. |
| [retrieved.py](retrieved.py#L363) | `RetrievedContextHandler._retrieve_from_tlb` | `query: str` | `list[dict[str, Any]]` | Implement `RetrievedContextHandler._retrieve_from_tlb`. |
| [retrieved.py](retrieved.py#L406) | `RetrievedContextHandler._resolve_archive_targets` | `None` | `Any` | Resolve which TLB/root pairs to archive to based on scope. |
| [retrieved.py](retrieved.py#L427) | `RetrievedContextHandler._archive_session` | `None` | `_ARCHIVE_RESULT` | Archive current session to knowledge bases. |
| [retrieved.py](retrieved.py#L464) | `RetrievedContextHandler._archive_to` | `tlb: Any, root: Path, session_md: str` | `_ARCHIVE_RESULT` | Archive to one knowledge base. |
| [retrieved.py](retrieved.py#L519) | `RetrievedContextHandler._export_archival_state` | `None` | `str` | Export structured archival state from linear handler (P0-K). |
| [retrieved.py](retrieved.py#L545) | `RetrievedContextHandler._classify_session` | `session_md: str, root: Path` | `dict[str, Any]` | Implement `RetrievedContextHandler._classify_session`. |
| [retrieved.py](retrieved.py#L595) | `RetrievedContextHandler._build_session_markdown` | `transcript: str` | `str \| None` | Implement `RetrievedContextHandler._build_session_markdown`. |
| [retrieved.py](retrieved.py#L652) | `RetrievedContextHandler._summarize_session` | `transcript: str` | `dict[str, Any]` | Implement `RetrievedContextHandler._summarize_session`. |
| [retrieved.py](retrieved.py#L672) | `RetrievedContextHandler._parse_session_file` | `path: Path` | `dict[str, Any] \| None` | Implement `RetrievedContextHandler._parse_session_file`. |
| [retrieved.py](retrieved.py#L707) | `RetrievedContextHandler._render_context` | `item: ContextItem` | `'_RenderedMessage'` | Project one durable context item onto the archival render shape. |
| [retrieved.py](retrieved.py#L748) | `RetrievedContextHandler._render_request` | `message: RequestMessage` | `'_RenderedMessage'` | Project one rendered request message onto the archival render shape. |
| [retrieved.py](retrieved.py#L758) | `RetrievedContextHandler._messages_to_text` | `messages: Sequence['_RenderedMessage']` | `str` | Flatten one archival render shape into retrieval text. |
| [retrieved.py](retrieved.py#L776) | `RetrievedContextHandler._update_index` | `index_path: Path, filename: str, topic: str, reason: str` | `None` | Implement `RetrievedContextHandler._update_index`. |
| [retrieved.py](retrieved.py#L800) | `RetrievedContextHandler._slugify` | `text: str` | `str` | Implement `RetrievedContextHandler._slugify`. |
| [retrieved.py](retrieved.py#L806) | `_image_markers` | `images: Any` | `str` | Render byte-free image provenance markers for one archived message. |
| [retrieved.py](retrieved.py#L812) | `_render_retrieved_memory` | `sessions: list[dict[str, Any]]` | `str` | Render retrieved sessions as a user-role context block (P0-I). |
| [storage.py](storage.py#L53) | `is_sqlite_context_pointer` | `pointer: Any` | `bool` | Return whether a parsed checkpoint is a v2 SQLite pointer. |
| [storage.py](storage.py#L81) | `ContextStorage.append_rows` | `database: Path, messages: Sequence[tuple[int, str]], archive: Sequence[tuple[int, str]], tool_results: Sequence[tuple[str, str]]` | `None` | Append or replace serialized rows atomically. |
| [storage.py](storage.py#L105) | `ContextStorage.replace_active` | `database: Path, rows: Sequence[tuple[int, str]]` | `None` | Replace every active row, leaving archived rows untouched. |
| [storage.py](storage.py#L117) | `ContextStorage.read_page` | `checkpoint: Path, before_timeline: int \| None, limit: int, include_archive: bool` | `PersistedContextPage` | Read a bounded page using the checkpoint's database pointer. |
| [storage.py](storage.py#L138) | `ContextStorage.read_archive_page` | `checkpoint: Path, before_timeline: int \| None, limit: int` | `PersistedArchivePage` | Read one archive-only page using the checkpoint's database pointer. |
| [storage.py](storage.py#L158) | `ContextStorage.read_rows` | `database: Path, include_archive: bool` | `list[tuple[int, str]]` | Read raw ``(timeline, payload)`` pairs in ascending timeline order. |
| [storage.py](storage.py#L175) | `ContextStorage.count` | `database: Path, table: str` | `int` | Count rows in one storage-owned table. |
| [storage.py](storage.py#L187) | `ContextStorage.max_timeline` | `database: Path, table: str` | `int` | Return the greatest timeline in one storage-owned table. |
| [storage.py](storage.py#L199) | `ContextStorage.read_tool_results` | `database: Path, result_ids: Sequence[str]` | `list[tuple[str, str]]` | Read raw ``(result_id, payload)`` pairs for the requested results. |
| [storage.py](storage.py#L217) | `ContextStorage.count_tool_results` | `database: Path` | `int` | Count the independently stored tool results. |
| [storage.py](storage.py#L241) | `SQLiteContextStorage._check_table` | `table: str` | `str` | Validate a table name against the storage-owned allowlist. |
| [storage.py](storage.py#L260) | `SQLiteContextStorage._connect` | `database: Path, readonly: bool` | `sqlite3.Connection` | Open a SQLite connection, read-only when requested. |
| [storage.py](storage.py#L278) | `SQLiteContextStorage._ensure_schema` | `connection: sqlite3.Connection` | `None` | Create the row tables and their timeline indexes when absent. |
| [storage.py](storage.py#L310) | `SQLiteContextStorage._database_path` | `checkpoint: Path` | `Path` | Resolve and validate the sidecar database named by a checkpoint. |
| [storage.py](storage.py#L333) | `SQLiteContextStorage.append_rows` | `database: Path, messages: Sequence[tuple[int, str]], archive: Sequence[tuple[int, str]], tool_results: Sequence[tuple[str, str]]` | `None` | Append or replace serialized rows in one transaction. |
| [storage.py](storage.py#L393) | `SQLiteContextStorage.read_tool_results` | `database: Path, result_ids: Sequence[str]` | `list[tuple[str, str]]` | Read the stored payloads for the requested result identities. |
| [storage.py](storage.py#L423) | `SQLiteContextStorage.count_tool_results` | `database: Path` | `int` | Count the independently stored tool results. |
| [storage.py](storage.py#L439) | `SQLiteContextStorage.replace_active` | `database: Path, rows: Sequence[tuple[int, str]]` | `None` | Replace every active message row in one transaction. |
| [storage.py](storage.py#L477) | `SQLiteContextStorage.read_rows` | `database: Path, include_archive: bool` | `list[tuple[int, str]]` | Read every stored row in ascending timeline order. |
| [storage.py](storage.py#L512) | `SQLiteContextStorage.read_page` | `checkpoint: Path, before_timeline: int \| None, limit: int, include_archive: bool` | `PersistedContextPage` | Read one bounded, newest-first page from the pointer's database. |
| [storage.py](storage.py#L576) | `SQLiteContextStorage.read_archive_page` | `checkpoint: Path, before_timeline: int \| None, limit: int` | `PersistedArchivePage` | Read one bounded, archive-only page from the pointer's database. |
| [storage.py](storage.py#L628) | `SQLiteContextStorage.count` | `database: Path, table: str` | `int` | Count rows in one storage-owned table. |
| [storage.py](storage.py#L646) | `SQLiteContextStorage.max_timeline` | `database: Path, table: str` | `int` | Return the greatest timeline in one storage-owned table. |
| [tlb.py](tlb.py#L49) | `TLBContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [tlb.py](tlb.py#L63) | `TLBContextHandler.add_assistant_message` | `turn: AssistantTurnInput, tool_results: Sequence[ToolResultInput], controller: ExecutionController \| None` | `None` | Record an LLM response into the conversation history. |
| [tlb.py](tlb.py#L82) | `TLBContextHandler.build_messages` | `system_prompt: str \| None` | `List[RequestMessage]` | Build context messages for an LLM request. |
| [tlb.py](tlb.py#L94) | `TLBContextHandler.save` | `path: str \| Path` | `bool` | Save context from disk. |
| [tlb.py](tlb.py#L108) | `TLBContextHandler.load` | `path: str \| Path` | `bool` | Load context from disk. |
| [tlb.py](tlb.py#L122) | `TLBContextHandler.clear_context` | `None` | `bool` | Clear context. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [archive_retrieval.py](archive_retrieval.py#L29) | `ArchiveRetrievalConfig` | `max_results: int, max_chars_per_record: int, min_score: float` | `object` | Hard bounds for local archive retrieval and returned evidence. |
| [archive_retrieval.py](archive_retrieval.py#L46) | `ArchiveEvidence` | `timeline_start: int, timeline_end: int, role: str, score: float, text: str, matched_terms: tuple[str, ...]` | `object` | A bounded, display-safe projection of one archived context record. |
| [archive_retrieval.py](archive_retrieval.py#L64) | `ArchiveRetrievalResult` | `query: str, evidence: tuple[ArchiveEvidence, ...], scanned_records: int` | `object` | Result metadata plus bounded evidence suitable for later injection. |
| [base.py](base.py#L72) | `ContextHandler` | `None` | `ABC` | Manages conversational state and exposes it as a context source. |
| [composer.py](composer.py#L12) | `ContextPosition` | `None` | `IntEnum` | Canonical position of a block in the assembled request. |
| [composer.py](composer.py#L29) | `ContextBlock` | `role: MessageRole, content: str, source: str, position: 'ContextPosition', priority: int, persistent: bool, enabled: bool, metadata: Mapping[str, JsonValue], message: RequestMessage \| None` | `object` | One bounded semantic contribution to a model request. |
| [composer.py](composer.py#L56) | `ContextBlockSource` | `source: str, position: 'ContextPosition'` | `object` | One block source a handler can emit, whether or not it emits one now. |
| [composer.py](composer.py#L73) | `ContextSource` | `None` | `Protocol` | Source contract consumed by :class:`ContextComposer`. |
| [composer.py](composer.py#L90) | `ContextHandlerPort` | `None` | `Protocol` | Handler capability the composer itself invokes for one request. |
| [composer.py](composer.py#L105) | `HandlerBlockSource` | `None` | `Protocol` | Read-only handler surface used by :class:`HandlerContextSource`. |
| [composer.py](composer.py#L118) | `ContextSnapshot` | `handler: ContextHandlerPort \| None, system_prompt: str \| None, current_message: str \| None, metadata: Mapping[str, JsonValue]` | `object` | Read-only information exposed to context providers for one request. |
| [composer.py](composer.py#L134) | `ContextProvider` | `provider_id: str` | `ContextSource, Protocol` | Plugin contract for adding context without owning conversation state. |
| [composer.py](composer.py#L155) | `ContextComposer` | `providers: Sequence[ContextSource], priority_overrides: Mapping[str, int] \| None` | `object` | Validate, order, and render provider-produced blocks. |
| [composer.py](composer.py#L379) | `HandlerContextSource` | `handler: HandlerBlockSource` | `object` | Adapter that exposes a context handler as a composer source. |
| [empty.py](empty.py#L35) | `NullContext` | `compacting_fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None` | `ContextHandler` | Index a composed linear transcript as a set of context trees. |
| [placement.py](placement.py#L11) | `ToolResultPlacement` | `None` | `StrEnum` | Where an assembled request places the results of a tool batch. |
| [registry.py](registry.py#L92) | `ContextSettingSpec` | `key: str, title: str, description: str, type: str, default: Any, enum: tuple[str, ...], minimum: float \| None, maximum: float \| None` | `object` | One UI and validation descriptor for a handler-specific setting. |
| [registry.py](registry.py#L106) | `ContextHandlerSpec` | `id: str, title: str, description: str, factory: Callable[..., ContextHandler], exposed_tools: tuple[str, ...], settings: tuple[ContextSettingSpec, ...]` | `object` | One host-selectable context implementation. |
| [retrieved.py](retrieved.py#L44) | `_RenderedMessage` | `role: str, content: str, images: tuple[ImageReference, ...], tool_calls: tuple[tuple[str, tuple[ImageReference, ...]], ...]` | `object` | One message projected onto the archival render shape. |
| [retrieved.py](retrieved.py#L146) | `RetrievedContextHandler` | `project_knowledge_root: str \| Path \| None, user_knowledge_root: str \| Path \| None, tlb_fetcher: CompactionFetcher, compacting_fetcher: CompactionFetcher, classify_fetcher: CompactionFetcher \| None, max_retrieved_sessions: int, retrieval_trigger: str, archive_scope: str, max_context_threshold: int` | `ContextHandler` | TLB-RAG powered conversation memory over linear context. |
| [storage.py](storage.py#L24) | `PersistedContextPage` | `rows: list[dict[str, Any]], next_before: int \| None, total: int` | `object` | One bounded page returned from durable context storage. |
| [storage.py](storage.py#L39) | `PersistedArchivePage` | `rows: list[dict[str, Any]], next_before: int \| None, has_more: bool` | `object` | One bounded archive-only page returned from durable storage. |
| [storage.py](storage.py#L74) | `ContextStorage` | `None` | `Protocol` | Storage contract used by durable context handlers. |
| [storage.py](storage.py#L229) | `SQLiteContextStorage` | `None` | `object` | SQLite implementation of :class:`ContextStorage`. |
| [tlb.py](tlb.py#L14) | `PathStatus` | `None` | `Enum` | An enumerate about paths. |
| [tlb.py](tlb.py#L24) | `WorkingStatus` | `current_focusing: str, other_path_names: List[str], path_status: List[str]` | `object` | Provide `WorkingStatus` behavior. |
| [tlb.py](tlb.py#L30) | `TLBContextHandler` | `context_save_path: str \| Path, llm_fetcher_instance: LLMFetcher` | `ContextHandler` | Provide `TLBContextHandler` behavior. |

<!-- END GENERATED SYMBOL MAP -->
