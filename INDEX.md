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
| Context | `context_handlers/` | Base contract; durable linear history with compaction and raw archive; provider-backed retrieval composition; TLB adapter. `context_less_context/` is an experimental local worktree directory, not part of the indexed API. |
| Graph memory | `graph_memory/` | Persistent entity/relation store, incremental extraction, hybrid graph retrieval, archive evidence, and stateless semantic extraction/reranking workers. |
| Swarm | `swarm_module/` | Dependency graph, concurrent scheduler, TaskBus, bounded report handoff, and quiescent graph save/load. Assignments may carry an opaque external plan-leaf correlation ID that is preserved through events and snapshots. Repeated `run()` calls retain graph vertices; terminal dispatched tasks remain inspectable but are not implicitly rescheduled, and may be revived with a new immutable assignment. |
| Tools | `tool_handler.py`, `tool_executor.py`, `tools/` | Tool schemas/registry, parallel execution, and built-in shell, knowledge, web, and dynamic-spawn factories; `create_swarm_tools` accepts a shared worker pool, a name-bound factory, an optional live-Agent binder, and optional external-plan leaf validation for worker-local handlers needing persistence/reload callbacks. |
| Retrieval modules | `rag_module/`, `rag_module_tlb/` | Legacy/knowledge-base RAG and auditable `INDEX.md` tree traversal. See [`rag_module_tlb/INDEX.md`](rag_module_tlb/INDEX.md). |
| Interfaces | `cli.py`, `webapp.py`, `web/`, `demo/` | Local CLI, standalone web console, and example entry point. |
| Verification | `tests/` | Unit and regression coverage for public API, context, DeepSeek routing, execution graph, TaskBus, and usage ledger. |

## Angelus Integration Points

| Component | Import / path | Why Angelus uses it |
|---|---|---|
| Fetching | `LLMFetcher`, `LLMBackendConfig`, `LLMRequestCancelled` | Configures primary/fallback backend calls; ordinary failures can retry, while `abort_active_requests()` is terminal and never retries or falls back. |
| Agent execution | `Agent`, `AgentRunControl` | Runs a session, accepts cooperative stop/steer controls, observes an optional `force_stopped` event during provider I/O, checkpoints completed context, and emits lifecycle events. |
| Durable context | `ContextHandlerLinear` | Active transcript, LLM compaction, and append-only archived pre-compaction turns. |
| Long-term graph | `GraphContextHandler`, `SemanticGraphWorker` | Graph/archive retrieval; extraction and reranking calls are isolated from the primary Agent's tools and transcript. |
| Observability | `ExecutionEvent`, `agent:usage`, `agent:internal_usage` | Supplies SSE/event-log evidence and non-duplicated five-dimension token accounting. |
| Swarms | `AgentSwarm`, `ExecutionGraph`, `TaskBus` | Schedules dependent agents and passes bounded reports rather than raw worker transcripts. |
| Agent context configuration | `Agent.set_context_threshold` | Updates the in-memory threshold; `Agent.run` reapplies the configured value after checkpoint load and persists it at a safe boundary. |

## Persistence Boundaries

- Linear context atomically persists active messages, compaction abstracts,
  raw archive, editing metadata, schema version, and checkpoint generation.
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

## Local Checks

```bash
../.venv/bin/python -m unittest discover -s llmfetcher/tests -p 'test_*.py'
```

