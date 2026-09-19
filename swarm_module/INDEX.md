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
| [execution_graph.py](execution_graph.py#L121) | `AgentFailure.__str__` | `None` | `str` | Implement `AgentFailure.__str__`. |
| [execution_graph.py](execution_graph.py#L219) | `ExecutionGraph.__str__` | `None` | `str` | Render a thread-safe human-readable snapshot of graph topology. |
| [execution_graph.py](execution_graph.py#L233) | `ExecutionGraph._default_agent_serializer` | `agent_name: str, agent: Agent` | `dict[str, Any]` | Serialize a standard tool-free Agent into JSON-compatible config. |
| [execution_graph.py](execution_graph.py#L269) | `ExecutionGraph._default_agent_resolver` | `agent_name: str, spec: Mapping[str, Any]` | `Agent` | Recreate a standard tool-free Agent from a persisted specification. |
| [execution_graph.py](execution_graph.py#L295) | `ExecutionGraph.to_snapshot` | `agent_serializer: AgentSerializer \| None, callback_serializer: CallbackSerializer \| None` | `dict[str, Any]` | Create a JSON-compatible snapshot of a quiescent graph. |
| [execution_graph.py](execution_graph.py#L355) | `ExecutionGraph.save` | `path: str \| Path, agent_serializer: AgentSerializer \| None, callback_serializer: CallbackSerializer \| None` | `Path` | Atomically save a quiescent graph snapshot to ``path``. |
| [execution_graph.py](execution_graph.py#L376) | `ExecutionGraph.load` | `path: str \| Path, agent_resolver: AgentResolver \| None, callback_resolver: CallbackResolver \| None` | `'ExecutionGraph'` | Load a graph snapshot into a new quiescent ExecutionGraph. |
| [execution_graph.py](execution_graph.py#L445) | `ExecutionGraph.add_hook` | `hook: ExecutionHook` | `None` | Register a hook that receives every :class:`ExecutionEvent`. |
| [execution_graph.py](execution_graph.py#L457) | `ExecutionGraph.remove_hook` | `hook: ExecutionHook` | `bool` | Remove one previously registered execution hook. |
| [execution_graph.py](execution_graph.py#L474) | `ExecutionGraph.view_snapshot` | `None` | `dict[str, Any]` | Return a JSON-safe live topology view without executable objects. |
| [execution_graph.py](execution_graph.py#L525) | `ExecutionGraph.finalize_tasks` | `None` | `dict[str, str]` | Close every unfinished dynamic task after the scheduler stops. |
| [execution_graph.py](execution_graph.py#L558) | `ExecutionGraph.request_shutdown` | `None` | `None` | Ask the scheduler to stop submitting further runnable Agents. |
| [execution_graph.py](execution_graph.py#L569) | `ExecutionGraph._emit` | `source: str, agent_name: str, event_type: str, message: str, data: Any` | `None` | Fire an event to all registered hooks. |
| [execution_graph.py](execution_graph.py#L597) | `ExecutionGraph._record_node_state` | `agent_name: str, event_type: str, message: str, data: Any` | `None` | Project one lifecycle event into the UI-facing node state cache. |
| [execution_graph.py](execution_graph.py#L653) | `ExecutionGraph._attach_agent_events` | `agent: Agent` | `None` | Forward one graph member's lifecycle events to graph hooks. |
| [execution_graph.py](execution_graph.py#L691) | `ExecutionGraph.add_agent` | `agent_name: str, agent_instance: Agent` | `bool` | Register an agent as a graph vertex. |
| [execution_graph.py](execution_graph.py#L724) | `ExecutionGraph.add_routing_node` | `name: str, router: RouterFn` | `bool` | Register a lightweight non-LLM routing node. |
| [execution_graph.py](execution_graph.py#L761) | `ExecutionGraph.remove_agent` | `agent_name: str` | `bool` | Remove an agent and every edge connected to it. |
| [execution_graph.py](execution_graph.py#L795) | `ExecutionGraph.add_connection` | `source: str, target: str` | `bool` | Add a directed dependency edge from one agent to another. |
| [execution_graph.py](execution_graph.py#L836) | `ExecutionGraph.add_split` | `source: str, targets: list[str]` | `None` | Broadcast one agent's output to multiple successor agents. |
| [execution_graph.py](execution_graph.py#L862) | `ExecutionGraph.add_gather` | `sources: list[str], target: str, mapper: MapperFn \| None` | `None` | Make one agent depend on and aggregate multiple source agents. |
| [execution_graph.py](execution_graph.py#L902) | `ExecutionGraph.set_mapper` | `agent_name: str, mapper: MapperFn` | `None` | Set a node-level mapper on *agent_name*. |
| [execution_graph.py](execution_graph.py#L933) | `ExecutionGraph.set_router` | `agent_name: str, router: RouterFn` | `None` | Attach a post-completion router to an existing agent. |
| [execution_graph.py](execution_graph.py#L967) | `ExecutionGraph.remove_router` | `agent_name: str` | `bool` | Remove a post-completion router from an agent. |
| [execution_graph.py](execution_graph.py#L986) | `ExecutionGraph.dispatch_task` | `agent_name: str, agent_instance: Agent, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create a worker, deliver an explicit task, and queue it to run. |
| [execution_graph.py](execution_graph.py#L1062) | `ExecutionGraph.task_id_for_agent` | `agent_name: str` | `str` | Return the latest TaskBus assignment owned by one worker. |
| [execution_graph.py](execution_graph.py#L1080) | `ExecutionGraph.redispatch_task` | `agent_name: str, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Assign a fresh task to an existing terminal dispatched worker. |
| [execution_graph.py](execution_graph.py#L1162) | `ExecutionGraph.report_task` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Accept a structured worker report without forwarding raw output. |
| [execution_graph.py](execution_graph.py#L1214) | `ExecutionGraph.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Block until requested structured reports arrive or time expires. |
| [execution_graph.py](execution_graph.py#L1230) | `ExecutionGraph.dynamic_add_agent` | `agent_name: str, agent_instance: Agent` | `str` | Register an Agent node while a graph run is active. |
| [execution_graph.py](execution_graph.py#L1258) | `ExecutionGraph.dynamic_remove_agent` | `agent_name: str` | `str` | Dynamically remove an agent and its edges during execution. |
| [execution_graph.py](execution_graph.py#L1282) | `ExecutionGraph.dynamic_add_connection` | `source: str, target: str` | `str` | Dynamically add a dependency edge during execution. |
| [execution_graph.py](execution_graph.py#L1312) | `ExecutionGraph.dynamic_remove_connection` | `source: str, target: str` | `str` | Remove one dependency edge while the graph is editable. |
| [execution_graph.py](execution_graph.py#L1332) | `ExecutionGraph.dynamic_set_mapper` | `agent_name: str, mode: str` | `str` | Set a safe declarative input aggregator on an Agent node. |
| [execution_graph.py](execution_graph.py#L1351) | `ExecutionGraph.dynamic_set_router` | `agent_name: str, targets: list[str]` | `str` | Set a declarative router selecting a fixed successor subset. |
| [execution_graph.py](execution_graph.py#L1374) | `ExecutionGraph._mapper_for_mode` | `mode: str` | `MapperFn` | Return the built-in mapper function for one persisted mode. |
| [execution_graph.py](execution_graph.py#L1397) | `ExecutionGraph._restore_declarative_mapper` | `agent_name: str, mode: str` | `None` | Install one persisted declarative mapper without emitting an event. |
| [execution_graph.py](execution_graph.py#L1412) | `ExecutionGraph._restore_declarative_router` | `agent_name: str, targets: list[str]` | `None` | Install one persisted fixed router without emitting an event. |
| [execution_graph.py](execution_graph.py#L1431) | `ExecutionGraph.dynamic_get_info` | `None` | `str` | Return the current graph state as a structured string. |
| [execution_graph.py](execution_graph.py#L1470) | `ExecutionGraph.run` | `message: str, max_rounds: int \| None, control: AgentRunControl \| None, target_agent: str \| None` | `dict[str, Any]` | Execute the graph using dependency-driven concurrent scheduling. |
| [execution_graph.py](execution_graph.py#L1864) | `ExecutionGraph._activate` | `completed_agent: str, successors: Iterable[str], remaining_dependencies: dict[str, int], ready: deque[str]` | `None` | Decrement dependency counts and enqueue ready successors. |
| [execution_graph.py](execution_graph.py#L1890) | `ExecutionGraph._drain_dynamic_ready` | `ready: deque[str], remaining_dependencies: dict[str, int]` | `None` | Move explicitly dispatched workers into the local scheduler queue. |
| [execution_graph.py](execution_graph.py#L1932) | `ExecutionGraph._render_assignment` | `assignment: TaskAssignment` | `str` | Render one explicit task package without exposing raw peer output. |
| [execution_graph.py](execution_graph.py#L1951) | `ExecutionGraph._build_input` | `agent_name: str, initial_message: str, outputs: Mapping[str, Any]` | `str` | Build the input message for one ready agent. |
| [execution_graph.py](execution_graph.py#L1997) | `ExecutionGraph._output_to_text` | `output: Any` | `str` | Convert an arbitrary agent output into message text. |
| [execution_graph.py](execution_graph.py#L2010) | `ExecutionGraph._require_agent` | `agent_name: str` | `None` | Ensure that an agent name is registered. |
| [swarm.py](swarm.py#L66) | `AgentSwarm.add_agent` | `agent_name: str, agent_instance: Agent` | `bool` | Register an ``Agent`` instance as a graph vertex. |
| [swarm.py](swarm.py#L70) | `AgentSwarm.save` | `path: str \| Path, agent_serializer: Callable[[str, Agent], dict[str, Any]] \| None, callback_serializer: CallbackSerializer \| None` | `Path` | Persist a quiescent Swarm through its execution-graph snapshot. |
| [swarm.py](swarm.py#L99) | `AgentSwarm.load` | `path: str \| Path, agent_resolver: AgentResolver \| None, callback_resolver: CallbackResolver \| None` | `'AgentSwarm'` | Restore a quiescent Swarm without exposing its private graph field. |
| [swarm.py](swarm.py#L128) | `AgentSwarm.add_routing_node` | `name: str, router: RouterFn` | `bool` | Register a lightweight non-LLM routing node. |
| [swarm.py](swarm.py#L132) | `AgentSwarm.remove_agent` | `agent_name: str` | `bool` | Remove a registered agent and every edge connected to it. |
| [swarm.py](swarm.py#L140) | `AgentSwarm.add_connection` | `source: str, target: str` | `bool` | Add a directed dependency edge from *source* to *target*. |
| [swarm.py](swarm.py#L144) | `AgentSwarm.add_split` | `source: str, targets: list[str]` | `None` | Broadcast one agent's output to multiple successors. |
| [swarm.py](swarm.py#L148) | `AgentSwarm.add_gather` | `sources: list[str], target: str, mapper: MapperFn \| None` | `None` | Make *target* depend on and aggregate outputs from *sources*. |
| [swarm.py](swarm.py#L161) | `AgentSwarm.set_mapper` | `agent_name: str, mapper: MapperFn` | `None` | Set a node-level mapper that converts predecessor outputs into the agent's input message. |
| [swarm.py](swarm.py#L170) | `AgentSwarm.set_router` | `agent_name: str, router: RouterFn` | `None` | Attach a post-completion router to an existing agent. |
| [swarm.py](swarm.py#L174) | `AgentSwarm.remove_router` | `agent_name: str` | `bool` | Remove a post-completion router from an agent. |
| [swarm.py](swarm.py#L182) | `AgentSwarm.dynamic_add_agent` | `agent_name: str, agent_instance: Agent` | `str` | Dynamically register an ``Agent`` instance during execution. |
| [swarm.py](swarm.py#L188) | `AgentSwarm.dispatch_task` | `agent_name: str, agent_instance: Agent, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create and immediately schedule a task-addressed subagent. |
| [swarm.py](swarm.py#L227) | `AgentSwarm.task_id_for_agent` | `agent_name: str` | `str` | Return the latest TaskBus assignment for a dispatched worker. |
| [swarm.py](swarm.py#L238) | `AgentSwarm.get_agent` | `agent_name: str` | `Agent \| None` | Return one restored or live Agent without exposing topology maps. |
| [swarm.py](swarm.py#L249) | `AgentSwarm.dispatched_agent_names` | `None` | `tuple[str, ...]` | Return worker identities that own TaskBus assignments. |
| [swarm.py](swarm.py#L258) | `AgentSwarm.redispatch_task` | `agent_name: str, objective: str, handoff: str, reply_to: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Reactivate one terminal dispatched worker with a new task record. |
| [swarm.py](swarm.py#L293) | `AgentSwarm.report_task` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Submit one structured worker report to the assigned coordinator. |
| [swarm.py](swarm.py#L334) | `AgentSwarm.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Wait for reports from explicitly dispatched subagent tasks. |
| [swarm.py](swarm.py#L350) | `AgentSwarm.dynamic_remove_agent` | `agent_name: str` | `str` | Dynamically remove an agent and its edges during execution. |
| [swarm.py](swarm.py#L354) | `AgentSwarm.dynamic_add_connection` | `source: str, target: str` | `str` | Dynamically add a dependency edge during execution. |
| [swarm.py](swarm.py#L358) | `AgentSwarm.dynamic_remove_connection` | `source: str, target: str` | `str` | Dynamically remove a dependency edge during execution. |
| [swarm.py](swarm.py#L362) | `AgentSwarm.dynamic_set_mapper` | `agent_name: str, mode: str` | `str` | Dynamically set a declarative predecessor-output mapper. |
| [swarm.py](swarm.py#L366) | `AgentSwarm.dynamic_set_router` | `agent_name: str, targets: list[str]` | `str` | Dynamically set a fixed successor router. |
| [swarm.py](swarm.py#L370) | `AgentSwarm.dynamic_get_info` | `None` | `str` | Return current graph state as a structured string. |
| [swarm.py](swarm.py#L378) | `AgentSwarm.add_hook` | `hook: ExecutionHook` | `None` | Register a hook that receives every :class:`ExecutionEvent`. |
| [swarm.py](swarm.py#L385) | `AgentSwarm.remove_hook` | `hook: ExecutionHook` | `bool` | Remove a hook previously forwarded to the execution graph. |
| [swarm.py](swarm.py#L396) | `AgentSwarm.view_snapshot` | `None` | `dict[str, Any]` | Return a safe, UI-oriented snapshot of the active graph topology. |
| [swarm.py](swarm.py#L405) | `AgentSwarm.finalize_tasks` | `None` | `dict[str, str]` | Close unfinished dynamic tasks after any terminal run outcome. |
| [swarm.py](swarm.py#L417) | `AgentSwarm.request_shutdown` | `None` | `None` | Stop scheduling further runnable Agents in the active graph. |
| [swarm.py](swarm.py#L433) | `AgentSwarm._cumulative_usage` | `agent: object` | `object` | Return the Agent counter that survives across lifecycles. |
| [swarm.py](swarm.py#L447) | `AgentSwarm.total_usage` | `None` | `dict[str, int]` | Aggregate lifetime token usage across every registered Agent. |
| [swarm.py](swarm.py#L475) | `AgentSwarm.agent_usage` | `None` | `dict[str, dict[str, int]]` | Project token usage for every currently registered Agent. |
| [swarm.py](swarm.py#L509) | `AgentSwarm.run` | `message: str, max_rounds: int \| None, control: AgentRunControl \| None, target_agent: str \| None` | `dict[str, Any]` | Execute the graph with an optional cooperative Agent control. |
| [task_bus.py](task_bus.py#L71) | `TaskReport.as_dict` | `None` | `dict[str, Any]` | Return a JSON-ready representation of the structured report. |
| [task_bus.py](task_bus.py#L101) | `TaskBus.create_assignment` | `recipient: str, reply_to: str, objective: str, handoff: str, expected_artifacts: Iterable[str], task_id: str, plan_task_id: str` | `TaskAssignment` | Create and enqueue one immutable subagent work package. |
| [task_bus.py](task_bus.py#L153) | `TaskBus.claim_assignment` | `task_id: str` | `TaskAssignment` | Mark one queued assignment running and return its work package. |
| [task_bus.py](task_bus.py#L175) | `TaskBus.submit_report` | `task_id: str, reporter: str, status: str, summary: str, findings: Iterable[str], evidence: Iterable[str], artifacts: Iterable[str], open_questions: Iterable[str], recommended_next_action: str` | `TaskReport` | Close a task with a bounded report and deliver it to its inbox. |
| [task_bus.py](task_bus.py#L239) | `TaskBus.set_terminal_state` | `task_id: str, state: str` | `bool` | Close one unfinished assignment without manufacturing a report. |
| [task_bus.py](task_bus.py#L266) | `TaskBus.finalize_unfinished` | `running_state: str, queued_state: str` | `dict[str, str]` | Close every non-terminal assignment at an execution boundary. |
| [task_bus.py](task_bus.py#L310) | `TaskBus.fail_unreported_task` | `task_id: str, reporter: str, reason: str` | `TaskReport \| None` | Submit a failure report when a worker exits without reporting. |
| [task_bus.py](task_bus.py#L332) | `TaskBus.interrupt_task` | `task_id: str, reporter: str, reason: str` | `TaskReport \| None` | Deliver a structured interruption report for an unfinished task. |
| [task_bus.py](task_bus.py#L357) | `TaskBus.wait_for_reports` | `task_ids: Iterable[str], timeout_seconds: float` | `list[TaskReport]` | Wait until every requested task has delivered a structured report. |
| [task_bus.py](task_bus.py#L380) | `TaskBus.get_assignment` | `task_id: str` | `TaskAssignment` | Return one immutable task assignment. |
| [task_bus.py](task_bus.py#L398) | `TaskBus.task_states` | `None` | `dict[str, str]` | Return a point-in-time view of each task lifecycle state. |
| [task_bus.py](task_bus.py#L410) | `TaskBus.to_snapshot` | `None` | `dict[str, Any]` | Return a JSON-compatible, point-in-time copy of TaskBus state. |
| [task_bus.py](task_bus.py#L433) | `TaskBus.from_snapshot` | `snapshot: Mapping[str, Any]` | `'TaskBus'` | Restore a TaskBus from :meth:`to_snapshot` output. |
| [task_bus.py](task_bus.py#L520) | `TaskBus._normalize_items` | `values: Iterable[str]` | `tuple[str, ...]` | Normalize, bound, and freeze a report list field. |
| [task_bus.py](task_bus.py#L534) | `TaskBus._state_for_report_status` | `status: str` | `str` | Map an Agent-supplied report status to a canonical task terminal. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [execution_graph.py](execution_graph.py#L97) | `GraphPersistenceError` | `None` | `ValueError` | Raised when an ExecutionGraph cannot be safely saved or restored. |
| [execution_graph.py](execution_graph.py#L102) | `AgentFailure` | `agent_name: str, error: str, exception: Exception \| None` | `object` | Non-fatal marker placed in :meth:`ExecutionGraph.run` outputs when an Agent raises during execution. |
| [execution_graph.py](execution_graph.py#L128) | `ExecutionGraph` | `max_concurrency_agents: int` | `object` | Directed acyclic graph that schedules dependent agents concurrently. |
| [swarm.py](swarm.py#L26) | `AgentSwarm` | `max_concurrency_agents: int` | `object` | Orchestrate multiple agents through an execution graph. |
| [task_bus.py](task_bus.py#L13) | `TaskAssignment` | `id: str, recipient: str, reply_to: str, objective: str, handoff: str, expected_artifacts: tuple[str, ...], created_at: float, plan_task_id: str` | `object` | Immutable work package delivered to one subagent. |
| [task_bus.py](task_bus.py#L39) | `TaskReport` | `task_id: str, reporter: str, recipient: str, status: str, summary: str, findings: tuple[str, ...], evidence: tuple[str, ...], artifacts: tuple[str, ...], open_questions: tuple[str, ...], recommended_next_action: str, created_at: float` | `object` | Immutable, bounded result package returned to a coordinator inbox. |
| [task_bus.py](task_bus.py#L80) | `TaskBus` | `None` | `object` | Thread-safe task dispatcher and report mailbox for one execution graph. |

<!-- END GENERATED SYMBOL MAP -->
