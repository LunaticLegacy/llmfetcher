# llmfetcher/ — Submodule INDEX

Git submodule containing the synchronous Python framework Angelus builds on.
It provides provider-neutral LLM dispatch, tool-using agents, durable context
handlers, graph/archive memory, and dependency-driven multi-agent execution.

> This file describes the checked-out submodule. Run submodule commands from
> the superproject only when deliberately updating its recorded revision.

## Package Map

| Area | Paths | Current responsibility |
|---|---|---|
| Public API | `__init__.py`, `llm_types.py` | Public imports, request/response, tool, context, token-usage, and terminal request-cancellation types. |
| Agent loop | `agent.py`, `events.py`, `usage_ledger.py` | Synchronous model/tool loop; the system message contains only system instructions while registered tools travel once through provider-native schemas; lifecycle events retain typed tool outcomes and credential-free preflight remote-request snapshots for UI consumers; one-call primary and internal-LLM usage ledger; optional force-stop observation during provider I/O. |
| LLM dispatch | `llm_fetcher.py`, `fetcher_handlers/` | Backend selection, ordinary retry/fallback, terminal request cancellation, credential-free preflight request observation, and OpenAI-compatible, DeepSeek, Anthropic, LiteLLM, OpenVINO, and ONNX Runtime adapters. |
| Context | `context_handlers/` | Base contract; durable linear history with compaction and raw archive; provider-backed retrieval composition; TLB adapter. `context_less_context/` is an experimental local worktree directory, not part of the indexed API. |
| Graph memory | `graph_memory/` | Persistent entity/relation store, incremental extraction, hybrid graph retrieval, archive evidence, and stateless semantic extraction/reranking workers. |
| Swarm | `swarm_module/` | Dependency graph, concurrent scheduler, TaskBus, bounded report handoff, and quiescent graph save/load. Repeated `run()` calls retain graph vertices; terminal dispatched tasks remain inspectable but are not implicitly rescheduled, and may be revived with a new immutable assignment. |
| Tools | `tool_handler.py`, `tool_executor.py`, `tools/` | Tool schemas/registry, parallel execution, and built-in shell, knowledge, web, and dynamic-spawn factories; `create_swarm_tools` accepts a shared worker pool, a name-bound factory, and an optional live-Agent binder for worker-local handlers needing persistence/reload callbacks. |
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
| Agent context configuration | `Agent.set_context_threshold` | Updates the active handler's compaction threshold and can persist it before a later `run()` reloads the context checkpoint. |

## Persistence Boundaries

- Linear context persists active messages, compaction abstracts, and an
  append-only raw-message archive in its context JSON.
- `GraphContextHandler` persists its graph in a companion
  `<context-path>.graph.json` file and flushes pending graph updates on save.
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