The full project may also have root-level integration tests; run those from the
Angelus superproject rather than treating them as submodule tests.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [agent.py](agent.py#L29) | `AgentRunControl.should_stop` | `None` | `bool` | Return whether the Agent should stop at the current safe boundary. |
| [agent.py](agent.py#L33) | `AgentRunControl.drain_steers` | `None` | `list[str]` | Return and consume queued user steering messages in FIFO order. |
| [agent.py](agent.py#L102) | `AgentRunOutcome.to_dict` | `None` | `dict[str, Any]` | Return the credential-free terminal fields for lifecycle events. |
| [agent.py](agent.py#L112) | `_tool_result_text` | `value: Any` | `str` | Return the complete tool-result string supplied back to the model. |
| [agent.py](agent.py#L230) | `Agent.add_hook` | `hook: ExecutionHook` | `None` | Register an execution-event receiver. |
| [agent.py](agent.py#L241) | `Agent.remove_hook` | `hook: ExecutionHook` | `bool` | Unregister one execution-event receiver. |
| [agent.py](agent.py#L256) | `Agent.request_completion` | `None` | `None` | Request completion after the active model-and-tool step finishes. |
| [agent.py](agent.py#L269) | `Agent.request_turn_stop` | `reason: str` | `None` | Request a normal boundary from the reserved ``stop_turn`` tool. |
| [agent.py](agent.py#L284) | `Agent.add_stop_turn_tool` | `None` | `bool` | Register the reserved model-visible control tool for ending a turn. |
| [agent.py](agent.py#L293) | `Agent._create_stop_turn_tool` | `None` | `Tool` | Create the reserved model-visible control tool for ending a turn. |
| [agent.py](agent.py#L321) | `Agent._set_outcome` | `termination: AgentRunTermination, rounds: int, detail: str, output: LLMOutput \| None` | `AgentRunOutcome` | Record and publish the single explicit terminal result of this run. |
| [agent.py](agent.py#L348) | `Agent.set_context_threshold` | `max_context_threshold: int, persist: bool` | `bool` | Update the compaction threshold used by this Agent's context. |
| [agent.py](agent.py#L388) | `Agent._emit` | `source: str, agent_name: str, event_type: str, message: str, data: Any` | `None` | Send one event to each registered hook, isolating hook failures. |
| [agent.py](agent.py#L422) | `Agent._compaction_event_hook` | `event_type: str, message: str, data: dict` | `None` | Publish a context-handler compaction lifecycle event. |
| [agent.py](agent.py#L446) | `Agent._usage_data` | `usage: TokenUsage` | `dict[str, int]` | Serialize every normalized usage dimension for durable events. |
| [agent.py](agent.py#L456) | `Agent._drain_internal_usage` | `name: str` | `None` | Publish and aggregate each hidden LLM call once, if supported. |
| [agent.py](agent.py#L473) | `Agent.add_tool` | `tool: Tool` | `bool` | Register one callable tool on this Agent. |
| [agent.py](agent.py#L484) | `Agent.add_tools` | `tools: List[Tool]` | `bool` | Register a batch of tools in the supplied order. |
| [agent.py](agent.py#L504) | `Agent._build_prompt` | `None` | `str` | Return the system prompt without serializing registered tools into it. |
| [agent.py](agent.py#L518) | `Agent._save_context` | `None` | `bool` | Persist the current context when this Agent has a storage path. |
| [agent.py](agent.py#L538) | `Agent._fetch_model_with_force_stop` | `control: AgentRunControl \| None, **fetch_kwargs: Any` | `LLMOutput` | Fetch one model response, allowing a terminal browser force-stop. |
| [agent.py](agent.py#L602) | `Agent._stream_model_response` | `name: str, round_idx: int, control: AgentRunControl \| None, **fetch_kwargs: Any` | `LLMOutput` | Stream one provider response, emit deltas, and rebuild its final form. |
| [agent.py](agent.py#L689) | `Agent.run` | `message: str, max_rounds: int \| None, temperature: float, max_tokens: int \| None, verbose: bool, control: AgentRunControl \| None, stream: bool \| None` | `LLMOutput` | Run the Agent until one explicit terminal outcome is reached. |
| [agent.py](agent.py#L1113) | `Agent.close` | `None` | `None` | Release sub-interpreter resources held by the tool executor. |
| [agent.py](agent.py#L1117) | `Agent.clear_context` | `None` | `None` | Clear context. |
| [cli.py](cli.py#L58) | `_load_tools` | `names: list[str]` | `list[Tool]` | Import and call tool factories by short name. |
| [cli.py](cli.py#L94) | `_build_parser` | `None` | `argparse.ArgumentParser` | Implement `_build_parser`. |
| [cli.py](cli.py#L190) | `_cmd_list_backends` | `None` | `None` | Print every registered backend provider. |
| [cli.py](cli.py#L201) | `_cmd_list_tools` | `None` | `None` | Print every known tool-set name + description. |
| [cli.py](cli.py#L214) | `_build_backend_config` | `args: argparse.Namespace` | `LLMBackendConfig` | Construct a single ``LLMBackendConfig`` from parsed args. |
| [cli.py](cli.py#L241) | `_bootstrap_agent` | `args: argparse.Namespace` | `Agent` | Create an ``Agent`` wired with the CLI config and requested tools. |
| [cli.py](cli.py#L272) | `_cmd_run` | `args: argparse.Namespace` | `None` | Execute a single prompt and print the final response. |
| [cli.py](cli.py#L299) | `_cmd_chat` | `args: argparse.Namespace` | `None` | Interactive read-eval-print loop. |
| [cli.py](cli.py#L330) | `main` | `argv: list[str] \| None` | `None` | Parse CLI arguments and dispatch the selected command. |
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
| [context_handlers/linear.py](context_handlers/linear.py#L26) | `CompactionFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Any` | `LLMOutput` | Generate one compacted context response. |
| [context_handlers/linear.py](context_handlers/linear.py#L174) | `ContextHandlerLinear.clear_context` | `None` | `Any` | Clear all conversation entries and restart timeline numbering. |
| [context_handlers/linear.py](context_handlers/linear.py#L188) | `ContextHandlerLinear.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed internal-call usage records exactly once. |
| [context_handlers/linear.py](context_handlers/linear.py#L193) | `ContextHandlerLinear.set_compaction_event_hook` | `hook: Optional[Callable[[str, str, dict], None]]` | `None` | Attach or detach the compaction lifecycle event observer. |
| [context_handlers/linear.py](context_handlers/linear.py#L208) | `ContextHandlerLinear._emit_compaction_event` | `event_type: str, message: str, data: Dict[str, Any]` | `None` | Notify the attached observer, isolating any observer failure. |
| [context_handlers/linear.py](context_handlers/linear.py#L232) | `ContextHandlerLinear.add_user_message` | `message: str` | `None` | Append an User input to conversation history. |
| [context_handlers/linear.py](context_handlers/linear.py#L256) | `ContextHandlerLinear.add_assistant_message` | `message: LLMOutput, tool_results: Optional[Dict[str, str]]` | `None` | Append an LLM output to the conversation history. |
| [context_handlers/linear.py](context_handlers/linear.py#L295) | `ContextHandlerLinear.compact` | `None` | `bool` | Compress the conversation history into a single abstract. |
| [context_handlers/linear.py](context_handlers/linear.py#L441) | `ContextHandlerLinear.get_prev_messages` | `None` | `List[LLMContext \| LLMContextCompacted]` | Return the stored conversation history. |
| [context_handlers/linear.py](context_handlers/linear.py#L449) | `ContextHandlerLinear.build_messages` | `None` | `List[Dict[str, Any]]` | Build context messages for an LLM request. |
| [context_handlers/linear.py](context_handlers/linear.py#L501) | `ContextHandlerLinear._estimate_context_size` | `None` | `int` | Estimate the size of the context that would reach the model. |
| [context_handlers/linear.py](context_handlers/linear.py#L517) | `ContextHandlerLinear._bound_result_text` | `value: str, limit: int` | `str` | Return a request-safe copy of a tool result bounded to *limit* chars. |
| [context_handlers/linear.py](context_handlers/linear.py#L549) | `ContextHandlerLinear._bounded_tool_results` | `tool_results: Optional[Dict[str, str]]` | `Dict[str, str]` | Copy complete tool output into the in-memory conversation history. |
| [context_handlers/linear.py](context_handlers/linear.py#L572) | `ContextHandlerLinear._build_compaction_input` | `None` | `str` | Render a bounded, newest-first transcript for one summary request. |
| [context_handlers/linear.py](context_handlers/linear.py#L610) | `ContextHandlerLinear._parse_compacted_abstract` | `raw: str` | `Optional[str]` | Extract the contents of the ``<context_abstract>`` tag. |
| [context_handlers/linear.py](context_handlers/linear.py#L638) | `ContextHandlerLinear.save` | `path: str \| Path, checkpoint_generation: str \| None, graph_checkpoint: str \| None` | `bool` | Serialize the conversation history to a JSON file. |
| [context_handlers/linear.py](context_handlers/linear.py#L707) | `ContextHandlerLinear.load` | `path: Optional[str \| Path]` | `bool` | Deserialize conversation history from a JSON file. |
| [context_handlers/linear.py](context_handlers/linear.py#L782) | `ContextHandlerLinear._context_to_dict` | `ctx: LLMContext` | `Dict[str, Any]` | Implement `ContextHandlerLinear._context_to_dict`. |
| [context_handlers/linear.py](context_handlers/linear.py#L786) | `ContextHandlerLinear._context_from_dict` | `data: Dict[str, Any]` | `LLMContext` | Implement `ContextHandlerLinear._context_from_dict`. |
| [context_handlers/linear.py](context_handlers/linear.py#L806) | `ContextHandlerLinear._compacted_to_dict` | `comp: Optional[LLMContextCompacted]` | `Optional[Dict[str, Any]]` | Implement `ContextHandlerLinear._compacted_to_dict`. |
| [context_handlers/linear.py](context_handlers/linear.py#L814) | `ContextHandlerLinear._compacted_from_dict` | `data: Optional[Dict[str, Any]]` | `Optional[LLMContextCompacted]` | Implement `ContextHandlerLinear._compacted_from_dict`. |
| [context_handlers/linear.py](context_handlers/linear.py#L828) | `ContextHandlerLinear._append_context_messages` | `messages: List[Dict[str, Any]], item: LLMContext, remaining_budget: Optional[List[int]]` | `None` | Append backend-neutral messages for a single context entry. |
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
| [graph_memory/handler.py](graph_memory/handler.py#L101) | `GraphContextHandler._init_session_state` | `None` | `None` | (Re)set all per-session transient state (keeps long-term graph). |
| [graph_memory/handler.py](graph_memory/handler.py#L112) | `GraphContextHandler.has_retrieved` | `None` | `bool` | True once a retrieval has been performed this session. |
| [graph_memory/handler.py](graph_memory/handler.py#L117) | `GraphContextHandler.graph_memory` | `None` | `str` | Last rendered ``<graph_memory>`` block (empty when none). |
| [graph_memory/handler.py](graph_memory/handler.py#L122) | `GraphContextHandler.compaction_generation` | `None` | `int` | Number of compactions observed since the session started. |
| [graph_memory/handler.py](graph_memory/handler.py#L127) | `GraphContextHandler.compress_threshold` | `None` | `int` | Compaction threshold forwarded from the inner linear handler. |
| [graph_memory/handler.py](graph_memory/handler.py#L137) | `GraphContextHandler.extra_usage` | `None` | `Any` | Aggregate token usage from linear compaction + graph LLM calls. |
| [graph_memory/handler.py](graph_memory/handler.py#L157) | `GraphContextHandler.record_usage` | `usage: Optional[Any]` | `None` | Forward one internal LLM call's usage to the inner linear handler. |
| [graph_memory/handler.py](graph_memory/handler.py#L161) | `GraphContextHandler.drain_usage_records` | `None` | `list[UsageRecord]` | Drain child internal-call records in the order their components run. |
| [graph_memory/handler.py](graph_memory/handler.py#L175) | `GraphContextHandler.retrieve` | `query: str` | `GraphRetrievalResult` | Run hybrid graph retrieval and store the rendered context block. |
| [graph_memory/handler.py](graph_memory/handler.py#L193) | `GraphContextHandler.add_user_message` | `message: str` | `None` | Append a user message and trigger retrieval when due. |
| [graph_memory/handler.py](graph_memory/handler.py#L204) | `GraphContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[dict[str, str]]` | `None` | Append an assistant output, detect compaction and flush the graph. |
| [graph_memory/handler.py](graph_memory/handler.py#L227) | `GraphContextHandler.build_messages` | `None` | `list[dict[str, Any]]` | Build messages: graph memory block (user), then linear history. |
| [graph_memory/handler.py](graph_memory/handler.py#L238) | `GraphContextHandler.save` | `path: str \| Path` | `bool` | Save the conversation AND the companion graph file. |
| [graph_memory/handler.py](graph_memory/handler.py#L280) | `GraphContextHandler.load` | `path: str \| Path` | `bool` | Restore the conversation and its companion graph. |
| [graph_memory/handler.py](graph_memory/handler.py#L351) | `GraphContextHandler.clear_context` | `None` | `bool` | Clear the session but keep the long-term memory graph. |
| [graph_memory/handler.py](graph_memory/handler.py#L359) | `GraphContextHandler._retrieve_archive_evidence` | `query: str` | `str` | Render small, provenance-labelled raw evidence for a new query. |
| [graph_memory/handler.py](graph_memory/handler.py#L392) | `GraphContextHandler._should_retrieve` | `None` | `bool` | Decide whether this newly stored user message should retrieve. |
| [graph_memory/handler.py](graph_memory/handler.py#L409) | `GraphContextHandler._flush_pending` | `None` | `None` | Ingest buffered messages into the graph and clear the buffer. |
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
| [llm_fetcher.py](llm_fetcher.py#L72) | `StreamUsageCapture.merge` | `raw_usage: Any` | `None` | Merge one raw usage payload (dict or provider object). |
| [llm_fetcher.py](llm_fetcher.py#L97) | `StreamUsageCapture.raw` | `None` | `dict[str, Any] \| None` | Return the merged raw usage mapping, or ``None`` when absent. |
| [llm_fetcher.py](llm_fetcher.py#L122) | `LLMFetcher.list_available_backend_providers` | `None` | `tuple[str, ...]` | Return all provider names supported by registered handlers, sorted. |
| [llm_fetcher.py](llm_fetcher.py#L186) | `LLMFetcher.backend_configs` | `None` | `Dict[str, LLMBackendConfig]` | Return a copy of all registered backend configurations. |
| [llm_fetcher.py](llm_fetcher.py#L196) | `LLMFetcher.fallback_order` | `None` | `List[str]` | Return the current fallback order (shallow copy). |
| [llm_fetcher.py](llm_fetcher.py#L206) | `LLMFetcher.default_backend_config` | `None` | `LLMBackendConfig` | Return the configuration of the default backend. |
| [llm_fetcher.py](llm_fetcher.py#L216) | `LLMFetcher._register_backend` | `backend: LLMBackendConfig` | `None` | Register a single backend and pre-create its handler. |
| [llm_fetcher.py](llm_fetcher.py#L236) | `LLMFetcher._resolve_backends` | `backend_name: Optional[str], fallback_order: Optional[Sequence[str]]` | `List[LLMBackendConfig]` | Resolve the ordered backend list for a single request. |
| [llm_fetcher.py](llm_fetcher.py#L282) | `LLMFetcher._handler_for_backend` | `backend: LLMBackendConfig` | `LLMBackendHandler` | Return the handler instance for a given backend configuration. |
| [llm_fetcher.py](llm_fetcher.py#L298) | `LLMFetcher._normalize_exception` | `backend: LLMBackendConfig, exc: Exception` | `LLMError` | Normalise any exception into an ``LLMError`` subclass. |
| [llm_fetcher.py](llm_fetcher.py#L326) | `LLMFetcher._sleep_before_retry` | `retry_index: int` | `None` | Wait with cancellation-aware exponential backoff before retrying. |
| [llm_fetcher.py](llm_fetcher.py#L343) | `LLMFetcher._raise_if_force_stopped` | `None` | `None` | Raise the terminal cancellation error without retrying providers. |
| [llm_fetcher.py](llm_fetcher.py#L354) | `LLMFetcher.abort_active_requests` | `None` | `int` | Close provider transports for this terminal force-stop. |
| [llm_fetcher.py](llm_fetcher.py#L382) | `LLMFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Optional[Sequence[ToolDefinition]], on_request: Optional[Callable[[RemoteRequestSnapshot], None]], on_retry: Optional[Callable[[int], None]]` | `LLMOutput` | Execute a non-streaming completion with backend fallback and retry. |
| [llm_fetcher.py](llm_fetcher.py#L495) | `LLMFetcher.fetch_stream` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, output_reasoning: bool, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Optional[Sequence[ToolDefinition]], on_request: Optional[Callable[[RemoteRequestSnapshot], None]], on_retry: Optional[Callable[[int], None]], usage_sink: Optional[TokenUsage]` | `Generator[str, None]` | Execute a streaming completion with backend fallback and retry. |
| [llm_fetcher.py](llm_fetcher.py#L630) | `LLMFetcher._max_attempts` | `backend: LLMBackendConfig` | `int` | Return the number of times to attempt a request for a backend. |
| [llm_fetcher.py](llm_fetcher.py#L645) | `LLMFetcher._build_messages` | `msg: str, system_prompt: Optional[str], context: Optional[ContextHandler]` | `List[Dict[str, Any]]` | Build the message list, delegating to a context handler when available. |
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
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L457) | `ExecutionGraph.view_snapshot` | `None` | `dict[str, Any]` | Return a JSON-safe live topology view without executable objects. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L508) | `ExecutionGraph.finalize_tasks` | `None` | `dict[str, str]` | Close every unfinished dynamic task after the scheduler stops. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L541) | `ExecutionGraph.request_shutdown` | `None` | `None` | Ask the scheduler to stop submitting further runnable Agents. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L552) | `ExecutionGraph._emit` | `source: str, agent_name: str, event_type: str, message: str, data: Any` | `None` | Fire an event to all registered hooks. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L580) | `ExecutionGraph._record_node_state` | `agent_name: str, event_type: str, message: str, data: Any` | `None` | Project one lifecycle event into the UI-facing node state cache. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L636) | `ExecutionGraph._attach_agent_events` | `agent: Agent` | `None` | Forward one graph member's lifecycle events to graph hooks. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L674) | `ExecutionGraph.add_agent` | `agent_name: str, agent_instance: Agent` | `bool` | Register an agent as a graph vertex. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L707) | `ExecutionGraph.add_routing_node` | `name: str, router: RouterFn` | `bool` | Register a lightweight non-LLM routing node. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L744) | `ExecutionGraph.remove_agent` | `agent_name: str` | `bool` | Remove an agent and every edge connected to it. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L778) | `ExecutionGraph.add_connection` | `source: str, target: str` | `bool` | Add a directed dependency edge from one agent to another. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L819) | `ExecutionGraph.add_split` | `source: str, targets: list[str]` | `None` | Broadcast one agent's output to multiple successor agents. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L845) | `ExecutionGraph.add_gather` | `sources: list[str], target: str, mapper: MapperFn \| None` | `None` | Make one agent depend on and aggregate multiple source agents. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L885) | `ExecutionGraph.set_mapper` | `agent_name: str, mapper: MapperFn` | `None` | Set a node-level mapper on *agent_name*. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L916) | `ExecutionGraph.set_router` | `agent_name: str, router: RouterFn` | `None` | Attach a post-completion router to an existing agent. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L950) | `ExecutionGraph.remove_router` | `agent_name: str` | `bool` | Remove a post-completion router from an agent. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L969) | `ExecutionGraph.dispatch_task` | `agent_name: str, agent_instance: Agent, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create a worker, deliver an explicit task, and queue it to run. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1045) | `ExecutionGraph.task_id_for_agent` | `agent_name: str` | `str` | Return the latest TaskBus assignment owned by one worker. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1063) | `ExecutionGraph.redispatch_task` | `agent_name: str, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Assign a fresh task to an existing terminal dispatched worker. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1145) | `ExecutionGraph.report_task` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Accept a structured worker report without forwarding raw output. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1197) | `ExecutionGraph.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Block until requested structured reports arrive or time expires. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1213) | `ExecutionGraph.dynamic_add_agent` | `agent_name: str, agent_instance: Agent` | `str` | Register an Agent node while a graph run is active. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1241) | `ExecutionGraph.dynamic_remove_agent` | `agent_name: str` | `str` | Dynamically remove an agent and its edges during execution. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1265) | `ExecutionGraph.dynamic_add_connection` | `source: str, target: str` | `str` | Dynamically add a dependency edge during execution. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1295) | `ExecutionGraph.dynamic_remove_connection` | `source: str, target: str` | `str` | Remove one dependency edge while the graph is editable. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1315) | `ExecutionGraph.dynamic_set_mapper` | `agent_name: str, mode: str` | `str` | Set a safe declarative input aggregator on an Agent node. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1334) | `ExecutionGraph.dynamic_set_router` | `agent_name: str, targets: list[str]` | `str` | Set a declarative router selecting a fixed successor subset. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1357) | `ExecutionGraph._mapper_for_mode` | `mode: str` | `MapperFn` | Return the built-in mapper function for one persisted mode. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1380) | `ExecutionGraph._restore_declarative_mapper` | `agent_name: str, mode: str` | `None` | Install one persisted declarative mapper without emitting an event. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1395) | `ExecutionGraph._restore_declarative_router` | `agent_name: str, targets: list[str]` | `None` | Install one persisted fixed router without emitting an event. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1414) | `ExecutionGraph.dynamic_get_info` | `None` | `str` | Return the current graph state as a structured string. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1453) | `ExecutionGraph.run` | `message: str, max_rounds: int \| None, control: AgentRunControl \| None` | `dict[str, Any]` | Execute the graph using dependency-driven concurrent scheduling. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1757) | `ExecutionGraph._activate` | `completed_agent: str, successors: Iterable[str], remaining_dependencies: dict[str, int], ready: deque[str]` | `None` | Decrement dependency counts and enqueue ready successors. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1783) | `ExecutionGraph._drain_dynamic_ready` | `ready: deque[str], remaining_dependencies: dict[str, int]` | `None` | Move explicitly dispatched workers into the local scheduler queue. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1825) | `ExecutionGraph._render_assignment` | `assignment: TaskAssignment` | `str` | Render one explicit task package without exposing raw peer output. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1844) | `ExecutionGraph._build_input` | `agent_name: str, initial_message: str, outputs: Mapping[str, Any]` | `str` | Build the input message for one ready agent. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1890) | `ExecutionGraph._output_to_text` | `output: Any` | `str` | Convert an arbitrary agent output into message text. |
| [swarm_module/execution_graph.py](swarm_module/execution_graph.py#L1903) | `ExecutionGraph._require_agent` | `agent_name: str` | `None` | Ensure that an agent name is registered. |
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
| [swarm_module/swarm.py](swarm_module/swarm.py#L385) | `AgentSwarm.view_snapshot` | `None` | `dict[str, Any]` | Return a safe, UI-oriented snapshot of the active graph topology. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L394) | `AgentSwarm.finalize_tasks` | `None` | `dict[str, str]` | Close unfinished dynamic tasks after any terminal run outcome. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L406) | `AgentSwarm.request_shutdown` | `None` | `None` | Stop scheduling further runnable Agents in the active graph. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L421) | `AgentSwarm.total_usage` | `None` | `dict[str, int]` | Aggregate token usage across every registered Agent. |
| [swarm_module/swarm.py](swarm_module/swarm.py#L448) | `AgentSwarm.run` | `message: str, max_rounds: int \| None, control: AgentRunControl \| None` | `dict[str, Any]` | Execute the graph with an optional cooperative Agent control. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L71) | `TaskReport.as_dict` | `None` | `dict[str, Any]` | Return a JSON-ready representation of the structured report. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L101) | `TaskBus.create_assignment` | `recipient: str, reply_to: str, objective: str, handoff: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create and enqueue one immutable subagent work package. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L153) | `TaskBus.claim_assignment` | `task_id: str` | `TaskAssignment` | Mark one queued assignment running and return its work package. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L175) | `TaskBus.submit_report` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Close a task with a bounded report and deliver it to its inbox. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L239) | `TaskBus.set_terminal_state` | `task_id: str, state: str` | `bool` | Close one unfinished assignment without manufacturing a report. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L266) | `TaskBus.finalize_unfinished` | `running_state: str, queued_state: str` | `dict[str, str]` | Close every non-terminal assignment at an execution boundary. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L310) | `TaskBus.fail_unreported_task` | `task_id: str, reporter: str, reason: str` | `TaskReport \| None` | Submit a failure report when a worker exits without reporting. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L332) | `TaskBus.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Wait until every requested task has delivered a structured report. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L355) | `TaskBus.get_assignment` | `task_id: str` | `TaskAssignment` | Return one immutable task assignment. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L373) | `TaskBus.task_states` | `None` | `dict[str, str]` | Return a point-in-time view of each task lifecycle state. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L385) | `TaskBus.to_snapshot` | `None` | `dict[str, Any]` | Return a JSON-compatible, point-in-time copy of TaskBus state. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L408) | `TaskBus.from_snapshot` | `snapshot: Mapping[str, Any]` | `'TaskBus'` | Restore a TaskBus from :meth:`to_snapshot` output. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L495) | `TaskBus._normalize_items` | `values: Iterable[str]` | `tuple[str, ...]` | Normalize, bound, and freeze a report list field. |
| [swarm_module/task_bus.py](swarm_module/task_bus.py#L509) | `TaskBus._state_for_report_status` | `status: str` | `str` | Map an Agent-supplied report status to a canonical task terminal. |
| [tests/test_agent_prompt.py](tests/test_agent_prompt.py#L23) | `_RecordingFetcher.fetch` | `**kwargs: Any` | `Any` | Capture the native tool channel and emit its matching snapshot. |
| [tests/test_agent_prompt.py](tests/test_agent_prompt.py#L48) | `AgentPromptTests.test_system_prompt_excludes_registered_tool_description` | `None` | `None` | Keep a tool's legacy text representation out of ``messages[0]``. |
| [tests/test_agent_prompt.py](tests/test_agent_prompt.py#L72) | `AgentPromptTests.test_remote_request_keeps_tools_out_of_the_system_message` | `None` | `None` | Expose one schema in ``tools`` without duplicating it in ``messages``. |
| [tests/test_agent_prompt.py](tests/test_agent_prompt.py#L90) | `AgentPromptTests.test_raw_tool_schema_retains_nested_external_contract` | `None` | `None` | Keep MCP-style nested schemas outside the flat parameter adapter. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L22) | `_SequenceFetcher.fetch` | `**kwargs: object` | `LLMOutput` | Record the tools passed natively and return the next response. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L34) | `_StreamingFetcher.fetch_stream` | `**_kwargs: object` | `Any` | Yield content and reasoning chunks in the normalized stream format. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L43) | `_output` | `content: str, calls: list[LLMToolCall] \| None` | `LLMOutput` | Create one compact test response with optional native tool calls. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L57) | `AgentTerminationTests.test_formal_content_ends_without_a_tool_result` | `None` | `None` | A normal assistant response is a successful terminal outcome. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L66) | `AgentTerminationTests.test_streamed_chunks_become_deltas_and_one_final_output` | `None` | `None` | Streaming remains incremental for the UI but final for persistence. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L80) | `AgentTerminationTests.test_empty_tool_result_does_not_end_the_agent_turn` | `None` | `None` | Tool-call presence, not its returned text, controls continuation. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L95) | `AgentTerminationTests.test_stop_turn_ends_after_its_tool_batch` | `None` | `None` | The reserved tool creates a visible terminal control outcome. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L106) | `AgentTerminationTests.test_empty_model_response_is_not_silent_completion` | `None` | `None` | A blank response without tools raises an observable invalid outcome. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L115) | `AgentTerminationTests.test_round_limit_rejects_an_unfinished_tool_loop` | `None` | `None` | Budget exhaustion cannot present a pending tool call as a final answer. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L127) | `AgentTerminationTests.test_workflow_completion_remains_distinct_from_stop_turn` | `None` | `None` | Worker-report style handlers retain their explicit completion reason. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L34) | `_RecordingCompactor.fetch` | `msg: str, system_prompt: str \| None, temperature: float, max_tokens: int, context_handler: Any, backend_name: str \| None, tools: Any` | `LLMOutput` | Record the request and return a valid compacted-context payload. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L78) | `ContextCompactionTests.test_compaction_uses_bounded_stateless_request` | `None` | `None` | Compact a large tool result without using full history as context. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L107) | `ContextCompactionTests.test_compaction_prompt_bounds_working_summary_and_treats_history_as_data` | `None` | `None` | Keep compaction instructions bounded and resistant to transcript prompts. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L114) | `ContextCompactionTests.test_compaction_accepts_truncated_tagged_summary` | `None` | `None` | Retain a usable summary when a provider omits only the closing tag. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L125) | `ContextCompactionTests.test_compaction_exposes_unparseable_model_response_for_diagnostics` | `None` | `None` | Keep failure details transient while allowing applications to show them. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L136) | `ContextCompactionTests.test_tool_result_is_complete_in_history_storage` | `None` | `None` | Retain the complete tool result for lossless persistence/export. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L159) | `ContextCompactionTests.test_load_restores_round_for_new_and_legacy_contexts` | `None` | `None` | Continue timeline numbering after loading either context format. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L184) | `ContextCompactionTests.test_load_restores_round_from_compacted_timeline` | `None` | `None` | Recover the counter when compaction leaves no retained messages. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L204) | `ContextCompactionTests.test_compaction_archives_raw_messages_and_owns_provenance` | `None` | `None` | Never trust model timeline tags or discard raw compacted turns. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L230) | `ContextCompactionTests.test_save_load_preserves_raw_compaction_archive` | `None` | `None` | Archived raw entries survive restart while staying out of prompts. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L251) | `ContextCompactionTests.test_clear_context_restarts_timeline` | `None` | `None` | Assign timeline one to the first message after an explicit clear. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L261) | `ContextCompactionTests.test_save_failure_keeps_previous_file_and_removes_temporary_file` | `None` | `None` | A failed replacement must not corrupt the last committed context. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L277) | `ContextCompactionTests.test_failed_load_preserves_live_state` | `None` | `None` | Malformed checkpoints must not replace a retained handler's memory. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L288) | `ContextCompactionTests.test_editing_metadata_survives_load_save` | `None` | `None` | Agent checkpoints retain revision and graph-staleness metadata. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L304) | `ContextCompactionTests.test_request_bounds_oversized_tool_result_but_keeps_history` | `None` | `None` | A huge tool result is trimmed on the request, never in storage. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L336) | `ContextCompactionTests.test_context_size_estimate_reflects_trimmed_request` | `None` | `None` | Oversized results must not inflate the compaction estimate. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L354) | `ContextCompactionTests.test_compaction_reanchors_latest_user_message_for_next_round` | `None` | `None` | The first post-compaction round still has an explicit user input. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L385) | `ContextCompactionTests.test_compaction_reanchors_most_recent_user_message` | `None` | `None` | The resume turn is derived, so no user message is re-stored. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L411) | `ContextCompactionTests.test_compaction_without_user_message_still_adds_resume_prompt` | `None` | `None` | A user-less archive still yields a usable next-round request. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L429) | `ContextCompactionTests.test_resume_turn_cleared_once_real_user_message_arrives` | `None` | `None` | A real user turn supersedes the derived resume prompt. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L460) | `CompactionLifecycleEventTests._handler` | `compactor: Any, **kwargs: Any` | `ContextHandlerLinear` | Implement `CompactionLifecycleEventTests._handler`. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L475) | `CompactionLifecycleEventTests.test_success_emits_started_then_success` | `None` | `None` | A successful compaction reports started -> success in order. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L506) | `CompactionLifecycleEventTests.test_skipped_emits_only_skipped` | `None` | `None` | Compacting an empty context reports skipped without a model call. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L520) | `CompactionLifecycleEventTests.test_empty_response_emits_failed_with_error` | `None` | `None` | An empty model response reports failed with the error message. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L538) | `CompactionLifecycleEventTests.test_unparseable_response_reports_failed_with_raw_retained` | `None` | `None` | An unparseable response reports failed while keeping raw content. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L555) | `CompactionLifecycleEventTests.test_model_exception_emits_failed_and_reraises` | `None` | `None` | A raising fetcher reports failed and still propagates the error. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L574) | `CompactionLifecycleEventTests.test_raising_hook_never_breaks_compaction` | `None` | `None` | A broken observer is isolated and compaction semantics stay intact. |
| [tests/test_context_persistence_errors.py](tests/test_context_persistence_errors.py#L26) | `_Fetcher.fetch` | `**kwargs: Any` | `LLMOutput` | Implement `_Fetcher.fetch`. |
| [tests/test_context_persistence_errors.py](tests/test_context_persistence_errors.py#L36) | `_FailingSaveHandler.save` | `path: Any, **kwargs: Any` | `bool` | Implement `_FailingSaveHandler.save`. |
| [tests/test_context_persistence_errors.py](tests/test_context_persistence_errors.py#L40) | `test_existing_corrupt_checkpoint_fails_before_remote_request` | `None` | `None` | A corrupt file is not treated as an absent, empty checkpoint. |
| [tests/test_context_persistence_errors.py](tests/test_context_persistence_errors.py#L54) | `test_checkpoint_save_failure_is_propagated` | `None` | `None` | A completed model boundary cannot report success without persistence. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L16) | `_make_handler` | `None` | `DeepSeekHandler` | Implement `_make_handler`. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L30) | `DeepSeekHandlerTests.test_provider_registered` | `None` | `None` | DeepSeek is a registered provider name for the dispatcher. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L35) | `DeepSeekHandlerTests.test_dispatch_prefers_specialised_handler` | `None` | `None` | provider='deepseek' resolves to DeepSeekHandler, not OpenAIHandler. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L44) | `DeepSeekHandlerTests.test_openai_compatible_deepseek_model_uses_specialised_handler` | `None` | `None` | A DeepSeek model must not lose native reasoning behaviour at a proxy. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L56) | `DeepSeekHandlerTests.test_openai_compatible_deepseek_profile_uses_specialised_handler` | `None` | `None` | An explicit profile supports gateways with provider-neutral models. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L69) | `DeepSeekHandlerTests.test_openai_compatible_deepseek_url_uses_specialised_handler` | `None` | `None` | The official DeepSeek endpoint is recognised without a model prefix. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L81) | `DeepSeekHandlerTests.test_openai_compatible_generic_endpoint_stays_generic` | `None` | `None` | Unrelated OpenAI-compatible configurations keep their old handler. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L93) | `DeepSeekHandlerTests.test_normalize_completion_response_reasoning` | `None` | `None` | reasoning_content is captured from a non-streamed message. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L113) | `DeepSeekHandlerTests.test_normalize_completion_response_ignores_alien_aliases` | `None` | `None` | No fallback to reasoning/thinking aliases owned by other platforms. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L131) | `DeepSeekHandlerTests.test_normalize_usage_cache_hit_tokens` | `None` | `None` | DeepSeek prompt_cache_hit_tokens maps onto cached_tokens. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L147) | `DeepSeekHandlerTests.test_normalize_usage_reasoning_from_details` | `None` | `None` | Nested completion_tokens_details.reasoning_tokens is flattened. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L162) | `DeepSeekHandlerTests.test_iter_stream_text_wraps_reasoning` | `None` | `None` | Streamed reasoning_content is wrapped in <think> when requested. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L176) | `DeepSeekHandlerTests.test_iter_stream_text_hides_reasoning_when_not_requested` | `None` | `None` | output_reasoning=False keeps the stream free of reasoning text. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L188) | `DeepSeekHandlerTests.test_iter_stream_text_ignores_alien_reasoning_aliases` | `None` | `None` | Streaming never treats reasoning/thinking deltas as DeepSeek CoT. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L199) | `DeepSeekHandlerTests.test_generic_openai_handler_keeps_alias_probing` | `None` | `None` | Regression guard: generic handler probes aliases; DeepSeek must not. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L222) | `DeepSeekThinkLeakTests._handler_with_fake_client` | `recorded: dict` | `DeepSeekHandler` | Implement `DeepSeekThinkLeakTests._handler_with_fake_client`. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L240) | `DeepSeekThinkLeakTests.test_create_completion_strips_think_blocks_outbound` | `None` | `None` | Assistant <think> wrappers from the context handler never reach DeepSeek. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L263) | `DeepSeekThinkLeakTests.test_openai_compatible_deepseek_strips_and_normalizes_think_blocks` | `None` | `None` | The compatibility route applies the same loop protection end-to-end. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L301) | `DeepSeekThinkLeakTests.test_create_completion_leaves_clean_messages_untouched` | `None` | `None` | Messages without think markers pass through byte-for-byte. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L314) | `DeepSeekThinkLeakTests.test_normalize_completion_response_extracts_think_leak` | `None` | `None` | A <think> block the model echoed inside content moves to reasoning. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L334) | `DeepSeekThinkLeakTests.test_normalize_completion_response_keeps_clean_content` | `None` | `None` | Content without think markers is returned unchanged. |
| [tests/test_execution_graph_persistence.py](tests/test_execution_graph_persistence.py#L14) | `_agent` | `prompt: str` | `Agent` | Build a tool-free Agent suitable for default persistence tests. |
| [tests/test_execution_graph_persistence.py](tests/test_execution_graph_persistence.py#L32) | `ExecutionGraphPersistenceTests.test_save_and_load_restores_agents_edges_and_callbacks` | `None` | `None` | Restore a graph with mapper/router callbacks through a registry. |
| [tests/test_execution_graph_persistence.py](tests/test_execution_graph_persistence.py#L61) | `ExecutionGraphPersistenceTests.test_callbacks_require_explicit_registry` | `None` | `None` | Reject implicit serialization of arbitrary executable callbacks. |
| [tests/test_execution_graph_persistence.py](tests/test_execution_graph_persistence.py#L69) | `ExecutionGraphPersistenceTests.test_declarative_dynamic_callbacks_restore_without_python_callback_registry` | `None` | `None` | Built-in mapper/router selections survive a restart as plain data. |
| [tests/test_public_api.py](tests/test_public_api.py#L12) | `PublicApiTests.test_package_exports_core_types` | `None` | `None` | Expose the primary orchestration classes from the package root. |
| [tests/test_public_api.py](tests/test_public_api.py#L17) | `PublicApiTests.test_execution_graph_prints_topology` | `None` | `None` | Render an empty graph with its configured concurrency limit. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L19) | `_TimeoutThenSuccessHandler.prepare_tools` | `_tools: object` | `None` | Return no provider tool schema for this retry-policy test. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L23) | `_TimeoutThenSuccessHandler.create_completion` | `**_: object` | `object` | Raise timeout errors until the configured successful attempt. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L30) | `_TimeoutThenSuccessHandler.normalize_completion_response` | `_raw: object` | `LLMOutput` | Return the stable success value after the final retry. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L40) | `_fetcher_for` | `handler: _TimeoutThenSuccessHandler, retries: int` | `LLMFetcher` | Build a no-SDK fetcher with one controllable retrying backend. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L57) | `RetryPolicyTests.test_retry_count_adds_attempts_and_uses_exponential_backoff` | `None` | `None` | Three configured retries permit a fourth successful model call. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L70) | `RetryPolicyTests.test_no_delay_is_scheduled_after_the_last_timeout` | `None` | `None` | Exhaustion reports the last error without sleeping pointlessly. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L83) | `RetryPolicyTests.test_default_backend_is_not_retried_again_as_its_own_fallback` | `None` | `None` | One backend receives exactly its configured initial-plus-retry budget. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L94) | `RetryPolicyTests.test_on_retry_callback_receives_attempt_index_before_backoff` | `None` | `None` | The retry observer is called once per scheduled retry with its index. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L106) | `RetryPolicyTests.test_on_retry_not_called_when_no_retry_occurs` | `None` | `None` | A clean first attempt never invokes the retry observer. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L117) | `RetryPolicyTests.test_on_retry_not_called_after_last_timeout_exhaustion` | `None` | `None` | Exhaustion reports the final error without a phantom retry callback. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L130) | `RetryPolicyTests.test_request_observer_receives_typed_dispatch_snapshot` | `None` | `None` | The preflight hook exposes a schema, not an untyped payload dict. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L28) | `_deepseek_handler` | `None` | `DeepSeekHandler` | Implement `_deepseek_handler`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L38) | `_openai_handler` | `None` | `OpenAIHandler` | Implement `_openai_handler`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L48) | `_anthropic_handler` | `None` | `AnthropicHandler` | Implement `_anthropic_handler`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L61) | `StreamUsageCaptureTests.test_openai_final_usage_chunk_is_captured` | `None` | `None` | A final usage-only chunk (empty choices) must not be discarded. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L89) | `StreamUsageCaptureTests.test_openai_usage_on_content_chunk_is_captured` | `None` | `None` | Some compatible endpoints attach usage to a normal choice chunk. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L105) | `StreamUsageCaptureTests.test_deepseek_stream_captures_cache_hit_tokens` | `None` | `None` | DeepSeek prompt-cache economics survive the streaming path. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L132) | `StreamUsageCaptureTests.test_anthropic_stream_merges_start_and_delta_usage` | `None` | `None` | Anthropic splits usage; both halves must be merged. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L158) | `LLMFetcherStreamUsageTests.test_fetch_stream_fills_usage_sink` | `None` | `None` | Implement `LLMFetcherStreamUsageTests.test_fetch_stream_fills_usage_sink`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L190) | `LLMFetcherStreamUsageTests.test_fetch_stream_no_usage_leaves_sink_untouched` | `None` | `None` | Implement `LLMFetcherStreamUsageTests.test_fetch_stream_no_usage_leaves_sink_untouched`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L212) | `_UsageStreamingFetcher.fetch_stream` | `usage_sink: TokenUsage \| None, **_kwargs: object` | `Any` | Implement `_UsageStreamingFetcher.fetch_stream`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L229) | `AgentStreamUsageTests.test_streamed_run_records_usage_in_ledger_event` | `None` | `None` | Implement `AgentStreamUsageTests.test_streamed_run_records_usage_in_ledger_event`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L258) | `AgentStreamUsageTests.test_streamed_run_round_usage_field_is_populated` | `None` | `None` | agent:round.round_usage reflects the real per-call usage. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L283) | `EndToEndStreamedAgentRunTests._stub_openai_fetcher` | `None` | `LLMFetcher` | Implement `EndToEndStreamedAgentRunTests._stub_openai_fetcher`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L312) | `EndToEndStreamedAgentRunTests.test_real_pipeline_publishes_ledger_usage_event` | `None` | `None` | Implement `EndToEndStreamedAgentRunTests.test_real_pipeline_publishes_ledger_usage_event`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L345) | `OpenAIHandlerWireTests.test_streaming_requests_include_usage` | `None` | `None` | Implement `OpenAIHandlerWireTests.test_streaming_requests_include_usage`. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L365) | `OpenAIHandlerWireTests.test_non_streaming_omits_include_usage` | `None` | `None` | Implement `OpenAIHandlerWireTests.test_non_streaming_omits_include_usage`. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L27) | `_CompletionFetcher.fetch` | `**kwargs: Any` | `LLMOutput` | Return a deterministic terminal tool call for one Agent round. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L61) | `_ReportingWorker.run` | `message: str, control: Any` | `str` | Record the task package and send a structured completion report. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L96) | `_CountingAgent.run` | `message: str, control: Any` | `str` | Count a graph submission and return the configured value. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L125) | `_ReportingCountingWorker.run` | `message: str, control: Any` | `str` | Submit task completion, then return the normal counting result. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L150) | `_WaitingCoordinator.run` | `message: str, control: Any` | `str` | Dispatch one worker and synthesize only its structured report. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L180) | `_DynamicChild.run` | `message: str, control: Any` | `str` | Return a deterministic value after receiving the graph input. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L205) | `_RouterCoordinator.run` | `message: str, control: Any` | `str` | Add a child after router configuration to exercise the regression. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L236) | `_RevivingCoordinator.run` | `message: str, control: Any` | `str` | Revive the terminal worker only while the second turn is running. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L261) | `TaskBusGraphTests.test_coordinator_receives_structured_report_not_worker_raw_output` | `None` | `None` | Run a task loop and verify the worker's raw text is not handed off. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L282) | `TaskBusGraphTests.test_router_does_not_skip_successor_added_after_router_setup` | `None` | `None` | Run a late successor that was outside the router's original scope. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L291) | `TaskBusGraphTests.test_next_graph_turn_retains_terminal_worker_without_resubmitting_it` | `None` | `None` | A retained Swarm reruns its coordinator but not old task workers. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L323) | `TaskBusGraphTests.test_terminal_worker_can_be_redispatched_with_a_new_task_identity` | `None` | `None` | Revival preserves the Agent but never mutates its old task record. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L353) | `TaskBusGraphTests.test_revive_mid_run_reschedules_terminal_worker` | `None` | `None` | A worker revived during a later turn must execute, not go zombie. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L386) | `TaskBusGraphTests.test_terminal_tool_stops_agent_before_another_model_round` | `None` | `None` | Stop the Agent after a terminal tool rather than using its full budget. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L407) | `TaskBusGraphTests.test_worker_tool_factory_builds_isolated_tools_for_both_spawn_paths` | `None` | `None` | Give each dynamically created worker its own name-bound tool set. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L455) | `TaskBusGraphTests.test_worker_tool_binder_receives_live_agents_for_both_spawn_paths` | `None` | `None` | Post-construction worker binding can safely capture live Agents. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L499) | `TaskBusGraphTests.test_revive_agent_tool_queues_a_new_assignment_for_terminal_worker` | `None` | `None` | The public revival tool keeps the worker while advancing task ID. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L536) | `TaskBusGraphTests.test_report_outcome_and_unfinished_cleanup_use_precise_terminals` | `None` | `None` | Preserve reports while interrupting running and cancelling queued work. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L579) | `TaskBusGraphTests.test_plan_task_correlation_survives_task_bus_snapshot` | `None` | `None` | Keep external plan-leaf correlation through durable Swarm recovery. |
| [tests/test_usage_ledger.py](tests/test_usage_ledger.py#L20) | `_Fetcher.fetch` | `**_kwargs: Any` | `Any` | Implement `_Fetcher.fetch`. |
| [tests/test_usage_ledger.py](tests/test_usage_ledger.py#L30) | `_AgentFetcher.fetch` | `**kwargs: Any` | `Any` | Implement `_AgentFetcher.fetch`. |
| [tests/test_usage_ledger.py](tests/test_usage_ledger.py#L44) | `UsageLedgerTests.test_compaction_record_is_drained_once` | `None` | `Any` | Implement `UsageLedgerTests.test_compaction_record_is_drained_once`. |
| [tests/test_usage_ledger.py](tests/test_usage_ledger.py#L57) | `UsageLedgerTests.test_graph_calls_have_distinct_kinds_and_preserve_dimensions` | `None` | `Any` | Implement `UsageLedgerTests.test_graph_calls_have_distinct_kinds_and_preserve_dimensions`. |
| [tests/test_usage_ledger.py](tests/test_usage_ledger.py#L79) | `UsageLedgerTests.test_agent_emits_primary_and_internal_usage_once` | `None` | `Any` | Implement `UsageLedgerTests.test_agent_emits_primary_and_internal_usage_once`. |
| [tool_executor.py](tool_executor.py#L54) | `ToolExecutor.execute` | `handler: Callable[..., Any], arguments: Dict[str, Any]` | `Any` | Run a single tool handler in the calling thread. |
| [tool_executor.py](tool_executor.py#L62) | `ToolExecutor.execute_timed` | `handler: Callable[..., Any], arguments: Dict[str, Any]` | `ToolExecution` | Run a single tool handler in the calling thread with timing. |
| [tool_executor.py](tool_executor.py#L93) | `ToolExecutor.execute_batch` | `handlers: List[Callable[..., Any] \| None], arguments_list: List[Dict[str, Any]]` | `List[Any]` | Execute tool handlers in parallel using a thread pool. |
| [tool_executor.py](tool_executor.py#L120) | `ToolExecutor.execute_batch_timed` | `handlers: List[Callable[..., Any] \| None], arguments_list: List[Dict[str, Any]]` | `List[ToolExecution]` | Execute tool handlers in parallel, measuring each one's duration. |
| [tool_executor.py](tool_executor.py#L193) | `ToolExecutor.close` | `None` | `None` | Release resources. (No-op — threads clean up on exit.) |
| [tool_handler.py](tool_handler.py#L23) | `ToolHandler.add_tool` | `tool: Tool` | `bool` | Register a tool. No-op if a tool with the same name exists. |
| [tool_handler.py](tool_handler.py#L35) | `ToolHandler.remove_tool` | `name: str` | `bool` | Unregister a tool by name. |
| [tool_handler.py](tool_handler.py#L50) | `ToolHandler.get` | `name: str` | `Tool \| None` | Look up a tool by name. |
| [tool_handler.py](tool_handler.py#L58) | `ToolHandler.get_handler` | `name: str` | `Any \| None` | Return the callable handler for a named tool. |
| [tool_handler.py](tool_handler.py#L67) | `ToolHandler.get_handlers_and_arguments` | `calls: List[LLMToolCall]` | `tuple[List[Any \| None], List[Dict[str, Any]]]` | Resolve a list of tool calls into (handlers, arguments). |
| [tool_handler.py](tool_handler.py#L94) | `ToolHandler.get_all_tool_description` | `None` | `str` | Concatenated ``__str__`` of all registered tools, newline-separated. |
| [tool_handler.py](tool_handler.py#L98) | `ToolHandler.get_all_tools` | `None` | `List[Tool]` | Return all registered tools as a list. |
| [tools/__init__.py](tools/__init__.py#L28) | `__getattr__` | `name: str` | `Any` | Resolve a lazily exported tool factory. |
| [tools/knowledge_tools.py](tools/knowledge_tools.py#L11) | `create_knowledge_tools` | `knowledge_base: KnowledgeBase \| None` | `list[Tool]` | Create tools for searching and reading the workspace knowledge base. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L23) | `_get_obscura_bin` | `None` | `str` | Resolve the configured Obscura executable. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L48) | `_unwrap_search_url` | `href: str` | `str` | Extract a destination URL from a DuckDuckGo redirect link. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L98) | `WebSearchStore._connect` | `None` | `sqlite3.Connection` | Open a short-lived WAL connection for a thread-safe operation. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L105) | `WebSearchStore._migrate` | `None` | `None` | Create settings and usage tables without disturbing Agent data. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L120) | `WebSearchStore.get_settings` | `None` | `dict[str, Any]` | Return saved search settings merged with safe defaults. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L127) | `WebSearchStore.update_settings` | `values: dict[str, Any]` | `dict[str, Any]` | Validate, persist, and return web-search settings. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L151) | `WebSearchStore.record` | `provider: str, ok: bool, result_count: int, duration_ms: int` | `None` | Add one provider attempt to today's durable usage aggregate. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L163) | `WebSearchStore.usage` | `days: int` | `list[dict[str, Any]]` | Return provider usage totals for the requested recent day window. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L175) | `configure_web_search_store` | `path: str \| Path, defaults: dict[str, Any] \| None` | `None` | Configure the process-wide persistent store used by new search tools. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L181) | `get_web_search_store` | `None` | `WebSearchStore` | Return the configured store, lazily defaulting to the local runtime DB. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L189) | `_search_duckduckgo` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search DuckDuckGo's HTML endpoint and normalize organic results. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L245) | `_curl_document` | `url: str, timeout: int, user_agent: str` | `tuple[Any \| None, str]` | Fetch one HTML document with bounded curl diagnostics. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L274) | `_search_baidu` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search Baidu's public HTML endpoint for domestic-first retrieval. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L298) | `_search_bing_html` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search Bing's public HTML endpoint without requiring an API key. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L322) | `_search_brave` | `query: str, max_results: int, timeout: int, api_key: str` | `dict[str, Any]` | Search Brave's JSON API using the configured subscription token. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L339) | `_search_bing` | `query: str, max_results: int, timeout: int, api_key: str` | `dict[str, Any]` | Search Bing Web Search API using the configured subscription key. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L356) | `_search_provider` | `provider: str, query: str, max_results: int, timeout: int, settings: dict[str, Any]` | `dict[str, Any]` | Dispatch one configured provider and return its normalized payload. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L375) | `_relevant_search_results` | `query: str, results: list[dict[str, Any]]` | `list[dict[str, Any]]` | Reject result pages with no lexical relationship to the query. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L402) | `_web_search` | `**kwargs: Any` | `dict[str, Any]` | Search domestic-first providers through curl with bounded fallback. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L443) | `_obscura_fetch_cli` | `**kwargs: Any` | `dict[str, Any]` | Execute obscura fetch via CLI. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L514) | `_obscura_scrape_cli` | `**kwargs: Any` | `dict[str, Any]` | Batch-scrape URLs with Obscura workers. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L596) | `create_obscura_tools` | `None` | `list[Tool]` | Create Agent-ready web search and browsing tools. |
| [tools/shell_tools.py](tools/shell_tools.py#L11) | `_kill_process_group` | `process: subprocess.Popen` | `None` | Terminate a shell command and descendants when possible. |
| [tools/shell_tools.py](tools/shell_tools.py#L22) | `create_shell_tools` | `allowed_commands: Optional[List[str]], max_timeout: float, sandbox_cwd: Optional[str], register_process: Optional[Callable[[subprocess.Popen], None]], unregister_process: Optional[Callable[[subprocess.Popen], None]], force_stop_event: Any` | `List[Tool]` | Create shell execution tool with security controls. |
| [tools/spawn_tools.py](tools/spawn_tools.py#L34) | `create_task_report_tool` | `swarm: AgentSwarm, reporter: str, on_report: Callable[[], None]` | `Tool` | Build the terminal report tool for one dispatched or restored worker. |
| [tools/spawn_tools.py](tools/spawn_tools.py#L92) | `create_swarm_tools` | `swarm: AgentSwarm, llm_fetcher: LLMFetcher, worker_tool_pool: list[Tool], worker_tool_factory: Callable[[str], list[Tool]] \| None, worker_tool_binder: Callable[[str, Agent, list[Tool]], list[Tool]] \| None, coordinator_name: str, worker_max_rounds: int, worker_max_tokens: int, worker_max_context_threshold: int, worker_enable_stop_turn: bool, worker_default_stream: bool, context_path_factory: Callable[[str], Any] \| None, require_plan_task_id: bool, plan_task_validator: Callable[[str], bool] \| None` | `list[Tool]` | Create tools that let a coordinator LLM manipulate the swarm at runtime. |
| [usage_ledger.py](usage_ledger.py#L24) | `copy_usage` | `usage: Optional[TokenUsage]` | `TokenUsage` | Copy provider usage, representing a missing provider report as zero. |
| [usage_ledger.py](usage_ledger.py#L37) | `add_usage` | `total: TokenUsage, usage: TokenUsage` | `None` | Add all dimensions without deriving total from its subdimensions. |
| [usage_ledger.py](usage_ledger.py#L46) | `drain_records` | `records: list[UsageRecord]` | `list[UsageRecord]` | Return and consume records in their completed-call order. |
| [web/static/app.js](web/static/app.js#L1) | `$` | `id: unknown` | `unknown` | Perform the browser runtime operation: $. |
| [web/static/app.js](web/static/app.js#L6) | `value` | `id: unknown` | `unknown` | Perform the browser runtime operation: value. |
| [web/static/app.js](web/static/app.js#L8) | `config` | `None` | `unknown` | Perform the browser runtime operation: config. |
| [web/static/app.js](web/static/app.js#L14) | `setStatus` | `text: unknown, state: unknown` | `unknown` | Perform the browser runtime operation: set status. |
| [web/static/app.js](web/static/app.js#L15) | `escapeHtml` | `text: unknown` | `unknown` | Perform the browser runtime operation: escape html. |
| [web/static/app.js](web/static/app.js#L16) | `removeWelcome` | `None` | `unknown` | Perform the browser runtime operation: remove welcome. |
| [web/static/app.js](web/static/app.js#L17) | `appendMessage` | `role: unknown, content: unknown, reasoning: unknown` | `unknown` | Perform the browser runtime operation: append message. |
| [web/static/app.js](web/static/app.js#L18) | `trace` | `title: unknown, message: unknown, data: unknown, kind: unknown` | `unknown` | Perform the browser runtime operation: trace. |
| [web/static/app.js](web/static/app.js#L19) | `metrics` | `data: unknown` | `unknown` | Perform the browser runtime operation: metrics. |
| [web/static/app.js](web/static/app.js#L20) | `setRunning` | `running: unknown` | `unknown` | Perform the browser runtime operation: set running. |
| [web/static/app.js](web/static/app.js#L21) | `loadWorkspaces` | `selected: unknown` | `Promise<unknown>` | Perform the browser runtime operation: load workspaces. |
| [web/static/app.js](web/static/app.js#L22) | `start` | `message: unknown` | `Promise<unknown>` | Perform the browser runtime operation: start. |
| [web/static/app.js](web/static/app.js#L32) | `handleEvent` | `event: unknown` | `unknown` | Perform the browser runtime operation: handle event. |
| [web/static/app.js](web/static/app.js#L39) | `finish` | `None` | `unknown` | Perform the browser runtime operation: finish. |
| [webapp.py](webapp.py#L76) | `BrowserRunControl.should_stop` | `None` | `bool` | Implement `BrowserRunControl.should_stop`. |
| [webapp.py](webapp.py#L79) | `BrowserRunControl.drain_steers` | `None` | `list[str]` | Implement `BrowserRunControl.drain_steers`. |
| [webapp.py](webapp.py#L87) | `BrowserRunControl.stop` | `None` | `None` | Implement `BrowserRunControl.stop`. |
| [webapp.py](webapp.py#L90) | `BrowserRunControl.steer` | `message: str` | `None` | Implement `BrowserRunControl.steer`. |
| [webapp.py](webapp.py#L115) | `_safe_id` | `value: str, label: str` | `str` | Validate IDs before using them in a local storage path. |
| [webapp.py](webapp.py#L122) | `_read_workspaces` | `None` | `list[dict[str, str]]` | Return the local workspace registry, repairing a missing registry. |
| [webapp.py](webapp.py#L137) | `_write_workspaces` | `workspaces: list[dict[str, str]]` | `None` | Atomically replace the small local workspace registry. |
| [webapp.py](webapp.py#L144) | `_workspace_exists` | `workspace_id: str` | `bool` | Return whether a workspace is registered locally. |
| [webapp.py](webapp.py#L149) | `_get_session` | `workspace_id: str, session_id: str` | `BrowserSession` | Get or create the in-memory holder for a validated browser session. |
| [webapp.py](webapp.py#L155) | `_event_payload` | `event: ExecutionEvent` | `dict[str, Any]` | Convert library events to JSON values suitable for Server-Sent Events. |
| [webapp.py](webapp.py#L167) | `_build_agent` | `config: RunConfig, workspace_id: str, session_id: str` | `Agent` | Create an Agent from current UI settings without persisting credentials. |
| [webapp.py](webapp.py#L197) | `index` | `None` | `FileResponse` | Serve the standalone chat console. |
| [webapp.py](webapp.py#L203) | `providers` | `None` | `dict[str, list[str]]` | Expose the providers currently registered by the library. |
| [webapp.py](webapp.py#L209) | `list_workspaces` | `None` | `dict[str, list[dict[str, str]]]` | List local workspaces available to the browser console. |
| [webapp.py](webapp.py#L215) | `create_workspace` | `request: WorkspaceRequest` | `dict[str, str]` | Create a local workspace with an isolated context directory. |
| [webapp.py](webapp.py#L231) | `start_run` | `request: RunRequest` | `dict[str, str]` | Start one synchronous Agent in a worker thread and return its run ID. |
| [webapp.py](webapp.py#L282) | `stream_events` | `workspace_id: str, session_id: str` | `StreamingResponse` | Stream queued lifecycle events as SSE until the active run completes. |
| [webapp.py](webapp.py#L301) | `stop_run` | `workspace_id: str, session_id: str` | `dict[str, bool]` | Request a stop at the next completed model-and-tool boundary. |
| [webapp.py](webapp.py#L311) | `steer_run` | `workspace_id: str, session_id: str, request: SteerRequest` | `dict[str, bool]` | Queue a steering message that Agent.run applies at a safe boundary. |
| [webapp.py](webapp.py#L320) | `main` | `None` | `None` | Run the local console with ``llmfetcher-web``. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [agent.py](agent.py#L21) | `AgentRunControl` | `None` | `Protocol` | Describe cooperative controls read between completed Agent steps. |
| [agent.py](agent.py#L38) | `AgentRunStopped` | `message: str, last_output: LLMOutput \| None` | `RuntimeError` | Signal a cooperative stop after durable completion of one Agent step. |
| [agent.py](agent.py#L56) | `AgentRunLimitReached` | `None` | `RuntimeError` | Signal that an Agent exhausted its round budget before a terminal result. |
| [agent.py](agent.py#L64) | `ContextLoadError` | `None` | `RuntimeError` | Signal that an existing Agent checkpoint could not be restored. |
| [agent.py](agent.py#L68) | `ContextSaveError` | `None` | `RuntimeError` | Signal that a configured Agent checkpoint could not be committed. |
| [agent.py](agent.py#L72) | `AgentRunTermination` | `None` | `str, Enum` | Explicit terminal classifications for one completed Agent invocation. |
| [agent.py](agent.py#L84) | `AgentRunOutcome` | `termination: AgentRunTermination, rounds: int, detail: str, output: LLMOutput \| None` | `object` | Inspectable terminal state for an Agent run. |
| [agent.py](agent.py#L128) | `Agent` | `llm_fetcher: LLMFetcher, system_prompt: str, max_concurrency: int, max_context_threshold: int, context_path: Optional[str \| Path], context_handler: Optional[ContextHandler], default_max_rounds: int, default_max_tokens: int, enable_stop_turn: bool, default_stream: bool` | `object` | Provide `Agent` behavior. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L27) | `ArchiveRetrievalConfig` | `max_results: int, max_chars_per_record: int, min_score: float` | `object` | Hard bounds for local archive retrieval and returned evidence. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L44) | `ArchiveEvidence` | `timeline_start: int, timeline_end: int, role: str, score: float, text: str, matched_terms: tuple[str, ...]` | `object` | A bounded, display-safe projection of one archived context record. |
| [context_handlers/archive_retrieval.py](context_handlers/archive_retrieval.py#L62) | `ArchiveRetrievalResult` | `query: str, evidence: tuple[ArchiveEvidence, ...], scanned_records: int` | `object` | Result metadata plus bounded evidence suitable for later injection. |
| [context_handlers/base.py](context_handlers/base.py#L8) | `ContextHandler` | `None` | `ABC` | Manages conversational context and builds API-ready message lists. |
| [context_handlers/linear.py](context_handlers/linear.py#L23) | `CompactionFetcher` | `None` | `Protocol` | Describe the minimal LLM interface used for context compaction. |
| [context_handlers/linear.py](context_handlers/linear.py#L90) | `ContextHandlerLinear` | `compacting_llmfetcher_handler: CompactionFetcher, max_context_threshold: int, compaction_input_char_limit: int, compaction_output_max_tokens: int, event_hook: Optional[Callable[[str, str, dict], None]]` | `ContextHandler` | A simple context handler that stores messages in a flat list. |
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
| [graph_memory/handler.py](graph_memory/handler.py#L41) | `GraphContextHandler` | `compacting_fetcher: CompactionFetcher, extraction_fetcher: Optional[ExtractionFetcher], query_fetcher: Optional[ExtractionFetcher], store: Optional[GraphStore], retriever_config: Optional[RetrievalConfig], retrieval_trigger: str, graph_update_every: int, max_context_threshold: int, graph_save_suffix: str` | `ContextHandler` | A context handler with an entity-relation long-term memory graph. |
| [graph_memory/models.py](graph_memory/models.py#L15) | `EntityNode` | `id: str, name: str, entity_type: str, aliases: list[str], summary: str, first_seen: int, last_seen: int, freq: int, embedding: Optional[list[float]]` | `object` | A single entity in the memory graph. |
| [graph_memory/models.py](graph_memory/models.py#L61) | `RelationEdge` | `source_id: str, target_id: str, relation: str, weight: float, first_seen: int, last_seen: int, valid: bool, evidence: list[int]` | `object` | A relation between two entities with temporal attributes. |
| [graph_memory/models.py](graph_memory/models.py#L109) | `CommunitySummary` | `level: int, community_id: str, summary: str, member_entity_ids: list[str], source_timelines: list[int]` | `object` | Summary of one community (cluster) of the memory graph. |
| [graph_memory/models.py](graph_memory/models.py#L137) | `GraphHit` | `entity: EntityNode, score: float, matched_relation: Optional[str], neighbor_ids: list[str]` | `object` | One retrieval hit: an entity plus its fused score. |
| [graph_memory/models.py](graph_memory/models.py#L155) | `GraphMemoryState` | `version: int, nodes: dict[str, EntityNode], edges: list[RelationEdge], communities: dict[int, list[CommunitySummary]], next_id: int` | `object` | Serialization container for the whole memory graph. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L135) | `RetrievalConfig` | `w_vec: float, w_ppr: float, w_kw: float, w_time: float, top_k: int, max_relations: int, max_communities: int, hop: int, time_decay_lambda: float, min_fused_score: float, include_neighbors: bool, include_communities: bool` | `object` | Weights and limits for the four-channel fusion retrieval. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L176) | `GraphRetrievalResult` | `query: str, seed_entities: list[EntityNode], hits: list[GraphHit], expanded_entities: dict[str, EntityNode], relations: list[RelationEdge], community_summaries: list[CommunitySummary], rendered: str, current_timeline: int` | `object` | Output of :meth:`GraphRetriever.retrieve`. |
| [graph_memory/retriever.py](graph_memory/retriever.py#L329) | `GraphRetriever` | `store: GraphStore, query_fetcher: Optional[ExtractionFetcher], config: Optional[RetrievalConfig], query_prompt: str` | `object` | Four-channel hybrid retrieval over a :class:`GraphStore`. |
| [graph_memory/semantic.py](graph_memory/semantic.py#L19) | `SemanticGraphWorker` | `fetcher: Any, backend_name: Optional[str]` | `object` | A no-history, no-tools adapter for graph semantic work. |
| [llm_fetcher.py](llm_fetcher.py#L52) | `StreamUsageCapture` | `None` | `object` | Per-call mutable capture of raw provider usage from one stream. |
| [llm_fetcher.py](llm_fetcher.py#L102) | `LLMFetcher` | `backends: Optional[Sequence[LLMBackendConfig]], default_backend: Optional[str]` | `object` | Route chat requests across one or more configured LLM backends. |
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
| [tests/test_agent_prompt.py](tests/test_agent_prompt.py#L18) | `_RecordingFetcher` | `None` | `object` | Minimal fetcher that exposes the Agent's preflight request boundary. |
| [tests/test_agent_prompt.py](tests/test_agent_prompt.py#L45) | `AgentPromptTests` | `None` | `unittest.TestCase` | Verify that native tool schemas are not duplicated into system text. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L12) | `_SequenceFetcher` | `outputs: list[LLMOutput]` | `object` | Return predetermined model outputs while recording native tool delivery. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L29) | `_StreamingFetcher` | `None` | `object` | Yield fixed provider chunks for Agent stream assembly coverage. |
| [tests/test_agent_termination.py](tests/test_agent_termination.py#L54) | `AgentTerminationTests` | `None` | `unittest.TestCase` | Verify formal answers, control tools, empty responses, and budgets differ. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L23) | `_RecordingCompactor` | `None` | `object` | Fake fetcher that records a compaction request without an LLM call. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L75) | `ContextCompactionTests` | `None` | `unittest.TestCase` | Verify oversized tool output cannot inflate a compaction request. |
| [tests/test_context_compaction.py](tests/test_context_compaction.py#L457) | `CompactionLifecycleEventTests` | `None` | `unittest.TestCase` | Verify compaction lifecycle events reach an optional observer. |
| [tests/test_context_persistence_errors.py](tests/test_context_persistence_errors.py#L16) | `_Fetcher` | `None` | `object` | Return one final answer while recording remote invocations. |
| [tests/test_context_persistence_errors.py](tests/test_context_persistence_errors.py#L33) | `_FailingSaveHandler` | `None` | `ContextHandlerLinear` | Context handler whose durable commit always fails. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L27) | `DeepSeekHandlerTests` | `None` | `unittest.TestCase` | Platform specialisation: reasoning field, cache accounting, dispatch. |
| [tests/test_deepseek_handler.py](tests/test_deepseek_handler.py#L219) | `DeepSeekThinkLeakTests` | `None` | `unittest.TestCase` | <think> feedback-loop control: outbound strip + inbound extraction. |
| [tests/test_execution_graph_persistence.py](tests/test_execution_graph_persistence.py#L29) | `ExecutionGraphPersistenceTests` | `None` | `unittest.TestCase` | Verify graph topology and callback identity survive a disk round trip. |
| [tests/test_public_api.py](tests/test_public_api.py#L9) | `PublicApiTests` | `None` | `unittest.TestCase` | Verify imports and graph diagnostics without contacting an LLM API. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L12) | `_TimeoutThenSuccessHandler` | `timeouts: int` | `object` | Fail a configured number of calls before returning a model output. |
| [tests/test_retry_policy.py](tests/test_retry_policy.py#L54) | `RetryPolicyTests` | `None` | `unittest.TestCase` | Verify retry count means additional timeout attempts, not total calls. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L58) | `StreamUsageCaptureTests` | `None` | `unittest.TestCase` | Handler-level capture of usage carried on streamed chunks. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L155) | `LLMFetcherStreamUsageTests` | `None` | `unittest.TestCase` | The fetch_stream glue normalizes captured usage into a sink. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L207) | `_UsageStreamingFetcher` | `None` | `object` | Yield normalized chunks and fill the usage sink like real fetchers. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L226) | `AgentStreamUsageTests` | `None` | `unittest.TestCase` | A streamed Agent round must publish real token usage. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L274) | `EndToEndStreamedAgentRunTests` | `None` | `unittest.TestCase` | Real handler + real fetcher through Agent.run, with a stubbed wire. |
| [tests/test_stream_usage.py](tests/test_stream_usage.py#L342) | `OpenAIHandlerWireTests` | `None` | `unittest.TestCase` | create_completion requests include_usage only for streamed calls. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L15) | `_CompletionFetcher` | `None` | `object` | Return a terminal-tool request and record how often the Agent fetches. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L47) | `_ReportingWorker` | `graph: ExecutionGraph, task_id: str` | `object` | Minimal worker that reports its assigned task through the graph bus. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L84) | `_CountingAgent` | `result: str` | `object` | Lightweight graph member that records executions across graph turns. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L111) | `_ReportingCountingWorker` | `graph: ExecutionGraph, agent_name: str` | `_CountingAgent` | Counting dispatched worker that records one terminal TaskBus report. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L137) | `_WaitingCoordinator` | `graph: ExecutionGraph` | `object` | Minimal coordinator that dispatches one worker then waits for its report. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L177) | `_DynamicChild` | `None` | `object` | Minimal dynamic successor used to validate router-scope behavior. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L194) | `_RouterCoordinator` | `graph: ExecutionGraph` | `object` | Creates a successor after setting an initially empty router scope. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L222) | `_RevivingCoordinator` | `graph: ExecutionGraph, worker_name: str` | `object` | Revives a terminal worker mid-run on its second graph turn. |
| [tests/test_task_bus.py](tests/test_task_bus.py#L258) | `TaskBusGraphTests` | `None` | `unittest.TestCase` | Verify report-only feedback loops and dynamic-router compatibility. |
| [tests/test_usage_ledger.py](tests/test_usage_ledger.py#L15) | `_Fetcher` | `content: str, usage: TokenUsage` | `object` | Provide `_Fetcher` behavior. |
| [tests/test_usage_ledger.py](tests/test_usage_ledger.py#L27) | `_AgentFetcher` | `None` | `_Fetcher` | Provide `_AgentFetcher` behavior. |
| [tests/test_usage_ledger.py](tests/test_usage_ledger.py#L43) | `UsageLedgerTests` | `None` | `unittest.TestCase` | Provide `UsageLedgerTests` behavior. |
| [tool_executor.py](tool_executor.py#L13) | `ToolExecution` | `result: Any, duration_ms: int` | `object` | One tool handler execution: its result and wall-clock duration. |
| [tool_executor.py](tool_executor.py#L26) | `ToolExecutor` | `max_concurrency: int` | `object` | Execute tool handlers in parallel using a thread pool. |
| [tool_handler.py](tool_handler.py#L8) | `ToolHandler` | `None` | `object` | Register, look up, and describe ``Tool`` objects. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L75) | `WebSearchStore` | `path: str \| Path, defaults: dict[str, Any] \| None` | `object` | Persist web-search settings and per-provider usage counters in SQLite. |
| [tools/obscura_tools.py](tools/obscura_tools.py#L572) | `ObscuraCDPClient` | `host: str, port: int` | `object` | Placeholder configuration for a future Obscura CDP client. |
| [usage_ledger.py](usage_ledger.py#L17) | `UsageRecord` | `kind: str, usage: TokenUsage` | `object` | Usage reported by one completed LLM call. |
| [webapp.py](webapp.py#L34) | `RunConfig` | `provider: str, model: str, api_key: str, api_url: str, system_prompt: str, temperature: float, max_tokens: int, max_rounds: int, enable_shell: bool` | `BaseModel` | Settings used to create the backend and Agent for a browser session. |
| [webapp.py](webapp.py#L48) | `RunRequest` | `session_id: str, workspace_id: str, message: str, config: RunConfig` | `BaseModel` | A message and its non-persisted browser-side configuration. |
| [webapp.py](webapp.py#L57) | `SteerRequest` | `message: str` | `BaseModel` | One instruction added at the next safe agent boundary. |
| [webapp.py](webapp.py#L63) | `WorkspaceRequest` | `name: str` | `BaseModel` | A user-visible workspace name, stored only on the local machine. |
| [webapp.py](webapp.py#L69) | `BrowserRunControl` | `None` | `AgentRunControl` | Thread-safe implementation of llmfetcher's cooperative run controls. |
| [webapp.py](webapp.py#L95) | `ActiveRun` | `control: BrowserRunControl, events: queue.Queue[dict[str, Any]], done: threading.Event` | `object` | Live work and its event queue, owned by one browser session. |
| [webapp.py](webapp.py#L104) | `BrowserSession` | `lock: threading.Lock, active: ActiveRun \| None` | `object` | In-memory state that prevents concurrent runs in the same chat. |

<!-- END GENERATED SYMBOL MAP -->
