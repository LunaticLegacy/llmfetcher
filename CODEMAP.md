# Code Semantic Map

## Architecture

- **What the system does**:  
  A framework for orchestrating multi-agent LLM interactions. Agents can use tools, share a reasoning graph (ThinkingGraph), and execute tasks on a DAG-based execution engine (ExecutionGraph) within a swarm container (AgentSwarm). The system includes background task management (RuntimeSlot), LLM backend routing with fallback (LLMFetcher), file I/O for agent workspace management (AgentFileIOManager), and a flexible tool system (Tool/ToolRegistry). The system is designed to be async-first and concurrency-aware, with support for streaming, timeouts, and stop signals.

- **Main execution path**:  
  1. User creates an `LLMFetcher` with backend configuration(s).  
  2. Optionally creates an `Agent` (standalone) or an `AgentSwarm`.  
  3. For `AgentSwarm`, builds a graph topology by adding input, output, agent, router, tool, join nodes and connecting them.  
  4. Calls `swarm.run(initial_input)` which delegates to `ExecutionGraph.run()`.  
  5. `ExecutionGraph` executes the DAG: starts from entry node, fans out downstream nodes as upstreams complete, respecting concurrency limits, route labels, timeouts, and stop requests.  
  6. Each `AgentNode` calls its `Agent.round_call()` to interact with LLM, possibly executing tools.  
  7. `ToolNode` wraps a `Tool` and executes it.  
  8. `RouterNode` uses an agent to select a route or falls back to default.  
  9. `OutputNode` collects final results via a callable.  
  10. Returns `GraphContext` with all node outputs.  
  For standalone `Agent`, `agent.round_call()` runs the multi-turn loop directly.

- **Major components and dependencies**:
  - `pack`: Package root; re-exports all public symbols.
  - `pack.agent.Agent`: Multi-turn tool-use agent with context management.
  - `pack.swarm.swarm.AgentSwarm`: Top-level orchestration container; owns ExecutionGraph, ThinkingGraph, ToolRegistry, LLMFetcher.
  - `pack.swarm.execution_graph.ExecutionGraph`: DAG execution engine; runs nodes concurrently with semaphore-limit.
  - `pack.thinking_graph.ThinkingGraph`: Persistent reasoning graph; shared cognitive state (nodes/edges) with validation and transaction log.
  - `pack.swarm.runtime_slot.RuntimeSlotManager`: Background task execution service (submit/poll/collect/stop).
  - `pack.llm_fetcher.LLMFetcher`: Unified LLM backend router with fallback, retry, streaming, reasoning extraction.
  - `pack.llm_context.LLMContextHandler`: Context storage, compression, memory generation for agents.
  - `pack.tool.Tool` / `ToolRegistry`: Base tool abstraction and registry.
  - `pack.agent_io.AgentFileIOManager`: Filesystem inspection for agent packages (manifests, specs, runtime files).
  - Tool factories: `create_builtin_tools`, `create_execution_graph_tools`, `create_obscura_tools`, `create_runtime_slot_tools`, `create_shell_tools`, `create_thinking_graph_tools`.

- **Scale and design philosophy**:  
  Designed for multi-agent coordination with shared memory (thinking graph) and controllable concurrency. Emphasizes async I/O, graceful degradation (fallback backends, tool error conversion), and explicit lifecycle management (stop signals, timeouts). The architecture is modular – each component has a well-defined API and is testable in isolation.

## Modules

