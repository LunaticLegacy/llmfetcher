# llmfetcher/context_handlers/ — Durable Context INDEX

Context storage and retrieval contracts used by `Agent` across a session. The
nearest index owns every `context_handlers/*.py` source; the top-level
[`../INDEX.md`](../INDEX.md) owns the package-level modules.

| File | Responsibility |
|---|---|
| `base.py` | `ContextHandler` abstract contract: message assembly, checkpoint save/load, compaction hooks, and an `extra_usage` counter for internal LLM calls. |
| `linear.py` | `ContextHandlerLinear` schema-3 SQLite row store with a small JSON pointer, bounded backward paging, compaction and raw archive; `CompactionFetcher` / `CompactionRequestPreview` support previewing compaction. |
| `retrieved.py` | `RetrievedContextHandler` composes durable linear history with a provider-backed retrieval channel. |
| `archive_retrieval.py` | Bounded lexical retrieval over raw archived `LLMContext` values: `ArchiveRetrievalConfig`, `ArchiveEvidence`, `ArchiveRetrievalResult`, `retrieve_archive`. No file I/O or LLM calls. |
| `tlb.py` | `TLBContextHandler` adapter over `rag_module_tlb`; `PathStatus` / `WorkingStatus` track traversal state. |
| `__init__.py` | Public exports for the package. |

## Boundaries

- Compaction is a prompt-size optimisation, never a deletion policy: archived
  raw turns stay retrievable through `archive_retrieval.py`.
