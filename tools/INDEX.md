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
| [knowledge_tools.py](knowledge_tools.py#L11) | `create_knowledge_tools` | `knowledge_base: KnowledgeBase \| None` | `list[Tool]` | Create tools for searching and reading the workspace knowledge base. |
| [obscura_tools.py](obscura_tools.py#L25) | `_get_obscura_bin` | `None` | `str` | Resolve the configured Obscura executable. |
| [obscura_tools.py](obscura_tools.py#L50) | `_kill_process_group` | `process: subprocess.Popen[str]` | `None` | Terminate one CLI tool process and all children it started. |
| [obscura_tools.py](obscura_tools.py#L61) | `_run_cli` | `command: list[str], timeout: int` | `subprocess.CompletedProcess[str]` | Run a cancellable CLI command for the current tool execution. |
| [obscura_tools.py](obscura_tools.py#L92) | `_unwrap_search_url` | `href: str` | `str` | Extract a destination URL from a DuckDuckGo redirect link. |
| [obscura_tools.py](obscura_tools.py#L142) | `WebSearchStore._connect` | `None` | `sqlite3.Connection` | Open a short-lived WAL connection for a thread-safe operation. |
| [obscura_tools.py](obscura_tools.py#L149) | `WebSearchStore._migrate` | `None` | `None` | Create settings and usage tables without disturbing Agent data. |
| [obscura_tools.py](obscura_tools.py#L164) | `WebSearchStore.get_settings` | `None` | `dict[str, Any]` | Return saved search settings merged with safe defaults. |
| [obscura_tools.py](obscura_tools.py#L171) | `WebSearchStore.update_settings` | `values: dict[str, Any]` | `dict[str, Any]` | Validate, persist, and return web-search settings. |
| [obscura_tools.py](obscura_tools.py#L195) | `WebSearchStore.record` | `provider: str, ok: bool, result_count: int, duration_ms: int` | `None` | Add one provider attempt to today's durable usage aggregate. |
| [obscura_tools.py](obscura_tools.py#L207) | `WebSearchStore.usage` | `days: int` | `list[dict[str, Any]]` | Return provider usage totals for the requested recent day window. |
| [obscura_tools.py](obscura_tools.py#L219) | `configure_web_search_store` | `path: str \| Path, defaults: dict[str, Any] \| None` | `None` | Configure the process-wide persistent store used by new search tools. |
| [obscura_tools.py](obscura_tools.py#L225) | `get_web_search_store` | `None` | `WebSearchStore` | Return the configured store, lazily defaulting to the local runtime DB. |
| [obscura_tools.py](obscura_tools.py#L233) | `_search_duckduckgo` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search DuckDuckGo's HTML endpoint and normalize organic results. |
| [obscura_tools.py](obscura_tools.py#L289) | `_curl_document` | `url: str, timeout: int, user_agent: str` | `tuple[Any \| None, str]` | Fetch one HTML document with bounded curl diagnostics. |
| [obscura_tools.py](obscura_tools.py#L316) | `_search_baidu` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search Baidu's public HTML endpoint for domestic-first retrieval. |
| [obscura_tools.py](obscura_tools.py#L340) | `_search_bing_html` | `query: str, max_results: int, timeout: int` | `dict[str, Any]` | Search Bing's public HTML endpoint without requiring an API key. |
| [obscura_tools.py](obscura_tools.py#L364) | `_search_brave` | `query: str, max_results: int, timeout: int, api_key: str` | `dict[str, Any]` | Search Brave's JSON API using the configured subscription token. |
| [obscura_tools.py](obscura_tools.py#L381) | `_search_bing` | `query: str, max_results: int, timeout: int, api_key: str` | `dict[str, Any]` | Search Bing Web Search API using the configured subscription key. |
| [obscura_tools.py](obscura_tools.py#L398) | `_search_provider` | `provider: str, query: str, max_results: int, timeout: int, settings: dict[str, Any]` | `dict[str, Any]` | Dispatch one configured provider and return its normalized payload. |
| [obscura_tools.py](obscura_tools.py#L417) | `_relevant_search_results` | `query: str, results: list[dict[str, Any]]` | `list[dict[str, Any]]` | Reject result pages with no lexical relationship to the query. |
| [obscura_tools.py](obscura_tools.py#L444) | `_web_search` | `**kwargs: Any` | `dict[str, Any]` | Search domestic-first providers through curl with bounded fallback. |
| [obscura_tools.py](obscura_tools.py#L485) | `_obscura_fetch_cli` | `**kwargs: Any` | `dict[str, Any]` | Execute obscura fetch via CLI. |
| [obscura_tools.py](obscura_tools.py#L554) | `_obscura_scrape_cli` | `**kwargs: Any` | `dict[str, Any]` | Batch-scrape URLs with Obscura workers. |
| [obscura_tools.py](obscura_tools.py#L634) | `create_obscura_tools` | `None` | `list[Tool]` | Create Agent-ready web search and browsing tools. |
| [shell_tools.py](shell_tools.py#L12) | `_kill_process_group` | `process: subprocess.Popen` | `None` | Terminate a shell command and descendants when possible. |
| [shell_tools.py](shell_tools.py#L23) | `create_shell_tools` | `allowed_commands: Optional[List[str]], max_timeout: float, sandbox_cwd: Optional[str], register_process: Optional[Callable[[subprocess.Popen], None]], unregister_process: Optional[Callable[[subprocess.Popen], None]], force_stop_event: Any` | `List[Tool]` | Create shell execution tool with security controls. |
| [spawn_tools.py](spawn_tools.py#L34) | `create_task_report_tool` | `swarm: AgentSwarm, reporter: str, on_report: Callable[[], None]` | `Tool` | Build the terminal report tool for one dispatched or restored worker. |
| [spawn_tools.py](spawn_tools.py#L92) | `create_swarm_tools` | `swarm: AgentSwarm, llm_fetcher: LLMFetcher, worker_tool_pool: list[Tool], worker_tool_factory: Callable[[str], list[Tool]] \| None, worker_tool_binder: Callable[[str, Agent, list[Tool]], list[Tool]] \| None, coordinator_name: str, worker_max_rounds: int, worker_max_tokens: int, worker_max_context_threshold: int, worker_enable_stop_turn: bool, worker_default_stream: bool, context_path_factory: Callable[[str], Any] \| None, require_plan_task_id: bool, plan_task_validator: Callable[[str], bool] \| None` | `list[Tool]` | Create tools that let a coordinator LLM manipulate the swarm at runtime. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [obscura_tools.py](obscura_tools.py#L119) | `WebSearchStore` | `path: str \| Path, defaults: dict[str, Any] \| None` | `object` | Persist web-search settings and per-provider usage counters in SQLite. |
| [obscura_tools.py](obscura_tools.py#L610) | `ObscuraCDPClient` | `host: str, port: int` | `object` | Placeholder configuration for a future Obscura CDP client. |

<!-- END GENERATED SYMBOL MAP -->
