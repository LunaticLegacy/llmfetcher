# Semantic map

## `llmfetcher.context_handlers.linear.ContextHandlerLinear`

Owns one durable linear Agent transcript, a bounded working abstract, and an
append-only archive of raw compacted turns. It implements the context-handler
contract and is owned by application-level `Agent` instances.

### `ContextHandlerLinear.compact()`

Builds a stateless, bounded transcript request and calls the configured
compaction fetcher at deterministic temperature `0.0`. The compaction prompt
treats transcript contents as untrusted reference data and asks for a 6,000
character working summary, prioritizing goals, decisions, actionable state,
and blockers over verbatim tool output. It parses one `context_abstract` XML
element, accepting a non-empty opening-tagged partial summary when a provider
truncates only the closing tag; on success it archives raw messages and
replaces active history with the abstract. Called automatically after
`add_assistant_message()` crosses the configured threshold and by
application-owned manual compaction routes. It returns `False` for empty input
or a response without usable tagged summary, and lets fetcher failures raise.
Its transient `last_compaction_error` and `last_compaction_raw` fields expose
the failed request reason and an unparseable model `content` response to an
application UI; neither is written into the durable context file.

## `llmfetcher.swarm_module.execution_graph.ExecutionGraph`

Owns a dependency DAG of `Agent` nodes, routing-only nodes, callbacks and a
`TaskBus`. It is called by `AgentSwarm` and application code; it calls Agent
`run()`, `TaskBus` lifecycle APIs, and registered event hooks. It has no base
class or known subclasses.

### `ExecutionGraph.to_snapshot(agent_serializer, callback_serializer)`

Builds a JSON-compatible snapshot of a quiescent graph. It serializes topology,
Agent specifications, callback IDs, router scopes, TaskBus state and dynamic
task indexes while holding the topology lock. Calls the supplied serializers or
the default tool-free Agent serializer, then `TaskBus.to_snapshot()`. It raises
`GraphPersistenceError` when executable application objects cannot be safely
identified. Called by `save()` and applications needing an external store.

### `ExecutionGraph.save(path, agent_serializer, callback_serializer)`

Calls `to_snapshot()`, creates the destination parent and atomically replaces
the JSON destination through a sibling temporary file. It is called by
application/session persistence code and returns the written `Path`.

### `ExecutionGraph.load(path, agent_resolver, callback_resolver)`

Reads a snapshot into a new graph, rebuilds nodes and edges, resolves callback
IDs, restores router scopes and calls `TaskBus.from_snapshot()`. It is called
by recovery/session loading code. It raises `GraphPersistenceError` for invalid
or unresolved data; it does not resume running threads.

### `ExecutionGraph._default_agent_serializer` / `_default_agent_resolver`

Persist and recreate only standard tool-free `Agent` instances using
`LLMBackendConfig` and `LLMFetcher`. Tool handlers and custom context handlers
must use application-owned serializer/resolver pairs.

## `llmfetcher.swarm_module.task_bus.TaskBus`

Thread-safe mailbox for immutable task assignments and reports. It has no base
class or subclasses. `ExecutionGraph` owns and calls it.

### `TaskBus.to_snapshot()` / `TaskBus.from_snapshot(snapshot)`

Round-trip assignments, states, reports and inbox ordering. The restore method
rejects malformed data and `running` task states because an active worker has
no safe process-restart continuation.
