# llmfetcher/ — Submodule INDEX

Git submodule containing the synchronous Python framework Angelus builds on.
It provides provider-neutral LLM dispatch, tool-using agents, durable context
handlers, graph/archive memory, and dependency-driven multi-agent execution.

> This file describes the checked-out submodule. Run submodule commands from
> the superproject only when deliberately updating its recorded revision.

This is the root of a per-directory INDEX tree: the generated symbol map below
covers only the top-level `*.py` modules owned by this file. Each source-owning
subdirectory has its own `INDEX.md`, and traversal stops at that boundary.

## Route Map

| Intent | Next index | Current authority |
|---|---|---|
| Provider adapters (OpenAI, Anthropic, LiteLLM, OpenVINO, ONNX) | [`fetcher_handlers/INDEX.md`](fetcher_handlers/INDEX.md) | Backend handler normalization |
| Durable linear/retrieved/TLB/archive context | [`context_handlers/INDEX.md`](context_handlers/INDEX.md) | Session transcript persistence |
| Graph long-term memory | [`graph_memory/INDEX.md`](graph_memory/INDEX.md) | Entity/relation store and retrieval |
| Provider-neutral memory contracts | [`memory/INDEX.md`](memory/INDEX.md) | Long-term memory protocol |
| Legacy/local knowledge-base RAG | [`rag_module/INDEX.md`](rag_module/INDEX.md) | ChromaDB vector knowledge base |
| Auditable `INDEX.md` tree traversal | [`rag_module_tlb/INDEX.md`](rag_module_tlb/INDEX.md) | TLB RAG traversal |
| Multi-agent swarm scheduling | [`swarm_module/INDEX.md`](swarm_module/INDEX.md) | Execution graph and TaskBus |
| Per-attempt stop/cancellation control | [`execution/INDEX.md`](execution/INDEX.md) | `ExecutionController` |
| Built-in tool factories | [`tools/INDEX.md`](tools/INDEX.md) | Shell/knowledge/web/spawn tools |
| Submodule regression tests | [`tests/INDEX.md`](tests/INDEX.md) | Local verification |
| Example entry point | [`demo/INDEX.md`](demo/INDEX.md) | Non-packaged demo |
| Packaged-import check | [`scripts/INDEX.md`](scripts/INDEX.md) | Wheel import CI |
| Design notes | [`docs/INDEX.md`](docs/INDEX.md) | Reference only |

## Package Map

| Area | Paths | Current responsibility |
|---|---|---|
| Public API | `__init__.py`, `llm_types.py` | Public imports, request/response, tool, context, token-usage, and terminal request-cancellation types. `ToolSchema` supports both compact first-party parameters and lossless external JSON Schema (for example MCP). |
| Agent loop | `agent.py`, `events.py`, `usage_ledger.py` | Synchronous model/tool loop; the system message contains only system instructions while registered tools travel once through provider-native schemas. Optional provider streaming emits incremental content/reasoning events but reconstructs the same final output for tools and durable context. Explicit `AgentRunOutcome` terminal states distinguish formal answers, reserved `stop_turn`, workflow completion, user stop, invalid empty responses, and exhausted tool-loop budgets. |
| LLM dispatch | `llm_fetcher.py`, [`fetcher_handlers/`](fetcher_handlers/INDEX.md) | Backend selection, typed/causal timeout classification and bounded retry/fallback, terminal request cancellation, credential-free preflight request observation, and OpenAI-compatible, DeepSeek, Anthropic, LiteLLM, OpenVINO, and ONNX Runtime adapters. |
| Execution control | [`execution/`](execution/INDEX.md) | Per-attempt `ExecutionController`, unified graceful/forced stop requests, resource canceller registration, stream interruption and queued steering messages. |
| Context | [`context_handlers/`](context_handlers/INDEX.md) | Base contract; durable linear history with compaction and raw archive; provider-backed retrieval composition; TLB adapter. `context_less_context/` is an experimental local worktree directory, not part of the indexed API. |
| Graph memory | [`graph_memory/`](graph_memory/INDEX.md) | Persistent entity/relation store, incremental extraction, hybrid graph retrieval, archive evidence, and stateless semantic extraction/reranking workers. |
| Swarm | [`swarm_module/`](swarm_module/INDEX.md) | Dependency graph, concurrent scheduler, TaskBus, bounded report handoff, and quiescent graph save/load. Assignments may carry an opaque external plan-leaf correlation ID that is preserved through events and snapshots. Repeated `run()` calls retain graph vertices; terminal dispatched tasks remain inspectable but are not implicitly rescheduled, and may be revived with a new immutable assignment. |
| Tools | `tool_handler.py`, `tool_executor.py`, [`tools/`](tools/INDEX.md) | Tool schemas/registry, parallel execution, and built-in shell, knowledge, web, and dynamic-spawn factories; `create_swarm_tools` accepts a shared worker pool, a name-bound factory, an optional live-Agent binder, and optional external-plan leaf validation for worker-local handlers needing persistence/reload callbacks. |
| Retrieval modules | [`rag_module/`](rag_module/INDEX.md), [`rag_module_tlb/`](rag_module_tlb/INDEX.md) | Legacy/knowledge-base RAG and auditable `INDEX.md` tree traversal. |
| Interfaces | `cli.py`, [`demo/`](demo/INDEX.md) | Local CLI and example entry point. Browser control-plane ownership belongs to Angelus. |
| Verification | [`tests/`](tests/INDEX.md) | Unit and regression coverage for public API, context, DeepSeek routing, execution graph, TaskBus, and usage ledger. |

