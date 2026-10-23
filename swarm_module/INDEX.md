# llmfetcher/swarm_module/ — Multi-Agent Swarm INDEX

Dependency-driven execution graph, concurrent scheduler and inter-agent
reporting used by Angelus sessions.

| File | Responsibility |
|---|---|
| `execution_graph.py` | `ExecutionGraph` DAG, `AgentFailure`, `GraphPersistenceError`, and the `MapperFn` / `RouterFn` contracts. |
| `swarm.py` | `AgentSwarm` dependency scheduler, lifetime usage aggregation and quiescent save/load. |
| `task_bus.py` | `TaskBus` structured task/report mailbox; `TaskAssignment`, `TaskReport`. |
| `__init__.py` | Public exports. |

## Boundaries

- Graph persistence is owned here; `AgentSwarm.save` / `.load` delegate to
  quiescent `ExecutionGraph` snapshots.
- Built-in declarative mapper/router choices serialize as data; arbitrary
  callbacks require an explicit registry.
- Reports are bounded; raw worker transcripts are never forwarded as handoff.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [execution_graph/errors.py](execution_graph/errors.py#L32) | `AgentFailure.__str__` | `None` | `str` | Implement `AgentFailure.__str__`. |
| [execution_graph/graph.py](execution_graph/graph.py#L117) | `_save_lock` | `destination: Path` | `threading.RLock` | Return the per-destination lock serialising snapshot replacement. |
| [execution_graph/graph.py](execution_graph/graph.py#L225) | `ExecutionGraph.__str__` | `None` | `str` | Render a thread-safe human-readable snapshot of graph topology. |
| [execution_graph/graph.py](execution_graph/graph.py#L239) | `ExecutionGraph._default_agent_serializer` | `agent_name: str, agent: Agent` | `JsonObject` | Serialize a standard tool-free Agent into JSON-compatible config. |
| [execution_graph/graph.py](execution_graph/graph.py#L248) | `ExecutionGraph._default_agent_resolver` | `agent_name: str, spec: JsonObject` | `Agent` | Recreate a standard tool-free Agent from a persisted specification. |
| [execution_graph/graph.py](execution_graph/graph.py#L256) | `ExecutionGraph.to_snapshot` | `agent_serializer: AgentSerializer \| None, callback_serializer: CallbackSerializer \| None` | `ExecutionGraphSnapshot` | Create a JSON-compatible snapshot of a quiescent graph. |
| [execution_graph/graph.py](execution_graph/graph.py#L329) | `ExecutionGraph.save` | `path: str \| Path, agent_serializer: AgentSerializer \| None, callback_serializer: CallbackSerializer \| None` | `Path` | Atomically save a quiescent graph snapshot to ``path``. |
| [execution_graph/graph.py](execution_graph/graph.py#L351) | `ExecutionGraph.load` | `path: str \| Path, agent_resolver: AgentResolver \| None, callback_resolver: CallbackResolver \| None` | `'ExecutionGraph'` | Load a graph snapshot into a new quiescent ExecutionGraph. |
| [execution_graph/graph.py](execution_graph/graph.py#L441) | `ExecutionGraph.add_hook` | `hook: ExecutionHook` | `None` | Register a hook that receives every :class:`ExecutionEvent`. |
| [execution_graph/graph.py](execution_graph/graph.py#L453) | `ExecutionGraph.remove_hook` | `hook: ExecutionHook` | `bool` | Remove one previously registered execution hook. |
| [execution_graph/graph.py](execution_graph/graph.py#L470) | `ExecutionGraph.view_snapshot` | `None` | `SwarmViewSnapshot` | Return a JSON-safe live topology view without executable objects. |
| [execution_graph/graph.py](execution_graph/graph.py#L516) | `ExecutionGraph.finalize_tasks` | `None` | `dict[str, str]` | Close every unfinished dynamic task after the scheduler stops. |
| [execution_graph/graph.py](execution_graph/graph.py#L549) | `ExecutionGraph.request_shutdown` | `None` | `None` | Ask the scheduler to stop submitting further runnable Agents. |
| [execution_graph/graph.py](execution_graph/graph.py#L560) | `ExecutionGraph._emit` | `source: str, agent_name: str, event_type: str, message: str, data: Any` | `None` | Fire an event to all registered hooks. |
| [execution_graph/graph.py](execution_graph/graph.py#L588) | `ExecutionGraph._record_node_state` | `agent_name: str, event_type: str, message: str, data: Any` | `None` | Project one lifecycle event into the UI-facing node state cache. |
| [execution_graph/graph.py](execution_graph/graph.py#L642) | `ExecutionGraph._attach_agent_events` | `agent: Agent` | `None` | Forward one graph member's lifecycle events to graph hooks. |
| [execution_graph/graph.py](execution_graph/graph.py#L678) | `ExecutionGraph.add_agent` | `agent_name: str, agent_instance: Agent` | `bool` | Register an agent as a graph vertex. |
| [execution_graph/graph.py](execution_graph/graph.py#L711) | `ExecutionGraph.add_routing_node` | `name: str, router: RouterFn` | `bool` | Register a lightweight non-LLM routing node. |
| [execution_graph/graph.py](execution_graph/graph.py#L748) | `ExecutionGraph.remove_agent` | `agent_name: str` | `bool` | Remove an agent and every edge connected to it. |
| [execution_graph/graph.py](execution_graph/graph.py#L782) | `ExecutionGraph.add_connection` | `source: str, target: str` | `bool` | Add a directed dependency edge from one agent to another. |
| [execution_graph/graph.py](execution_graph/graph.py#L823) | `ExecutionGraph.add_split` | `source: str, targets: list[str]` | `None` | Broadcast one agent's output to multiple successor agents. |
| [execution_graph/graph.py](execution_graph/graph.py#L849) | `ExecutionGraph.add_gather` | `sources: list[str], target: str, mapper: MapperFn \| None` | `None` | Make one agent depend on and aggregate multiple source agents. |
| [execution_graph/graph.py](execution_graph/graph.py#L889) | `ExecutionGraph.set_mapper` | `agent_name: str, mapper: MapperFn` | `None` | Set a node-level mapper on *agent_name*. |
| [execution_graph/graph.py](execution_graph/graph.py#L920) | `ExecutionGraph.set_router` | `agent_name: str, router: RouterFn` | `None` | Attach a post-completion router to an existing agent. |
| [execution_graph/graph.py](execution_graph/graph.py#L954) | `ExecutionGraph.remove_router` | `agent_name: str` | `bool` | Remove a post-completion router from an agent. |
| [execution_graph/graph.py](execution_graph/graph.py#L973) | `ExecutionGraph.dispatch_task` | `agent_name: str, agent_instance: Agent, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create a worker, deliver an explicit task, and queue it to run. |
| [execution_graph/graph.py](execution_graph/graph.py#L1052) | `ExecutionGraph.task_id_for_agent` | `agent_name: str` | `str` | Return the latest TaskBus assignment owned by one worker. |
| [execution_graph/graph.py](execution_graph/graph.py#L1070) | `ExecutionGraph.redispatch_task` | `agent_name: str, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Assign a fresh task to an existing terminal dispatched worker. |
| [execution_graph/graph.py](execution_graph/graph.py#L1155) | `ExecutionGraph.report_task` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Accept a structured worker report without forwarding raw output. |
| [execution_graph/graph.py](execution_graph/graph.py#L1207) | `ExecutionGraph.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Block until requested structured reports arrive or time expires. |
| [execution_graph/graph.py](execution_graph/graph.py#L1223) | `ExecutionGraph.dynamic_add_agent` | `agent_name: str, agent_instance: Agent` | `str` | Register an Agent node while a graph run is active. |
| [execution_graph/graph.py](execution_graph/graph.py#L1251) | `ExecutionGraph.dynamic_remove_agent` | `agent_name: str` | `str` | Dynamically remove an agent and its edges during execution. |
| [execution_graph/graph.py](execution_graph/graph.py#L1275) | `ExecutionGraph.dynamic_add_connection` | `source: str, target: str` | `str` | Dynamically add a dependency edge during execution. |
| [execution_graph/graph.py](execution_graph/graph.py#L1305) | `ExecutionGraph.dynamic_remove_connection` | `source: str, target: str` | `str` | Remove one dependency edge while the graph is editable. |
| [execution_graph/graph.py](execution_graph/graph.py#L1325) | `ExecutionGraph.dynamic_set_mapper` | `agent_name: str, mode: str` | `str` | Set a safe declarative input aggregator on an Agent node. |
| [execution_graph/graph.py](execution_graph/graph.py#L1344) | `ExecutionGraph.dynamic_set_router` | `agent_name: str, targets: list[str]` | `str` | Set a declarative router selecting a fixed successor subset. |
| [execution_graph/graph.py](execution_graph/graph.py#L1367) | `ExecutionGraph._mapper_for_mode` | `mode: str` | `MapperFn` | Return the built-in mapper function for one persisted mode. |
| [execution_graph/graph.py](execution_graph/graph.py#L1390) | `ExecutionGraph._restore_declarative_mapper` | `agent_name: str, mode: str` | `None` | Install one persisted declarative mapper without emitting an event. |
| [execution_graph/graph.py](execution_graph/graph.py#L1405) | `ExecutionGraph._restore_declarative_router` | `agent_name: str, targets: list[str]` | `None` | Install one persisted fixed router without emitting an event. |
| [execution_graph/graph.py](execution_graph/graph.py#L1424) | `ExecutionGraph.dynamic_get_info` | `None` | `str` | Return the current graph state as a structured string. |
| [execution_graph/graph.py](execution_graph/graph.py#L1463) | `ExecutionGraph.run` | `message: str, max_rounds: int \| None, control: AgentRunControl \| None, target_agent: str \| None, entry_agent: str \| None` | `dict[str, Any]` | Execute the graph using dependency-driven concurrent scheduling. |
| [execution_graph/graph.py](execution_graph/graph.py#L1886) | `ExecutionGraph._activate` | `completed_agent: str, successors: Iterable[str], remaining_dependencies: dict[str, int], ready: deque[str]` | `None` | Decrement dependency counts and enqueue ready successors. |
| [execution_graph/graph.py](execution_graph/graph.py#L1912) | `ExecutionGraph._drain_dynamic_ready` | `ready: deque[str], remaining_dependencies: dict[str, int]` | `None` | Move explicitly dispatched workers into the local scheduler queue. |
| [execution_graph/graph.py](execution_graph/graph.py#L1954) | `ExecutionGraph._render_assignment` | `assignment: TaskAssignment` | `str` | Render one explicit task package without exposing raw peer output. |
| [execution_graph/graph.py](execution_graph/graph.py#L1973) | `ExecutionGraph._build_input` | `agent_name: str, initial_message: str, outputs: Mapping[str, Any]` | `str` | Build the input message for one ready agent. |
| [execution_graph/graph.py](execution_graph/graph.py#L2019) | `ExecutionGraph._output_to_text` | `output: Any` | `str` | Convert an arbitrary agent output into message text. |
| [execution_graph/graph.py](execution_graph/graph.py#L2030) | `ExecutionGraph._require_agent` | `agent_name: str` | `None` | Ensure that an agent name is registered. |
| [execution_graph/serialization.py](execution_graph/serialization.py#L24) | `default_agent_serializer` | `agent_name: str, agent: Agent` | `JsonObject` | Serialize a standard tool-free Agent into JSON-compatible config. |
| [execution_graph/serialization.py](execution_graph/serialization.py#L67) | `default_agent_resolver` | `agent_name: str, spec: JsonObject` | `Agent` | Recreate a standard tool-free Agent from a persisted specification. |
| [snapshots.py](snapshots.py#L37) | `GraphNodeView.to_json` | `None` | `JsonObject` | Return the wire form consumed by the graph projection. |
| [snapshots.py](snapshots.py#L55) | `GraphEdgeView.to_json` | `None` | `JsonObject` | Return the wire form consumed by the graph projection. |
| [snapshots.py](snapshots.py#L76) | `GraphNodeState.to_json` | `None` | `JsonObject` | Return the wire form consumed by the graph projection. |
| [snapshots.py](snapshots.py#L108) | `SwarmViewSnapshot.to_json` | `None` | `JsonObject` | Return the JSON-safe mapping accepted by the host projection. |
| [snapshots.py](snapshots.py#L142) | `GraphSpecNode.to_json` | `None` | `JsonObject` | Return the persisted node object. |
| [snapshots.py](snapshots.py#L157) | `GraphSpecEdge.to_json` | `None` | `JsonObject` | Return the persisted edge object. |
| [snapshots.py](snapshots.py#L169) | `GraphCallbackIds.to_json` | `None` | `JsonObject` | Return the persisted callback identifier object. |
| [snapshots.py](snapshots.py#L183) | `GraphDeclarativeCallbacks.to_json` | `None` | `JsonObject` | Return the persisted declarative callback object. |
| [snapshots.py](snapshots.py#L213) | `ExecutionGraphSnapshot.to_json` | `None` | `JsonObject` | Return the persisted graph document. |
| [snapshots.py](snapshots.py#L233) | `ExecutionGraphSnapshot.from_json` | `value: JsonValue` | `'ExecutionGraphSnapshot'` | Decode one persisted graph document. |
| [snapshots.py](snapshots.py#L295) | `_mapping` | `value: JsonValue, where: str` | `JsonObject` | Return one JSON object, rejecting any other value. |
| [snapshots.py](snapshots.py#L302) | `_sequence` | `value: JsonValue, where: str` | `list[JsonValue]` | Return one JSON array, rejecting any other value. |
| [snapshots.py](snapshots.py#L309) | `_text` | `value: JsonValue, where: str` | `str` | Return one JSON string, rejecting any other value. |
| [snapshots.py](snapshots.py#L316) | `_integer` | `value: JsonValue, where: str` | `int` | Return one JSON integer, rejecting booleans and floats. |
| [snapshots.py](snapshots.py#L323) | `_string_map` | `value: JsonValue, where: str` | `dict[str, str]` | Return a JSON object whose every value is a string. |
| [snapshots.py](snapshots.py#L329) | `_string_tuple_map` | `value: JsonValue, where: str` | `dict[str, tuple[str, ...]]` | Return a JSON object mapping string keys to arrays of strings. |
| [snapshots.py](snapshots.py#L341) | `_reject_unknown` | `value: JsonObject, allowed: set[str], where: str` | `None` | Reject fields the writer never emits for this schema version. |
| [snapshots.py](snapshots.py#L350) | `_spec_node` | `value: JsonValue, index: int` | `GraphSpecNode` | Decode one persisted node entry. |
| [snapshots.py](snapshots.py#L369) | `_spec_edge` | `value: JsonValue, index: int` | `GraphSpecEdge` | Decode one persisted edge entry. |
| [swarm.py](swarm.py#L68) | `AgentSwarm.add_agent` | `agent_name: str, agent_instance: Agent` | `bool` | Register an ``Agent`` instance as a graph vertex. |
| [swarm.py](swarm.py#L72) | `AgentSwarm.save` | `path: str \| Path, agent_serializer: Callable[[str, Agent], JsonObject] \| None, callback_serializer: CallbackSerializer \| None` | `Path` | Persist a quiescent Swarm through its execution-graph snapshot. |
| [swarm.py](swarm.py#L101) | `AgentSwarm.load` | `path: str \| Path, agent_resolver: AgentResolver \| None, callback_resolver: CallbackResolver \| None` | `'AgentSwarm'` | Restore a quiescent Swarm without exposing its private graph field. |
| [swarm.py](swarm.py#L130) | `AgentSwarm.add_routing_node` | `name: str, router: RouterFn` | `bool` | Register a lightweight non-LLM routing node. |
| [swarm.py](swarm.py#L134) | `AgentSwarm.remove_agent` | `agent_name: str` | `bool` | Remove a registered agent and every edge connected to it. |
| [swarm.py](swarm.py#L142) | `AgentSwarm.add_connection` | `source: str, target: str` | `bool` | Add a directed dependency edge from *source* to *target*. |
| [swarm.py](swarm.py#L146) | `AgentSwarm.add_split` | `source: str, targets: list[str]` | `None` | Broadcast one agent's output to multiple successors. |
| [swarm.py](swarm.py#L150) | `AgentSwarm.add_gather` | `sources: list[str], target: str, mapper: MapperFn \| None` | `None` | Make *target* depend on and aggregate outputs from *sources*. |
| [swarm.py](swarm.py#L163) | `AgentSwarm.set_mapper` | `agent_name: str, mapper: MapperFn` | `None` | Set a node-level mapper that converts predecessor outputs into the agent's input message. |
| [swarm.py](swarm.py#L172) | `AgentSwarm.set_router` | `agent_name: str, router: RouterFn` | `None` | Attach a post-completion router to an existing agent. |
| [swarm.py](swarm.py#L176) | `AgentSwarm.remove_router` | `agent_name: str` | `bool` | Remove a post-completion router from an agent. |
| [swarm.py](swarm.py#L184) | `AgentSwarm.dynamic_add_agent` | `agent_name: str, agent_instance: Agent` | `str` | Dynamically register an ``Agent`` instance during execution. |
| [swarm.py](swarm.py#L190) | `AgentSwarm.dispatch_task` | `agent_name: str, agent_instance: Agent, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create and immediately schedule a task-addressed subagent. |
| [swarm.py](swarm.py#L229) | `AgentSwarm.task_id_for_agent` | `agent_name: str` | `str` | Return the latest TaskBus assignment for a dispatched worker. |
| [swarm.py](swarm.py#L240) | `AgentSwarm.get_agent` | `agent_name: str` | `Agent \| None` | Return one restored or live Agent without exposing topology maps. |
| [swarm.py](swarm.py#L251) | `AgentSwarm.dispatched_agent_names` | `None` | `tuple[str, ...]` | Return worker identities that own TaskBus assignments. |
| [swarm.py](swarm.py#L260) | `AgentSwarm.redispatch_task` | `agent_name: str, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Reactivate one terminal dispatched worker with a new task record. |
| [swarm.py](swarm.py#L295) | `AgentSwarm.report_task` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Submit one structured worker report to the assigned coordinator. |
| [swarm.py](swarm.py#L336) | `AgentSwarm.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Wait for reports from explicitly dispatched subagent tasks. |
| [swarm.py](swarm.py#L352) | `AgentSwarm.dynamic_remove_agent` | `agent_name: str` | `str` | Dynamically remove an agent and its edges during execution. |
| [swarm.py](swarm.py#L356) | `AgentSwarm.dynamic_add_connection` | `source: str, target: str` | `str` | Dynamically add a dependency edge during execution. |
| [swarm.py](swarm.py#L360) | `AgentSwarm.dynamic_remove_connection` | `source: str, target: str` | `str` | Dynamically remove a dependency edge during execution. |
| [swarm.py](swarm.py#L364) | `AgentSwarm.dynamic_set_mapper` | `agent_name: str, mode: str` | `str` | Dynamically set a declarative predecessor-output mapper. |
| [swarm.py](swarm.py#L368) | `AgentSwarm.dynamic_set_router` | `agent_name: str, targets: list[str]` | `str` | Dynamically set a fixed successor router. |
| [swarm.py](swarm.py#L372) | `AgentSwarm.dynamic_get_info` | `None` | `str` | Return current graph state as a structured string. |
| [swarm.py](swarm.py#L380) | `AgentSwarm.add_hook` | `hook: ExecutionHook` | `None` | Register a hook that receives every :class:`ExecutionEvent`. |
| [swarm.py](swarm.py#L387) | `AgentSwarm.remove_hook` | `hook: ExecutionHook` | `bool` | Remove a hook previously forwarded to the execution graph. |
| [swarm.py](swarm.py#L398) | `AgentSwarm.view_snapshot` | `None` | `SwarmViewSnapshot` | Return a safe, UI-oriented snapshot of the active graph topology. |
| [swarm.py](swarm.py#L407) | `AgentSwarm.finalize_tasks` | `None` | `dict[str, str]` | Close unfinished dynamic tasks after any terminal run outcome. |
| [swarm.py](swarm.py#L419) | `AgentSwarm.request_shutdown` | `None` | `None` | Stop scheduling further runnable Agents in the active graph. |
| [swarm.py](swarm.py#L435) | `AgentSwarm._cumulative_usage` | `agent: object` | `object` | Return the Agent counter that survives across lifecycles. |
| [swarm.py](swarm.py#L449) | `AgentSwarm.total_usage` | `None` | `dict[str, int]` | Aggregate lifetime token usage across every registered Agent. |
| [swarm.py](swarm.py#L477) | `AgentSwarm.agent_usage` | `None` | `dict[str, dict[str, int]]` | Project token usage for every currently registered Agent. |
| [swarm.py](swarm.py#L511) | `AgentSwarm.run` | `message: str, max_rounds: int \| None, control: AgentRunControl \| None, target_agent: str \| None, entry_agent: str \| None` | `dict[str, Any]` | Execute the graph with an optional cooperative Agent control. |
| [task_bus.py](task_bus.py#L21) | `append_subagent_report_instruction` | `system_prompt: str` | `str` | Append the fixed terminal-report instruction to a subagent prompt. |
| [task_bus.py](task_bus.py#L98) | `TaskReport.as_dict` | `None` | `dict[str, Any]` | Return a JSON-ready representation of the structured report. |
| [task_bus.py](task_bus.py#L128) | `TaskBus.create_assignment` | `recipient: str, reply_to: str, objective: str, handoff: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create and enqueue one immutable subagent work package. |
| [task_bus.py](task_bus.py#L180) | `TaskBus.claim_assignment` | `task_id: str` | `TaskAssignment` | Mark one queued assignment running and return its work package. |
| [task_bus.py](task_bus.py#L202) | `TaskBus.submit_report` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Close a task with a bounded report and deliver it to its inbox. |
| [task_bus.py](task_bus.py#L266) | `TaskBus.set_terminal_state` | `task_id: str, state: str` | `bool` | Close one unfinished assignment without manufacturing a report. |
| [task_bus.py](task_bus.py#L293) | `TaskBus.finalize_unfinished` | `running_state: str, queued_state: str` | `dict[str, str]` | Close every non-terminal assignment at an execution boundary. |
| [task_bus.py](task_bus.py#L337) | `TaskBus.fail_unreported_task` | `task_id: str, reporter: str, reason: str` | `TaskReport \| None` | Submit a failure report when a worker exits without reporting. |
| [task_bus.py](task_bus.py#L359) | `TaskBus.interrupt_task` | `task_id: str, reporter: str, reason: str` | `TaskReport \| None` | Deliver a structured interruption report for an unfinished task. |
| [task_bus.py](task_bus.py#L384) | `TaskBus.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Wait until every requested task has delivered a structured report. |
| [task_bus.py](task_bus.py#L407) | `TaskBus.get_assignment` | `task_id: str` | `TaskAssignment` | Return one immutable task assignment. |
| [task_bus.py](task_bus.py#L425) | `TaskBus.task_states` | `None` | `dict[str, str]` | Return a point-in-time view of each task lifecycle state. |
| [task_bus.py](task_bus.py#L437) | `TaskBus.to_snapshot` | `None` | `JsonObject` | Return a JSON-compatible, point-in-time copy of TaskBus state. |
| [task_bus.py](task_bus.py#L463) | `TaskBus.from_snapshot` | `snapshot: JsonObject` | `'TaskBus'` | Restore a TaskBus from :meth:`to_snapshot` output. |
| [task_bus.py](task_bus.py#L550) | `TaskBus._normalize_items` | `values: Iterable[str]` | `tuple[str, ...]` | Normalize, bound, and freeze a report list field. |
| [task_bus.py](task_bus.py#L564) | `TaskBus._state_for_report_status` | `status: str` | `str` | Map an Agent-supplied report status to a canonical task terminal. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [execution_graph/errors.py](execution_graph/errors.py#L8) | `GraphPersistenceError` | `None` | `ValueError` | Raised when an ExecutionGraph cannot be safely saved or restored. |
| [execution_graph/errors.py](execution_graph/errors.py#L13) | `AgentFailure` | `agent_name: str, error: str, exception: Exception \| None` | `object` | Non-fatal marker placed in :meth:`ExecutionGraph.run` outputs when an Agent raises during execution. |
| [execution_graph/graph.py](execution_graph/graph.py#L134) | `ExecutionGraph` | `max_concurrency_agents: int` | `object` | Directed acyclic graph that schedules dependent agents concurrently. |
| [snapshots.py](snapshots.py#L22) | `GraphNodeView` | `id: str, kind: str, dynamic: bool, parent: str \| None` | `object` | One node as a UI draws it. |
| [snapshots.py](snapshots.py#L48) | `GraphEdgeView` | `source: str, target: str, kind: str` | `object` | One directed dependency edge between two nodes. |
| [snapshots.py](snapshots.py#L61) | `GraphNodeState` | `state: str, message: str, updated_at: float, task_id: str \| None` | `object` | Current execution state of one node. |
| [snapshots.py](snapshots.py#L89) | `SwarmViewSnapshot` | `nodes: tuple[GraphNodeView, ...], edges: tuple[GraphEdgeView, ...], max_concurrency_agents: int, assignments: dict[str, str], task_states: dict[str, str], node_states: dict[str, GraphNodeState]` | `object` | Point-in-time, JSON-safe view of one live execution graph. |
| [snapshots.py](snapshots.py#L126) | `GraphSpecNode` | `name: str, kind: str, spec: JsonObject \| None` | `object` | One node of a durable graph snapshot. |
| [snapshots.py](snapshots.py#L151) | `GraphSpecEdge` | `source: str, target: str` | `object` | One persisted dependency edge. |
| [snapshots.py](snapshots.py#L163) | `GraphCallbackIds` | `mappers: dict[str, str], routers: dict[str, str]` | `object` | Stable identifiers for custom mapper and router callbacks. |
| [snapshots.py](snapshots.py#L177) | `GraphDeclarativeCallbacks` | `mappers: dict[str, str], routers: dict[str, tuple[str, ...]]` | `object` | Declarative mapper modes and router target sets. |
| [snapshots.py](snapshots.py#L193) | `ExecutionGraphSnapshot` | `version: int, max_concurrency_agents: int, nodes: tuple[GraphSpecNode, ...], edges: tuple[GraphSpecEdge, ...], callbacks: GraphCallbackIds, declarative_callbacks: GraphDeclarativeCallbacks, router_scopes: dict[str, tuple[str, ...]], task_bus: JsonObject, task_by_agent: dict[str, str], task_by_id: dict[str, str]` | `object` | The complete durable representation of a quiescent execution graph. |
| [swarm.py](swarm.py#L28) | `AgentSwarm` | `max_concurrency_agents: int` | `object` | Orchestrate multiple agents through an execution graph. |
| [task_bus.py](task_bus.py#L40) | `TaskAssignment` | `id: str, recipient: str, reply_to: str, objective: str, handoff: str, expected_artifacts: tuple[str, ...], created_at: float, plan_task_id: str` | `object` | Immutable work package delivered to one subagent. |
| [task_bus.py](task_bus.py#L66) | `TaskReport` | `task_id: str, reporter: str, recipient: str, status: str, summary: str, findings: tuple[str, ...], evidence: tuple[str, ...], artifacts: tuple[str, ...], open_questions: tuple[str, ...], recommended_next_action: str, created_at: float` | `object` | Immutable, bounded result package returned to a coordinator inbox. |
| [task_bus.py](task_bus.py#L107) | `TaskBus` | `None` | `object` | Thread-safe task dispatcher and report mailbox for one execution graph. |

<!-- END GENERATED SYMBOL MAP -->
