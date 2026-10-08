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
| [archive_retrieval.py](archive_retrieval.py#L35) | `ArchiveRetrievalConfig.__post_init__` | `None` | `None` | Implement `ArchiveRetrievalConfig.__post_init__`. |
| [archive_retrieval.py](archive_retrieval.py#L71) | `retrieve_archive` | `query: str, records: Sequence[LLMContext] \| Iterable[LLMContext], config: ArchiveRetrievalConfig \| None` | `ArchiveRetrievalResult` | Lexically retrieve relevant raw archived records without mutation. |
| [archive_retrieval.py](archive_retrieval.py#L141) | `_tokenize` | `text: str` | `list[str]` | Return case-insensitive lexical tokens, with useful CJK fallback. |
| [archive_retrieval.py](archive_retrieval.py#L153) | `_record_search_text` | `record: LLMContext` | `str` | Construct the local lexical index text for one raw context record. |
| [archive_retrieval.py](archive_retrieval.py#L170) | `_bounded_record_text` | `record: LLMContext, limit: int` | `str` | Render a source record with one total character cap. |
| [base.py](base.py#L37) | `ContextHandler.extra_usage` | `None` | `TokenUsage` | Token usage accumulated by internal (non-round) LLM calls. |
| [base.py](base.py#L46) | `ContextHandler.record_usage` | `usage: Optional[TokenUsage]` | `None` | Accumulate one internal LLM call's usage into ``extra_usage``. |
| [base.py](base.py#L61) | `ContextHandler.compact` | `controller: 'ExecutionController \| None'` | `bool` | Compact this handler through its linear context implementation. |
| [base.py](base.py#L75) | `ContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [base.py](base.py#L89) | `ContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]], usage: Optional[Dict[str, int]], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float], controller: 'ExecutionController \| None'` | `None` | Record an LLM response into the conversation history. |
| [base.py](base.py#L117) | `ContextHandler.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [base.py](base.py#L131) | `ContextHandler.save` | `path: str \| Path` | `bool` | Save context from disk. |
| [base.py](base.py#L143) | `ContextHandler.load` | `path: str \| Path` | `bool` | Load context from disk. |
| [base.py](base.py#L155) | `ContextHandler.clear_context` | `None` | `bool` | Clear context. |
| [registry.py](registry.py#L25) | `_create_linear` | `fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None` | `ContextHandler` | Build the flat durable transcript handler. |
| [registry.py](registry.py#L41) | `_create_sage` | `fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None` | `ContextHandler` | Build the tree-indexed transcript handler. |
| [registry.py](registry.py#L57) | `_create_graph` | `fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None` | `ContextHandler` | Build the transcript plus entity-relation graph handler. |
| [registry.py](registry.py#L120) | `available_context_handlers` | `None` | `tuple[str, ...]` | Return every selectable handler id, sorted. |
| [registry.py](registry.py#L129) | `context_handler_specs` | `None` | `tuple[ContextHandlerSpec, ...]` | Return the catalog in the order a host should present it. |
| [registry.py](registry.py#L138) | `create_context_handler` | `name: str, fetcher: CompactionFetcher, max_context_threshold: int, compaction_output_max_tokens: int, storage: ContextStorage \| None` | `ContextHandler` | Build one registered context handler. |
| [retrieved.py](retrieved.py#L65) | `_extract_json_from_text` | `text: str` | `dict[str, Any]` | Extract and parse the first valid JSON object from text via raw_decode. |
| [retrieved.py](retrieved.py#L164) | `RetrievedContextHandler._init_session_state` | `None` | `None` | (Re)set all per-session transient state (P0-J). |
| [retrieved.py](retrieved.py#L177) | `RetrievedContextHandler.has_retrieved` | `None` | `bool` | Implement `RetrievedContextHandler.has_retrieved`. |
| [retrieved.py](retrieved.py#L180) | `RetrievedContextHandler.retrieve` | `query: str` | `list[dict[str, Any]]` | Explicitly trigger TLB retrieval. |
| [retrieved.py](retrieved.py#L188) | `RetrievedContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Implement `RetrievedContextHandler.add_user_message`. |
| [retrieved.py](retrieved.py#L194) | `RetrievedContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: dict[str, str] \| None, usage: dict[str, int] \| None, model_duration_ms: int \| None, round_duration_ms: int \| None, created_at: float \| None, controller: ExecutionController \| None` | `None` | Implement `RetrievedContextHandler.add_assistant_message`. |
| [retrieved.py](retrieved.py#L214) | `RetrievedContextHandler.build_messages` | `None` | `list[dict[str, Any]]` | Build messages: retrieved as **user** role (P0-I), then linear. |
| [retrieved.py](retrieved.py#L227) | `RetrievedContextHandler.save` | `path: str \| Path` | `bool` | Implement `RetrievedContextHandler.save`. |
| [retrieved.py](retrieved.py#L235) | `RetrievedContextHandler.load` | `path: str \| Path` | `bool` | Implement `RetrievedContextHandler.load`. |
| [retrieved.py](retrieved.py#L238) | `RetrievedContextHandler.clear_context` | `None` | `bool` | Clear linear context AND reset all per-session state (P0-J). |
| [retrieved.py](retrieved.py#L246) | `RetrievedContextHandler.create_save_tool` | `None` | `Tool` | Return a Tool for LLM-triggered mid-session archival. |
| [retrieved.py](retrieved.py#L288) | `RetrievedContextHandler._should_retrieve` | `None` | `bool` | Return whether the newly added user message requires retrieval. |
| [retrieved.py](retrieved.py#L310) | `RetrievedContextHandler._retrieve_from_tlb` | `query: str` | `list[dict[str, Any]]` | Implement `RetrievedContextHandler._retrieve_from_tlb`. |
| [retrieved.py](retrieved.py#L353) | `RetrievedContextHandler._resolve_archive_targets` | `None` | `Any` | Resolve which TLB/root pairs to archive to based on scope. |
| [retrieved.py](retrieved.py#L374) | `RetrievedContextHandler._archive_session` | `None` | `_ARCHIVE_RESULT` | Archive current session to knowledge bases. |
| [retrieved.py](retrieved.py#L411) | `RetrievedContextHandler._archive_to` | `tlb: Any, root: Path, session_md: str` | `_ARCHIVE_RESULT` | Archive to one knowledge base. |
| [retrieved.py](retrieved.py#L466) | `RetrievedContextHandler._export_archival_state` | `None` | `str` | Export structured archival state from linear handler (P0-K). |
| [retrieved.py](retrieved.py#L502) | `RetrievedContextHandler._classify_session` | `session_md: str, root: Path` | `dict[str, Any]` | Implement `RetrievedContextHandler._classify_session`. |
| [retrieved.py](retrieved.py#L552) | `RetrievedContextHandler._build_session_markdown` | `transcript: str` | `str \| None` | Implement `RetrievedContextHandler._build_session_markdown`. |
| [retrieved.py](retrieved.py#L609) | `RetrievedContextHandler._summarize_session` | `transcript: str` | `dict[str, Any]` | Implement `RetrievedContextHandler._summarize_session`. |
| [retrieved.py](retrieved.py#L629) | `RetrievedContextHandler._parse_session_file` | `path: Path` | `dict[str, Any] \| None` | Implement `RetrievedContextHandler._parse_session_file`. |
| [retrieved.py](retrieved.py#L665) | `RetrievedContextHandler._messages_to_text` | `messages: list[dict[str, Any]]` | `str` | Implement `RetrievedContextHandler._messages_to_text`. |
| [retrieved.py](retrieved.py#L681) | `RetrievedContextHandler._update_index` | `index_path: Path, filename: str, topic: str, reason: str` | `None` | Implement `RetrievedContextHandler._update_index`. |
| [retrieved.py](retrieved.py#L705) | `RetrievedContextHandler._slugify` | `text: str` | `str` | Implement `RetrievedContextHandler._slugify`. |
| [retrieved.py](retrieved.py#L711) | `_image_markers` | `images: Any` | `str` | Render byte-free image provenance markers for one archived message. |
| [retrieved.py](retrieved.py#L717) | `_render_retrieved_memory` | `sessions: list[dict[str, Any]]` | `str` | Render retrieved sessions as a user-role context block (P0-I). |
| [storage.py](storage.py#L36) | `is_sqlite_context_pointer` | `pointer: Any` | `bool` | Return whether a parsed checkpoint is a schema-3 SQLite pointer. |
| [storage.py](storage.py#L63) | `ContextStorage.append_rows` | `database: Path, messages: Sequence[tuple[int, str]], archive: Sequence[tuple[int, str]]` | `None` | Append or replace serialized active and archived rows atomically. |
| [storage.py](storage.py#L82) | `ContextStorage.replace_active` | `database: Path, rows: Sequence[tuple[int, str]]` | `None` | Replace every active row, leaving archived rows untouched. |
| [storage.py](storage.py#L94) | `ContextStorage.read_page` | `checkpoint: Path, before_timeline: int \| None, limit: int, include_archive: bool` | `PersistedContextPage` | Read a bounded page using the checkpoint's database pointer. |
| [storage.py](storage.py#L114) | `ContextStorage.read_rows` | `database: Path, include_archive: bool` | `list[tuple[int, str]]` | Read raw ``(timeline, payload)`` pairs in ascending timeline order. |
| [storage.py](storage.py#L130) | `ContextStorage.count` | `database: Path, table: str` | `int` | Count rows in one storage-owned table. |
| [storage.py](storage.py#L141) | `ContextStorage.max_timeline` | `database: Path, table: str` | `int` | Return the greatest timeline in one storage-owned table. |
| [storage.py](storage.py#L165) | `SQLiteContextStorage._check_table` | `table: str` | `str` | Validate a table name against the storage-owned allowlist. |
| [storage.py](storage.py#L184) | `SQLiteContextStorage._connect` | `database: Path, readonly: bool` | `sqlite3.Connection` | Open a SQLite connection, read-only when requested. |
| [storage.py](storage.py#L202) | `SQLiteContextStorage._ensure_schema` | `connection: sqlite3.Connection` | `None` | Create the row tables and their timeline indexes when absent. |
| [storage.py](storage.py#L227) | `SQLiteContextStorage.append_rows` | `database: Path, messages: Sequence[tuple[int, str]], archive: Sequence[tuple[int, str]]` | `None` | Append or replace serialized rows, archiving in one transaction. |
| [storage.py](storage.py#L265) | `SQLiteContextStorage.replace_active` | `database: Path, rows: Sequence[tuple[int, str]]` | `None` | Replace every active message row in one transaction. |
| [storage.py](storage.py#L295) | `SQLiteContextStorage.read_rows` | `database: Path, include_archive: bool` | `list[tuple[int, str]]` | Read every stored row in ascending timeline order. |
| [storage.py](storage.py#L330) | `SQLiteContextStorage.read_page` | `checkpoint: Path, before_timeline: int \| None, limit: int, include_archive: bool` | `PersistedContextPage` | Read one bounded, newest-first page from the pointer's database. |
| [storage.py](storage.py#L403) | `SQLiteContextStorage.count` | `database: Path, table: str` | `int` | Count rows in one storage-owned table. |
| [storage.py](storage.py#L421) | `SQLiteContextStorage.max_timeline` | `database: Path, table: str` | `int` | Return the greatest timeline in one storage-owned table. |
| [tlb.py](tlb.py#L48) | `TLBContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [tlb.py](tlb.py#L62) | `TLBContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]], usage: Optional[Dict[str, int]], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float], controller: ExecutionController \| None` | `None` | Record an LLM response into the conversation history. |
| [tlb.py](tlb.py#L86) | `TLBContextHandler.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [tlb.py](tlb.py#L101) | `TLBContextHandler.save` | `path: str \| Path` | `bool` | Save context from disk. |
| [tlb.py](tlb.py#L115) | `TLBContextHandler.load` | `path: str \| Path` | `bool` | Load context from disk. |
| [tlb.py](tlb.py#L129) | `TLBContextHandler.clear_context` | `None` | `bool` | Clear context. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [archive_retrieval.py](archive_retrieval.py#L28) | `ArchiveRetrievalConfig` | `max_results: int, max_chars_per_record: int, min_score: float` | `object` | Hard bounds for local archive retrieval and returned evidence. |
| [archive_retrieval.py](archive_retrieval.py#L45) | `ArchiveEvidence` | `timeline_start: int, timeline_end: int, role: str, score: float, text: str, matched_terms: tuple[str, ...]` | `object` | A bounded, display-safe projection of one archived context record. |
| [archive_retrieval.py](archive_retrieval.py#L63) | `ArchiveRetrievalResult` | `query: str, evidence: tuple[ArchiveEvidence, ...], scanned_records: int` | `object` | Result metadata plus bounded evidence suitable for later injection. |
| [base.py](base.py#L12) | `ContextHandler` | `None` | `ABC` | Manages conversational context and builds API-ready message lists. |
| [registry.py](registry.py#L77) | `ContextHandlerSpec` | `id: str, title: str, description: str, factory: Callable[..., ContextHandler]` | `object` | One host-selectable context implementation. |
| [retrieved.py](retrieved.py#L88) | `RetrievedContextHandler` | `project_knowledge_root: str \| Path \| None, user_knowledge_root: str \| Path \| None, tlb_fetcher: CompactionFetcher, compacting_fetcher: CompactionFetcher, classify_fetcher: CompactionFetcher \| None, max_retrieved_sessions: int, retrieval_trigger: str, archive_scope: str, max_context_threshold: int` | `ContextHandler` | TLB-RAG powered conversation memory over linear context. |
| [storage.py](storage.py#L22) | `PersistedContextPage` | `rows: list[dict[str, Any]], next_before: int \| None, total: int` | `object` | One bounded page returned from durable context storage. |
| [storage.py](storage.py#L56) | `ContextStorage` | `None` | `Protocol` | Storage contract used by durable context handlers. |
| [storage.py](storage.py#L153) | `SQLiteContextStorage` | `None` | `object` | SQLite implementation of :class:`ContextStorage`. |
| [tlb.py](tlb.py#L13) | `PathStatus` | `None` | `Enum` | An enumerate about paths. |
| [tlb.py](tlb.py#L23) | `WorkingStatus` | `current_focusing: str, other_path_names: List[str], path_status: List[str]` | `object` | Provide `WorkingStatus` behavior. |
| [tlb.py](tlb.py#L29) | `TLBContextHandler` | `context_save_path: str \| Path, llm_fetcher_instance: LLMFetcher` | `ContextHandler` | Provide `TLBContextHandler` behavior. |

<!-- END GENERATED SYMBOL MAP -->
