# llmfetcher/tools/ — Built-in Tool Factories INDEX

Built-in Agent tool factories. Heavy factories load lazily to avoid circular
imports during startup.

| File | Responsibility |
|---|---|
| `__init__.py` | Aggregates factories; lazy `__getattr__` for knowledge and obscura. |
| `shell_tools.py` | `create_shell_tools` sandboxed shell execution, process-group kill, execution-controller cancellation. |
| `knowledge_tools.py` | `create_knowledge_tools` canonical knowledge-base search/read tools. |
| `obscura_tools.py` | `create_obscura_tools` web search/browser tools; `WebSearchStore`, `ObscuraCDPClient`. |
| `spawn_tools.py` | `create_swarm_tools` dynamic swarm graph mutation for coordinators. |

## Boundaries

- `create_knowledge_tools` is the sole knowledge-tool factory.
- Shell tools honour the per-attempt `ExecutionController` for forced stops.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [__init__.py](__init__.py#L28) | `__getattr__` | `name: str` | `Any` | Resolve a lazily exported tool factory. |
| [knowledge_tools.py](knowledge_tools.py#L9) | `create_knowledge_tools` | `knowledge_base: KnowledgeBase \| None` | `list[Tool]` | Create tools for searching and reading the workspace knowledge base. |
| [obscura_tools.py](obscura_tools.py#L26) | `_get_obscura_bin` | `None` | `str` | Resolve the configured Obscura executable. |
| [obscura_tools.py](obscura_tools.py#L51) | `_kill_process_group` | `process: subprocess.Popen[str]` | `None` | Terminate one CLI tool process and all children it started. |
| [obscura_tools.py](obscura_tools.py#L56) | `_run_cli` | `command: list[str], timeout: int` | `subprocess.CompletedProcess[str]` | Run a cancellable CLI command for the current tool execution. |
| [obscura_tools.py](obscura_tools.py#L89) | `_unwrap_search_url` | `href: str` | `str` | Extract a destination URL from a DuckDuckGo redirect link. |
| [obscura_tools.py](obscura_tools.py#L139) | `WebSearchStore._connect` | `None` | `sqlite3.Connection` | Open a short-lived WAL connection for a thread-safe operation. |
| [obscura_tools.py](obscura_tools.py#L147) | `WebSearchStore._connection` | `None` | `Any` | Yield one connection and always close it on Windows and POSIX. |
| [obscura_tools.py](obscura_tools.py#L155) | `WebSearchStore._migrate` | `None` | `None` | Create settings and usage tables without disturbing Agent data. |
| [obscura_tools.py](obscura_tools.py#L170) | `WebSearchStore.get_settings` | `None` | `dict[str, Any]` | Return saved search settings merged with safe defaults. |
| [obscura_tools.py](obscura_tools.py#L177) | `WebSearchStore.update_settings` | `values: dict[str, Any]` | `dict[str, Any]` | Validate, persist, and return web-search settings. |
| [obscura_tools.py](obscura_tools.py#L201) | `WebSearchStore.record` | `provider: str, ok: bool, result_count: int, duration_ms: int` | `None` | Add one provider attempt to today's durable usage aggregate. |
| [obscura_tools.py](obscura_tools.py#L213) | `WebSearchStore.usage` | `days: int` | `list[dict[str, Any]]` | Return provider usage totals for the requested recent day window. |
| [obscura_tools.py](obscura_tools.py#L225) | `configure_web_search_store` | `path: str \| Path, defaults: dict[str, Any] \| None` | `None` | Configure the process-wide persistent store used by new search tools. |
| [obscura_tools.py](obscura_tools.py#L231) | `get_web_search_store` | `None` | `WebSearchStore` | Return the configured store, lazily defaulting to the local runtime DB. |
| [obscura_tools.py](obscura_tools.py#L239) | `_search_duckduckgo` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search DuckDuckGo's HTML endpoint and normalize organic results. |
| [obscura_tools.py](obscura_tools.py#L295) | `_curl_document` | `url: str, timeout: int, user_agent: str` | `tuple[Any \| None, str]` | Fetch one HTML document with bounded curl diagnostics. |
| [obscura_tools.py](obscura_tools.py#L322) | `_search_baidu` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search Baidu's public HTML endpoint for domestic-first retrieval. |
| [obscura_tools.py](obscura_tools.py#L346) | `_search_bing_html` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search Bing's public HTML endpoint without requiring an API key. |
| [obscura_tools.py](obscura_tools.py#L370) | `_search_brave` | `query: str, max_results: int, timeout: int, api_key: str` | `dict[str, Any]` | Search Brave's JSON API using the configured subscription token. |
| [obscura_tools.py](obscura_tools.py#L387) | `_search_bing` | `query: str, max_results: int, timeout: int, api_key: str` | `dict[str, Any]` | Search Bing Web Search API using the configured subscription key. |
| [obscura_tools.py](obscura_tools.py#L404) | `_search_provider` | `provider: str, query: str, max_results: int, timeout: int, settings: dict[str, Any]` | `dict[str, Any]` | Dispatch one configured provider and return its normalized payload. |
| [obscura_tools.py](obscura_tools.py#L423) | `_relevant_search_results` | `query: str, results: list[dict[str, Any]]` | `list[dict[str, Any]]` | Reject result pages with no lexical relationship to the query. |
| [obscura_tools.py](obscura_tools.py#L450) | `_web_search` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search domestic-first providers through curl with bounded fallback. |
| [obscura_tools.py](obscura_tools.py#L495) | `_obscura_fetch_cli` | `url: str, mode: str, selector: str, wait: int, wait_until: str, stealth: bool, eval_js: str, include_images: bool` | `dict[str, Any]` | Execute obscura fetch via CLI. |
| [obscura_tools.py](obscura_tools.py#L573) | `_obscura_scrape_cli` | `urls: list[str] \| str, concurrency: int, timeout: int, eval_js: str` | `dict[str, Any]` | Batch-scrape URLs with Obscura workers. |
| [obscura_tools.py](obscura_tools.py#L658) | `create_obscura_tools` | `None` | `list[Tool]` | Create Agent-ready web search and browsing tools. |
| [process_runtime.py](process_runtime.py#L64) | `popen_platform_kwargs` | `None` | `dict[str, Any]` | Return subprocess creation options for the current operating system. |
| [process_runtime.py](process_runtime.py#L71) | `attach_process_tree` | `process: subprocess.Popen[Any]` | `None` | Attach a process to a kill-on-close Windows Job Object when possible. |
| [process_runtime.py](process_runtime.py#L97) | `terminate_process_tree` | `process: subprocess.Popen[Any]` | `None` | Terminate a process and all descendants, using native platform APIs. |
| [process_runtime.py](process_runtime.py#L130) | `close_process_tree` | `process: subprocess.Popen[Any]` | `None` | Release a Windows Job Object after normal process completion. |
| [shell_tools.py](shell_tools.py#L12) | `_kill_process_group` | `process: subprocess.Popen` | `None` | Terminate a shell command and descendants when possible. |
| [shell_tools.py](shell_tools.py#L17) | `create_shell_tools` | `allowed_commands: Optional[List[str]], max_timeout: float, sandbox_cwd: Optional[str], register_process: Optional[Callable[[subprocess.Popen], None]], unregister_process: Optional[Callable[[subprocess.Popen], None]], force_stop_event: Any` | `List[Tool]` | Create shell execution tool with security controls. |
| [spawn_tools.py](spawn_tools.py#L37) | `_text` | `arguments: Mapping[str, object], key: str, default: str` | `str` | Return one string argument, treating JSON null as absent. |
| [spawn_tools.py](spawn_tools.py#L45) | `_string_list` | `value: object` | `tuple[str, ...]` | Normalize one model-provided scalar or array into string values. |
| [spawn_tools.py](spawn_tools.py#L52) | `_artifact_list` | `value: object` | `tuple[str, ...]` | Normalize expected artifact names, rejecting non-array scalars. |
| [spawn_tools.py](spawn_tools.py#L61) | `_as_int` | `value: object, field: str` | `int` | Coerce a model-provided integer without accepting booleans. |
| [spawn_tools.py](spawn_tools.py#L71) | `_as_float` | `value: object, field: str` | `float` | Coerce a model-provided number without accepting booleans. |
| [spawn_tools.py](spawn_tools.py#L94) | `DispatchSpecification.from_arguments` | `arguments: Mapping[str, object], default_reply_to: str` | `'DispatchSpecification'` | Decode one tool call, rejecting missing required fields. |
| [spawn_tools.py](spawn_tools.py#L131) | `ReviveSpecification.from_arguments` | `arguments: Mapping[str, object], default_reply_to: str` | `'ReviveSpecification'` | Decode one revive tool call, rejecting missing required fields. |
| [spawn_tools.py](spawn_tools.py#L167) | `TaskReport.from_arguments` | `arguments: Mapping[str, object]` | `'TaskReport'` | Decode one report tool call with the documented defaults. |
| [spawn_tools.py](spawn_tools.py#L180) | `create_task_report_tool` | `swarm: AgentSwarm, reporter: str, on_report: Callable[[], None]` | `Tool` | Build the terminal report tool for one dispatched or restored worker. |
| [spawn_tools.py](spawn_tools.py#L249) | `create_swarm_tools` | `swarm: AgentSwarm, llm_fetcher: LLMFetcher, worker_tool_pool: list[Tool], worker_tool_factory: Callable[[str], list[Tool]] \| None, worker_tool_binder: Callable[[str, Agent, list[Tool]], list[Tool]] \| None, coordinator_name: str, worker_max_rounds: int, worker_max_tokens: int, worker_max_context_threshold: int, worker_enable_stop_turn: bool, worker_default_stream: bool, context_path_factory: Callable[[str], str \| Path \| None] \| None, require_plan_task_id: bool, plan_task_validator: Callable[[str], bool] \| None` | `list[Tool]` | Create tools that let a coordinator LLM manipulate the swarm at runtime. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [obscura_tools.py](obscura_tools.py#L116) | `WebSearchStore` | `path: str \| Path, defaults: dict[str, Any] \| None` | `object` | Persist web-search settings and per-provider usage counters in SQLite. |
| [obscura_tools.py](obscura_tools.py#L634) | `ObscuraCDPClient` | `host: str, port: int` | `object` | Placeholder configuration for a future Obscura CDP client. |
| [spawn_tools.py](spawn_tools.py#L82) | `DispatchSpecification` | `name: str, system_prompt: str, objective: str, handoff: str, reply_to: str, expected_artifacts: tuple[str, ...], plan_task_id: str` | `object` | One coordinator request to dispatch a fresh worker. |
| [spawn_tools.py](spawn_tools.py#L120) | `ReviveSpecification` | `name: str, objective: str, handoff: str, reply_to: str, expected_artifacts: tuple[str, ...], plan_task_id: str` | `object` | One coordinator request to reuse a terminal worker. |
| [spawn_tools.py](spawn_tools.py#L155) | `TaskReport` | `status: str, summary: str, findings: tuple[str, ...], evidence: tuple[str, ...], artifacts: tuple[str, ...], open_questions: tuple[str, ...], recommended_next_action: str` | `object` | One worker's terminal structured report. |

<!-- END GENERATED SYMBOL MAP -->
