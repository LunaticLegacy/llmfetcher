# llmfetcher/ — Submodule INDEX

Git submodule containing the synchronous Python framework Angelus builds on.
It provides provider-neutral LLM dispatch, tool-using agents, durable context
handlers, graph/archive memory, and dependency-driven multi-agent execution.

> This file describes the checked-out submodule. Run submodule commands from
> the superproject only when deliberately updating its recorded revision.

## Package Map

| Area | Paths | Current responsibility |
|---|---|---|
| Public API | `__init__.py`, `llm_types.py` | Public imports, request/response, tool, context, token-usage, and terminal request-cancellation types. `ToolSchema` supports both compact first-party parameters and lossless external JSON Schema (for example MCP). |
| Agent loop | `agent.py`, `events.py`, `usage_ledger.py` | Synchronous model/tool loop; the system message contains only system instructions while registered tools travel once through provider-native schemas. Optional provider streaming emits incremental content/reasoning events but reconstructs the same final output for tools and durable context. Explicit `AgentRunOutcome` terminal states distinguish formal answers, reserved `stop_turn`, workflow completion, user stop, invalid empty responses, and exhausted tool-loop budgets. |
| LLM dispatch | `llm_fetcher.py`, `fetcher_handlers/` | Backend selection, ordinary retry/fallback, terminal request cancellation, credential-free preflight request observation, and OpenAI-compatible, DeepSeek, Anthropic, LiteLLM, OpenVINO, and ONNX Runtime adapters. |
| Execution control | `execution/` | Per-attempt `ExecutionController`, unified graceful/forced stop requests, resource canceller registration, stream interruption and queued steering messages. |
| Context | `context_handlers/` | Base contract; durable linear history with compaction and raw archive; provider-backed retrieval composition; TLB adapter. `context_less_context/` is an experimental local worktree directory, not part of the indexed API. |
| Graph memory | `graph_memory/` | Persistent entity/relation store, incremental extraction, hybrid graph retrieval, archive evidence, and stateless semantic extraction/reranking workers. |
| Swarm | `swarm_module/` | Dependency graph, concurrent scheduler, TaskBus, bounded report handoff, and quiescent graph save/load. Assignments may carry an opaque external plan-leaf correlation ID that is preserved through events and snapshots. Repeated `run()` calls retain graph vertices; terminal dispatched tasks remain inspectable but are not implicitly rescheduled, and may be revived with a new immutable assignment. |
| Tools | `tool_handler.py`, `tool_executor.py`, `tools/` | Tool schemas/registry, parallel execution, and built-in shell, knowledge, web, and dynamic-spawn factories; `create_swarm_tools` accepts a shared worker pool, a name-bound factory, an optional live-Agent binder, and optional external-plan leaf validation for worker-local handlers needing persistence/reload callbacks. |
| Retrieval modules | `rag_module/`, `rag_module_tlb/` | Legacy/knowledge-base RAG and auditable `INDEX.md` tree traversal. See [`rag_module_tlb/INDEX.md`](rag_module_tlb/INDEX.md). |
| Interfaces | `cli.py`, `demo/` | Local CLI and example entry point. Browser control-plane ownership belongs to Angelus. |
| Verification | `tests/` | Unit and regression coverage for public API, context, DeepSeek routing, execution graph, TaskBus, and usage ledger. |

## Angelus Integration Points

| Component | Import / path | Why Angelus uses it |
|---|---|---|
| Fetching | `LLMFetcher`, `LLMBackendConfig`, `LLMRequestCancelled` | Configures primary/fallback backend calls; ordinary failures can retry, while `abort_active_requests()` is terminal and never retries or falls back. |
| Agent execution | `Agent`, `AgentRunControl` | Runs a session, forwards cooperative stop/steer controls to both ordinary and streaming provider calls, observes an optional `force_stopped` event during provider I/O, checkpoints completed context, and emits lifecycle events. |
| Execution control | `ExecutionController`, `StopMode`, `StopRequest` | One attempt-local stop authority. Graceful and force-stop share a terminal request; force invokes registered resource cancellers and wakes blocking stream waits. |
| Durable context | `ContextHandlerLinear` | Schema 3 SQLite row-store with a small JSON pointer: recovery loads only the newest 200 active turns, API readers page backward by timeline, and compaction archives rows without full-transcript rewrites. Legacy JSON remains readable for the one-shot migration script. |
| Long-term graph | `GraphContextHandler`, `SemanticGraphWorker` | Graph/archive retrieval; extraction and reranking calls are isolated from the primary Agent's tools and transcript. |
| Observability | `ExecutionEvent`, `agent:usage`, `agent:internal_usage` | Supplies SSE/event-log evidence and non-duplicated five-dimension token accounting. |
| Swarms | `AgentSwarm`, `ExecutionGraph`, `TaskBus` | Schedules dependent agents and passes bounded reports rather than raw worker transcripts. |
| Agent context configuration | `Agent.set_context_threshold` | Updates the in-memory threshold; `Agent.run` reapplies the configured value after checkpoint load and persists it at a safe boundary. |

## Persistence Boundaries

- Linear context atomically persists a small metadata pointer while transcript
  rows live in SQLite. Normal saves append only new timelines; recovery and
  inspection query bounded windows rather than parsing a complete transcript.
- `GraphContextHandler` writes an immutable generation graph first, then
  atomically commits its filename from the primary context JSON. Legacy fixed
  `<context-path>.graph.json` companions remain readable.
- Execution-graph persistence is owned by `swarm_module`; `AgentSwarm.save`
  and `.load` delegate to quiescent `ExecutionGraph` snapshots. Built-in
  declarative mapper/router choices serialize as data; arbitrary callbacks
  still require an explicit registry. Runtime events are emitted by the
  caller's hook rather than written by this package globally.
- API-key storage is an application concern; `LLMBackendConfig` receives a key
  only for the process making the request.

## Execution Control Boundary

- `ExecutionController` is created per Angelus `ExecutionAttempt`; it is not
  a process-global cancellation latch and must never be reused by a later run.
- A graceful request is observed at Agent safe boundaries. A forced request
  additionally calls registered cancellers (provider I/O, tool processes) and
  interrupts registered stream resources. Both remain one stop lifecycle.
- The package does not own journal/checkpoint directories. Angelus records
  controller lifecycle facts and durable interruption evidence around it.

## Local Checks

```bash
../.venv/bin/python -m unittest discover -s llmfetcher/tests -p 'test_*.py'
```

The full project may also have root-level integration tests; run those from the
Angelus superproject rather than treating them as submodule tests.