| Module | Role & Responsibilities | Collaborators |
|--------|------------------------|---------------|
| `pack/__init__.py` | Package root; re-exports all public types/classes/functions from submodules. | All submodules |
| `pack/agent.py` | Defines `Agent` class: multi-turn LLM + tool use with context, streaming, parallel tool execution, fallback summary. | LLMFetcher, LLMContextHandler, ToolRegistry, builtin_tools |
| `pack/agent_io.py` | Defines `AgentFileIOManager` and data classes for reading agent packages from disk (manifest, specs, runtime files). | (none) – pure filesystem |
| `pack/llm_context.py` | Defines `LLMContextHandler` and context dataclasses for storing/compressing/memory-summarizing conversation history. | LLMFetcher |
| `pack/llm_fetcher.py` | Defines `LLMFetcher`: unified LLM backend router with OpenAI/LiteLLM providers, timeout retries, fallback order, streaming with reasoning extraction. | openai, litellm (optional) |
| `pack/swarm/__init__.py` | Subpackage init; re-exports from execution_graph, runtime_slot, swarm. | (re-exports) |
| `pack/swarm/execution_graph.py` | Defines `ExecutionGraph` DAG engine, node types (AgentNode, ToolNode, RouterNode, InputNode, OutputNode, JoinNode), GraphContext. | Agent, Tool |
| `pack/swarm/runtime_slot.py` | Defines `RuntimeSlotManager`, `RuntimeSlot`, `SlotStatus`; background task lifecycle management with ThinkingGraph integration. | ThinkingGraph, Tool |
| `pack/swarm/swarm.py` | Defines `AgentSwarm` and `SwarmSpec`; top-level orchestration container; fluent builder API for graph/tool/agent management; save/load/checkpoint. | ExecutionGraph, ThinkingGraph, Agent, ToolRegistry, LLMFetcher |
| `pack/thinking_graph.py` | Defines `ThinkingGraph`, node/edge types, transaction log, schema validation, serialization/deserialization. Shared reasoning memory. | (none) – self-contained |
| `pack/tool.py` | Defines `Tool` dataclass and `ToolRegistry`; base tool abstraction with sync/async handler support and OpenAI schema generation. | (none) |
| `pack/tools/__init__.py` | Subpackage init; doc-only; empty `__all__`. | (none) |
| `pack/tools/builtin_tools.py` | Factory `create_builtin_tools` returns `round_end` tool (no-op signal). | Tool |
| `pack/tools/execution_graph_tools.py` | Factory `create_execution_graph_tools(graph)` returns 10 tools for graph manipulation (add/remove nodes/edges, manage agents/tools, get info). | ExecutionGraph, Agent, Tool |
| `pack/tools/obscura_tools.py` | Factory `create_obscura_tools` returns `web_fetch` and `web_scrape` tools wrapping an external `obscura` CLI binary. (Blocking async, shell‑command injection risk, hardcoded path.) | subprocess, Tool |
| `pack/tools/runtime_slot_tools.py` | Factory `create_runtime_slot_tools(manager)` returns 5 tools: poll, list, collect, cancel (hard stop), soft_stop. Contains a hidden `_slot_submit` closure (not exposed). | RuntimeSlotManager, SlotStatus, Tool |
| `pack/tools/shell_tools.py` | Factory `create_shell_tools` returns `shell` tool for arbitrary shell commands with basic destructive‑command filter. | asyncio.subprocess, Tool |
| `pack/tools/thinking_graph_tools.py` | Factory `create_thinking_graph_tools(graph)` returns 7 tools: add_node, add_edge, validate_context, get_node_info, get_usage, get_schema, get_full_graph. | ThinkingGraph, Tool |
| `pack/tests/test_agent_io.py` | Pytest tests for `AgentFileIOManager` (happy-path reads of agent snapshot and ID listing). Uses hardcoded import path `modules.llm_fetcher.agent_io` – **mismatch** with actual path `pack.agent_io`. | pytest, AgentFileIOManager |
| `pack/tests/test_llmdemo.py` | Empty placeholder (1 byte). No tests. | (none) |
| `demo.py` | Minimal demo: creates a single-agent `AgentSwarm` with linear input → agent → output graph, runs a fixed query. | LLMFetcher, AgentSwarm |
| `demo_agent_and_swarm.py` | Full demo: demonstrates standalone `Agent` with tool (greet) and concurrent tool execution, and an `AgentSwarm` with a router node and two agents. Checks endpoint availability. | LLMFetcher, Agent, Tool, AgentSwarm |

## Types

### `pack/agent.py`

- `MessageDict = Dict[str, str]` – single message with `role` and `content`.
- `Messages = List[MessageDict]` – conversation history.
- `ToolArgs = Dict[str, object]` – keyword arguments to a tool.
- `AssistantMessageDict = Dict[str, object]` – assistant message with `role` and `content`.
- `ToolList = List[Tool]`
- `OptionalToolList = Optional[List[Tool]]`

### `pack/llm_context.py`

- `LLMContext(role: str, content: str, tool_call_id: Optional[str] = None)` – one chat message. Method `to_dict()` returns dict with `role`, `content` and optionally `tool_call_id`.
- `LLMContextPair(context_in: LLMContext, context_out: LLMContext)` – user→assistant pair. Method `to_dict()` returns `{"context_in": ..., "context_out": ...}` (returns objects, not dicts).
- `LLMContextCompressed(abstract_msg: str, source: List[LLMContextPair])` – compressed summary with source pairs. Method `to_dict()` returns dict.
- `LLMInfo = Union[LLMContextPair, LLMContextCompressed]`

### `pack/llm_fetcher.py`

- `LLMContext(role: str, content: str)` – dataclass for one message.
- `LLMBackendConfig(name: str, provider: str, model: str, api_key: str, api_url: Optional[str] = None, timeout: float = 60.0, max_retries: int = 0, extra: Dict[str, Any] = {})` – single backend configuration.
- `LLMError(RuntimeError)` – base exception.
- `LLMTimeoutError(LLMError, TimeoutError)` – timeout exception.
- `LLMBackendError(LLMError)` – all backends failed.

### `pack/thinking_graph.py`

- `ThinkingNodeType(str, Enum)` – 16 node type values (e.g., ACTION, OBSERVATION, ERROR, GOAL, …).
- `ThinkingEdgeType(str, Enum)` – 11 edge type values (e.g., PRODUCES, BLOCKS, INPUT_OF, …).
- `ThinkingGraphObject(id: int, created_by: str, description: str)` – base dataclass.
- `ThinkingGraphNode(node_type: ThinkingNodeType, info: str, tags: List[str], confidence: float, payload: Dict[str, Any])` extends `ThinkingGraphObject`.
- `ThinkingGraphEdge(edge_type: ThinkingEdgeType, source_id: int, target_id: int, strength: float)` extends `ThinkingGraphObject`.
- `ThinkingGraphTransactionRecord(transaction_id: int, operation: str, object_kind: str, object_id: int, before: Optional[Dict], after: Optional[Dict], version_before: int, version_after: int, created_by: str, timestamp: str, metadata: Optional[Dict])`.
- `ALLOWED_EDGE_SCHEMA: Dict[ThinkingEdgeType, Set[Tuple[ThinkingNodeType, ThinkingNodeType]]]` – module-level global defining allowed (source_type, target_type) per edge type. Validated at `ThinkingGraph.__init__`.