- Only the linear handler owns durable transcript persistence; retrieved and
  TLB handlers delegate storage to the linear handler.
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
| [base.py](base.py#L34) | `ContextHandler.extra_usage` | `None` | `TokenUsage` | Token usage accumulated by internal (non-round) LLM calls. |
| [base.py](base.py#L43) | `ContextHandler.record_usage` | `usage: Optional[TokenUsage]` | `None` | Accumulate one internal LLM call's usage into ``extra_usage``. |
| [base.py](base.py#L59) | `ContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [base.py](base.py#L73) | `ContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]], usage: Optional[Dict[str, int]], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float]` | `None` | Record an LLM response into the conversation history. |
| [base.py](base.py#L100) | `ContextHandler.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [base.py](base.py#L114) | `ContextHandler.save` | `path: str \| Path` | `bool` | Save context from disk. |
| [base.py](base.py#L126) | `ContextHandler.load` | `path: str \| Path` | `bool` | Load context from disk. |
| [base.py](base.py#L138) | `ContextHandler.clear_context` | `None` | `bool` | Clear context. |
| [linear.py](linear.py#L29) | `CompactionFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Any` | `LLMOutput` | Generate one compacted context response. |
| [linear.py](linear.py#L118) | `read_persisted_context_page` | `path: str \| Path, before_timeline: int \| None, limit: int, include_archive: bool` | `tuple[list[LLMContext], int \| None, int]` | Read one reverse-timeline page without loading the full checkpoint. |
| [linear.py](linear.py#L284) | `ContextHandlerLinear.clear_context` | `None` | `Any` | Clear all conversation entries and restart timeline numbering. |
| [linear.py](linear.py#L300) | `ContextHandlerLinear.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed internal-call usage records exactly once. |
| [linear.py](linear.py#L305) | `ContextHandlerLinear.set_compaction_event_hook` | `hook: Optional[Callable[[str, str, dict], None]]` | `None` | Attach or detach the compaction lifecycle event observer. |
| [linear.py](linear.py#L320) | `ContextHandlerLinear._emit_compaction_event` | `event_type: str, message: str, data: Dict[str, Any]` | `None` | Notify the attached observer, isolating any observer failure. |
| [linear.py](linear.py#L344) | `ContextHandlerLinear.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [linear.py](linear.py#L371) | `ContextHandlerLinear.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]], usage: Optional[Dict[str, int]], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float]` | `None` | Append an LLM output to the conversation history. |
| [linear.py](linear.py#L422) | `ContextHandlerLinear.compact` | `None` | `bool` | Compress the conversation history into a single abstract. |
| [linear.py](linear.py#L569) | `ContextHandlerLinear.get_prev_messages` | `None` | `List[LLMContext \| LLMContextCompacted]` | Return the stored conversation history. |
| [linear.py](linear.py#L577) | `ContextHandlerLinear.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [linear.py](linear.py#L622) | `ContextHandlerLinear._estimate_context_size` | `None` | `int` | Estimate the size of the context that would reach the model. |
| [linear.py](linear.py#L637) | `ContextHandlerLinear._bounded_tool_results` | `tool_results: Optional[Dict[str, str]]` | `Dict[str, str]` | Copy complete tool output into the in-memory conversation history. |
| [linear.py](linear.py#L658) | `ContextHandlerLinear.compaction_request_preview` | `None` | `CompactionRequestPreview` | Build the exact compaction request parameters without sending them. |
| [linear.py](linear.py#L699) | `ContextHandlerLinear._build_compaction_input` | `None` | `str` | Render a bounded, newest-first transcript for one summary request. |
| [linear.py](linear.py#L714) | `ContextHandlerLinear._parse_compacted_abstract` | `raw: str` | `Optional[str]` | Extract the contents of the ``<context_abstract>`` tag. |
| [linear.py](linear.py#L742) | `ContextHandlerLinear.save` | `path: str \| Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Persist metadata plus only newly-created transcript rows. |
| [linear.py](linear.py#L818) | `ContextHandlerLinear.load` | `path: Optional[str \| Path]` | `bool` | Deserialize conversation history from a JSON file. |
| [linear.py](linear.py#L904) | `ContextHandlerLinear._save_sqlite_rows` | `database: Path` | `None` | Append changed context rows in one SQLite transaction. |
| [linear.py](linear.py#L937) | `ContextHandlerLinear._sqlite_count` | `database: Path, table: str` | `int` | Return one table row count without reading transcript payloads. |
| [linear.py](linear.py#L954) | `ContextHandlerLinear._sqlite_max_timeline` | `database: Path, table: str` | `int` | Return the latest persisted timeline without loading rows. |
| [linear.py](linear.py#L974) | `ContextHandlerLinear._context_to_dict` | `ctx: LLMContext` | `Dict[str, Any]` | Implement `ContextHandlerLinear._context_to_dict`. |
| [linear.py](linear.py#L978) | `ContextHandlerLinear._context_from_dict` | `data: Dict[str, Any]` | `LLMContext` | Implement `ContextHandlerLinear._context_from_dict`. |
| [linear.py](linear.py#L1003) | `ContextHandlerLinear._compacted_to_dict` | `comp: Optional[LLMContextCompacted]` | `Optional[Dict[str, Any]]` | Implement `ContextHandlerLinear._compacted_to_dict`. |
| [linear.py](linear.py#L1011) | `ContextHandlerLinear._compacted_from_dict` | `data: Optional[Dict[str, Any]]` | `Optional[LLMContextCompacted]` | Implement `ContextHandlerLinear._compacted_from_dict`. |
| [linear.py](linear.py#L1025) | `ContextHandlerLinear._append_context_messages` | `messages: List[Dict[str, Any]], item: LLMContext` | `None` | Append backend-neutral messages for a single context entry. |
| [retrieved.py](retrieved.py#L64) | `_extract_json_from_text` | `text: str` | `dict[str, Any]` | Extract and parse the first valid JSON object from text via raw_decode. |
| [retrieved.py](retrieved.py#L163) | `RetrievedContextHandler._init_session_state` | `None` | `None` | (Re)set all per-session transient state (P0-J). |
| [retrieved.py](retrieved.py#L176) | `RetrievedContextHandler.has_retrieved` | `None` | `bool` | Implement `RetrievedContextHandler.has_retrieved`. |
| [retrieved.py](retrieved.py#L179) | `RetrievedContextHandler.retrieve` | `query: str` | `list[dict[str, Any]]` | Explicitly trigger TLB retrieval. |
| [retrieved.py](retrieved.py#L187) | `RetrievedContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Implement `RetrievedContextHandler.add_user_message`. |
| [retrieved.py](retrieved.py#L193) | `RetrievedContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: dict[str, str] \| None, usage: dict[str, int] \| None, model_duration_ms: int \| None, round_duration_ms: int \| None, created_at: float \| None` | `None` | Implement `RetrievedContextHandler.add_assistant_message`. |
| [retrieved.py](retrieved.py#L211) | `RetrievedContextHandler.build_messages` | `None` | `list[dict[str, Any]]` | Build messages: retrieved as **user** role (P0-I), then linear. |
| [retrieved.py](retrieved.py#L224) | `RetrievedContextHandler.save` | `path: str \| Path` | `bool` | Implement `RetrievedContextHandler.save`. |
| [retrieved.py](retrieved.py#L232) | `RetrievedContextHandler.load` | `path: str \| Path` | `bool` | Implement `RetrievedContextHandler.load`. |
| [retrieved.py](retrieved.py#L235) | `RetrievedContextHandler.clear_context` | `None` | `bool` | Clear linear context AND reset all per-session state (P0-J). |
| [retrieved.py](retrieved.py#L243) | `RetrievedContextHandler.create_save_tool` | `None` | `Tool` | Return a Tool for LLM-triggered mid-session archival. |
| [retrieved.py](retrieved.py#L285) | `RetrievedContextHandler._should_retrieve` | `None` | `bool` | Return whether the newly added user message requires retrieval. |
| [retrieved.py](retrieved.py#L307) | `RetrievedContextHandler._retrieve_from_tlb` | `query: str` | `list[dict[str, Any]]` | Implement `RetrievedContextHandler._retrieve_from_tlb`. |
| [retrieved.py](retrieved.py#L350) | `RetrievedContextHandler._resolve_archive_targets` | `None` | `Any` | Resolve which TLB/root pairs to archive to based on scope. |
| [retrieved.py](retrieved.py#L371) | `RetrievedContextHandler._archive_session` | `None` | `_ARCHIVE_RESULT` | Archive current session to knowledge bases. |
| [retrieved.py](retrieved.py#L408) | `RetrievedContextHandler._archive_to` | `tlb: Any, root: Path, session_md: str` | `_ARCHIVE_RESULT` | Archive to one knowledge base. |
| [retrieved.py](retrieved.py#L463) | `RetrievedContextHandler._export_archival_state` | `None` | `str` | Export structured archival state from linear handler (P0-K). |
| [retrieved.py](retrieved.py#L499) | `RetrievedContextHandler._classify_session` | `session_md: str, root: Path` | `dict[str, Any]` | Implement `RetrievedContextHandler._classify_session`. |
| [retrieved.py](retrieved.py#L549) | `RetrievedContextHandler._build_session_markdown` | `transcript: str` | `str \| None` | Implement `RetrievedContextHandler._build_session_markdown`. |
| [retrieved.py](retrieved.py#L606) | `RetrievedContextHandler._summarize_session` | `transcript: str` | `dict[str, Any]` | Implement `RetrievedContextHandler._summarize_session`. |
| [retrieved.py](retrieved.py#L626) | `RetrievedContextHandler._parse_session_file` | `path: Path` | `dict[str, Any] \| None` | Implement `RetrievedContextHandler._parse_session_file`. |
| [retrieved.py](retrieved.py#L662) | `RetrievedContextHandler._messages_to_text` | `messages: list[dict[str, Any]]` | `str` | Implement `RetrievedContextHandler._messages_to_text`. |
| [retrieved.py](retrieved.py#L678) | `RetrievedContextHandler._update_index` | `index_path: Path, filename: str, topic: str, reason: str` | `None` | Implement `RetrievedContextHandler._update_index`. |
| [retrieved.py](retrieved.py#L702) | `RetrievedContextHandler._slugify` | `text: str` | `str` | Implement `RetrievedContextHandler._slugify`. |
| [retrieved.py](retrieved.py#L708) | `_image_markers` | `images: Any` | `str` | Render byte-free image provenance markers for one archived message. |
| [retrieved.py](retrieved.py#L714) | `_render_retrieved_memory` | `sessions: list[dict[str, Any]]` | `str` | Render retrieved sessions as a user-role context block (P0-I). |
| [tlb.py](tlb.py#L47) | `TLBContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append an User input to conversation history. |
| [tlb.py](tlb.py#L61) | `TLBContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]], usage: Optional[Dict[str, int]], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float]` | `None` | Record an LLM response into the conversation history. |
| [tlb.py](tlb.py#L84) | `TLBContextHandler.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [tlb.py](tlb.py#L99) | `TLBContextHandler.save` | `path: str \| Path` | `bool` | Save context from disk. |
| [tlb.py](tlb.py#L113) | `TLBContextHandler.load` | `path: str \| Path` | `bool` | Load context from disk. |
| [tlb.py](tlb.py#L127) | `TLBContextHandler.clear_context` | `None` | `bool` | Clear context. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [archive_retrieval.py](archive_retrieval.py#L28) | `ArchiveRetrievalConfig` | `max_results: int, max_chars_per_record: int, min_score: float` | `object` | Hard bounds for local archive retrieval and returned evidence. |
| [archive_retrieval.py](archive_retrieval.py#L45) | `ArchiveEvidence` | `timeline_start: int, timeline_end: int, role: str, score: float, text: str, matched_terms: tuple[str, ...]` | `object` | A bounded, display-safe projection of one archived context record. |
| [archive_retrieval.py](archive_retrieval.py#L63) | `ArchiveRetrievalResult` | `query: str, evidence: tuple[ArchiveEvidence, ...], scanned_records: int` | `object` | Result metadata plus bounded evidence suitable for later injection. |
| [base.py](base.py#L9) | `ContextHandler` | `None` | `ABC` | Manages conversational context and builds API-ready message lists. |
| [linear.py](linear.py#L26) | `CompactionFetcher` | `None` | `Protocol` | Describe the minimal LLM interface used for context compaction. |
| [linear.py](linear.py#L94) | `CompactionRequestPreview` | `text: str, system_prompt: str, temperature: float, max_tokens: int, messages: int, omitted: int, threshold: int, round: int` | `object` | One exact, credential-free compaction request plan. |
| [linear.py](linear.py#L196) | `ContextHandlerLinear` | `compacting_llmfetcher_handler: CompactionFetcher, max_context_threshold: int, compaction_input_char_limit: int, compaction_output_max_tokens: int, event_hook: Optional[Callable[[str, str, dict], None]]` | `ContextHandler` | A simple context handler that stores messages in a flat list. |
| [retrieved.py](retrieved.py#L87) | `RetrievedContextHandler` | `project_knowledge_root: str \| Path \| None, user_knowledge_root: str \| Path \| None, tlb_fetcher: CompactionFetcher, compacting_fetcher: CompactionFetcher, classify_fetcher: CompactionFetcher \| None, max_retrieved_sessions: int, retrieval_trigger: str, archive_scope: str, max_context_threshold: int` | `ContextHandler` | TLB-RAG powered conversation memory over linear context. |
| [tlb.py](tlb.py#L12) | `PathStatus` | `None` | `Enum` | An enumerate about paths. |
| [tlb.py](tlb.py#L22) | `WorkingStatus` | `current_focusing: str, other_path_names: List[str], path_status: List[str]` | `object` | Provide `WorkingStatus` behavior. |
| [tlb.py](tlb.py#L28) | `TLBContextHandler` | `context_save_path: str \| Path, llm_fetcher_instance: LLMFetcher` | `ContextHandler` | Provide `TLBContextHandler` behavior. |

<!-- END GENERATED SYMBOL MAP -->