## Angelus Integration Points

| Component | Import / path | Why Angelus uses it |
|---|---|---|
| Fetching | `LLMFetcher`, `LLMBackendConfig`, `LLMRequestCancelled` | Configures primary/fallback backend calls; only normalized timeout failures retry, streamed calls stop retrying after their first delta, and `abort_active_requests()` is terminal. |
| Agent execution | `Agent`, `AgentRunControl` | Runs a session, forwards cooperative stop/steer controls to both ordinary and streaming provider calls, observes an optional `force_stopped` event during provider I/O, checkpoints completed context, then emits `agent:context_checkpoint` for the host's safe graph-generation commit. |
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
| [agent.py](agent.py#L31) | `_supports_force_control` | `control: object` | `bool` | Return whether one cooperative control can cancel provider resources. |
| [agent.py](agent.py#L59) | `AgentRunControl.should_stop` | `None` | `bool` | Return whether the Agent should stop at the current safe boundary. |
| [agent.py](agent.py#L63) | `AgentRunControl.drain_steers` | `None` | `list[str]` | Return and consume queued user steering messages in FIFO order. |
| [agent.py](agent.py#L132) | `AgentRunOutcome.to_dict` | `None` | `dict[str, Any]` | Return the credential-free terminal fields for lifecycle events. |
| [agent.py](agent.py#L142) | `_tool_result_text` | `value: Any` | `str` | Return the complete tool-result string supplied back to the model. |
| [agent.py](agent.py#L279) | `Agent.add_hook` | `hook: ExecutionHook` | `None` | Register an execution-event receiver. |
| [agent.py](agent.py#L290) | `Agent.remove_hook` | `hook: ExecutionHook` | `bool` | Unregister one execution-event receiver. |
| [agent.py](agent.py#L305) | `Agent.request_completion` | `None` | `None` | Request completion after the active model-and-tool step finishes. |
| [agent.py](agent.py#L318) | `Agent.request_turn_stop` | `reason: str` | `None` | Request a normal boundary from the reserved ``stop_turn`` tool. |
| [agent.py](agent.py#L333) | `Agent.add_stop_turn_tool` | `None` | `bool` | Register the reserved model-visible control tool for ending a turn. |
| [agent.py](agent.py#L342) | `Agent._create_stop_turn_tool` | `None` | `Tool` | Create the reserved model-visible control tool for ending a turn. |
| [agent.py](agent.py#L370) | `Agent._set_outcome` | `termination: AgentRunTermination, rounds: int, detail: str, output: LLMOutput \| None` | `AgentRunOutcome` | Record and publish the single explicit terminal result of this run. |
| [agent.py](agent.py#L397) | `Agent.set_context_threshold` | `max_context_threshold: int, persist: bool` | `bool` | Update the compaction threshold used by this Agent's context. |
| [agent.py](agent.py#L437) | `Agent._emit` | `source: str, agent_name: str, event_type: str, message: str, data: Any` | `None` | Send one event to each registered hook, isolating hook failures. |
| [agent.py](agent.py#L471) | `Agent._compaction_event_hook` | `event_type: str, message: str, data: dict` | `None` | Publish a context-handler compaction lifecycle event. |
| [agent.py](agent.py#L495) | `Agent._usage_data` | `usage: TokenUsage` | `dict[str, int]` | Serialize every normalized usage dimension for durable events. |
| [agent.py](agent.py#L505) | `Agent._drain_internal_usage` | `name: str` | `None` | Publish and aggregate each hidden LLM call once, if supported. |
| [agent.py](agent.py#L523) | `Agent.add_tool` | `tool: Tool` | `bool` | Register one callable tool on this Agent. |
| [agent.py](agent.py#L534) | `Agent.add_tools` | `tools: List[Tool]` | `bool` | Register a batch of tools in the supplied order. |
| [agent.py](agent.py#L554) | `Agent._build_prompt` | `None` | `str` | Return the system prompt without serializing registered tools into it. |
| [agent.py](agent.py#L568) | `Agent._save_context` | `None` | `bool` | Persist the current context when this Agent has a storage path. |
| [agent.py](agent.py#L599) | `Agent._fetch_model_with_force_stop` | `control: AgentRunControl \| None, **fetch_kwargs: Any` | `LLMOutput` | Fetch one model response, allowing a terminal browser force-stop. |
| [agent.py](agent.py#L631) | `Agent._stream_model_response` | `name: str, round_idx: int, control: AgentRunControl \| None, **fetch_kwargs: Any` | `LLMOutput` | Stream one provider response, emit deltas, and rebuild its final form. |
| [agent.py](agent.py#L743) | `Agent.run` | `message: str, max_rounds: int \| None, temperature: float, max_tokens: int \| None, verbose: bool, control: AgentRunControl \| None, stream: bool \| None` | `LLMOutput` | Run the Agent until one explicit terminal outcome is reached. |
| [agent.py](agent.py#L1233) | `Agent.close` | `None` | `None` | Release sub-interpreter resources held by the tool executor. |
| [agent.py](agent.py#L1237) | `Agent.clear_context` | `None` | `None` | Clear context. |
| [cli.py](cli.py#L58) | `_load_tools` | `names: list[str]` | `list[Tool]` | Import and call tool factories by short name. |
| [cli.py](cli.py#L94) | `_build_parser` | `None` | `argparse.ArgumentParser` | Implement `_build_parser`. |
| [cli.py](cli.py#L178) | `_cmd_list_backends` | `None` | `None` | Print every registered backend provider. |
| [cli.py](cli.py#L189) | `_cmd_list_tools` | `None` | `None` | Print every known tool-set name + description. |
| [cli.py](cli.py#L202) | `_build_backend_config` | `args: argparse.Namespace` | `LLMBackendConfig` | Construct a single ``LLMBackendConfig`` from parsed args. |
| [cli.py](cli.py#L229) | `_bootstrap_agent` | `args: argparse.Namespace` | `Agent` | Create an ``Agent`` wired with the CLI config and requested tools. |
| [cli.py](cli.py#L260) | `_cmd_run` | `args: argparse.Namespace` | `None` | Execute a single prompt and print the final response. |
| [cli.py](cli.py#L287) | `_cmd_chat` | `args: argparse.Namespace` | `None` | Interactive read-eval-print loop. |
| [cli.py](cli.py#L318) | `main` | `argv: list[str] \| None` | `None` | Parse CLI arguments and dispatch the selected command. |
| [llm_fetcher.py](llm_fetcher.py#L73) | `StreamUsageCapture.merge` | `raw_usage: Any` | `None` | Merge one raw usage payload (dict or provider object). |
| [llm_fetcher.py](llm_fetcher.py#L98) | `StreamUsageCapture.raw` | `None` | `dict[str, Any] \| None` | Return the merged raw usage mapping, or ``None`` when absent. |
| [llm_fetcher.py](llm_fetcher.py#L123) | `LLMFetcher.list_available_backend_providers` | `None` | `tuple[str, ...]` | Return all provider names supported by registered handlers, sorted. |
| [llm_fetcher.py](llm_fetcher.py#L185) | `LLMFetcher.backend_configs` | `None` | `Dict[str, LLMBackendConfig]` | Return a copy of all registered backend configurations. |
| [llm_fetcher.py](llm_fetcher.py#L195) | `LLMFetcher.fallback_order` | `None` | `List[str]` | Return the current fallback order (shallow copy). |
| [llm_fetcher.py](llm_fetcher.py#L205) | `LLMFetcher.default_backend_config` | `None` | `LLMBackendConfig` | Return the configuration of the default backend. |
| [llm_fetcher.py](llm_fetcher.py#L215) | `LLMFetcher._register_backend` | `backend: LLMBackendConfig` | `None` | Register a single backend and pre-create its handler. |
| [llm_fetcher.py](llm_fetcher.py#L235) | `LLMFetcher._resolve_backends` | `backend_name: Optional[str], fallback_order: Optional[Sequence[str]]` | `List[LLMBackendConfig]` | Resolve the ordered backend list for a single request. |
| [llm_fetcher.py](llm_fetcher.py#L281) | `LLMFetcher._handler_for_backend` | `backend: LLMBackendConfig` | `LLMBackendHandler` | Return the handler instance for a given backend configuration. |
| [llm_fetcher.py](llm_fetcher.py#L297) | `LLMFetcher._is_timeout_exception` | `exc: Exception` | `bool` | Recognise transport/provider timeouts without importing optional SDKs. |
| [llm_fetcher.py](llm_fetcher.py#L330) | `LLMFetcher._normalize_exception` | `backend: LLMBackendConfig, exc: Exception` | `LLMError` | Normalise any exception into an ``LLMError`` subclass. |
| [llm_fetcher.py](llm_fetcher.py#L355) | `LLMFetcher._sleep_before_retry` | `retry_index: int, controller: ExecutionController \| None` | `None` | Wait with cancellation-aware exponential backoff before retrying. |
| [llm_fetcher.py](llm_fetcher.py#L380) | `LLMFetcher._raise_if_force_stopped` | `controller: ExecutionController \| None` | `None` | Raise the terminal cancellation error without retrying providers. |
| [llm_fetcher.py](llm_fetcher.py#L394) | `LLMFetcher.abort_active_requests` | `None` | `int` | Close provider transports for this terminal force-stop. |
| [llm_fetcher.py](llm_fetcher.py#L418) | `LLMFetcher.prepare_request` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Optional[Sequence[ToolDefinition]], stream: bool` | `RemoteRequestSnapshot` | Build the first dispatch-ready request without provider I/O. |
| [llm_fetcher.py](llm_fetcher.py#L458) | `LLMFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Optional[Sequence[ToolDefinition]], on_request: Optional[Callable[[RemoteRequestSnapshot], None]], on_retry: Optional[Callable[[int], None]], controller: ExecutionController \| None` | `LLMOutput` | Execute a non-streaming completion with backend fallback and retry. |
| [llm_fetcher.py](llm_fetcher.py#L585) | `LLMFetcher.fetch_stream` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, output_reasoning: bool, context_handler: Optional[ContextHandler], backend_name: Optional[str], tools: Optional[Sequence[ToolDefinition]], on_request: Optional[Callable[[RemoteRequestSnapshot], None]], on_retry: Optional[Callable[[int], None]], usage_sink: Optional[TokenUsage], controller: ExecutionController \| None` | `Generator[str, None]` | Execute a streaming completion with backend fallback and retry. |
| [llm_fetcher.py](llm_fetcher.py#L733) | `LLMFetcher._prepare_backend_request` | `backend: LLMBackendConfig, messages: List[JsonObject], temperature: float, max_tokens: int, tools: Optional[Sequence[ToolDefinition]], stream: bool` | `tuple[LLMBackendHandler, RemoteRequestSnapshot]` | Prepare one backend's tool schemas and safe request snapshot. |
| [llm_fetcher.py](llm_fetcher.py#L778) | `LLMFetcher._max_attempts` | `backend: LLMBackendConfig` | `int` | Return the number of times to attempt a request for a backend. |
| [llm_fetcher.py](llm_fetcher.py#L793) | `LLMFetcher._build_messages` | `msg: str, system_prompt: Optional[str], context: Optional[ContextHandler]` | `List[Dict[str, Any]]` | Build the message list, delegating to a context handler when available. |
| [llm_types.py](llm_types.py#L43) | `RemoteRequestSnapshot.to_dict` | `None` | `JsonObject` | Return the JSON-safe event payload used by application hosts. |
| [llm_types.py](llm_types.py#L106) | `LLMBackendConfig.__str__` | `None` | `str` | Render the backend config in a compact human-readable form. |
| [llm_types.py](llm_types.py#L162) | `TokenUsage.cache_hit_rate` | `None` | `float` | Fraction of input tokens served from the provider's prompt cache. |
| [llm_types.py](llm_types.py#L186) | `LLMOutput.text` | `None` | `str` | Alias for assistant text content. |
| [llm_types.py](llm_types.py#L190) | `LLMOutput.__str__` | `None` | `str` | Return the assistant content for debug printing and logging. |
| [llm_types.py](llm_types.py#L225) | `LLMContextCompacted.__str__` | `None` | `str` | Implement `LLMContextCompacted.__str__`. |
| [llm_types.py](llm_types.py#L261) | `ToolSchema.to_dict` | `None` | `Dict[str, Any]` | Convert this schema to an isolated JSON-ready mapping. |
| [llm_types.py](llm_types.py#L301) | `Tool.__str__` | `None` | `Any` | Implement `Tool.__str__`. |
| [multimodal.py](multimodal.py#L15) | `bounded_resolver` | `resolver: Any` | `Any` | Enforce a per-request decoded-size budget before any network call. |
| [multimodal.py](multimodal.py#L32) | `validate_images` | `images: list[ImageReference]` | `list[ImageReference]` | Copy references and reject inline bytes and transport-specific fields. |
| [multimodal.py](multimodal.py#L53) | `UserMessage.__post_init__` | `None` | `Any` | Implement `UserMessage.__post_init__`. |
| [multimodal.py](multimodal.py#L56) | `UserMessage.__str__` | `None` | `Any` | Implement `UserMessage.__str__`. |
| [multimodal.py](multimodal.py#L65) | `image_reference_markers` | `images: Any` | `list[str]` | Render bounded, byte-free provenance markers for image references. |
| [multimodal.py](multimodal.py#L85) | `image_blocks` | `images: Any, resolver: Any, provider: Any` | `Any` | Resolve local references at the wire boundary, never for previews. |
| [multimodal.py](multimodal.py#L109) | `openai_image_messages` | `messages: Any, resolver: Any` | `Any` | Place tool images after all tool replies, preserving protocol ordering. |
| [tool_executor.py](tool_executor.py#L59) | `ToolExecutor.execute` | `handler: Callable[..., Any], arguments: Dict[str, Any]` | `Any` | Run a single tool handler in the calling thread. |
| [tool_executor.py](tool_executor.py#L67) | `ToolExecutor.execute_timed` | `handler: Callable[..., Any], arguments: Dict[str, Any]` | `ToolExecution` | Run a single tool handler in the calling thread with timing. |
| [tool_executor.py](tool_executor.py#L98) | `ToolExecutor.execute_batch` | `handlers: List[Callable[..., Any] \| None], arguments_list: List[Dict[str, Any]], controller: ExecutionController \| None` | `List[Any]` | Execute tool handlers in parallel using a thread pool. |
| [tool_executor.py](tool_executor.py#L130) | `ToolExecutor.execute_batch_timed` | `handlers: List[Callable[..., Any] \| None], arguments_list: List[Dict[str, Any]], controller: ExecutionController \| None` | `List[ToolExecution]` | Execute tool handlers in parallel, measuring each one's duration. |
| [tool_executor.py](tool_executor.py#L226) | `ToolExecutor.close` | `None` | `None` | Release resources. (No-op — threads clean up on exit.) |
| [tool_handler.py](tool_handler.py#L27) | `ToolHandler.add_tool` | `tool: Tool` | `bool` | Register a tool. No-op if a tool with the same name exists. |
| [tool_handler.py](tool_handler.py#L39) | `ToolHandler.remove_tool` | `name: str` | `bool` | Unregister a tool by name. |
| [tool_handler.py](tool_handler.py#L54) | `ToolHandler.get` | `name: str` | `Tool \| None` | Look up a tool by name. |
| [tool_handler.py](tool_handler.py#L62) | `ToolHandler.get_handler` | `name: str` | `Any \| None` | Return the callable handler for a named tool. |
| [tool_handler.py](tool_handler.py#L71) | `ToolHandler.get_handlers_and_arguments` | `calls: List[LLMToolCall]` | `tuple[List[Any \| None], List[Dict[str, Any]]]` | Resolve a list of tool calls into (handlers, arguments). |
| [tool_handler.py](tool_handler.py#L99) | `ToolHandler.get_all_tool_description` | `None` | `str` | Concatenated ``__str__`` of all registered tools, newline-separated. |
| [tool_handler.py](tool_handler.py#L103) | `ToolHandler.get_all_tools` | `None` | `List[Tool]` | Return all registered tools as a list. |
| [tool_handler.py](tool_handler.py#L108) | `_reject_tool_call` | `message: str` | `Any` | Return a handler that reports one validation failure to the model. |
| [tool_handler.py](tool_handler.py#L115) | `_validate_tool_call` | `tool: Tool \| None, call: LLMToolCall` | `str \| None` | Validate one model call before a local handler can observe it. |
| [tool_handler.py](tool_handler.py#L159) | `_matches_json_type` | `value: Any, expected: str` | `bool` | Return whether a JSON-compatible value matches one primitive type. |
| [usage_ledger.py](usage_ledger.py#L24) | `copy_usage` | `usage: Optional[TokenUsage]` | `TokenUsage` | Copy provider usage, representing a missing provider report as zero. |
| [usage_ledger.py](usage_ledger.py#L37) | `add_usage` | `total: TokenUsage, usage: TokenUsage` | `None` | Add all dimensions without deriving total from its subdimensions. |
| [usage_ledger.py](usage_ledger.py#L46) | `drain_records` | `records: list[UsageRecord]` | `list[UsageRecord]` | Return and consume records in their completed-call order. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [agent.py](agent.py#L51) | `AgentRunControl` | `None` | `Protocol` | Describe cooperative controls read between completed Agent steps. |
| [agent.py](agent.py#L68) | `AgentRunStopped` | `message: str, last_output: LLMOutput \| None` | `RuntimeError` | Signal a cooperative stop after durable completion of one Agent step. |
| [agent.py](agent.py#L86) | `AgentRunLimitReached` | `None` | `RuntimeError` | Signal that an Agent exhausted its round budget before a terminal result. |
| [agent.py](agent.py#L94) | `ContextLoadError` | `None` | `RuntimeError` | Signal that an existing Agent checkpoint could not be restored. |
| [agent.py](agent.py#L98) | `ContextSaveError` | `None` | `RuntimeError` | Signal that a configured Agent checkpoint could not be committed. |
| [agent.py](agent.py#L102) | `AgentRunTermination` | `None` | `str, Enum` | Explicit terminal classifications for one completed Agent invocation. |
| [agent.py](agent.py#L114) | `AgentRunOutcome` | `termination: AgentRunTermination, rounds: int, detail: str, output: LLMOutput \| None` | `object` | Inspectable terminal state for an Agent run. |
| [agent.py](agent.py#L158) | `Agent` | `llm_fetcher: LLMFetcher, system_prompt: str, max_concurrency: int, max_context_threshold: int, context_path: Optional[str \| Path], context_handler: Optional[ContextHandler], default_max_rounds: int, default_max_tokens: int, enable_stop_turn: bool, default_stream: bool, output_reasoning: bool, tool_result_transformer: Callable[[str, str, str], str] \| None` | `object` | Provide `Agent` behavior. |
| [events.py](events.py#L16) | `ExecutionEvent` | `timestamp: float, source: str, agent_name: str, event_type: str, message: str, data: Any` | `object` | Immutable event emitted during swarm execution. |
| [llm_fetcher.py](llm_fetcher.py#L53) | `StreamUsageCapture` | `None` | `object` | Per-call mutable capture of raw provider usage from one stream. |
| [llm_fetcher.py](llm_fetcher.py#L103) | `LLMFetcher` | `backends: Optional[Sequence[LLMBackendConfig]], default_backend: Optional[str], image_resolver: Any` | `object` | Route chat requests across one or more configured LLM backends. |
| [llm_types.py](llm_types.py#L18) | `RemoteRequestSnapshot` | `model: str, messages: list[JsonObject], temperature: float, max_tokens: int, stream: bool, tools: list[JsonObject]` | `object` | Credential-free schema for one dispatch-ready remote model request. |
| [llm_types.py](llm_types.py#L65) | `LLMError` | `None` | `Exception` | Base exception for all LLM-related errors. |
| [llm_types.py](llm_types.py#L69) | `LLMTimeoutError` | `None` | `LLMError` | Raised when an LLM request times out. |
| [llm_types.py](llm_types.py#L73) | `LLMBackendError` | `None` | `LLMError` | Raised when all candidate backends fail. |
| [llm_types.py](llm_types.py#L77) | `LLMRequestCancelled` | `None` | `LLMError` | Raised when a terminal force-stop cancels an in-flight LLM request. |
| [llm_types.py](llm_types.py#L86) | `LLMBackendConfig` | `name: str, provider: str, model: str, api_key: str, api_url: Optional[str], timeout: float, max_retries: int, compatibility_profile: Optional[str], extra: Dict[str, Any]` | `object` | Configuration for one routable LLM backend. |
| [llm_types.py](llm_types.py#L124) | `LLMToolCall` | `name: str, arguments: JsonObject, call_id: Optional[str], source: Optional[str]` | `object` | Backend-neutral tool call emitted by a model. |
| [llm_types.py](llm_types.py#L134) | `ToolInfo` | `call: LLMToolCall, result: Optional[str], images: list[ImageReference]` | `object` | A tool call paired with its execution result. |
| [llm_types.py](llm_types.py#L148) | `TokenUsage` | `input_tokens: int, output_tokens: int, total_tokens: int, cached_tokens: int, reasoning_tokens: int` | `object` | Platform-irrelevant token usage summary produced by every LLM handler. |
| [llm_types.py](llm_types.py#L169) | `LLMOutput` | `content: str, provider: str, backend_name: str, model: str, role: str, reasoning_content: str, tool_calls: List[LLMToolCall], stop_reason: Optional[str], usage: TokenUsage` | `object` | Backend-neutral non-streaming model output. this class will be created by handlers that handle the LLM call. |
| [llm_types.py](llm_types.py#L197) | `LLMContext` | `role: str, timeline: int, content: str, content_reasoning: str, tool_calls: List[ToolInfo], tags: List[str], usage: Dict[str, int], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float], images: list[ImageReference]` | `object` | A single message in the conversation timeline. |
| [llm_types.py](llm_types.py#L217) | `LLMContextCompacted` | `abstract_msg: str, source_timeline: List[int], source_uuid: List[str], tags: List[str]` | `object` | Summarised representation of one or more LLMContext entries. |
| [llm_types.py](llm_types.py#L234) | `ToolParameter` | `name: str, type: str, description: str, required: bool, enum: Optional[List[str]], default: Optional[Any]` | `object` | A single parameter in a tool's JSON Schema. |
| [llm_types.py](llm_types.py#L246) | `ToolSchema` | `type: str, properties: List[ToolParameter], raw_schema: Optional[Dict[str, Any]]` | `object` | Structured JSON Schema for tool parameters and external tool protocols. |
| [llm_types.py](llm_types.py#L293) | `Tool` | `name: str, description: str, schemas: ToolSchema, handler: Callable[..., Any]` | `object` | A single tool that an Agent can call. |
| [llm_types.py](llm_types.py#L309) | `ToolBatch` | `None` | `object` | Provide `ToolBatch` behavior. |
| [multimodal.py](multimodal.py#L6) | `ImageReference` | `attachment_id: str, media_type: str, detail: NotRequired[Literal['auto', 'low', 'high']]` | `TypedDict` | Provide `ImageReference` behavior. |
| [multimodal.py](multimodal.py#L49) | `UserMessage` | `text: str, images: list[ImageReference]` | `object` | Provide `UserMessage` behavior. |
| [multimodal.py](multimodal.py#L61) | `ImageToolResult` | `None` | `UserMessage` | Tool feedback containing native image inputs and explanatory text. |
| [tool_executor.py](tool_executor.py#L13) | `ToolBatchCancelled` | `None` | `RuntimeError` | Signal that force-stop abandoned the active tool batch. |
| [tool_executor.py](tool_executor.py#L18) | `ToolExecution` | `result: Any, duration_ms: int` | `object` | One tool handler execution: its result and wall-clock duration. |
| [tool_executor.py](tool_executor.py#L31) | `ToolExecutor` | `max_concurrency: int` | `object` | Execute tool handlers in parallel using a thread pool. |
| [tool_handler.py](tool_handler.py#L8) | `ToolCallValidationError` | `None` | `ValueError` | A model-requested tool call does not match a registered Tool contract. |
| [tool_handler.py](tool_handler.py#L12) | `ToolHandler` | `None` | `object` | Register, look up, and describe ``Tool`` objects. |
| [usage_ledger.py](usage_ledger.py#L17) | `UsageRecord` | `kind: str, usage: TokenUsage` | `object` | Usage reported by one completed LLM call. |

<!-- END GENERATED SYMBOL MAP -->