`GraphContextHandler` forwards `compaction_output_max_tokens` to its linear
history handler. This limits only the compactor's generated summary, never the
primary model response.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [agent.py](agent.py#L37) | `AgentRunControl.should_stop` | `None` | `bool` | Return whether the Agent should stop at the current safe boundary. |
| [agent.py](agent.py#L41) | `AgentRunControl.drain_steers` | `None` | `list[str]` | Return and consume queued user steering messages in FIFO order. |
| [agent.py](agent.py#L110) | `AgentRunOutcome.to_dict` | `None` | `dict[str, Any]` | Return the credential-free terminal fields for lifecycle events. |
| [agent.py](agent.py#L120) | `_tool_result_text` | `value: Any` | `str` | Return the complete tool-result string supplied back to the model. |
| [agent.py](agent.py#L245) | `Agent.add_hook` | `hook: ExecutionHook` | `None` | Register an execution-event receiver. |
| [agent.py](agent.py#L256) | `Agent.remove_hook` | `hook: ExecutionHook` | `bool` | Unregister one execution-event receiver. |
| [agent.py](agent.py#L271) | `Agent.request_completion` | `None` | `None` | Request completion after the active model-and-tool step finishes. |
| [agent.py](agent.py#L284) | `Agent.request_turn_stop` | `reason: str` | `None` | Request a normal boundary from the reserved ``stop_turn`` tool. |
| [agent.py](agent.py#L299) | `Agent.add_stop_turn_tool` | `None` | `bool` | Register the reserved model-visible control tool for ending a turn. |
| [agent.py](agent.py#L308) | `Agent._create_stop_turn_tool` | `None` | `Tool` | Create the reserved model-visible control tool for ending a turn. |
| [agent.py](agent.py#L336) | `Agent._set_outcome` | `termination: AgentRunTermination, rounds: int, detail: str, output: LLMOutput \| None` | `AgentRunOutcome` | Record and publish the single explicit terminal result of this run. |
| [agent.py](agent.py#L363) | `Agent.set_context_threshold` | `max_context_threshold: int, persist: bool` | `bool` | Update the compaction threshold used by this Agent's context. |
| [agent.py](agent.py#L403) | `Agent._emit` | `source: str, agent_name: str, event_type: str, message: str, data: Any` | `None` | Send one event to each registered hook, isolating hook failures. |
| [agent.py](agent.py#L437) | `Agent._compaction_event_hook` | `event_type: str, message: str, data: dict` | `None` | Publish a context-handler compaction lifecycle event. |
| [agent.py](agent.py#L461) | `Agent._usage_data` | `usage: TokenUsage` | `dict[str, int]` | Serialize every normalized usage dimension for durable events. |
| [agent.py](agent.py#L471) | `Agent._drain_internal_usage` | `name: str` | `None` | Publish and aggregate each hidden LLM call once, if supported. |
| [agent.py](agent.py#L488) | `Agent.add_tool` | `tool: Tool` | `bool` | Register one callable tool on this Agent. |
| [agent.py](agent.py#L499) | `Agent.add_tools` | `tools: List[Tool]` | `bool` | Register a batch of tools in the supplied order. |
| [agent.py](agent.py#L519) | `Agent._build_prompt` | `None` | `str` | Return the system prompt without serializing registered tools into it. |
| [agent.py](agent.py#L533) | `Agent._save_context` | `None` | `bool` | Persist the current context when this Agent has a storage path. |
| [agent.py](agent.py#L553) | `Agent._fetch_model_with_force_stop` | `control: AgentRunControl \| None, **fetch_kwargs: Any` | `LLMOutput` | Fetch one model response, allowing a terminal browser force-stop. |
| [agent.py](agent.py#L585) | `Agent._stream_model_response` | `name: str, round_idx: int, control: AgentRunControl \| None, **fetch_kwargs: Any` | `LLMOutput` | Stream one provider response, emit deltas, and rebuild its final form. |
| [agent.py](agent.py#L667) | `Agent.run` | `message: str, max_rounds: int \| None, temperature: float, max_tokens: int \| None, verbose: bool, control: AgentRunControl \| None, stream: bool \| None` | `LLMOutput` | Run the Agent until one explicit terminal outcome is reached. |
| [agent.py](agent.py#L1110) | `Agent.close` | `None` | `None` | Release sub-interpreter resources held by the tool executor. |
| [agent.py](agent.py#L1114) | `Agent.clear_context` | `None` | `None` | Clear context. |
| [cli.py](cli.py#L58) | `_load_tools` | `names: list[str]` | `list[Tool]` | Import and call tool factories by short name. |
| [cli.py](cli.py#L94) | `_build_parser` | `None` | `argparse.ArgumentParser` | Implement `_build_parser`. |
| [cli.py](cli.py#L178) | `_cmd_list_backends` | `None` | `None` | Print every registered backend provider. |
| [cli.py](cli.py#L189) | `_cmd_list_tools` | `None` | `None` | Print every known tool-set name + description. |
| [cli.py](cli.py#L202) | `_build_backend_config` | `args: argparse.Namespace` | `LLMBackendConfig` | Construct a single ``LLMBackendConfig`` from parsed args. |
| [cli.py](cli.py#L229) | `_bootstrap_agent` | `args: argparse.Namespace` | `Agent` | Create an ``Agent`` wired with the CLI config and requested tools. |
| [cli.py](cli.py#L260) | `_cmd_run` | `args: argparse.Namespace` | `None` | Execute a single prompt and print the final response. |
| [cli.py](cli.py#L287) | `_cmd_chat` | `args: argparse.Namespace` | `None` | Interactive read-eval-print loop. |
| [cli.py](cli.py#L318) | `main` | `argv: list[str] \| None` | `None` | Parse CLI arguments and dispatch the selected command. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L34) | `ArchiveRetrievalConfig.__post_init__` | `None` | `None` | Implement `ArchiveRetrievalConfig.__post_init__`. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L70) | `retrieve_archive` | `query: str, records: Sequence[LLMContext] \| Iterable[LLMContext], config: ArchiveRetrievalConfig \| None` | `ArchiveRetrievalResult` | Lexically retrieve relevant raw archived records without mutation. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L140) | `_tokenize` | `text: str` | `list[str]` | Return case-insensitive lexical tokens, with useful CJK fallback. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L152) | `_record_search_text` | `record: LLMContext` | `str` | Construct the local lexical index text for one raw context record. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L163) | `_bounded_record_text` | `record: LLMContext, limit: int` | `str` | Render a source record with one total character cap. |
| [context_handlers/base.py](context_handlers/base.py#L28) | `ContextHandler.extra_usage` | `None` | `TokenUsage` | Token usage accumulated by internal (non-round) LLM calls. |
| [context_handlers/base.py](context_handlers/base.py#L37) | `ContextHandler.record_usage` | `usage: Optional[TokenUsage]` | `None` | Accumulate one internal LLM call's usage into ``extra_usage``. |
| [context_handlers/base.py](context_handlers/base.py#L53) | `ContextHandler.add_user_message` | `message: str` | `None` | Append an User input to conversation history. |
| [context_handlers/base.py](context_handlers/base.py#L65) | `ContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]]` | `None` | Record an LLM response into the conversation history. |
| [context_handlers/base.py](context_handlers/base.py#L83) | `ContextHandler.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [context_handlers/base.py](context_handlers/base.py#L97) | `ContextHandler.save` | `path: str \| Path` | `bool` | Save context from disk. |
| [context_handlers/base.py](context_handlers/base.py#L109) | `ContextHandler.load` | `path: str \| Path` | `bool` | Load context from disk. |
| [context_handlers/base.py](context_handlers/base.py#L121) | `ContextHandler.clear_context` | `None` | `bool` | Clear context. |
| [context_handlers/linear.py](context_handlers/linear.py#L27) | `CompactionFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Any` | `LLMOutput` | Generate one compacted context response. |
| [context_handlers/linear.py](context_handlers/linear.py#L119) | `read_persisted_context_page` | `path: str \| Path, before_timeline: int \| None, limit: int` | `tuple[list[LLMContext], int \| None, int]` | Read one reverse-timeline page without loading the full checkpoint. |
| [context_handlers/linear.py](context_handlers/linear.py#L271) | `ContextHandlerLinear.clear_context` | `None` | `Any` | Clear all conversation entries and restart timeline numbering. |
| [context_handlers/linear.py](context_handlers/linear.py#L287) | `ContextHandlerLinear.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed internal-call usage records exactly once. |
| [context_handlers/linear.py](context_handlers/linear.py#L292) | `ContextHandlerLinear.set_compaction_event_hook` | `hook: Optional[Callable[[str, str, dict], None]]` | `None` | Attach or detach the compaction lifecycle event observer. |
| [context_handlers/linear.py](context_handlers/linear.py#L307) | `ContextHandlerLinear._emit_compaction_event` | `event_type: str, message: str, data: Dict[str, Any]` | `None` | Notify the attached observer, isolating any observer failure. |
| [context_handlers/linear.py](context_handlers/linear.py#L331) | `ContextHandlerLinear.add_user_message` | `message: str` | `None` | Append an User input to conversation history. |
| [context_handlers/linear.py](context_handlers/linear.py#L355) | `ContextHandlerLinear.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]]` | `None` | Append an LLM output to the conversation history. |
| [context_handlers/linear.py](context_handlers/linear.py#L394) | `ContextHandlerLinear.compact` | `None` | `bool` | Compress the conversation history into a single abstract. |
| [context_handlers/linear.py](context_handlers/linear.py#L541) | `ContextHandlerLinear.get_prev_messages` | `None` | `List[LLMContext \| LLMContextCompacted]` | Return the stored conversation history. |
| [context_handlers/linear.py](context_handlers/linear.py#L549) | `ContextHandlerLinear.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [context_handlers/linear.py](context_handlers/linear.py#L601) | `ContextHandlerLinear._estimate_context_size` | `None` | `int` | Estimate the size of the context that would reach the model. |
| [context_handlers/linear.py](context_handlers/linear.py#L617) | `ContextHandlerLinear._bound_result_text` | `value: str, limit: int` | `str` | Return a request-safe copy of a tool result bounded to *limit* chars. |
| [context_handlers/linear.py](context_handlers/linear.py#L649) | `ContextHandlerLinear._bounded_tool_results` | `tool_results: Optional[Dict[str, str]]` | `Dict[str, str]` | Copy complete tool output into the in-memory conversation history. |
| [context_handlers/linear.py](context_handlers/linear.py#L672) | `ContextHandlerLinear.compaction_request_preview` | `None` | `CompactionRequestPreview` | Build the exact compaction request parameters without sending them. |
| [context_handlers/linear.py](context_handlers/linear.py#L713) | `ContextHandlerLinear._build_compaction_input` | `None` | `str` | Render a bounded, newest-first transcript for one summary request. |
| [context_handlers/linear.py](context_handlers/linear.py#L728) | `ContextHandlerLinear._parse_compacted_abstract` | `raw: str` | `Optional[str]` | Extract the contents of the ``<context_abstract>`` tag. |
| [context_handlers/linear.py](context_handlers/linear.py#L756) | `ContextHandlerLinear.save` | `path: str \| Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Persist metadata plus only newly-created transcript rows. |
| [context_handlers/linear.py](context_handlers/linear.py#L829) | `ContextHandlerLinear.load` | `path: Optional[str \| Path]` | `bool` | Deserialize conversation history from a JSON file. |
| [context_handlers/linear.py](context_handlers/linear.py#L915) | `ContextHandlerLinear._save_sqlite_rows` | `database: Path` | `None` | Append changed context rows in one SQLite transaction. |
| [context_handlers/linear.py](context_handlers/linear.py#L948) | `ContextHandlerLinear._sqlite_count` | `database: Path, table: str` | `int` | Return one table row count without reading transcript payloads. |
| [context_handlers/linear.py](context_handlers/linear.py#L965) | `ContextHandlerLinear._sqlite_max_timeline` | `database: Path, table: str` | `int` | Return the latest persisted timeline without loading rows. |
| [context_handlers/linear.py](context_handlers/linear.py#L985) | `ContextHandlerLinear._context_to_dict` | `ctx: LLMContext` | `Dict[str, Any]` | Implement `ContextHandlerLinear._context_to_dict`. |
| [context_handlers/linear.py](context_handlers/linear.py#L989) | `ContextHandlerLinear._context_from_dict` | `data: Dict[str, Any]` | `LLMContext` | Implement `ContextHandlerLinear._context_from_dict`. |
| [context_handlers/linear.py](context_handlers/linear.py#L1009) | `ContextHandlerLinear._compacted_to_dict` | `comp: Optional[LLMContextCompacted]` | `Optional[Dict[str, Any]]` | Implement `ContextHandlerLinear._compacted_to_dict`. |
| [context_handlers/linear.py](context_handlers/linear.py#L1017) | `ContextHandlerLinear._compacted_from_dict` | `data: Optional[Dict[str, Any]]` | `Optional[LLMContextCompacted]` | Implement `ContextHandlerLinear._compacted_from_dict`. |
| [context_handlers/linear.py](context_handlers/linear.py#L1031) | `ContextHandlerLinear._append_context_messages` | `messages: List[Dict[str, Any]], item: LLMContext, remaining_budget: Optional[List[int]]` | `None` | Append backend-neutral messages for a single context entry. |
| [context_handlers/linear.py](context_handlers/linear.py#L1103) | `ContextHandlerLinear._render_tool_result_for_model` | `raw_result: str, remaining_budget: Optional[List[int]]` | `str` | Bound one result and annotate it when it is large for the model. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L63) | `_extract_json_from_text` | `text: str` | `dict[str, Any]` | Extract and parse the first valid JSON object from text via raw_decode. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L162) | `RetrievedContextHandler._init_session_state` | `None` | `None` | (Re)set all per-session transient state (P0-J). |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L175) | `RetrievedContextHandler.has_retrieved` | `None` | `bool` | Implement `RetrievedContextHandler.has_retrieved`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L178) | `RetrievedContextHandler.retrieve` | `query: str` | `list[dict[str, Any]]` | Explicitly trigger TLB retrieval. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L186) | `RetrievedContextHandler.add_user_message` | `message: str` | `None` | Implement `RetrievedContextHandler.add_user_message`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L192) | `RetrievedContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: dict[str, str] \| None` | `None` | Implement `RetrievedContextHandler.add_assistant_message`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L197) | `RetrievedContextHandler.build_messages` | `None` | `list[dict[str, Any]]` | Build messages: retrieved as **user** role (P0-I), then linear. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L210) | `RetrievedContextHandler.save` | `path: str \| Path` | `bool` | Implement `RetrievedContextHandler.save`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L218) | `RetrievedContextHandler.load` | `path: str \| Path` | `bool` | Implement `RetrievedContextHandler.load`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L221) | `RetrievedContextHandler.clear_context` | `None` | `bool` | Clear linear context AND reset all per-session state (P0-J). |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L229) | `RetrievedContextHandler.create_save_tool` | `None` | `Tool` | Return a Tool for LLM-triggered mid-session archival. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L271) | `RetrievedContextHandler._should_retrieve` | `None` | `bool` | Return whether the newly added user message requires retrieval. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L293) | `RetrievedContextHandler._retrieve_from_tlb` | `query: str` | `list[dict[str, Any]]` | Implement `RetrievedContextHandler._retrieve_from_tlb`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L336) | `RetrievedContextHandler._resolve_archive_targets` | `None` | `Any` | Resolve which TLB/root pairs to archive to based on scope. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L357) | `RetrievedContextHandler._archive_session` | `None` | `_ARCHIVE_RESULT` | Archive current session to knowledge bases. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L394) | `RetrievedContextHandler._archive_to` | `tlb: Any, root: Path, session_md: str` | `_ARCHIVE_RESULT` | Archive to one knowledge base. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L449) | `RetrievedContextHandler._export_archival_state` | `None` | `str` | Export structured archival state from linear handler (P0-K). |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L475) | `RetrievedContextHandler._classify_session` | `session_md: str, root: Path` | `dict[str, Any]` | Implement `RetrievedContextHandler._classify_session`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L525) | `RetrievedContextHandler._build_session_markdown` | `transcript: str` | `str \| None` | Implement `RetrievedContextHandler._build_session_markdown`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L582) | `RetrievedContextHandler._summarize_session` | `transcript: str` | `dict[str, Any]` | Implement `RetrievedContextHandler._summarize_session`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L602) | `RetrievedContextHandler._parse_session_file` | `path: Path` | `dict[str, Any] \| None` | Implement `RetrievedContextHandler._parse_session_file`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L638) | `RetrievedContextHandler._messages_to_text` | `messages: list[dict[str, Any]]` | `str` | Implement `RetrievedContextHandler._messages_to_text`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L654) | `RetrievedContextHandler._update_index` | `index_path: Path, filename: str, topic: str, reason: str` | `None` | Implement `RetrievedContextHandler._update_index`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L678) | `RetrievedContextHandler._slugify` | `text: str` | `str` | Implement `RetrievedContextHandler._slugify`. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L684) | `_render_retrieved_memory` | `sessions: list[dict[str, Any]]` | `str` | Render retrieved sessions as a user-role context block (P0-I). |
| [context_handlers/tlb.py](context_handlers/tlb.py#L47) | `TLBContextHandler.add_user_message` | `message: str` | `None` | Append an User input to conversation history. |
| [context_handlers/tlb.py](context_handlers/tlb.py#L60) | `TLBContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]]` | `None` | Record an LLM response into the conversation history. |
| [context_handlers/tlb.py](context_handlers/tlb.py#L78) | `TLBContextHandler.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [context_handlers/tlb.py](context_handlers/tlb.py#L93) | `TLBContextHandler.save` | `path: str \| Path` | `bool` | Save context from disk. |
| [context_handlers/tlb.py](context_handlers/tlb.py#L107) | `TLBContextHandler.load` | `path: str \| Path` | `bool` | Load context from disk. |
| [context_handlers/tlb.py](context_handlers/tlb.py#L121) | `TLBContextHandler.clear_context` | `None` | `bool` | Clear context. |
| [demo/demo.py](demo/demo.py#L23) | `main` | `None` | `Any` | Implement `main`. |
| [fetcher_handlers/_tool_schemas.py](fetcher_handlers/_tool_schemas.py#L8) | `tool_to_openai_schema` | `tool: Tool` | `ToolSchemaDict` | Serialize an executable tool into OpenAI-style function schema. |
| [fetcher_handlers/_tool_schemas.py](fetcher_handlers/_tool_schemas.py#L20) | `to_openai_tool_schemas` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Normalize runtime tools or legacy schemas into OpenAI-compatible payloads. |
| [fetcher_handlers/_tool_schemas.py](fetcher_handlers/_tool_schemas.py#L36) | `to_anthropic_tool_schemas` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Normalize runtime tools or legacy schemas into Anthropic tool payloads. |
| [fetcher_handlers/anthropic.py](fetcher_handlers/anthropic.py#L26) | `AnthropicHandler.convert_messages` | `messages: list[dict[str, str]]` | `tuple[list[dict[str, JSONValue]], Optional[str]]` | Implement `AnthropicHandler.convert_messages`. |
| [fetcher_handlers/anthropic.py](fetcher_handlers/anthropic.py#L55) | `AnthropicHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Prepare tools for Anthropic's `input_schema` tool format. |
| [fetcher_handlers/anthropic.py](fetcher_handlers/anthropic.py#L62) | `AnthropicHandler._normalize_anthropic_blocks` | `blocks: Iterable[object \| Mapping[str, JSONValue]]` | `tuple[str, str, list[LLMToolCall]]` | Implement `AnthropicHandler._normalize_anthropic_blocks`. |
| [fetcher_handlers/anthropic.py](fetcher_handlers/anthropic.py#L94) | `AnthropicHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: Any` | `Any` | Implement `AnthropicHandler.create_completion`. |
| [fetcher_handlers/anthropic.py](fetcher_handlers/anthropic.py#L118) | `AnthropicHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `AnthropicHandler.normalize_completion_response`. |
| [fetcher_handlers/anthropic.py](fetcher_handlers/anthropic.py#L133) | `AnthropicHandler.iter_stream_text` | `response: Any, output_reasoning: bool, usage_capture: Any` | `Iterable[str]` | Implement `AnthropicHandler.iter_stream_text`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L30) | `_UsageLike.model_dump` | `None` | `JSONObject` | Implement `_UsageLike.model_dump`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L58) | `LLMBackendHandler.supports_backend` | `backend: LLMBackendConfig` | `bool` | Args: cls: The class to check. Should be a subclass of `LLMBackendHandler`. backend: The backend configuration to check. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L70) | `LLMBackendHandler.from_backend` | `fetcher: 'LLMFetcher', backend: LLMBackendConfig` | `'LLMBackendHandler'` | Create an instance from a backend config. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L86) | `LLMBackendHandler._iter_descendants` | `None` | `Iterable[type['LLMBackendHandler']]` | Implement `LLMBackendHandler._iter_descendants`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L92) | `LLMBackendHandler.create_for_backend` | `fetcher: 'LLMFetcher', backend: LLMBackendConfig` | `'LLMBackendHandler'` | Implement `LLMBackendHandler.create_for_backend`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L111) | `LLMBackendHandler.create_completion` | `messages: list[dict[str, str]], temperature: float, max_tokens: int, stream: bool, tools: Optional[list[ToolSchemaDict]]` | `Any` | Implement `LLMBackendHandler.create_completion`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L123) | `LLMBackendHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `LLMBackendHandler.normalize_completion_response`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L127) | `LLMBackendHandler.iter_stream_text` | `response: Any, output_reasoning: bool, usage_capture: Any` | `Iterable[str]` | Yield normalized text chunks, optionally capturing raw usage. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L150) | `LLMBackendHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Convert registry tools or prebuilt schemas into this provider's shape. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L167) | `LLMBackendHandler.build_chat_history` | `messages: list[dict[str, str]], tools: Optional[list[ToolSchemaDict]]` | `Any` | Implement `LLMBackendHandler.build_chat_history`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L174) | `LLMBackendHandler.generation_config` | `temperature: float, max_tokens: int` | `JSONObject` | Generate a JSON object for the LLM backend to use as a generation configuration. Optional for inhereting classes. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L181) | `LLMBackendHandler.abort_active_request` | `None` | `bool` | Close this handler's client to interrupt an in-flight request. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L201) | `LLMBackendHandler.result_text` | `result: Any` | `str` | Implement `LLMBackendHandler.result_text`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L204) | `LLMBackendHandler._read_field` | `value: object \| Mapping[str, JSONValue] \| None, name: str, default: object \| JSONValue \| None` | `object \| JSONValue \| None` | Read a field from a value. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L222) | `LLMBackendHandler._coerce_content_to_text` | `content: str \| Sequence[JSONValue] \| object \| None` | `str` | Implement `LLMBackendHandler._coerce_content_to_text`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L245) | `LLMBackendHandler._usage_to_dict` | `usage: _UsageLike \| Mapping[str, JSONValue] \| None` | `JSONObject` | Deprecated: use _normalize_usage() instead. Kept for subclasses that may override this method. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L271) | `LLMBackendHandler.normalize_usage` | `usage: _UsageLike \| Mapping[str, JSONValue] \| None` | `TokenUsage` | Normalize a provider-specific usage response into a platform-irrelevant TokenUsage. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L309) | `LLMBackendHandler._parse_arguments` | `arguments: str \| Mapping[str, JSONValue] \| None` | `JSONObject` | Implement `LLMBackendHandler._parse_arguments`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L320) | `LLMBackendHandler._extract_content` | `delta: object \| Mapping[str, JSONValue] \| None` | `Optional[str]` | Implement `LLMBackendHandler._extract_content`. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L332) | `LLMBackendHandler._extract_reasoning` | `delta: object \| Mapping[str, JSONValue] \| None` | `Optional[str]` | Implement `LLMBackendHandler._extract_reasoning`. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L58) | `DeepSeekHandler.supports_backend` | `backend: LLMBackendConfig` | `bool` | Recognise DeepSeek behind an OpenAI-compatible configuration. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L86) | `DeepSeekHandler._message_reasoning` | `message: object \| Mapping[str, object] \| None` | `str` | DeepSeek exposes reasoning exclusively via ``reasoning_content``. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L98) | `DeepSeekHandler._delta_reasoning` | `delta: object \| Mapping[str, object] \| None` | `Optional[str]` | Read ``reasoning_content`` from one streamed delta (and only that). |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L114) | `DeepSeekHandler._strip_think_blocks` | `text: str` | `str` | Remove ``<think>...</think>`` blocks from assistant content. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L125) | `DeepSeekHandler._split_think_blocks` | `text: str` | `tuple[str, str]` | Move ``<think>...</think>`` blocks out of model content. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L141) | `DeepSeekHandler._sanitize_messages` | `messages: Sequence[Mapping[str, Any]]` | `list[dict[str, Any]]` | Strip context-handler ``<think>`` wrappers from assistant turns. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L158) | `DeepSeekHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: List['Any']` | `Any` | Send a request with assistant ``<think>`` wrappers removed. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L176) | `DeepSeekHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Extract any ``<think>`` the model echoed into ``reasoning_content``. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L199) | `DeepSeekHandler.normalize_usage` | `usage: object \| Mapping[str, object] \| None` | `TokenUsage` | Map DeepSeek's ``prompt_cache_hit_tokens`` onto cached tokens. |
| [fetcher_handlers/litellm.py](fetcher_handlers/litellm.py#L13) | `LiteLLMHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: Any` | `Any` | Implement `LiteLLMHandler.create_completion`. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L21) | `_ensure_cuda_runtime` | `None` | `bool` | Pre-load CUDA 12 compat .so files from nvidia pip packages. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L65) | `_parse_xml_tool_calls` | `text: str` | `list[_ParsedToolCall]` | Extract ``<tool_call>`` blocks containing JSON from *text*. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L88) | `_strip_xml_tool_calls` | `text: str` | `str` | Remove ``<tool_call>`` XML blocks from *text*. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L121) | `_resolve_model_options` | `device: str` | `dict[str, Any]` | Map a human-readable device name to onnxruntime-genai model options. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L154) | `_resolve_search_options` | `temperature: float, max_tokens: int, extra: Optional[dict[str, Any]]` | `dict[str, Any]` | Build the search-options dict passed to ``GeneratorParams.set_search_options``. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L175) | `_coerce_chat_template_context` | `value: Any` | `dict[str, Any]` | Return backend ``extra_context`` as template keyword arguments. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L184) | `_infer_enable_thinking` | `messages: Sequence[dict[str, str]]` | `Optional[bool]` | Infer Qwen thinking mode from the last explicit prompt directive. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L194) | `_apply_thinking_prefix` | `prompt: str, context: dict[str, Any]` | `str` | Inject Qwen3's no-thinking prefix after ORT renders the chat template. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L260) | `OnnxRuntimeGenAIHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Implement `OnnxRuntimeGenAIHandler.prepare_tools`. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L268) | `OnnxRuntimeGenAIHandler.build_chat_history` | `messages: list[dict[str, str]], tools: Optional[list[ToolSchemaDict]]` | `list[dict[str, str]]` | Return messages as-is; the tokenizer's built-in chat template handles the formatting during ``tokenizer.encode_chat()``. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L280) | `OnnxRuntimeGenAIHandler.generation_config` | `temperature: float, max_tokens: int` | `JSONObject` | Implement `OnnxRuntimeGenAIHandler.generation_config`. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L296) | `OnnxRuntimeGenAIHandler.chat_template_context` | `messages: Sequence[dict[str, str]]` | `dict[str, Any]` | Implement `OnnxRuntimeGenAIHandler.chat_template_context`. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L309) | `OnnxRuntimeGenAIHandler.create_completion` | `messages: list[dict[str, str]], temperature: float, max_tokens: int, stream: bool, tools: Optional[list[ToolSchemaDict]]` | `Any` | Implement `OnnxRuntimeGenAIHandler.create_completion`. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L339) | `OnnxRuntimeGenAIHandler._create_completion_blocking` | `input_ids: Any, params: Any` | `_ONNXCompletionResponse` | Generate the full output sequence without streaming. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L366) | `OnnxRuntimeGenAIHandler._create_stream` | `input_ids: Any, params: Any` | `Iterable[str]` | Yield text chunks as they are generated, via a background thread. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L401) | `OnnxRuntimeGenAIHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `OnnxRuntimeGenAIHandler.normalize_completion_response`. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L429) | `OnnxRuntimeGenAIHandler.iter_stream_text` | `response: Any, output_reasoning: bool` | `Iterable[str]` | Implement `OnnxRuntimeGenAIHandler.iter_stream_text`. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L23) | `OpenAIHandler._normalize_messages` | `messages: list[dict[str, Any]]` | `list[dict[str, Any]]` | Convert backend-neutral ``tool_calls`` to OpenAI format. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L53) | `OpenAIHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Prepare tools for OpenAI-compatible chat-completion APIs. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L60) | `OpenAIHandler._normalize_openai_tool_calls` | `message: object \| Mapping[str, Any] \| None` | `list[LLMToolCall]` | Implement `OpenAIHandler._normalize_openai_tool_calls`. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L78) | `OpenAIHandler._message_reasoning` | `message: object \| Mapping[str, Any] \| None` | `str` | Extract reasoning text from a non-streamed assistant message. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L95) | `OpenAIHandler._delta_reasoning` | `delta: object \| Mapping[str, Any] \| None` | `Optional[str]` | Extract reasoning text from a single streamed delta. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L119) | `OpenAIHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `OpenAIHandler.normalize_completion_response`. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L138) | `OpenAIHandler.iter_stream_text` | `response: Any, output_reasoning: bool, usage_capture: Any` | `Iterable[str]` | Implement `OpenAIHandler.iter_stream_text`. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L247) | `OpenAIHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: List['Tool']` | `Any` | Implement `OpenAIHandler.create_completion`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L14) | `_OpenVINOChatHistory.append` | `item: dict[str, JSONValue]` | `None` | Implement `_OpenVINOChatHistory.append`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L16) | `_OpenVINOChatHistory.set_tools` | `tools: Sequence[ToolSchemaDict]` | `None` | Implement `_OpenVINOChatHistory.set_tools`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L18) | `_OpenVINOChatHistory.set_extra_context` | `extra_context: JSONValue` | `None` | Implement `_OpenVINOChatHistory.set_extra_context`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L65) | `OpenVINOHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Prepare tools for OpenVINO chat history/template consumption. 当前的实现采用的仍然是 openai 的 tool schema，这个……可以改。 |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L74) | `OpenVINOHandler.build_chat_history` | `messages: list[dict[str, str]], tools: Optional[list[ToolSchemaDict]]` | `OpenVINOHistory` | Implement `OpenVINOHandler.build_chat_history`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L102) | `OpenVINOHandler.generation_config` | `temperature: float, max_tokens: int` | `JSONObject` | Implement `OpenVINOHandler.generation_config`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L109) | `OpenVINOHandler.result_text` | `result: OpenVINOGenerateResult` | `str` | Implement `OpenVINOHandler.result_text`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L120) | `OpenVINOHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: Any` | `Any` | Implement `OpenVINOHandler.create_completion`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L139) | `OpenVINOHandler.call_generate` | `prompt_or_history: OpenVINOGenerateInputs, config: JSONObject` | `OpenVINOGenerateResult` | Implement `OpenVINOHandler.call_generate`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L142) | `OpenVINOHandler.create_stream` | `prompt_or_history: OpenVINOGenerateInputs, config: JSONObject` | `Iterable[str]` | Implement `OpenVINOHandler.create_stream`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L177) | `OpenVINOHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `OpenVINOHandler.normalize_completion_response`. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L188) | `OpenVINOHandler.iter_stream_text` | `response: Any, output_reasoning: bool` | `Iterable[str]` | Implement `OpenVINOHandler.iter_stream_text`. |
| [graph_memory/builder.py](graph_memory/builder.py#L32) | `ExtractionFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Any, backend_name: Optional[str], tools: Any` | `Any` | Return an object with a ``content`` attribute. |
| [graph_memory/builder.py](graph_memory/builder.py#L56) | `IngestStats.__str__` | `None` | `str` | Implement `IngestStats.__str__`. |
| [graph_memory/builder.py](graph_memory/builder.py#L64) | `_extract_json_object` | `text: str` | `Optional[dict[str, Any]]` | Extract the first valid JSON object from arbitrary text. |
| [graph_memory/builder.py](graph_memory/builder.py#L101) | `GraphBuilder.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed graph-extraction calls exactly once. |
| [graph_memory/builder.py](graph_memory/builder.py#L107) | `GraphBuilder.ingest` | `messages: list[Any]` | `IngestStats` | Extract and upsert entities/relations from an LLMContext list. |
| [graph_memory/builder.py](graph_memory/builder.py#L168) | `GraphBuilder._render_transcript` | `messages: list[Any]` | `str` | Render the newest messages as a bounded transcript. |
| [graph_memory/builder.py](graph_memory/builder.py#L189) | `GraphBuilder._apply_extraction` | `extraction: dict[str, Any], timeline: int, stats: IngestStats` | `None` | Upsert extracted entities + relations into the store. |
| [graph_memory/builder.py](graph_memory/builder.py#L244) | `GraphBuilder._resolve_entity_id` | `name: str, entity_map: dict[str, str]` | `Optional[str]` | Resolve an entity name to a canonical id, searching by name too. |
| [graph_memory/extraction_prompts.py](graph_memory/extraction_prompts.py#L83) | `extract_regex` | `text: str` | `dict` | Deterministic entity extraction fallback (no LLM required). |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L31) | `normalize_entity_id` | `name: str, entity_type: str` | `str` | Produce a deterministic stable id for an entity name. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L51) | `personalized_pagerank` | `adjacency: dict[str, list[str]], seed_ids: Iterable[str], alpha: float, max_iter: int, tol: float` | `dict[str, float]` | Personalized PageRank over an undirected adjacency map. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L118) | `GraphStore.upsert_entity` | `name: str, entity_type: str, aliases: Optional[list[str]], timeline: Optional[int], summary: Optional[str], embedding: Optional[list[float]]` | `EntityNode` | Insert or merge an entity. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L173) | `GraphStore._find_same_as` | `entity_id: str, name: str, aliases: list[str]` | `Optional[EntityNode]` | Find an existing node that should be merged with the new entity. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L190) | `GraphStore.get_entity` | `entity_id: str` | `Optional[EntityNode]` | Implement `GraphStore.get_entity`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L193) | `GraphStore.find_entity_by_name` | `name: str, entity_type: str` | `Optional[EntityNode]` | Find an entity by (possibly partial) name or alias match. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L219) | `GraphStore.upsert_relation` | `source_id: str, target_id: str, relation: str, timeline: Optional[int], weight: float, valid: bool, evidence: Optional[list[int]]` | `Optional[RelationEdge]` | Insert or merge an undirected relation edge. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L269) | `GraphStore._iter_edges_between` | `a: str, b: str` | `Iterable[RelationEdge]` | Implement `GraphStore._iter_edges_between`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L274) | `GraphStore.edges` | `None` | `list[RelationEdge]` | Implement `GraphStore.edges`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L277) | `GraphStore.edges_for` | `entity_id: str` | `list[RelationEdge]` | Implement `GraphStore.edges_for`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L284) | `GraphStore.neighbors` | `entity_id: str, max_hop: int` | `dict[str, int]` | Return neighbor entity ids at exact hop distance <= max_hop. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L305) | `GraphStore.invalidate_relation` | `source_id: str, target_id: str` | `int` | Mark all relations between two entities invalid (fact superseded). |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L316) | `GraphStore._adjacency` | `valid_only: bool` | `dict[str, list[str]]` | Implement `GraphStore._adjacency`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L325) | `GraphStore.pagerank` | `seed_ids: Iterable[str], alpha: float, max_iter: int, tol: float` | `dict[str, float]` | Personalized PageRank from seed entities (graph diffusion). |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L337) | `GraphStore.detect_communities` | `seed: int` | `list[list[str]]` | Community detection via NetworkX Louvain. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L364) | `GraphStore._communities_connected_components` | `None` | `list[list[str]]` | Implement `GraphStore._communities_connected_components`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L393) | `GraphStore.time_decay` | `age: int, lam: float` | `float` | Recency weight for an entity/relation of given timeline age. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L404) | `GraphStore.subgraph` | `entity_ids: Iterable[str], hop: int` | `tuple[dict[str, EntityNode], list[RelationEdge]]` | Export nodes + edges within ``hop`` hops of the given seeds. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L438) | `GraphStore.to_state` | `None` | `GraphMemoryState` | Implement `GraphStore.to_state`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L449) | `GraphStore.clear` | `None` | `None` | Reset the graph to an empty state (keeps the lock alive). |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L461) | `GraphStore.from_state` | `state: GraphMemoryState` | `None` | Implement `GraphStore.from_state`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L472) | `GraphStore.to_dict` | `None` | `dict[str, Any]` | Implement `GraphStore.to_dict`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L475) | `GraphStore.from_dict` | `data: dict[str, Any]` | `None` | Implement `GraphStore.from_dict`. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L478) | `GraphStore.save` | `path: str \| Path` | `bool` | Serialize the graph to JSON. Returns True on success. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L511) | `GraphStore.load` | `path: str \| Path` | `bool` | Deserialize the graph from JSON. Returns True on success. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L525) | `GraphStore.__len__` | `None` | `int` | Implement `GraphStore.__len__`. |
| [graph_memory/handler.py](graph_memory/handler.py#L105) | `GraphContextHandler._init_session_state` | `None` | `None` | (Re)set all per-session transient state (keeps long-term graph). |
| [graph_memory/handler.py](graph_memory/handler.py#L116) | `GraphContextHandler.has_retrieved` | `None` | `bool` | True once a retrieval has been performed this session. |
| [graph_memory/handler.py](graph_memory/handler.py#L121) | `GraphContextHandler.graph_memory` | `None` | `str` | Last rendered ``<graph_memory>`` block (empty when none). |
| [graph_memory/handler.py](graph_memory/handler.py#L126) | `GraphContextHandler.compaction_generation` | `None` | `int` | Number of compactions observed since the session started. |
| [graph_memory/handler.py](graph_memory/handler.py#L131) | `GraphContextHandler.compress_threshold` | `None` | `int` | Compaction threshold forwarded from the inner linear handler. |
| [graph_memory/handler.py](graph_memory/handler.py#L141) | `GraphContextHandler.extra_usage` | `None` | `Any` | Aggregate token usage from linear compaction + graph LLM calls. |
| [graph_memory/handler.py](graph_memory/handler.py#L161) | `GraphContextHandler.record_usage` | `usage: Optional[Any]` | `None` | Forward one internal LLM call's usage to the inner linear handler. |
| [graph_memory/handler.py](graph_memory/handler.py#L165) | `GraphContextHandler.drain_usage_records` | `None` | `list[UsageRecord]` | Drain child internal-call records in the order their components run. |
| [graph_memory/handler.py](graph_memory/handler.py#L179) | `GraphContextHandler.retrieve` | `query: str` | `GraphRetrievalResult` | Run hybrid graph retrieval and store the rendered context block. |
| [graph_memory/handler.py](graph_memory/handler.py#L197) | `GraphContextHandler.add_user_message` | `message: str` | `None` | Append a user message and trigger retrieval when due. |
| [graph_memory/handler.py](graph_memory/handler.py#L208) | `GraphContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[dict[str, str]]` | `None` | Append an assistant output, detect compaction and flush the graph. |
| [graph_memory/handler.py](graph_memory/handler.py#L231) | `GraphContextHandler.build_messages` | `None` | `list[dict[str, Any]]` | Build messages: graph memory block (user), then linear history. |
| [graph_memory/handler.py](graph_memory/handler.py#L242) | `GraphContextHandler.save` | `path: str \| Path` | `bool` | Save the conversation AND the companion graph file. |
| [graph_memory/handler.py](graph_memory/handler.py#L284) | `GraphContextHandler.load` | `path: str \| Path` | `bool` | Restore the conversation and its companion graph. |
| [graph_memory/handler.py](graph_memory/handler.py#L355) | `GraphContextHandler.clear_context` | `None` | `bool` | Clear the session but keep the long-term memory graph. |
| [graph_memory/handler.py](graph_memory/handler.py#L363) | `GraphContextHandler._retrieve_archive_evidence` | `query: str` | `str` | Render small, provenance-labelled raw evidence for a new query. |
| [graph_memory/handler.py](graph_memory/handler.py#L396) | `GraphContextHandler._should_retrieve` | `None` | `bool` | Decide whether this newly stored user message should retrieve. |
| [graph_memory/handler.py](graph_memory/handler.py#L413) | `GraphContextHandler._flush_pending` | `None` | `None` | Ingest buffered messages into the graph and clear the buffer. |
| [graph_memory/models.py](graph_memory/models.py#L42) | `EntityNode.to_dict` | `None` | `dict[str, Any]` | Implement `EntityNode.to_dict`. |
| [graph_memory/models.py](graph_memory/models.py#L46) | `EntityNode.from_dict` | `data: dict[str, Any]` | `'EntityNode'` | Implement `EntityNode.from_dict`. |
| [graph_memory/models.py](graph_memory/models.py#L86) | `RelationEdge.key` | `None` | `tuple[str, str]` | Undirected canonical edge key (sorted pair). |
| [graph_memory/models.py](graph_memory/models.py#L91) | `RelationEdge.to_dict` | `None` | `dict[str, Any]` | Implement `RelationEdge.to_dict`. |
| [graph_memory/models.py](graph_memory/models.py#L95) | `RelationEdge.from_dict` | `data: dict[str, Any]` | `'RelationEdge'` | Implement `RelationEdge.from_dict`. |
| [graph_memory/models.py](graph_memory/models.py#L122) | `CommunitySummary.to_dict` | `None` | `dict[str, Any]` | Implement `CommunitySummary.to_dict`. |
| [graph_memory/models.py](graph_memory/models.py#L126) | `CommunitySummary.from_dict` | `data: dict[str, Any]` | `'CommunitySummary'` | Implement `CommunitySummary.from_dict`. |
| [graph_memory/models.py](graph_memory/models.py#L145) | `GraphHit.to_dict` | `None` | `dict[str, Any]` | Implement `GraphHit.to_dict`. |
| [graph_memory/models.py](graph_memory/models.py#L164) | `GraphMemoryState.to_dict` | `None` | `dict[str, Any]` | Implement `GraphMemoryState.to_dict`. |
| [graph_memory/models.py](graph_memory/models.py#L177) | `GraphMemoryState.from_dict` | `data: dict[str, Any]` | `'GraphMemoryState'` | Implement `GraphMemoryState.from_dict`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L53) | `_tokenize` | `text: str` | `list[str]` | Casefolded alnum/underscore tokens (keeps ``graph_store`` intact). |
| [graph_memory/retriever.py](graph_memory/retriever.py#L58) | `_alnum` | `text: str` | `str` | Strip every non-alphanumeric char (for fuzzy exact-name matching). |
| [graph_memory/retriever.py](graph_memory/retriever.py#L63) | `_cosine` | `a: list[float], b: list[float]` | `float` | Implement `_cosine`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L74) | `_jaccard` | `a: Iterable[str], b: Iterable[str]` | `float` | Implement `_jaccard`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L82) | `_bm25_scores` | `docs: list[list[str]], query_tokens: list[str], k1: float, b: float` | `list[float]` | Classic BM25 term-scores for each document against the query. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L119) | `_normalize` | `scores: dict[str, float]` | `dict[str, float]` | Divide by the channel max -> [0, 1]. All-zero -> all zero. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L158) | `RetrievalConfig.effective_weights` | `None` | `tuple[float, float, float, float]` | Implement `RetrievalConfig.effective_weights`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L189) | `GraphRetrievalResult.empty` | `None` | `bool` | Implement `GraphRetrievalResult.empty`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L192) | `GraphRetrievalResult.to_dict` | `None` | `dict[str, Any]` | Implement `GraphRetrievalResult.to_dict`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L207) | `GraphRetrievalResult.from_dict` | `data: dict[str, Any]` | `'GraphRetrievalResult'` | Implement `GraphRetrievalResult.from_dict`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L243) | `render_graph_memory` | `query: str, seed_entities: Optional[list[EntityNode]], hits: Optional[list[GraphHit]], expanded: Optional[dict[str, EntityNode]], relations: Optional[list[RelationEdge]], communities: Optional[list[CommunitySummary]]` | `str` | Render retrieval results as a user-role ``<graph_memory>`` block. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L356) | `GraphRetriever.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed graph-query calls exactly once. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L362) | `GraphRetriever.retrieve` | `query: str, current_timeline: Optional[int]` | `GraphRetrievalResult` | Run the hybrid retrieval pipeline and render the context block. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L416) | `GraphRetriever._semantic_rerank` | `query: str, hits: list[GraphHit]` | `list[GraphHit]` | Optionally let a stateless semantic worker reorder fused hits. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L456) | `GraphRetriever._extract_seed_entities` | `query: str` | `list[EntityNode]` | Resolve query entities to graph nodes (LLM then regex fallback). |
| [graph_memory/retriever.py](graph_memory/retriever.py#L500) | `GraphRetriever._channel_vector` | `query: str, seed_nodes: list[EntityNode], node_ids: list[str]` | `dict[str, float]` | Seed-anchored cosine over embeddings; token Jaccard fallback. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L529) | `GraphRetriever._channel_ppr` | `seed_nodes: list[EntityNode], node_ids: list[str]` | `dict[str, float]` | Implement `GraphRetriever._channel_ppr`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L539) | `GraphRetriever._channel_keyword` | `query: str, node_ids: list[str]` | `dict[str, float]` | BM25 + exact/substring bonus over name/aliases/summary. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L569) | `GraphRetriever._channel_time` | `node_ids: list[str], current_timeline: int` | `dict[str, float]` | Implement `GraphRetriever._channel_time`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L582) | `GraphRetriever._fuse` | `query: str, seed_nodes: list[EntityNode], current_timeline: int` | `list[GraphHit]` | Implement `GraphRetriever._fuse`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L618) | `GraphRetriever._expand` | `hits: list[GraphHit]` | `dict[str, EntityNode]` | Top-K hits + their neighbors; annotate hit metadata. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L650) | `GraphRetriever._collect_relations` | `expanded: dict[str, EntityNode]` | `list[RelationEdge]` | Implement `GraphRetriever._collect_relations`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L662) | `GraphRetriever._select_communities` | `hits: list[GraphHit]` | `list[CommunitySummary]` | Implement `GraphRetriever._select_communities`. |
| [graph_memory/semantic.py](graph_memory/semantic.py#L33) | `SemanticGraphWorker.drain_rerank_usage_records` | `None` | `list[UsageRecord]` | Return usage from direct reranking calls exactly once. |
| [graph_memory/semantic.py](graph_memory/semantic.py#L42) | `SemanticGraphWorker.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Any, backend_name: Optional[str], tools: Any` | `Any` | Make one isolated completion, discarding caller history/tools. |
| [graph_memory/semantic.py](graph_memory/semantic.py#L63) | `SemanticGraphWorker.rerank` | `query: str, candidates: list[dict[str, Any]], max_tokens: int` | `list[str]` | Return valid candidate IDs in semantic relevance order. |
| [llm_fetcher.py](llm_fetcher.py#L73) | `StreamUsageCapture.merge` | `raw_usage: Any` | `None` | Merge one raw usage payload (dict or provider object). |
| [llm_fetcher.py](llm_fetcher.py#L98) | `StreamUsageCapture.raw` | `None` | `dict[str, Any] \| None` | Return the merged raw usage mapping, or ``None`` when absent. |
| [llm_fetcher.py](llm_fetcher.py#L123) | `LLMFetcher.list_available_backend_providers` | `None` | `tuple[str, ...]` | Return all provider names supported by registered handlers, sorted. |
| [llm_fetcher.py](llm_fetcher.py#L183) | `LLMFetcher.backend_configs` | `None` | `Dict[str, LLMBackendConfig]` | Return a copy of all registered backend configurations. |
| [llm_fetcher.py](llm_fetcher.py#L193) | `LLMFetcher.fallback_order` | `None` | `List[str]` | Return the current fallback order (shallow copy). |
| [llm_fetcher.py](llm_fetcher.py#L203) | `LLMFetcher.default_backend_config` | `None` | `LLMBackendConfig` | Return the configuration of the default backend. |
| [llm_fetcher.py](llm_fetcher.py#L213) | `LLMFetcher._register_backend` | `backend: LLMBackendConfig` | `None` | Register a single backend and pre-create its handler. |
| [llm_fetcher.py](llm_fetcher.py#L233) | `LLMFetcher._resolve_backends` | `backend_name: Optional[str], fallback_order: Optional[Sequence[str]]` | `List[LLMBackendConfig]` | Resolve the ordered backend list for a single request. |
| [llm_fetcher.py](llm_fetcher.py#L279) | `LLMFetcher._handler_for_backend` | `backend: LLMBackendConfig` | `LLMBackendHandler` | Return the handler instance for a given backend configuration. |
| [llm_fetcher.py](llm_fetcher.py#L295) | `LLMFetcher._normalize_exception` | `backend: LLMBackendConfig, exc: Exception` | `LLMError` | Normalise any exception into an ``LLMError`` subclass. |
| [llm_fetcher.py](llm_fetcher.py#L323) | `LLMFetcher._sleep_before_retry` | `retry_index: int, controller: ExecutionController \| None` | `None` | Wait with cancellation-aware exponential backoff before retrying. |
| [llm_fetcher.py](llm_fetcher.py#L348) | `LLMFetcher._raise_if_force_stopped` | `controller: ExecutionController \| None` | `None` | Raise the terminal cancellation error without retrying providers. |
| [llm_fetcher.py](llm_fetcher.py#L362) | `LLMFetcher.abort_active_requests` | `None` | `int` | Close provider transports for this terminal force-stop. |
| [llm_fetcher.py](llm_fetcher.py#L386) | `LLMFetcher.prepare_request` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Optional[Sequence[ToolDefinition]], stream: bool` | `RemoteRequestSnapshot` | Build the first dispatch-ready request without provider I/O. |
| [llm_fetcher.py](llm_fetcher.py#L426) | `LLMFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Optional[Sequence[ToolDefinition]], on_request: Optional[Callable[[RemoteRequestSnapshot], None]], on_retry: Optional[Callable[[int], None]], controller: ExecutionController \| None` | `LLMOutput` | Execute a non-streaming completion with backend fallback and retry. |
| [llm_fetcher.py](llm_fetcher.py#L553) | `LLMFetcher.fetch_stream` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, output_reasoning: bool, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Optional[Sequence[ToolDefinition]], on_request: Optional[Callable[[RemoteRequestSnapshot], None]], on_retry: Optional[Callable[[int], None]], usage_sink: Optional[TokenUsage], controller: ExecutionController \| None` | `Generator[str, None]` | Execute a streaming completion with backend fallback and retry. |
| [llm_fetcher.py](llm_fetcher.py#L701) | `LLMFetcher._prepare_backend_request` | `backend: LLMBackendConfig, messages: List[JsonObject], temperature: float, max_tokens: int, tools: Optional[Sequence[ToolDefinition]], stream: bool` | `tuple[LLMBackendHandler, RemoteRequestSnapshot]` | Prepare one backend's tool schemas and safe request snapshot. |
| [llm_fetcher.py](llm_fetcher.py#L736) | `LLMFetcher._max_attempts` | `backend: LLMBackendConfig` | `int` | Return the number of times to attempt a request for a backend. |
| [llm_fetcher.py](llm_fetcher.py#L751) | `LLMFetcher._build_messages` | `msg: str, system_prompt: Optional[str], context: Optional[ContextHandler]` | `List[Dict[str, Any]]` | Build the message list, delegating to a context handler when available. |
| [llm_types.py](llm_types.py#L42) | `RemoteRequestSnapshot.to_dict` | `None` | `JsonObject` | Return the JSON-safe event payload used by application hosts. |
| [llm_types.py](llm_types.py#L105) | `LLMBackendConfig.__str__` | `None` | `str` | Render the backend config in a compact human-readable form. |
| [llm_types.py](llm_types.py#L160) | `TokenUsage.cache_hit_rate` | `None` | `float` | Fraction of input tokens served from the provider's prompt cache. |
| [llm_types.py](llm_types.py#L184) | `LLMOutput.text` | `None` | `str` | Alias for assistant text content. |
| [llm_types.py](llm_types.py#L188) | `LLMOutput.__str__` | `None` | `str` | Return the assistant content for debug printing and logging. |
| [llm_types.py](llm_types.py#L215) | `LLMContextCompacted.__str__` | `None` | `str` | Implement `LLMContextCompacted.__str__`. |
| [llm_types.py](llm_types.py#L251) | `ToolSchema.to_dict` | `None` | `Dict[str, Any]` | Convert this schema to an isolated JSON-ready mapping. |
| [llm_types.py](llm_types.py#L291) | `Tool.__str__` | `None` | `Any` | Implement `Tool.__str__`. |
| [memory/base.py](memory/base.py#L30) | `MemoryProvider.search` | `query: str, limit: int, namespace: str` | `list[MemoryItem]` | Return memories relevant to a query. |
| [memory/base.py](memory/base.py#L33) | `MemoryProvider.add` | `item: MemoryItem, namespace: str` | `None` | Persist one memory item in a namespace. |
| [rag_module/knowledge/config.py](rag_module/knowledge/config.py#L52) | `KnowledgeConfig.from_environment` | `root: Path \| str \| None` | `'KnowledgeConfig'` | Build configuration from environment variables and defaults. |
| [rag_module/knowledge/config.py](rag_module/knowledge/config.py#L99) | `KnowledgeConfig.index_path` | `None` | `Path` | Return the manifest path inside the configured knowledge root. |
| [rag_module/knowledge/config.py](rag_module/knowledge/config.py#L110) | `KnowledgeConfig.chroma_path` | `None` | `Path` | Return the Chroma persistence directory path. |
| [rag_module/knowledge/context_builder.py](rag_module/knowledge/context_builder.py#L28) | `TaskContextBuilder.build` | `hits: List[KnowledgeHit]` | `str` | Build system-prompt context from ranked knowledge hits. |
| [rag_module/knowledge/embedding_model.py](rag_module/knowledge/embedding_model.py#L39) | `EmbeddingModelProvider.dependencies_available` | `None` | `tuple[bool, str]` | Check whether sentence-transformers can be imported. |
| [rag_module/knowledge/embedding_model.py](rag_module/knowledge/embedding_model.py#L67) | `EmbeddingModelProvider.get_model` | `None` | `Any` | Load and return the configured embedding model. |
| [rag_module/knowledge/embedding_model.py](rag_module/knowledge/embedding_model.py#L99) | `EmbeddingModelProvider.resolve_model_source` | `None` | `str` | Resolve the configured model name to a local path when possible. |
| [rag_module/knowledge/embedding_model.py](rag_module/knowledge/embedding_model.py#L136) | `EmbeddingModelProvider.encode_documents` | `documents: Sequence[str]` | `list[list[float]]` | Encode document texts into normalized embedding vectors. |
| [rag_module/knowledge/embedding_model.py](rag_module/knowledge/embedding_model.py#L174) | `EmbeddingModelProvider.encode_query` | `query_text: str` | `list[float]` | Encode a query string into one normalized embedding vector. |
| [rag_module/knowledge/embedding_model.py](rag_module/knowledge/embedding_model.py#L209) | `EmbeddingModelProvider.format_error` | `exc: Exception` | `str` | Format an exception into a compact diagnostic string. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L102) | `KnowledgeBase.available` | `None` | `bool` | Return whether the knowledge-base directory exists. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L113) | `KnowledgeBase.search` | `query: str, limit: int` | `list[KnowledgeHit]` | Search the knowledge base by freeform query text. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L137) | `KnowledgeBase.search_for_task` | `task_name: str, task_type: str, target: str, file_descriptions: str, limit: int` | `list[KnowledgeHit]` | Prefetch knowledge entries relevant to a task. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L185) | `KnowledgeBase.build_task_context` | `task_name: str, task_type: str, target: str, file_descriptions: str, limit: int` | `str` | Build prompt-ready knowledge context for a task. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L217) | `KnowledgeBase.ensure_vector_index` | `force: bool` | `dict[str, KnowledgeIndexEntry]` | Ensure the vector index manifest exists and is fresh. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L230) | `KnowledgeBase.rebuild_vector_index` | `None` | `dict[str, KnowledgeIndexEntry]` | Rebuild the vector index and manifest from source documents. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L242) | `KnowledgeBase.vector_status` | `None` | `JsonObject` | Return semantic index and dependency status. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L252) | `KnowledgeBase.get_full_text` | `path: str` | `str \| None` | Retrieve full text content of a knowledge document by its path. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L277) | `KnowledgeBase._resolve_document_path` | `path: str` | `Path \| None` | Resolve either root-relative or repository-relative document paths. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L305) | `KnowledgeBase.get_documents_by_paths` | `paths: list[str]` | `dict[str, str]` | Retrieve full text content for multiple documents by their paths. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L322) | `KnowledgeBase.get_chunk` | `path: str, chunk_key: str, chunk_index: int \| None` | `KnowledgeChunk \| None` | Retrieve one chunk from a knowledge document. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L372) | `KnowledgeBase.get_chunk_text` | `path: str, chunk_key: str, chunk_index: int \| None` | `str \| None` | Retrieve the raw Markdown content for one chunk. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L392) | `KnowledgeBase.get_chunk_text_from_hit` | `hit: KnowledgeHit` | `str \| None` | Retrieve chunk text for one ranked retrieval hit. |
| [rag_module/knowledge/hybrid_retriever.py](rag_module/knowledge/hybrid_retriever.py#L54) | `HybridRetriever.search` | `query: RetrievalQuery` | `list[KnowledgeHit]` | Search documents with hybrid lexical and semantic ranking. |
| [rag_module/knowledge/hybrid_retriever.py](rag_module/knowledge/hybrid_retriever.py#L128) | `HybridRetriever.fallback_hits_for_task_type` | `task_type: str, limit: int` | `list[KnowledgeHit]` | Build fallback hits for sparse task-aware retrieval. |
| [rag_module/knowledge/index_manager.py](rag_module/knowledge/index_manager.py#L55) | `VectorIndexManager.ensure_vector_index` | `force: bool` | `dict[str, KnowledgeIndexEntry]` | Ensure the vector manifest exists and matches current documents. |
| [rag_module/knowledge/index_manager.py](rag_module/knowledge/index_manager.py#L87) | `VectorIndexManager.rebuild_vector_index` | `documents: list \| None` | `dict[str, KnowledgeIndexEntry]` | Rebuild vector index entries and the Chroma collection. |
| [rag_module/knowledge/index_manager.py](rag_module/knowledge/index_manager.py#L165) | `VectorIndexManager.vector_status` | `None` | `JsonObject` | Return the current vector-index status payload. |
| [rag_module/knowledge/index_manager.py](rag_module/knowledge/index_manager.py#L203) | `VectorIndexManager.semantic_candidate_limit` | `limit: int, chunk_count: int` | `int` | Calculate the number of vector candidates to request. |
| [rag_module/knowledge/index_manager.py](rag_module/knowledge/index_manager.py#L219) | `VectorIndexManager.format_error` | `exc: Exception` | `str` | Format an exception into a compact diagnostic string. |
| [rag_module/knowledge/keyword_retriever.py](rag_module/knowledge/keyword_retriever.py#L28) | `KeywordRetriever.extract_terms` | `values: list[str]` | `list[str]` | Extract searchable keyword terms from text values. |
| [rag_module/knowledge/keyword_retriever.py](rag_module/knowledge/keyword_retriever.py#L42) | `KeywordRetriever.score_document` | `document: KnowledgeDocument, terms: list[str]` | `int` | Score a document using deterministic keyword matching. |
| [rag_module/knowledge/keyword_retriever.py](rag_module/knowledge/keyword_retriever.py#L72) | `KeywordRetriever.score_chunk` | `chunk: KnowledgeChunk, terms: list[str]` | `int` | Score a chunk using deterministic keyword matching. |
| [rag_module/knowledge/manifest_store.py](rag_module/knowledge/manifest_store.py#L33) | `KnowledgeManifestStore.load` | `path: Path \| None` | `dict[str, KnowledgeIndexEntry] \| None` | Load index entries from the manifest file. |
| [rag_module/knowledge/manifest_store.py](rag_module/knowledge/manifest_store.py#L89) | `KnowledgeManifestStore.save` | `entries: dict[str, KnowledgeIndexEntry], chunk_count: int, backend_ready: bool, last_error: str` | `None` | Write the vector-index manifest to disk. |
| [rag_module/knowledge/manifest_store.py](rag_module/knowledge/manifest_store.py#L127) | `KnowledgeManifestStore.build_meta` | `entry_count: int, chunk_count: int, backend_ready: bool, last_error: str` | `ManifestMeta` | Build manifest metadata using configured constants. |
| [rag_module/knowledge/manifest_store.py](rag_module/knowledge/manifest_store.py#L151) | `KnowledgeManifestStore.is_fresh` | `loaded: dict[str, KnowledgeIndexEntry], documents: list[KnowledgeDocument]` | `bool` | Return whether a loaded manifest matches the current documents. |
| [rag_module/knowledge/manifest_store.py](rag_module/knowledge/manifest_store.py#L181) | `KnowledgeManifestStore.fingerprint_document` | `document: KnowledgeDocument` | `str` | Calculate the manifest fingerprint for a parsed document. |
| [rag_module/knowledge/manifest_store.py](rag_module/knowledge/manifest_store.py#L195) | `KnowledgeManifestStore.fingerprint_text` | `title: str, content: str` | `str` | Calculate a stable fingerprint from title and content. |
| [rag_module/knowledge/manifest_store.py](rag_module/knowledge/manifest_store.py#L210) | `KnowledgeManifestStore.document_id` | `relative_path: str` | `str` | Build the stable vector-store document ID for a path. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L30) | `MarkdownKnowledgeLoader.available` | `None` | `bool` | Return whether the configured knowledge root exists. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L40) | `MarkdownKnowledgeLoader.iter_entry_files` | `None` | `Iterable[Path]` | Yield Markdown files that should be treated as knowledge entries. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L72) | `MarkdownKnowledgeLoader.read_document` | `path: Path` | `KnowledgeDocument` | Read and parse a single Markdown knowledge document. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L101) | `MarkdownKnowledgeLoader.load_documents` | `None` | `list[KnowledgeDocument]` | Load every knowledge entry document under the root. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L111) | `MarkdownKnowledgeLoader.extract_title` | `path: Path, content: str` | `str` | Extract a document title from Markdown content. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L140) | `MarkdownKnowledgeLoader._load_ignore_patterns` | `None` | `list[str]` | Load repository-level `.kbignore` patterns. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L161) | `MarkdownKnowledgeLoader._is_ignored_path` | `root_relative: str, patterns: list[str]` | `bool` | Return whether a path matches any configured `.kbignore` pattern. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L168) | `MarkdownKnowledgeLoader._match_ignore_pattern` | `path: str, pattern: str` | `bool` | Match one path against a `.kbignore` pattern. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L69) | `KnowledgeIndexEntry.to_dict` | `None` | `JsonObject` | Convert the index entry to a JSON-serializable dictionary. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L236) | `ManifestMeta.to_dict` | `None` | `dict[str, Any]` | Convert manifest metadata into a JSON-compatible dictionary. |
| [rag_module/knowledge/task_policy.py](rag_module/knowledge/task_policy.py#L32) | `TaskRetrievalPolicy.build_freeform_query` | `query: str, limit: int, max_limit: int` | `RetrievalQuery \| None` | Build a normalized retrieval query for direct user search. |
| [rag_module/knowledge/task_policy.py](rag_module/knowledge/task_policy.py#L60) | `TaskRetrievalPolicy.build_task_query` | `task_name: str, task_type: str, target: str, file_descriptions: str, limit: int` | `RetrievalQuery \| None` | Build a normalized retrieval query from task metadata. |
| [rag_module/knowledge/task_policy.py](rag_module/knowledge/task_policy.py#L107) | `TaskRetrievalPolicy.default_topic_keywords` | `task_type: str` | `list[str]` | Return default query keywords for a task type. |
| [rag_module/knowledge/task_policy.py](rag_module/knowledge/task_policy.py#L135) | `TaskRetrievalPolicy.boost_for_task_type` | `document: KnowledgeDocument, task_type: str` | `int` | Return an additional deterministic boost for task-aware search. |
| [rag_module/knowledge/task_policy.py](rag_module/knowledge/task_policy.py#L151) | `TaskRetrievalPolicy.boost_for_chunk` | `chunk: KnowledgeChunk, task_type: str` | `int` | Return an additional deterministic boost for a chunk hit. |
| [rag_module/knowledge/task_policy.py](rag_module/knowledge/task_policy.py#L167) | `TaskRetrievalPolicy._boost_for_path_and_text` | `task_type: str, relative_path: str, combined_text: str` | `int` | Apply the old task-specific heuristic to path and text metadata. |
| [rag_module/knowledge/task_policy.py](rag_module/knowledge/task_policy.py#L190) | `TaskRetrievalPolicy.fallback_paths` | `task_type: str` | `list[Path]` | Return fallback documents for a task type. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L40) | `TextTools.extract_terms` | `values: Sequence[str]` | `list[str]` | Extract normalized keyword terms from arbitrary text values. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L73) | `TextTools.build_excerpt` | `content: str, terms: Sequence[str]` | `str` | Build a short excerpt from Markdown content. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L112) | `TextTools.chunk_document` | `document: KnowledgeDocument` | `list[KnowledgeChunk]` | Split one Markdown document into retrieval chunks. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L216) | `TextTools.should_skip_excerpt_line` | `line: str` | `bool` | Return whether a line is unsuitable for excerpt display. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L229) | `TextTools.should_skip_excerpt_block` | `block: MarkdownBlock` | `bool` | Return whether a parsed Markdown block is unsuitable for excerpts. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L260) | `TextTools.trim_excerpt` | `text: str` | `str` | Normalize and trim an excerpt string. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L279) | `TextTools.build_chunk_semantic_document` | `chunk: KnowledgeChunk` | `str` | Build the text payload stored for one semantic chunk. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L302) | `TextTools.build_semantic_document` | `title: str, relative_path: str, content: str` | `str` | Build the text payload stored in the semantic vector index. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L323) | `TextTools.excerpt_from_semantic_document` | `document: str` | `str` | Extract a display excerpt from a stored semantic document payload. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L341) | `TextTools._markdown_blocks` | `content: str` | `list[MarkdownBlock]` | Split raw markdown into heading and body blocks. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L363) | `TextTools._markdown_blocks_from_tokens` | `tokens: list[Token], lines: list[str], line_offset: int` | `list[MarkdownBlock]` | Convert markdown-it tokens into logical Markdown blocks. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L441) | `TextTools._fallback_markdown_blocks` | `content: str, line_offset: int` | `list[MarkdownBlock]` | Split markdown with a conservative line-based fallback parser. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L490) | `TextTools._block_from_token` | `token: Token, lines: list[str], line_offset: int, kind: str, text: str \| None, level: int \| None, info: str \| None` | `MarkdownBlock \| None` | Build a `MarkdownBlock` from a markdown-it token. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L512) | `TextTools._token_lines` | `token: Token, line_offset: int, line_count: int` | `tuple[int, int]` | Return 1-based original line numbers for a token. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L523) | `TextTools._raw_block_text` | `token: Token, lines: list[str], default: str` | `str` | Extract the source slice for a token when line information exists. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L535) | `TextTools._next_inline_token` | `tokens: list[Token], index: int` | `Token \| None` | Return the next inline token after a block opener, if present. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L541) | `TextTools._skip_until` | `tokens: list[Token], index: int, token_type: str` | `int` | Advance the token index until the matching close token is seen. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L549) | `TextTools._inline_text` | `token: Token \| None` | `str` | Render inline markdown tokens as readable text. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L563) | `TextTools._heading_level` | `token: Token` | `int \| None` | Convert a markdown-it heading token tag into a numeric level. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L569) | `TextTools._strip_yaml_frontmatter` | `content: str` | `tuple[str, int]` | Remove a leading YAML frontmatter block before Markdown parsing. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L594) | `TextTools._chunk_key` | `source_path: str, chunk_index: int, start_line: int, end_line: int, heading_path: str, chunk_title: str, content: str` | `str` | Build a stable chunk identifier for vector storage. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L40) | `ChromaVectorStore.dependencies_available` | `None` | `tuple[bool, str]` | Check whether ChromaDB can be imported. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L67) | `ChromaVectorStore.rebuild` | `ids: Sequence[str], documents: Sequence[str], metadatas: Sequence[dict[str, str]]` | `bool` | Rebuild the Chroma collection with supplied documents. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L104) | `ChromaVectorStore.query` | `query_text: str, limit: int` | `dict[str, VectorHit]` | Query the Chroma collection for semantic candidates. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L170) | `ChromaVectorStore.get_client` | `None` | `Any` | Return the persistent ChromaDB client. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L192) | `ChromaVectorStore.get_collection` | `recreate: bool` | `Any \| None` | Return the configured Chroma collection. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L235) | `ChromaVectorStore.create_collection` | `client: Any` | `Any` | Create or fetch the configured Chroma collection. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L268) | `ChromaVectorStore.distance_to_similarity` | `distance: Any` | `float` | Convert Chroma cosine distance to bounded similarity. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L289) | `ChromaVectorStore.format_error` | `exc: Exception` | `str` | Format an exception into a compact diagnostic string. |
| [scripts/check_packaged_imports.py](scripts/check_packaged_imports.py#L10) | `packaged_modules` | `package_name: str` | `list[str]` | Return the installed package and every recursively discoverable module. |
| [scripts/check_packaged_imports.py](scripts/check_packaged_imports.py#L35) | `import_modules` | `module_names: list[str]` | `list[tuple[str, BaseException]]` | Import each module and return failures without stopping at the first one. |
| [scripts/check_packaged_imports.py](scripts/check_packaged_imports.py#L54) | `main` | `None` | `int` | Run the packaged-module import check and print an actionable report. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L121) | `AgentFailure.__str__` | `None` | `str` | Implement `AgentFailure.__str__`. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L219) | `ExecutionGraph.__str__` | `None` | `str` | Render a thread-safe human-readable snapshot of graph topology. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L233) | `ExecutionGraph._default_agent_serializer` | `agent_name: str, agent: Agent` | `dict[str, Any]` | Serialize a standard tool-free Agent into JSON-compatible config. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L269) | `ExecutionGraph._default_agent_resolver` | `agent_name: str, spec: Mapping[str, Any]` | `Agent` | Recreate a standard tool-free Agent from a persisted specification. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L295) | `ExecutionGraph.to_snapshot` | `agent_serializer: AgentSerializer \| None, callback_serializer: CallbackSerializer \| None` | `dict[str, Any]` | Create a JSON-compatible snapshot of a quiescent graph. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L355) | `ExecutionGraph.save` | `path: str \| Path, agent_serializer: AgentSerializer \| None, callback_serializer: CallbackSerializer \| None` | `Path` | Atomically save a quiescent graph snapshot to ``path``. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L376) | `ExecutionGraph.load` | `path: str \| Path, agent_resolver: AgentResolver \| None, callback_resolver: CallbackResolver \| None` | `'ExecutionGraph'` | Load a graph snapshot into a new quiescent ExecutionGraph. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L445) | `ExecutionGraph.add_hook` | `hook: ExecutionHook` | `None` | Register a hook that receives every :class:`ExecutionEvent`. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L457) | `ExecutionGraph.remove_hook` | `hook: ExecutionHook` | `bool` | Remove one previously registered execution hook. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L474) | `ExecutionGraph.view_snapshot` | `None` | `dict[str, Any]` | Return a JSON-safe live topology view without executable objects. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L525) | `ExecutionGraph.finalize_tasks` | `None` | `dict[str, str]` | Close every unfinished dynamic task after the scheduler stops. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L558) | `ExecutionGraph.request_shutdown` | `None` | `None` | Ask the scheduler to stop submitting further runnable Agents. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L569) | `ExecutionGraph._emit` | `source: str, agent_name: str, event_type: str, message: str, data: Any` | `None` | Fire an event to all registered hooks. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L597) | `ExecutionGraph._record_node_state` | `agent_name: str, event_type: str, message: str, data: Any` | `None` | Project one lifecycle event into the UI-facing node state cache. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L653) | `ExecutionGraph._attach_agent_events` | `agent: Agent` | `None` | Forward one graph member's lifecycle events to graph hooks. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L691) | `ExecutionGraph.add_agent` | `agent_name: str, agent_instance: Agent` | `bool` | Register an agent as a graph vertex. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L724) | `ExecutionGraph.add_routing_node` | `name: str, router: RouterFn` | `bool` | Register a lightweight non-LLM routing node. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L761) | `ExecutionGraph.remove_agent` | `agent_name: str` | `bool` | Remove an agent and every edge connected to it. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L795) | `ExecutionGraph.add_connection` | `source: str, target: str` | `bool` | Add a directed dependency edge from one agent to another. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L836) | `ExecutionGraph.add_split` | `source: str, targets: list[str]` | `None` | Broadcast one agent's output to multiple successor agents. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L862) | `ExecutionGraph.add_gather` | `sources: list[str], target: str, mapper: MapperFn \| None` | `None` | Make one agent depend on and aggregate multiple source agents. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L902) | `ExecutionGraph.set_mapper` | `agent_name: str, mapper: MapperFn` | `None` | Set a node-level mapper on *agent_name*. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L933) | `ExecutionGraph.set_router` | `agent_name: str, router: RouterFn` | `None` | Attach a post-completion router to an existing agent. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L967) | `ExecutionGraph.remove_router` | `agent_name: str` | `bool` | Remove a post-completion router from an agent. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L986) | `ExecutionGraph.dispatch_task` | `agent_name: str, agent_instance: Agent, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create a worker, deliver an explicit task, and queue it to run. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1062) | `ExecutionGraph.task_id_for_agent` | `agent_name: str` | `str` | Return the latest TaskBus assignment owned by one worker. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1080) | `ExecutionGraph.redispatch_task` | `agent_name: str, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Assign a fresh task to an existing terminal dispatched worker. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1162) | `ExecutionGraph.report_task` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Accept a structured worker report without forwarding raw output. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1214) | `ExecutionGraph.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Block until requested structured reports arrive or time expires. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1230) | `ExecutionGraph.dynamic_add_agent` | `agent_name: str, agent_instance: Agent` | `str` | Register an Agent node while a graph run is active. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1258) | `ExecutionGraph.dynamic_remove_agent` | `agent_name: str` | `str` | Dynamically remove an agent and its edges during execution. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1282) | `ExecutionGraph.dynamic_add_connection` | `source: str, target: str` | `str` | Dynamically add a dependency edge during execution. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1312) | `ExecutionGraph.dynamic_remove_connection` | `source: str, target: str` | `str` | Remove one dependency edge while the graph is editable. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1332) | `ExecutionGraph.dynamic_set_mapper` | `agent_name: str, mode: str` | `str` | Set a safe declarative input aggregator on an Agent node. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1351) | `ExecutionGraph.dynamic_set_router` | `agent_name: str, targets: list[str]` | `str` | Set a declarative router selecting a fixed successor subset. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1374) | `ExecutionGraph._mapper_for_mode` | `mode: str` | `MapperFn` | Return the built-in mapper function for one persisted mode. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1397) | `ExecutionGraph._restore_declarative_mapper` | `agent_name: str, mode: str` | `None` | Install one persisted declarative mapper without emitting an event. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1412) | `ExecutionGraph._restore_declarative_router` | `agent_name: str, targets: list[str]` | `None` | Install one persisted fixed router without emitting an event. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1431) | `ExecutionGraph.dynamic_get_info` | `None` | `str` | Return the current graph state as a structured string. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1470) | `ExecutionGraph.run` | `message: str, max_rounds: int \| None, control: AgentRunControl \| None` | `dict[str, Any]` | Execute the graph using dependency-driven concurrent scheduling. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1844) | `ExecutionGraph._activate` | `completed_agent: str, successors: Iterable[str], remaining_dependencies: dict[str, int], ready: deque[str]` | `None` | Decrement dependency counts and enqueue ready successors. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1870) | `ExecutionGraph._drain_dynamic_ready` | `ready: deque[str], remaining_dependencies: dict[str, int]` | `None` | Move explicitly dispatched workers into the local scheduler queue. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1912) | `ExecutionGraph._render_assignment` | `assignment: TaskAssignment` | `str` | Render one explicit task package without exposing raw peer output. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1931) | `ExecutionGraph._build_input` | `agent_name: str, initial_message: str, outputs: Mapping[str, Any]` | `str` | Build the input message for one ready agent. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1977) | `ExecutionGraph._output_to_text` | `output: Any` | `str` | Convert an arbitrary agent output into message text. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1990) | `ExecutionGraph._require_agent` | `agent_name: str` | `None` | Ensure that an agent name is registered. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L66) | `AgentSwarm.add_agent` | `agent_name: str, agent_instance: Agent` | `bool` | Register an ``Agent`` instance as a graph vertex. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L70) | `AgentSwarm.save` | `path: str \| Path, agent_serializer: Callable[[str, Agent], dict[str, Any]] \| None, callback_serializer: CallbackSerializer \| None` | `Path` | Persist a quiescent Swarm through its execution-graph snapshot. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L99) | `AgentSwarm.load` | `path: str \| Path, agent_resolver: AgentResolver \| None, callback_resolver: CallbackResolver \| None` | `'AgentSwarm'` | Restore a quiescent Swarm without exposing its private graph field. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L128) | `AgentSwarm.add_routing_node` | `name: str, router: RouterFn` | `bool` | Register a lightweight non-LLM routing node. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L132) | `AgentSwarm.remove_agent` | `agent_name: str` | `bool` | Remove a registered agent and every edge connected to it. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L140) | `AgentSwarm.add_connection` | `source: str, target: str` | `bool` | Add a directed dependency edge from *source* to *target*. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L144) | `AgentSwarm.add_split` | `source: str, targets: list[str]` | `None` | Broadcast one agent's output to multiple successors. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L148) | `AgentSwarm.add_gather` | `sources: list[str], target: str, mapper: MapperFn \| None` | `None` | Make *target* depend on and aggregate outputs from *sources*. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L161) | `AgentSwarm.set_mapper` | `agent_name: str, mapper: MapperFn` | `None` | Set a node-level mapper that converts predecessor outputs into the agent's input message. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L170) | `AgentSwarm.set_router` | `agent_name: str, router: RouterFn` | `None` | Attach a post-completion router to an existing agent. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L174) | `AgentSwarm.remove_router` | `agent_name: str` | `bool` | Remove a post-completion router from an agent. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L182) | `AgentSwarm.dynamic_add_agent` | `agent_name: str, agent_instance: Agent` | `str` | Dynamically register an ``Agent`` instance during execution. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L188) | `AgentSwarm.dispatch_task` | `agent_name: str, agent_instance: Agent, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create and immediately schedule a task-addressed subagent. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L227) | `AgentSwarm.task_id_for_agent` | `agent_name: str` | `str` | Return the latest TaskBus assignment for a dispatched worker. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L238) | `AgentSwarm.get_agent` | `agent_name: str` | `Agent \| None` | Return one restored or live Agent without exposing topology maps. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L249) | `AgentSwarm.dispatched_agent_names` | `None` | `tuple[str, ...]` | Return worker identities that own TaskBus assignments. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L258) | `AgentSwarm.redispatch_task` | `agent_name: str, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Reactivate one terminal dispatched worker with a new task record. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L293) | `AgentSwarm.report_task` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Submit one structured worker report to the assigned coordinator. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L334) | `AgentSwarm.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Wait for reports from explicitly dispatched subagent tasks. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L350) | `AgentSwarm.dynamic_remove_agent` | `agent_name: str` | `str` | Dynamically remove an agent and its edges during execution. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L354) | `AgentSwarm.dynamic_add_connection` | `source: str, target: str` | `str` | Dynamically add a dependency edge during execution. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L358) | `AgentSwarm.dynamic_remove_connection` | `source: str, target: str` | `str` | Dynamically remove a dependency edge during execution. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L362) | `AgentSwarm.dynamic_set_mapper` | `agent_name: str, mode: str` | `str` | Dynamically set a declarative predecessor-output mapper. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L366) | `AgentSwarm.dynamic_set_router` | `agent_name: str, targets: list[str]` | `str` | Dynamically set a fixed successor router. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L370) | `AgentSwarm.dynamic_get_info` | `None` | `str` | Return current graph state as a structured string. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L378) | `AgentSwarm.add_hook` | `hook: ExecutionHook` | `None` | Register a hook that receives every :class:`ExecutionEvent`. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L385) | `AgentSwarm.remove_hook` | `hook: ExecutionHook` | `bool` | Remove a hook previously forwarded to the execution graph. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L396) | `AgentSwarm.view_snapshot` | `None` | `dict[str, Any]` | Return a safe, UI-oriented snapshot of the active graph topology. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L405) | `AgentSwarm.finalize_tasks` | `None` | `dict[str, str]` | Close unfinished dynamic tasks after any terminal run outcome. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L417) | `AgentSwarm.request_shutdown` | `None` | `None` | Stop scheduling further runnable Agents in the active graph. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L432) | `AgentSwarm.total_usage` | `None` | `dict[str, int]` | Aggregate token usage across every registered Agent. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L459) | `AgentSwarm.run` | `message: str, max_rounds: int \| None, control: AgentRunControl \| None` | `dict[str, Any]` | Execute the graph with an optional cooperative Agent control. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L71) | `TaskReport.as_dict` | `None` | `dict[str, Any]` | Return a JSON-ready representation of the structured report. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L101) | `TaskBus.create_assignment` | `recipient: str, reply_to: str, objective: str, handoff: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create and enqueue one immutable subagent work package. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L153) | `TaskBus.claim_assignment` | `task_id: str` | `TaskAssignment` | Mark one queued assignment running and return its work package. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L175) | `TaskBus.submit_report` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Close a task with a bounded report and deliver it to its inbox. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L239) | `TaskBus.set_terminal_state` | `task_id: str, state: str` | `bool` | Close one unfinished assignment without manufacturing a report. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L266) | `TaskBus.finalize_unfinished` | `running_state: str, queued_state: str` | `dict[str, str]` | Close every non-terminal assignment at an execution boundary. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L310) | `TaskBus.fail_unreported_task` | `task_id: str, reporter: str, reason: str` | `TaskReport \| None` | Submit a failure report when a worker exits without reporting. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L332) | `TaskBus.interrupt_task` | `task_id: str, reporter: str, reason: str` | `TaskReport \| None` | Deliver a structured interruption report for an unfinished task. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L357) | `TaskBus.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Wait until every requested task has delivered a structured report. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L380) | `TaskBus.get_assignment` | `task_id: str` | `TaskAssignment` | Return one immutable task assignment. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L398) | `TaskBus.task_states` | `None` | `dict[str, str]` | Return a point-in-time view of each task lifecycle state. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L410) | `TaskBus.to_snapshot` | `None` | `dict[str, Any]` | Return a JSON-compatible, point-in-time copy of TaskBus state. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L433) | `TaskBus.from_snapshot` | `snapshot: Mapping[str, Any]` | `'TaskBus'` | Restore a TaskBus from :meth:`to_snapshot` output. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L520) | `TaskBus._normalize_items` | `values: Iterable[str]` | `tuple[str, ...]` | Normalize, bound, and freeze a report list field. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L534) | `TaskBus._state_for_report_status` | `status: str` | `str` | Map an Agent-supplied report status to a canonical task terminal. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L21) | `ExecutionControllerTests.test_graceful_stop_wakes_waiters_without_closing_resources` | `None` | `None` | Graceful mode shares the request path but preserves active I/O. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L33) | `ExecutionControllerTests.test_force_stop_escalates_and_closes_existing_and_late_resources` | `None` | `None` | Force mode upgrades graceful intent and closes every registered resource. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L46) | `ExecutionControllerTests.test_force_stop_closes_active_fetcher_transport` | `None` | `None` | A fetch request registers its transport and exits as cancellation. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L71) | `ExecutionControllerTests.test_force_stop_closes_an_active_stream` | `None` | `None` | The stream keeps its registration until its generator is closed. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L96) | `ExecutionControllerTests.test_force_stop_cancels_a_tool_batch_and_binds_its_controller` | `None` | `None` | A running tool can close its resource through the bound controller. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L130) | `ExecutionControllerTests.test_force_stop_kills_a_shell_tool_process_group` | `None` | `None` | Shell tools register their spawned process group with the controller. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L167) | `_BlockingHandler.prepare_tools` | `tools: object` | `object` | Implement `_BlockingHandler.prepare_tools`. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L170) | `_BlockingHandler.create_completion` | `**_kwargs: object` | `object` | Implement `_BlockingHandler.create_completion`. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L175) | `_BlockingHandler.abort_active_request` | `None` | `int` | Implement `_BlockingHandler.abort_active_request`. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L187) | `_StreamingHandler.create_completion` | `**_kwargs: object` | `object` | Implement `_StreamingHandler.create_completion`. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L190) | `_StreamingHandler.iter_stream_text` | `_raw: object, **_kwargs: object` | `Any` | Implement `_StreamingHandler.iter_stream_text`. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L197) | `_fetch_in_thread` | `fetcher: LLMFetcher, controller: ExecutionController, errors: list[BaseException]` | `None` | Implement `_fetch_in_thread`. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L208) | `_advance_stream` | `stream: object, errors: list[BaseException]` | `None` | Implement `_advance_stream`. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L215) | `_run_tool_batch` | `executor: ToolExecutor, controller: ExecutionController, handler: object, errors: list[BaseException], arguments: dict[str, object] \| None` | `None` | Implement `_run_tool_batch`. |
| [tool_executor.py](tool_executor.py#L59) | `ToolExecutor.execute` | `handler: Callable[..., Any], arguments: Dict[str, Any]` | `Any` | Run a single tool handler in the calling thread. |
| [tool_executor.py](tool_executor.py#L67) | `ToolExecutor.execute_timed` | `handler: Callable[..., Any], arguments: Dict[str, Any]` | `ToolExecution` | Run a single tool handler in the calling thread with timing. |
| [tool_executor.py](tool_executor.py#L98) | `ToolExecutor.execute_batch` | `handlers: List[Callable[..., Any] \| None], arguments_list: List[Dict[str, Any]], controller: ExecutionController \| None` | `List[Any]` | Execute tool handlers in parallel using a thread pool. |
| [tool_executor.py](tool_executor.py#L130) | `ToolExecutor.execute_batch_timed` | `handlers: List[Callable[..., Any] \| None], arguments_list: List[Dict[str, Any]], controller: ExecutionController \| None` | `List[ToolExecution]` | Execute tool handlers in parallel, measuring each one's duration. |
| [tool_executor.py](tool_executor.py#L226) | `ToolExecutor.close` | `None` | `None` | Release resources. (No-op — threads clean up on exit.) |
| [tool_handler.py](tool_handler.py#L23) | `ToolHandler.add_tool` | `tool: Tool` | `bool` | Register a tool. No-op if a tool with the same name exists. |
| [tool_handler.py](tool_handler.py#L35) | `ToolHandler.remove_tool` | `name: str` | `bool` | Unregister a tool by name. |
| [tool_handler.py](tool_handler.py#L50) | `ToolHandler.get` | `name: str` | `Tool \| None` | Look up a tool by name. |
| [tool_handler.py](tool_handler.py#L58) | `ToolHandler.get_handler` | `name: str` | `Any \| None` | Return the callable handler for a named tool. |
| [tool_handler.py](tool_handler.py#L67) | `ToolHandler.get_handlers_and_arguments` | `calls: List[LLMToolCall]` | `tuple[List[Any \| None], List[Dict[str, Any]]]` | Resolve a list of tool calls into (handlers, arguments). |
| [tool_handler.py](tool_handler.py#L94) | `ToolHandler.get_all_tool_description` | `None` | `str` | Concatenated ``__str__`` of all registered tools, newline-separated. |
| [tool_handler.py](tool_handler.py#L98) | `ToolHandler.get_all_tools` | `None` | `List[Tool]` | Return all registered tools as a list. |
| [tools/__init__.py](tools/__init__.py#L28) | `__getattr__` | `name: str` | `Any` | Resolve a lazily exported tool factory. |
| [tools/knowledge_tools.py](tools/knowledge_tools.py#L11) | `create_knowledge_tools` | `knowledge_base: KnowledgeBase \| None` | `list[Tool]` | Create tools for searching and reading the workspace knowledge base. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L25) | `_get_obscura_bin` | `None` | `str` | Resolve the configured Obscura executable. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L50) | `_kill_process_group` | `process: subprocess.Popen[str]` | `None` | Terminate one CLI tool process and all children it started. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L61) | `_run_cli` | `command: list[str], timeout: int` | `subprocess.CompletedProcess[str]` | Run a cancellable CLI command for the current tool execution. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L92) | `_unwrap_search_url` | `href: str` | `str` | Extract a destination URL from a DuckDuckGo redirect link. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L142) | `WebSearchStore._connect` | `None` | `sqlite3.Connection` | Open a short-lived WAL connection for a thread-safe operation. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L149) | `WebSearchStore._migrate` | `None` | `None` | Create settings and usage tables without disturbing Agent data. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L164) | `WebSearchStore.get_settings` | `None` | `dict[str, Any]` | Return saved search settings merged with safe defaults. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L171) | `WebSearchStore.update_settings` | `values: dict[str, Any]` | `dict[str, Any]` | Validate, persist, and return web-search settings. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L195) | `WebSearchStore.record` | `provider: str, ok: bool, result_count: int, duration_ms: int` | `None` | Add one provider attempt to today's durable usage aggregate. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L207) | `WebSearchStore.usage` | `days: int` | `list[dict[str, Any]]` | Return provider usage totals for the requested recent day window. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L219) | `configure_web_search_store` | `path: str \| Path, defaults: dict[str, Any] \| None` | `None` | Configure the process-wide persistent store used by new search tools. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L225) | `get_web_search_store` | `None` | `WebSearchStore` | Return the configured store, lazily defaulting to the local runtime DB. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L233) | `_search_duckduckgo` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search DuckDuckGo's HTML endpoint and normalize organic results. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L289) | `_curl_document` | `url: str, timeout: int, user_agent: str` | `tuple[Any \| None, str]` | Fetch one HTML document with bounded curl diagnostics. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L316) | `_search_baidu` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search Baidu's public HTML endpoint for domestic-first retrieval. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L340) | `_search_bing_html` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search Bing's public HTML endpoint without requiring an API key. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L364) | `_search_brave` | `query: str, max_results: int, timeout: int, api_key: str` | `dict[str, Any]` | Search Brave's JSON API using the configured subscription token. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L381) | `_search_bing` | `query: str, max_results: int, timeout: int, api_key: str` | `dict[str, Any]` | Search Bing Web Search API using the configured subscription key. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L398) | `_search_provider` | `provider: str, query: str, max_results: int, timeout: int, settings: dict[str, Any]` | `dict[str, Any]` | Dispatch one configured provider and return its normalized payload. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L417) | `_relevant_search_results` | `query: str, results: list[dict[str, Any]]` | `list[dict[str, Any]]` | Reject result pages with no lexical relationship to the query. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L444) | `_web_search` | `**kwargs: Any` | `dict[str, Any]` | Search domestic-first providers through curl with bounded fallback. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L485) | `_obscura_fetch_cli` | `**kwargs: Any` | `dict[str, Any]` | Execute obscura fetch via CLI. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L554) | `_obscura_scrape_cli` | `**kwargs: Any` | `dict[str, Any]` | Batch-scrape URLs with Obscura workers. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L634) | `create_obscura_tools` | `None` | `list[Tool]` | Create Agent-ready web search and browsing tools. |
| [tools/shell_tools.py](tools/shell_tools.py#L12) | `_kill_process_group` | `process: subprocess.Popen` | `None` | Terminate a shell command and descendants when possible. |
| [tools/shell_tools.py](tools/shell_tools.py#L23) | `create_shell_tools` | `allowed_commands: Optional[List[str]], max_timeout: float, sandbox_cwd: Optional[str], register_process: Optional[Callable[[subprocess.Popen], None]], unregister_process: Optional[Callable[[subprocess.Popen], None]], force_stop_event: Any` | `List[Tool]` | Create shell execution tool with security controls. |
| [tools/spawn_tools.py](tools/spawn_tools.py#L34) | `create_task_report_tool` | `swarm: AgentSwarm, reporter: str, on_report: Callable[[], None]` | `Tool` | Build the terminal report tool for one dispatched or restored worker. |
| [tools/spawn_tools.py](tools/spawn_tools.py#L92) | `create_swarm_tools` | `swarm: AgentSwarm, llm_fetcher: LLMFetcher, worker_tool_pool: list[Tool], worker_tool_factory: Callable[[str], list[Tool]] \| None, worker_tool_binder: Callable[[str, Agent, list[Tool]], list[Tool]] \| None, coordinator_name: str, worker_max_rounds: int, worker_max_tokens: int, worker_max_context_threshold: int, worker_enable_stop_turn: bool, worker_default_stream: bool, context_path_factory: Callable[[str], Any] \| None, require_plan_task_id: bool, plan_task_validator: Callable[[str], bool] \| None` | `list[Tool]` | Create tools that let a coordinator LLM manipulate the swarm at runtime. |
| [usage_ledger.py](usage_ledger.py#L24) | `copy_usage` | `usage: Optional[TokenUsage]` | `TokenUsage` | Copy provider usage, representing a missing provider report as zero. |
| [usage_ledger.py](usage_ledger.py#L37) | `add_usage` | `total: TokenUsage, usage: TokenUsage` | `None` | Add all dimensions without deriving total from its subdimensions. |
| [usage_ledger.py](usage_ledger.py#L46) | `drain_records` | `records: list[UsageRecord]` | `list[UsageRecord]` | Return and consume records in their completed-call order. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [agent.py](agent.py#L29) | `AgentRunControl` | `None` | `Protocol` | Describe cooperative controls read between completed Agent steps. |
| [agent.py](agent.py#L46) | `AgentRunStopped` | `message: str, last_output: LLMOutput \| None` | `RuntimeError` | Signal a cooperative stop after durable completion of one Agent step. |
| [agent.py](agent.py#L64) | `AgentRunLimitReached` | `None` | `RuntimeError` | Signal that an Agent exhausted its round budget before a terminal result. |
| [agent.py](agent.py#L72) | `ContextLoadError` | `None` | `RuntimeError` | Signal that an existing Agent checkpoint could not be restored. |
| [agent.py](agent.py#L76) | `ContextSaveError` | `None` | `RuntimeError` | Signal that a configured Agent checkpoint could not be committed. |
| [agent.py](agent.py#L80) | `AgentRunTermination` | `None` | `str, Enum` | Explicit terminal classifications for one completed Agent invocation. |
| [agent.py](agent.py#L92) | `AgentRunOutcome` | `termination: AgentRunTermination, rounds: int, detail: str, output: LLMOutput \| None` | `object` | Inspectable terminal state for an Agent run. |
| [agent.py](agent.py#L136) | `Agent` | `llm_fetcher: LLMFetcher, system_prompt: str, max_concurrency: int, max_context_threshold: int, context_path: Optional[str \| Path], context_handler: Optional[ContextHandler], default_max_rounds: int, default_max_tokens: int, enable_stop_turn: bool, default_stream: bool` | `object` | Provide `Agent` behavior. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L27) | `ArchiveRetrievalConfig` | `max_results: int, max_chars_per_record: int, min_score: float` | `object` | Hard bounds for local archive retrieval and returned evidence. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L44) | `ArchiveEvidence` | `timeline_start: int, timeline_end: int, role: str, score: float, text: str, matched_terms: tuple[str, ...]` | `object` | A bounded, display-safe projection of one archived context record. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L62) | `ArchiveRetrievalResult` | `query: str, evidence: tuple[ArchiveEvidence, ...], scanned_records: int` | `object` | Result metadata plus bounded evidence suitable for later injection. |
| [context_handlers/base.py](context_handlers/base.py#L8) | `ContextHandler` | `None` | `ABC` | Manages conversational context and builds API-ready message lists. |
| [context_handlers/linear.py](context_handlers/linear.py#L24) | `CompactionFetcher` | `None` | `Protocol` | Describe the minimal LLM interface used for context compaction. |
| [context_handlers/linear.py](context_handlers/linear.py#L95) | `CompactionRequestPreview` | `text: str, system_prompt: str, temperature: float, max_tokens: int, messages: int, omitted: int, threshold: int, round: int` | `object` | One exact, credential-free compaction request plan. |
| [context_handlers/linear.py](context_handlers/linear.py#L183) | `ContextHandlerLinear` | `compacting_llmfetcher_handler: CompactionFetcher, max_context_threshold: int, compaction_input_char_limit: int, compaction_output_max_tokens: int, event_hook: Optional[Callable[[str, str, dict], None]]` | `ContextHandler` | A simple context handler that stores messages in a flat list. |
| [context_handlers/retrieved.py](context_handlers/retrieved.py#L86) | `RetrievedContextHandler` | `project_knowledge_root: str \| Path \| None, user_knowledge_root: str \| Path \| None, tlb_fetcher: CompactionFetcher, compacting_fetcher: CompactionFetcher, classify_fetcher: CompactionFetcher \| None, max_retrieved_sessions: int, retrieval_trigger: str, archive_scope: str, max_context_threshold: int` | `ContextHandler` | TLB-RAG powered conversation memory over linear context. |
| [context_handlers/tlb.py](context_handlers/tlb.py#L12) | `PathStatus` | `None` | `Enum` | An enumerate about paths. |
| [context_handlers/tlb.py](context_handlers/tlb.py#L22) | `WorkingStatus` | `current_focusing: str, other_path_names: List[str], path_status: List[str]` | `object` | Provide `WorkingStatus` behavior. |
| [context_handlers/tlb.py](context_handlers/tlb.py#L28) | `TLBContextHandler` | `context_save_path: str \| Path, llm_fetcher_instance: LLMFetcher` | `ContextHandler` | Provide `TLBContextHandler` behavior. |
| [events.py](events.py#L16) | `ExecutionEvent` | `timestamp: float, source: str, agent_name: str, event_type: str, message: str, data: Any` | `object` | Immutable event emitted during swarm execution. |
| [fetcher_handlers/anthropic.py](fetcher_handlers/anthropic.py#L11) | `AnthropicHandler` | `fetcher: Any, backend: LLMBackendConfig` | `LLMBackendHandler` | Provide `AnthropicHandler` behavior. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L20) | `_UsageLike` | `prompt_tokens: int \| None, completion_tokens: int \| None, total_tokens: int \| None, input_tokens: int \| None, output_tokens: int \| None` | `Protocol` | A protocol for a usage object. |
| [fetcher_handlers/base.py](fetcher_handlers/base.py#L33) | `LLMBackendHandler` | `fetcher: 'LLMFetcher', backend: LLMBackendConfig` | `ABC` | Base class for backend-specific request/response handlers. |
| [fetcher_handlers/deepseek.py](fetcher_handlers/deepseek.py#L51) | `DeepSeekHandler` | `None` | `OpenAIHandler` | OpenAI-compatible chat-completions handler specialised for DeepSeek. |
| [fetcher_handlers/litellm.py](fetcher_handlers/litellm.py#L7) | `LiteLLMHandler` | `fetcher: Any, backend: LLMBackendConfig` | `OpenAIHandler` | Provide `LiteLLMHandler` behavior. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L59) | `_ParsedToolCall` | `tool_name: str, arguments: dict[str, Any]` | `object` | Result of parsing a single ``<tool_call>`` block. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L103) | `_StreamSentinel` | `None` | `object` | Provide `_StreamSentinel` behavior. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L108) | `_ONNXCompletionResponse` | `content: str, raw: str, usage: JSONObject, stop_reason: Optional[str], tool_calls: list[ToolCallDict]` | `object` | Lightweight container returned by non-streaming create_completion. |
| [fetcher_handlers/onnxruntime.py](fetcher_handlers/onnxruntime.py#L208) | `OnnxRuntimeGenAIHandler` | `fetcher: Any, backend: LLMBackendConfig` | `LLMBackendHandler` | Backend handler for decoder-only LLMs via onnxruntime-genai. |
| [fetcher_handlers/openai.py](fetcher_handlers/openai.py#L11) | `OpenAIHandler` | `fetcher: Any, backend: Any` | `LLMBackendHandler` | Provide `OpenAIHandler` behavior. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L13) | `_OpenVINOChatHistory` | `None` | `Protocol` | Provide `_OpenVINOChatHistory` behavior. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L21) | `_OpenVINOTextsResult` | `texts: Sequence[str]` | `Protocol` | Provide `_OpenVINOTextsResult` behavior. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L25) | `_OpenVINOTextResult` | `text: str` | `Protocol` | Provide `_OpenVINOTextResult` behavior. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L29) | `_StreamSentinel` | `None` | `object` | Provide `_StreamSentinel` behavior. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L40) | `_OpenVINOCompletionResponse` | `content: str, raw: str, usage: JSONObject, stop_reason: Optional[str]` | `object` | Provide `_OpenVINOCompletionResponse` behavior. |
| [fetcher_handlers/openvino.py](fetcher_handlers/openvino.py#L47) | `OpenVINOHandler` | `fetcher: Any, backend: LLMBackendConfig` | `LLMBackendHandler` | Provide `OpenVINOHandler` behavior. |
| [graph_memory/builder.py](graph_memory/builder.py#L29) | `ExtractionFetcher` | `None` | `Protocol` | Minimal LLM interface used for graph extraction. |
| [graph_memory/builder.py](graph_memory/builder.py#L47) | `IngestStats` | `entities_added: int, relations_added: int, llm_used: bool, fallback_regex: bool, error: str` | `object` | Statistics for one ingest batch. |
| [graph_memory/builder.py](graph_memory/builder.py#L83) | `GraphBuilder` | `store: GraphStore, fetcher: Optional[ExtractionFetcher], max_batch_chars: int, max_entities_per_batch: int` | `object` | Incremental conversation -> memory-graph builder. |
| [graph_memory/graph_store.py](graph_memory/graph_store.py#L104) | `GraphStore` | `None` | `object` | In-memory entity-relation graph with temporal + provenance metadata. |
| [graph_memory/handler.py](graph_memory/handler.py#L41) | `GraphContextHandler` | `compacting_fetcher: CompactionFetcher, extraction_fetcher: Optional[ExtractionFetcher], query_fetcher: Optional[ExtractionFetcher], store: Optional[GraphStore], retriever_config: Optional[RetrievalConfig], retrieval_trigger: str, graph_update_every: int, max_context_threshold: int, compaction_output_max_tokens: int, graph_save_suffix: str` | `ContextHandler` | A context handler with an entity-relation long-term memory graph. |
| [graph_memory/models.py](graph_memory/models.py#L15) | `EntityNode` | `id: str, name: str, entity_type: str, aliases: list[str], summary: str, first_seen: int, last_seen: int, freq: int, embedding: Optional[list[float]]` | `object` | A single entity in the memory graph. |
| [graph_memory/models.py](graph_memory/models.py#L61) | `RelationEdge` | `source_id: str, target_id: str, relation: str, weight: float, first_seen: int, last_seen: int, valid: bool, evidence: list[int]` | `object` | A relation between two entities with temporal attributes. |
| [graph_memory/models.py](graph_memory/models.py#L109) | `CommunitySummary` | `level: int, community_id: str, summary: str, member_entity_ids: list[str], source_timelines: list[int]` | `object` | Summary of one community (cluster) of the memory graph. |
| [graph_memory/models.py](graph_memory/models.py#L137) | `GraphHit` | `entity: EntityNode, score: float, matched_relation: Optional[str], neighbor_ids: list[str]` | `object` | One retrieval hit: an entity plus its fused score. |
| [graph_memory/models.py](graph_memory/models.py#L155) | `GraphMemoryState` | `version: int, nodes: dict[str, EntityNode], edges: list[RelationEdge], communities: dict[int, list[CommunitySummary]], next_id: int` | `object` | Serialization container for the whole memory graph. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L135) | `RetrievalConfig` | `w_vec: float, w_ppr: float, w_kw: float, w_time: float, top_k: int, max_relations: int, max_communities: int, hop: int, time_decay_lambda: float, min_fused_score: float, include_neighbors: bool, include_communities: bool` | `object` | Weights and limits for the four-channel fusion retrieval. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L176) | `GraphRetrievalResult` | `query: str, seed_entities: list[EntityNode], hits: list[GraphHit], expanded_entities: dict[str, EntityNode], relations: list[RelationEdge], community_summaries: list[CommunitySummary], rendered: str, current_timeline: int` | `object` | Output of :meth:`GraphRetriever.retrieve`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L329) | `GraphRetriever` | `store: GraphStore, query_fetcher: Optional[ExtractionFetcher], config: Optional[RetrievalConfig], query_prompt: str` | `object` | Four-channel hybrid retrieval over a :class:`GraphStore`. |
| [graph_memory/semantic.py](graph_memory/semantic.py#L19) | `SemanticGraphWorker` | `fetcher: Any, backend_name: Optional[str]` | `object` | A no-history, no-tools adapter for graph semantic work. |
| [llm_fetcher.py](llm_fetcher.py#L53) | `StreamUsageCapture` | `None` | `object` | Per-call mutable capture of raw provider usage from one stream. |
| [llm_fetcher.py](llm_fetcher.py#L103) | `LLMFetcher` | `backends: Optional[Sequence[LLMBackendConfig]], default_backend: Optional[str]` | `object` | Route chat requests across one or more configured LLM backends. |
| [llm_types.py](llm_types.py#L17) | `RemoteRequestSnapshot` | `model: str, messages: list[JsonObject], temperature: float, max_tokens: int, stream: bool, tools: list[JsonObject]` | `object` | Credential-free schema for one dispatch-ready remote model request. |
| [llm_types.py](llm_types.py#L64) | `LLMError` | `None` | `Exception` | Base exception for all LLM-related errors. |
| [llm_types.py](llm_types.py#L68) | `LLMTimeoutError` | `None` | `LLMError` | Raised when an LLM request times out. |
| [llm_types.py](llm_types.py#L72) | `LLMBackendError` | `None` | `LLMError` | Raised when all candidate backends fail. |
| [llm_types.py](llm_types.py#L76) | `LLMRequestCancelled` | `None` | `LLMError` | Raised when a terminal force-stop cancels an in-flight LLM request. |
| [llm_types.py](llm_types.py#L85) | `LLMBackendConfig` | `name: str, provider: str, model: str, api_key: str, api_url: Optional[str], timeout: float, max_retries: int, compatibility_profile: Optional[str], extra: Dict[str, Any]` | `object` | Configuration for one routable LLM backend. |
| [llm_types.py](llm_types.py#L123) | `LLMToolCall` | `name: str, arguments: JsonObject, call_id: Optional[str], source: Optional[str]` | `object` | Backend-neutral tool call emitted by a model. |
| [llm_types.py](llm_types.py#L133) | `ToolInfo` | `call: LLMToolCall, result: Optional[str]` | `object` | A tool call paired with its execution result. |
| [llm_types.py](llm_types.py#L146) | `TokenUsage` | `input_tokens: int, output_tokens: int, total_tokens: int, cached_tokens: int, reasoning_tokens: int` | `object` | Platform-irrelevant token usage summary produced by every LLM handler. |
| [llm_types.py](llm_types.py#L167) | `LLMOutput` | `content: str, provider: str, backend_name: str, model: str, role: str, reasoning_content: str, tool_calls: List[LLMToolCall], stop_reason: Optional[str], usage: TokenUsage` | `object` | Backend-neutral non-streaming model output. this class will be created by handlers that handle the LLM call. |
| [llm_types.py](llm_types.py#L195) | `LLMContext` | `role: str, timeline: int, content: str, content_reasoning: str, tool_calls: List[ToolInfo], tags: List[str]` | `object` | A single message in the conversation timeline. |
| [llm_types.py](llm_types.py#L207) | `LLMContextCompacted` | `abstract_msg: str, source_timeline: List[int], source_uuid: List[str], tags: List[str]` | `object` | Summarised representation of one or more LLMContext entries. |
| [llm_types.py](llm_types.py#L224) | `ToolParameter` | `name: str, type: str, description: str, required: bool, enum: Optional[List[str]], default: Optional[Any]` | `object` | A single parameter in a tool's JSON Schema. |
| [llm_types.py](llm_types.py#L236) | `ToolSchema` | `type: str, properties: List[ToolParameter], raw_schema: Optional[Dict[str, Any]]` | `object` | Structured JSON Schema for tool parameters and external tool protocols. |
| [llm_types.py](llm_types.py#L283) | `Tool` | `name: str, description: str, schemas: ToolSchema, handler: Callable[..., Any]` | `object` | A single tool that an Agent can call. |
| [llm_types.py](llm_types.py#L299) | `ToolBatch` | `None` | `object` | Provide `ToolBatch` behavior. |
| [memory/base.py](memory/base.py#L10) | `MemoryItem` | `content: str, score: float, memory_id: str, metadata: dict[str, Any]` | `object` | One retrieved or persisted memory fragment. |
| [memory/base.py](memory/base.py#L27) | `MemoryProvider` | `None` | `Protocol` | Protocol implemented by vector, hybrid, or remote memory stores. |
| [rag_module/knowledge/config.py](rag_module/knowledge/config.py#L11) | `KnowledgeConfig` | `root: Path, embedding_model_name: str, local_files_only: bool, result_limit: int, context_limit: int, excerpt_chars: int, embedding_max_chars: int, chunk_max_chars: int, chunk_overlap_chars: int, semantic_candidates: int, strategy_prefix: str, index_filename: str, chroma_dirname: str, collection_name: str, manifest_version: int, semantic_backend: str` | `object` | Stores runtime configuration for knowledge-base indexing and retrieval. |
| [rag_module/knowledge/context_builder.py](rag_module/knowledge/context_builder.py#L10) | `TaskContextBuilder` | `strategy_prefix: str` | `object` | Formats retrieval results into task-oriented prompt context. |
| [rag_module/knowledge/embedding_model.py](rag_module/knowledge/embedding_model.py#L14) | `EmbeddingModelProvider` | `config: KnowledgeConfig` | `object` | Loads and uses the configured sentence-transformers embedding model. |
| [rag_module/knowledge/facade.py](rag_module/knowledge/facade.py#L25) | `KnowledgeBase` | `root: Path \| None` | `object` | Facade for local Markdown knowledge-base retrieval and indexing. |
| [rag_module/knowledge/hybrid_retriever.py](rag_module/knowledge/hybrid_retriever.py#L15) | `HybridRetriever` | `config: KnowledgeConfig, loader: MarkdownKnowledgeLoader, keyword: KeywordRetriever, vector_store: ChromaVectorStore, index_manager: VectorIndexManager, policy: TaskRetrievalPolicy, text: TextTools` | `object` | Merges keyword scores, vector scores, and task-policy boosts. |
| [rag_module/knowledge/index_manager.py](rag_module/knowledge/index_manager.py#L18) | `VectorIndexManager` | `config: KnowledgeConfig, loader: MarkdownKnowledgeLoader, manifest: KnowledgeManifestStore, vector_store: ChromaVectorStore, embeddings: EmbeddingModelProvider, text: TextTools` | `object` | Coordinates manifest freshness checks and vector-index rebuilds. |
| [rag_module/knowledge/keyword_retriever.py](rag_module/knowledge/keyword_retriever.py#L11) | `KeywordRetriever` | `text: TextTools` | `object` | Scores documents using deterministic title, path, and content matches. |
| [rag_module/knowledge/manifest_store.py](rag_module/knowledge/manifest_store.py#L14) | `KnowledgeManifestStore` | `config: KnowledgeConfig` | `object` | Reads, writes, and validates the `.vector_index.json` manifest. |
| [rag_module/knowledge/markdown_loader.py](rag_module/knowledge/markdown_loader.py#L12) | `MarkdownKnowledgeLoader` | `root: Path` | `object` | Loads Markdown knowledge documents from a configured root directory. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L13) | `KnowledgeHit` | `path: str, title: str, score: float, excerpt: str, chunk_key: str, chunk_index: int, chunk_title: str, heading_path: str, start_line: int, end_line: int, keyword_score: float, vector_score: float` | `object` | Represents one final knowledge-base retrieval result. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L49) | `KnowledgeIndexEntry` | `path: str, title: str, fingerprint: str, excerpt: str, document_id: str` | `object` | Represents one document entry stored in the vector-index manifest. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L84) | `KnowledgeDocument` | `absolute_path: Path, root_relative_path: str, repository_relative_path: str, title: str, content: str` | `object` | Represents one parsed Markdown document from the knowledge root. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L106) | `KnowledgeChunk` | `source_path: str, source_title: str, chunk_key: str, chunk_index: int, chunk_title: str, heading_path: str, start_line: int, end_line: int, content: str` | `object` | Represents one chunk produced from a source Markdown document. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L136) | `MarkdownBlock` | `kind: str, text: str, start_line: int, end_line: int, level: int \| None, info: str \| None` | `object` | Represent one logical block extracted from Markdown content. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L159) | `VectorHit` | `path: str, chunk_key: str, chunk_index: int, chunk_title: str, heading_path: str, start_line: int, end_line: int, score: float, excerpt: str` | `object` | Represents one semantic retrieval result from the vector backend. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L189) | `RetrievalQuery` | `query_text: str, terms: list[str], limit: int, task_type: str, semantic_multiplier: float` | `object` | Represents a normalized retrieval request. |
| [rag_module/knowledge/models.py](rag_module/knowledge/models.py#L212) | `ManifestMeta` | `version: int, backend: str, embedding_model: str, backend_ready: bool, entry_count: int, chunk_count: int, last_error: str` | `object` | Represents manifest-level metadata stored beside vector entries. |
| [rag_module/knowledge/task_policy.py](rag_module/knowledge/task_policy.py#L11) | `TaskRetrievalPolicy` | `keyword: KeywordRetriever, root: Path` | `object` | Builds retrieval queries and task-specific boosts. |
| [rag_module/knowledge/text_utils.py](rag_module/knowledge/text_utils.py#L16) | `TextTools` | `excerpt_chars: int, embedding_max_chars: int, chunk_max_chars: int` | `object` | Provides reusable text extraction and excerpt helpers. |
| [rag_module/knowledge/vector_store.py](rag_module/knowledge/vector_store.py#L13) | `ChromaVectorStore` | `config: KnowledgeConfig, embeddings: EmbeddingModelProvider, text: TextTools` | `object` | Wraps ChromaDB collection management and semantic querying. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L97) | `GraphPersistenceError` | `None` | `ValueError` | Raised when an ExecutionGraph cannot be safely saved or restored. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L102) | `AgentFailure` | `agent_name: str, error: str, exception: Exception \| None` | `object` | Non-fatal marker placed in :meth:`ExecutionGraph.run` outputs when an Agent raises during execution. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L128) | `ExecutionGraph` | `max_concurrency_agents: int` | `object` | Directed acyclic graph that schedules dependent agents concurrently. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L26) | `AgentSwarm` | `max_concurrency_agents: int` | `object` | Orchestrate multiple agents through an execution graph. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L13) | `TaskAssignment` | `id: str, recipient: str, reply_to: str, objective: str, handoff: str, expected_artifacts: tuple[str, ...], created_at: float, plan_task_id: str` | `object` | Immutable work package delivered to one subagent. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L39) | `TaskReport` | `task_id: str, reporter: str, recipient: str, status: str, summary: str, findings: tuple[str, ...], evidence: tuple[str, ...], artifacts: tuple[str, ...], open_questions: tuple[str, ...], recommended_next_action: str, created_at: float` | `object` | Immutable, bounded result package returned to a coordinator inbox. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L80) | `TaskBus` | `None` | `object` | Thread-safe task dispatcher and report mailbox for one execution graph. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L18) | `ExecutionControllerTests` | `None` | `unittest.TestCase` | Verify one stop request governs resource cancellation and observation. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L160) | `_BlockingHandler` | `None` | `object` | Minimal provider double whose close wakes a blocked completion call. |
| [tests/test_execution_controller.py](tests/test_execution_controller.py#L180) | `_StreamingHandler` | `None` | `_BlockingHandler` | Provider double that emits one chunk then blocks on the transport. |
| [tool_executor.py](tool_executor.py#L13) | `ToolBatchCancelled` | `None` | `RuntimeError` | Signal that force-stop abandoned the active tool batch. |
| [tool_executor.py](tool_executor.py#L18) | `ToolExecution` | `result: Any, duration_ms: int` | `object` | One tool handler execution: its result and wall-clock duration. |
| [tool_executor.py](tool_executor.py#L31) | `ToolExecutor` | `max_concurrency: int` | `object` | Execute tool handlers in parallel using a thread pool. |
| [tool_handler.py](tool_handler.py#L8) | `ToolHandler` | `None` | `object` | Register, look up, and describe ``Tool`` objects. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L119) | `WebSearchStore` | `path: str \| Path, defaults: dict[str, Any] \| None` | `object` | Persist web-search settings and per-provider usage counters in SQLite. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L610) | `ObscuraCDPClient` | `host: str, port: int` | `object` | Placeholder configuration for a future Obscura CDP client. |
| [usage_ledger.py](usage_ledger.py#L17) | `UsageRecord` | `kind: str, usage: TokenUsage` | `object` | Usage reported by one completed LLM call. |

<!-- END GENERATED SYMBOL MAP -->