### `pack/swarm/execution_graph.py`

- `Edge(source_id: str, target_id: str, label: Optional[str] = None)` – directed connection, optional label for routing.
- `ExecutionStopState(soft_requested: bool = False, hard_requested: bool = False, reason: Optional[str] = None)` – mutable stop signal.
- `GraphContext` – execution context: `node_inputs: Dict[str, List]`, `node_outputs: Dict[str, Any]`, `executed: Set[str]`, `metadata: Dict[str, Any]`, `graph: 'ExecutionGraph'`. Methods: `get_output(node_id)`, `get_inputs(node_id)`.
- `ExecutionNode` – ABC with `node_id`, `node_type`, abstract `run(ctx, inputs) -> Any`.
- `AgentNode(agent: Agent)` – wraps Agent; `run` formats inputs and calls `agent.round_call`.
- `ToolNode(tool: Tool)` – wraps Tool; `run` constructs kwargs and calls `tool.execute`.
- `RouterNode(routes: Dict[str, str], agent: Optional[Agent], default_route: Optional[str])` – uses agent to select route or falls back to default. Output dict `{"route": ..., "raw": ..., "input": ...}`.
- `InputNode` – passthrough; returns `inputs[0]` or `None`.
- `OutputNode(collector)` – calls `collector(inputs)` (default identity). `collector` receives list.
- `JoinNode(strategy: str)` – merges inputs; `"first"` returns `{"result": first, "inputs": [...]}`; `"all"` returns `{"results": [...], "count": N}`.
- `ExecutionGraph` – main container; holds nodes, edges, tool_pool, semaphore, stop state, timeouts, active tasks, version counter, `_lock` (asyncio.Lock, not awaited in current code). Methods for node/edge CRUD, run, version/stop control.

### `pack/swarm/runtime_slot.py`

- `SlotStatus(Enum)` – `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `TIMEOUT`, `CANCELLED`.
- `RuntimeSlot(slot_id, name, task_coro, status, result, error, timeout, stop_requested, created_at, started_at, completed_at, last_polled_at, poll_count, metadata, action_node_id, result_node_id)` – dataclass for a background task. Method `to_dict()` returns snapshot with result truncated to 500 chars.
- `RuntimeSlotManager` – class managing slots; constructor accepts optional `ThinkingGraph`, `default_timeout=300.0`, `max_concurrent=4`. Methods: `submit`, `poll`, `list_slots`, `collect`, `request_soft_stop`, `request_hard_stop`, `to_dict`, `__repr__`. Internal `_run_slot` handles lifecycle, semaphore, timeout, stop detection, thinking graph recording.

### `pack/tool.py`

- `Tool(name: str, description: str, parameters: Dict[str, Any], handler: Callable[..., Any])` – dataclass. Method `execute(**kwargs)` – async: if handler is coroutine, await it; else run in executor. `parameters` expected to be JSON Schema.
- `ToolRegistry` – class with `_tools: Dict[str, Tool]`. Methods: `register(tool) -> Tool` (raises ValueError on duplicate), `unregister(name) -> Tool` (raises KeyError), `get(name) -> Tool` (raises KeyError), `async execute(name, arguments) -> Any`, `schemas` property (list of OpenAI function defs), `get_prompt_hint() -> str` (instruction for LLM to use JSON tool calls).

### `pack/agent_io.py`

- `AgentWorkspacePolicy` (frozen dataclass) – `mode: str`, `root: Path`, `raw_root: str`. Resolved workspace policy.
- `AgentFileLocations` (frozen dataclass) – resolved paths for source and runtime files of an agent (agent_file, prompting_file, skill_files, state_path, context_path, memory_path, log_path).
- `AgentFileSnapshot` (mutable dataclass) – full snapshot: `agent_id`, `agent_spec`, `prompt_text`, `state`, `context`, `memory`, `log_tail`, `workspace`, `package_name`, `package_root`, `locations`. Represents one agent's loaded data.

### `pack/swarm/swarm.py`

- `SwarmSpec(name: str = "", description: str = "", version: str = "0.1.0", metadata: Dict[str, Any] = {})` – dataclass for swarm metadata.

## Functions

### `pack/agent.py`

#### `Agent` class

- **`__init__(self, llm_handler: LLMFetcher, system_prompt: str, tools: OptionalToolList = None, max_concurrent_tools: int = 1, fallback_order: Optional[List[str]] = None)`**
  - **Inputs**: LLMFetcher, system prompt, optional tools, max concurrent tool calls (default 1), fallback order for LLM backends.
  - **Side effects**: Registers builtin tools via `create_builtin_tools()`. Sets attributes including misspelled `llm_context_hanlder` (duplicate of `llm_context_handler`).
  - **Failure modes**: If tools list contains non-Tool objects, `register` may raise ValueError.
- **`async round_call(self, msg: str, stream: bool = False, verbose_info: bool = False, max_turns: int = 3) -> str`**
  - **Purpose**: Process a user message through up to `max_turns` LLM+tool cycles, then always run fallback summary.
  - **Inputs**: Message, stream flag (prints chunks if True), verbose flag (prints debug info), max turns.
  - **Outputs**: Final assistant response string.
  - **Side effects**: Calls LLM fetcher, executes tools (sequentially or in parallel via `asyncio.gather`), prints to stdout if verbose/stream, saves context pair via `llm_context_hanlder.add_context()`.
  - **Preconditions**: LLM fetcher returns `ChatCompletion`-like object with `choices[0].message.content`.
  - **Failure modes**: Exceptions from LLM fetch propagate; tool exceptions caught and returned as `"Error: ..."` string; if `max_concurrent_tools > 1`, exceptions from `asyncio.gather(return_exceptions=True)` are converted to error strings; `round_end` tool acts as break signal.
- **`_parse_json_tool_calls(content: str) -> List[Dict[str, Any]]`**: Strips code fences, parses JSON; expects `{"tool_calls": [...]}` or single tool dict or list; falls back to fragment extraction. Returns empty list on failure.
- **`_is_valid_tool_call(payload: Any) -> bool`**: Checks payload is dict with `tool` (str) and `arguments` (dict).
- **`_extract_json_fragment(text: str) -> Optional[Any]`**: Scans for first `{` or `[` and attempts `json.JSONDecoder.raw_decode`. Returns None if none found.
- **`_build_round_messages(msg: str) -> Messages`**: Builds message list: system, history from context, user. Skips system if prompt empty.
- **`_format_assistant_message(content: str) -> AssistantMessageDict`**: Returns `{"role": "assistant", "content": content}`.
- **`_format_tool_result_message(tool_name, result) -> str`**: JSON string `{"type": "tool_result", "tool": ..., "result": ...}`.
- **`_execute_single_tool(tool_call, verbose) -> str`**: Executes tool via registry; returns `"Round ended."` for `"round_end"`; catches all exceptions and returns `"Error: {exc}"`.
- **`_strip_code_fence(text: str) -> str`**: Strips outermost triple backticks if present.
- **Property `system_prompt`**: Returns base prompt with optional tool hint from registry.
- **`update_system_prompt(new_prompt) -> None`**: Sets `_base_system_prompt`.
- **`add_tool(tool) -> None`**: Registers tool in registry.
- **`remove_tool(tool_name) -> None`**: Unregisters from registry.

### `pack/llm_fetcher.py`

#### `LLMFetcher` class

- **`__init__(self, api_url=None, api_key=None, model=None, *, provider="openai", timeout=60.0, backends=None, default_backend=None, limiter=None)`**
  - **Purpose**: Initialize fetcher with legacy parameters or a list of `LLMBackendConfig`.
  - **Side effects**: Registers backends; creates OpenAI clients for `"openai"` providers.
  - **Failure modes**: ValueError if no valid combination; if openai package missing; if backend name duplicates.
- **`async fetch(self, msg, system_prompt=None, temperature=0.4, max_tokens=4096, prev_messages=None, backend_name=None, fallback_order=None, tools=None)`**
  - **Purpose**: Non-streaming LLM call with retry on timeout and fallback across backends.
  - **Output**: Raw ChatCompletion object.
  - **Side effects**: Acquires/releases rate limiter if present; uses `asyncio.to_thread` for blocking SDK calls.
  - **Failure modes**: `LLMBackendError` if all backends fail.
- **`async fetch_stream(self, msg, ..., tools=None) -> AsyncGenerator[str, None]`**
  - **Purpose**: Streaming LLM call; yields normalized text chunks, optionally including reasoning delimiters (`<<<THINKING>>>` / `<<<THINK_END>>>`).
  - **Side effects**: Same as fetch. Once any text is yielded, no fallback on failure.
- **`_build_messages(self, msg, prev_messages, system_prompt) -> List[Dict[str,str]]`**: Constructs messages with system, history, user. Skips items with empty role.
- **`_create_completion(self, backend, *, messages, temperature, max_tokens, stream, tools=None)`**: Makes SDK call; supports OpenAI and LiteLLM.
- **`_normalize_exception(self, backend, exc) -> LLMError`**: Returns `LLMTimeoutError` if timeout-related, else `LLMError`.
- **`_timeout_retry_count(self, backend) -> int`**: Returns `max(1, int(backend.max_retries))` – **note bug**: for max_retries=0, returns 1, leading to 2 total attempts (initial + 1 retry).
- **`_extract_content(self, delta) -> Optional[str]`**: Extracts `content` from stream delta (dict or object). Returns None if absent.
- **`_extract_reasoning(self, delta) -> Optional[str]`**: Extracts `reasoning_content` or `reasoning` from stream delta.
- **`_iter_stream_text(self, response, *, output_reasoning)`**: Generator that yields text chunks from streaming response, adding thinking delimiters when reasoning appears. Handles both dict and object representations.

### `pack/llm_context.py`

#### `LLMContextHandler` class

- **`__init__(self, llm_handler: LLMFetcher, fallback_order=None)`**: Stores fetcher, initializes empty context dict and counter.
- **`async add_context(self, context_pair: LLMContextPair) -> None`**: Adds pair to dict at current ID, increments ID.
- **`async get_now_context(self) -> List[Dict[str,str]]`**: Returns chronologically ordered message dicts (user, assistant) for each pair; compressed entries contribute one assistant message.
- **`async get_now_context_as_single_str(self) -> str`**: Formats context as `[User]: ...\n[Assistant]: ...`.
- **`async compress_context(self, id_list: Optional[List[int]] = None) -> bool`**
  - **Purpose**: Compress entire context into one `LLMContextCompressed` entry. **Bug**: `id_list` parameter is ignored.
  - **Side effects**: Replaces `context_dict` with a single compressed entry at key 0, resets ID to 1.
  - **Failure modes**: Returns False if context empty.
- **`async get_context_by_id(self, id_list: List[int]) -> List[LLMInfo]`**: Returns entries for given IDs; missing IDs silently skipped.
- **`async generate_memory(self, id_list: List[int]) -> Optional[str]`**
  - **Purpose**: Generate memory summary. **Bug**: `id_list` parameter ignored; always uses full context.
  - **Output**: LLM-generated summary string, or None if context empty.
- **`to_dict` methods on context classes**: `LLMContext.to_dict()` returns flat dict; `LLMContextPair.to_dict()` returns dict with objects (not recursively serialized) – potential serialization inconsistency.

### `pack/thinking_graph.py`

#### `ThinkingGraph` class

- **`__init__(self)`**: Calls `validate_edge_schema()`; initializes empty dicts, zero version/transaction IDs, empty log, asyncio lock.
- **`serialize(self) -> Dict[str, Any]`**: Returns JSON-safe dict with format `"thinking-graph/config"`, schema version `"1.0"`, nodes/edges, transaction log, counts.
- **`to_dict(self)`**: Alias for `serialize`.
- **`from_dict(cls, data)`**: Classmethod; restores graph from dict. Handles missing/zero metadata gracefully. Raises TypeError/ValueError on malformed data.
- **`deserialize(cls, data)`**: Alias for `from_dict`.
- **`async get_full_graph(self)`**: Locked read of full graph dict.
- **`validate_edge_schema()`** (static): Validates `ALLOWED_EDGE_SCHEMA` global; raises ValueError/TypeError if inconsistent. Called once in `__init__`.
- **`add_node`** (partially visible; signature inferred): Adds a ThinkingGraphNode; returns node ID. Expected to increment version and log transaction.
- **`_alloc_id(self) -> int`**: Returns monotonically increasing ID.
- **`version` property**: Returns `_version`.
- **`transaction_log` property**: Returns shallow copy of log.
- **`clear_transaction_log(self) -> None`**: Empties log.
- **`get_transaction_log(self) -> List[ThinkingGraphTransactionRecord]`**: Same as property.
- **`_snapshot_object(obj)`** (static): Converts dataclass/dict to serializable snapshot; returns `None` if None.
- **`_next_transaction_id(self) -> int`**: Returns current transaction ID and increments.
- **`_record_transaction(self, ...)`**: Creates and appends a `ThinkingGraphTransactionRecord`.
- **Note**: Remaining 70% of file truncated; `add_edge`, `remove_node`, `remove_edge`, and other methods not visible.

### `pack/swarm/execution_graph.py`

#### `ExecutionGraph` class

- **`__init__(self, llm_fetcher=None, max_concurrency=None)`**: Initializes empty graph, semaphore if max_concurrency given, stop state, counters, lock.
- **`run(self, initial_input=None, entry_node_id=None, event_hook=None) -> GraphContext`**
  - **Purpose**: Execute the DAG from entry node(s). Uses `asyncio.Queue` for completion signals.
  - **Output**: Completed `GraphContext`.
  - **Side effects**: Populates `_active_run_ctx`, `_active_run_task`, `_active_run_tasks`. Calls `event_hook` on lifecycle events. Accumulates `node_inputs` and `node_outputs`.
  - **Failure modes**: ValueError if no entry node; `CancelledError` if hard stop; exceptions from node runs caught and stored as error dict; finally gathers all active tasks.
  - **Algorithm**: Start entry node; while any node is running, wait for completion; start downstream nodes if all upstreams executed; respect stop signals.
- **Node management**: `add_agent_node`, `add_tool_node`, `add_router_node`, `add_input_node`, `add_output_node`, `add_join_node` – each creates appropriate node, stores, bumps version.
- **Edge management**: `connect`, `disconnect` – add/remove edges, bump version. `_upstream_of`, `_downstream_of` for traversal.
- **Tool management**: `register_tool`, `unregister_tool`, `get_tool`.
- **Modification**: `remove_node`, `update_agent_prompt`, `add_tool_to_agent`, `remove_tool_from_agent`, `set_node_timeout`.
- **Stop control**: `request_soft_stop(reason)`, `request_hard_stop(reason)`, `clear_stop_requests()`.
- **Version/properties**: `version`, `stop_state`.
- **Note**: The `_lock` (asyncio.Lock) is declared but never awaited in provided code; concurrency during run is handled by semaphore and task tracking.

#### Node classes (run methods)

- **`AgentNode.run(ctx, inputs)`**: Formats `inputs` into a message; calls `agent.round_call(msg, stream=False, max_turns=3)`. Returns string.
- **`ToolNode.run(ctx, inputs)`**: If single input is dict, use as kwargs; else if single input, wrap as `{"input": ...}`; else wrap as `{"inputs": ...}`. Calls `tool.execute(**kwargs)`. Catches Exception and returns `{"error": ..., "tool": name}`.
- **`RouterNode.run(ctx, inputs)`**: If agent set and >1 route, constructs prompt to choose route, calls agent one turn, matches route label; else uses `default_route`. Returns `{"route": ..., "raw": ..., "input": ...}`.
- **`InputNode.run(ctx, inputs)`**: Returns `inputs[0]` or `None`.
- **`OutputNode.run(ctx, inputs)`**: Calls `self.collector(inputs)` (default identity).
- **`JoinNode.run(ctx, inputs)`**: Based on strategy: `"first"` returns `{"result": inputs[0] if any else None, "inputs": inputs}`; `"all"` returns `{"results": inputs, "count": len(inputs)}`.

### `pack/swarm/runtime_slot.py`

#### `RuntimeSlotManager` class

- **`__init__(self, thinking_graph=None, default_timeout=300.0, max_concurrent=4)`**: Initializes empty slots dict, tasks dict, semaphore, thinking graph reference.
- **`async submit(self, tool: Tool, arguments: Dict, *, name=None, timeout=None, metadata=None) -> str`**: Creates `RuntimeSlot`, starts background task via `_run_slot`, optionally adds ACTION node to thinking graph. Returns 12-char hex slot ID.
- **`async poll(self, slot_id: str) -> RuntimeSlot`**: Returns slot with updated `last_polled_at` and incremented `poll_count`.
- **`async list_slots(self, status_filter: Optional[List[SlotStatus]] = None) -> List[RuntimeSlot]`**: Returns slots matching status filter.
- **`async collect(self, slot_id: str) -> Any`**: Removes slot from dict and returns its result. Raises RuntimeError if slot still PENDING/RUNNING.
- **`async request_soft_stop(self, slot_id: str) -> bool`**: Sets stop_requested="soft", cancels task, awaits completion. Returns True if task existed.
- **`async request_hard_stop(self, slot_id: str) -> bool`**: Sets stop_requested="hard", cancels task, does not await. Returns True if task existed.
- **`cancel`** and **`soft_stop`** and **`hard_stop`**: Aliases.
- **`to_dict(self) -> Dict[str, Any]`**: Returns slot count, active tasks, slots sub-dict.
- **`__repr__(self) -> str`**: Summary with counts per status.

#### `_run_slot(slot: RuntimeSlot)` (internal async)
- Acquires semaphore; sets status RUNNING; runs coroutine with optional timeout; handles TimeoutError, CancelledError, generic Exception; after success checks `stop_requested` flag (set externally) – if set, marks as CANCELLED even if coroutine succeeded; on success/failure records OBSERVATION/ERROR nodes and edges to ThinkingGraph; cleans up task dict.

### `pack/swarm/swarm.py`

#### `AgentSwarm` class

- **`__init__(self, llm_fetcher: LLMFetcher, name="default", spec=None, max_concurrency=None)`**: Creates ExecutionGraph, ThinkingGraph, ToolRegistry; initializes agent dict, run counter.
- **`from_existing(cls, ...)`**: Classmethod; adopts existing ExecutionGraph, agents, etc. Value error if no LLMFetcher inferable.
- **`add_tool(tool) -> AgentSwarm`**: Registers tool in registry and graph's tool_pool.
- **`add_tools(tools) -> AgentSwarm`**: Iterative.
- **`remove_tool(tool_name) -> Tool`**: Unregisters; may raise KeyError.
- **`add_agent(node_id, system_prompt, *, tools=None, share_thinking_tools=True, share_graph_tools=False, extra_tools=None, max_concurrent_tools=1, fallback_order=None) -> AgentSwarm`**: Creates Agent with combined, deduplicated toolset (global + thinking tools + graph tools + extras). Adds AgentNode to graph.
- **`remove_agent(node_id) -> None`**: Removes from dict and graph.
- **`get_agent(node_id) -> Agent`**: Dict lookup.
- **`update_agent_prompt(node_id, system_prompt) -> AgentSwarm`**: Delegates to graph.
- **`add_tool_to_agent`, `remove_tool_from_agent`**: Delegates.
- **Topology helpers**: `add_input`, `add_output`, `add_router`, `add_join`, `add_tool_node`, `connect`, `disconnect`, `set_timeout`, `request_soft_stop`, `request_hard_stop`, `clear_stop_requests` – all return self (fluent).
- **`async run(self, initial_input=None, entry_node_id=None, event_hook=None) -> GraphContext`**: Increments run counter, stores last context, delegates to graph.run.
- **`last_context` property**: Returns last GraphContext.
- **`save(path: str | Path) -> None`**: Writes JSON snapshot with spec, graph, thinking graph, agents, run count. Excludes built-in tool names.
- **`load(cls, path, llm_fetcher, tool_pool=None) -> AgentSwarm`**: Classmethod; restores from file. Handles both snapshot and checkpoint formats. Restores ThinkingGraph and ExecutionGraph. Agents restored without re-injecting thinking/graph tools.
- **`checkpoint(self, ctx=None, path=None) -> Dict[str, Any]`** (partially visible): Returns dict with snapshot + runtime progress. Raises RuntimeError if no context.

### Tool factories

- **`create_builtin_tools() -> List[Tool]`**: Returns one Tool `"round_end"` (handler returns `"Round ended."`). Parameter schema uses nonstandard `"type": "Any"`.
- **`create_execution_graph_tools(graph) -> List[Tool]`**: Returns 10 tools for graph manipulation (add_agent, remove_node, connect, disconnect, update_agent_prompt, add/remove tool from agent, add_tool_node, set_node_timeout, get_info). All async. Inconsistent error handling: some catch exceptions and return error strings, others propagate.
- **`create_obscura_tools() -> List[Tool]`**: Returns `web_fetch` and `web_scrape` tools wrapping external `obscura` CLI. Handlers are `async def` but block on `subprocess.run` (no await). Uses hardcoded binary path and `shell=True` (shell injection risk).
- **`create_runtime_slot_tools(manager) -> List[Tool]`**: Returns 5 tools: `slot_poll`, `slot_list`, `slot_collect`, `slot_cancel`, `slot_soft_stop`. Hidden `_slot_submit` closure defined but not returned. Error handling varies; only slot_collect catches RuntimeError.
- **`create_shell_tools() -> List[Tool]`**: Returns one Tool `"shell"` wrapping `asyncio.create_subprocess_shell`. Simple dangerous-command filter (substring match). Timeout enforced via `asyncio.wait_for`. Error handling: returns `"Error: ..."` string for timeout and generic exceptions.
- **`create_thinking_graph_tools(graph) -> List[Tool]`**: Returns 7 tools: `thinking_graph_add_node`, `_add_edge`, `_validate_context`, `_get_node_info`, `_get_usage`, `_get_schema`, `_get_full_graph`. Note: `_add_node` handler accepts `payload` kwarg but tool schema does not expose it (bug). `_validate_context` always returns success string regardless of validation result.

### `pack/agent_io.py`

- **`AgentFileIOManager.__init__(self, swarm_root="agents", *, manifest_name="swarm.toml", runtime_dir_name="runtime", agent_runtime_dir_name="agents")`**: Resolves swarm root to absolute path.
- **`discover_packages(self) -> List[Path]`**: Lists directories under swarm_root that contain a manifest file.
- **`list_agent_ids(self) -> List[str]`**: Returns sorted unique agent IDs across all packages.
- **`read_agent_snapshot(self, agent_id, *, package_name=None, include_runtime_files=True) -> AgentFileSnapshot`**: Full read of agent spec, prompt, runtime files. Raises KeyError/ValueError if agent missing/ambiguous.
- **`get_agent_record(self, agent_id, package_name=None) -> Dict[str, Any]`**: Returns dict with agent_id, spec, file, package_root/name, manifest.
- **`read_agent_state`, `read_agent_context`, `read_agent_prompt`, `read_agent_log_tail`**: Thin wrappers extracting single field. `read_agent_log_tail` accepts `max_lines=200`; returns `""` if max_lines <= 0, `None` if file missing.
- **Internal methods**: `_load_manifest` (reads TOML), `_iter_agent_specs` (iterates agent_files), `_load_agent_specs` (AST then module import fallback – **security risk** for untrusted files), `_resolve_locations`, `_resolve_prompt_text` (precedence: inline > prompt_file > character_prompt + skill files), `_resolve_workspace`, `_read_json_if_exists`, `_read_jsonl_if_exists`, `_read_json_or_text_if_exists`, `_read_log_tail_if_exists` (all with `utf-8` encoding; memory.json falls back to raw text on JSON failure).

## Runtime Flow

### startup
- System starts by creating an `LLMFetcher` with backend(s) configured (env vars or hardcoded).
- For demos: `asyncio.run(main())` runs async main.
- `AgentSwarm` creates empty `ExecutionGraph`, `ThinkingGraph`, `ToolRegistry`. Fluent builder adds nodes and edges.
- `Agent` init creates `ToolRegistry` with built-in tools and user tools, sets up context handler.

### normal execution
- **Standalone Agent**: `round_call(msg)` builds messages, loops up to max_turns: calls LLM, parses tool calls, executes tools (sequential/parallel), appends results. After loop, always runs fallback summary (extra LLM call). Saves context pair.
- **Swarm**: `swarm.run(initial_input)` delegates to `ExecutionGraph.run()`:
  - Creates `GraphContext`.
  - Finds entry node(s), seeds initial input.
  - Asynchronously executes nodes as upstream dependencies complete.
  - For each node: acquire semaphore, run node with optional timeout.
  - On node completion: store output, emit event hook, trigger downstream nodes if route matches (if edge has label) or unconditionally.
  - Stop signals: soft stop allows current nodes to finish but prevents new starts; hard stop cancels all pending tasks.
  - Returns `GraphContext` with all node outputs and inputs.
- **RuntimeSlots**: Background tasks submitted via `submit()`, run immediately, can be polled/collected/cancelled.

### error paths
- **LLM call failures**: LLMFetcher retries on timeout (up to `_timeout_retry_count` times) across fallback backends. If all fail, raises `LLMBackendError`.
- **Streaming failures**: If no text yielded yet, fallback is attempted; once text yielded, exception raised immediately.
- **Tool execution errors**: `Agent` catches exceptions and returns `"Error: ..."` string to LLM. `ToolNode` catches exceptions and returns error dict. `RuntimeSlot` catches exceptions and sets FAILED status.
- **Graph execution errors**: Node exceptions caught by `worker` coroutine, stored as error dict in context. Downstream nodes still receive error output (no error propagation stop).
- **Stop signals**: Hard stop raises `CancelledError`; finally block gathers pending tasks.

### teardown
- `ExecutionGraph.run()` finally gathers all active tasks with `return_exceptions=True`, clears task references, resets stop state.
- `RuntimeSlot.soft_stop` awaits task completion; `hard_stop` cancels without await.
- `Agent` does not persist state by default; context handler keeps history in memory (may be serialized via swarm save/checkpoint).
- `AgentSwarm` save/checkpoint writes to disk.

## Side Effects

- **Files written**:
  - `AgentSwarm.save(path)` writes JSON to disk.
  - `RuntimeSlotManager` (no file I/O by itself; ThinkingGraph recording is in-memory unless persisted externally).
  - `demo_agent_and_swarm.py` writes nothing.
- **Files read**:
  - `AgentFileIOManager` reads manifest TOML, agent Python source files (AST or import), prompt/skill files, runtime JSON/JSONL/log files.
  - `AgentSwarm.load(path)` reads JSON snapshot.
- **Network calls**:
  - `LLMFetcher` makes HTTP(S) requests to LLM backends via `openai` or `litellm` SDK.
  - `LLMContextHandler.compress_context` and `generate_memory` call LLMFetcher.
  - `Agent.round_call` calls LLMFetcher multiple times.
  - `ExecutionGraph.AgentNode.run` calls Agent.round_call.
  - `RouterNode.run` calls Agent.round_call if agent set and >1 route.
  - `demo_agent_and_swarm.py.check_endpoint` makes HTTP GET to `/v1/models`.
- **Process spawning**:
  - `pack.tools.shell_tools.shell` spawns a subprocess via `asyncio.create_subprocess_shell`.
  - `pack.tools.obscura_tools` spawns `obscura` CLI via `subprocess.run` (blocking, shell=True).
- **State changes**:
  - `ExecutionGraph._version` increments on structural changes.
  - `ThinkingGraph._version` increments on node/edge changes.
  - `RuntimeSlotManager` mutates slot state (status, timestamps, poll count).
  - `LLMContextHandler` appends context pairs.
  - `Agent.run` updates internal context handler.
  - `AgentSwarm._run_count` increments.
- **Caches or temporary artifacts**:
  - `ThinkingGraph._transaction_log` accumulates transaction records (can be cleared).
  - `RuntimeSlotManager._slots` and `_tasks` accumulate; `collect` removes slot.
  - `Agent.memory_list` is declared but never used (dead code).
  - `ExecutionGraph._tool_pool` is a mutable dict.

## Agent Change Protocol

- **Before editing**: Read this semantic map and the source files relevant to the requested change.
- **During editing**: Treat this map as the current behavioral contract unless source inspection proves it stale.
- **After editing**: Update changed module, function, runtime-flow, and side-effect sections in the same change.
- **If code and map disagree**: Trust observed code, then repair the map before relying on it for further edits.
- **Particular attention to**:
  - `Agent` has a persistent typo: `llm_context_hanlder` vs `llm_context_handler` – both refer to same object but misspelled one is used in critical methods. Any change to `__init__` that breaks the duplicate will cause AttributeError.
  - `LLMContextHandler.compress_context` and `generate_memory` ignore their `id_list` parameters. Fixing this will change behavior.
  - `LLMLFetcher._timeout_retry_count` results in one extra retry (2 total attempts for max_retries=0). Changing this will affect retry behavior.
  - `thinking_graph.py` is 70% truncated; any edits should verify completeness of methods.
  - `execution_graph.py` has a declared `_lock` that is never awaited – design may be incomplete.
  - `obscura_tools.py` uses blocking subprocess.run inside async functions – if concurrency is important, replace with `asyncio.create_subprocess_exec`.
  - `test_agent_io.py` imports from `modules.llm_fetcher.agent_io` which does not exist in current structure – must fix to `pack.agent_io`.

## Change Sync

- **No changes synchronized yet.**
