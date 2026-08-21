"""
AgentSwarm — multi-agent orchestration via dependency-driven execution graph.

Wraps :class:`ExecutionGraph` with a simplified API. See the graph module
for full details on scheduling semantics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from ..agent import Agent, AgentRunControl
from ..events import ExecutionHook
from .execution_graph import (
    AgentResolver,
    CallbackResolver,
    CallbackSerializer,
    ExecutionGraph,
    MapperFn,
    RouterFn,
)
from .task_bus import TaskAssignment, TaskReport


class AgentSwarm:
    """Orchestrate multiple agents through an execution graph.

    Typical usage — sequential pipeline::

        swarm = AgentSwarm(max_concurrency_agents=2)
        swarm.add_agent("researcher", researcher_agent)
        swarm.add_agent("writer", writer_agent)
        swarm.add_connection("researcher", "writer")
        outputs = swarm.run("Explore and report on topic X")

    Fan-out + fan-in::

        swarm = AgentSwarm(max_concurrency_agents=4)
        swarm.add_agent("root", root_agent)
        swarm.add_agent("a", agent_a)
        swarm.add_agent("b", agent_b)
        swarm.add_agent("merge", merge_agent)
        swarm.add_split("root", ["a", "b"])
        swarm.add_gather(["a", "b"], "merge")
        outputs = swarm.run("Analyze from two perspectives")
    """

    def __init__(self, max_concurrency_agents: int = 8) -> None:
        """Create a public facade around an execution graph.

        Args:
            max_concurrency_agents: Maximum concurrent Agent executions.

        Returns:
            None.
        """
        self._graph = ExecutionGraph(
            max_concurrency_agents=max_concurrency_agents,
        )

    # ------------------------------------------------------------------
    # Graph construction  —  agents
    # ------------------------------------------------------------------

    def add_agent(self, agent_name: str, agent_instance: Agent) -> bool:
        """Register an ``Agent`` instance as a graph vertex."""
        return self._graph.add_agent(agent_name, agent_instance)

    def save(
        self,
        path: str | Path,
        *,
        agent_serializer: Callable[[str, Agent], dict[str, Any]] | None = None,
        callback_serializer: CallbackSerializer | None = None,
    ) -> Path:
        """Persist a quiescent Swarm through its execution-graph snapshot.

        Args:
            path: Destination JSON file, replaced atomically by the graph.
            agent_serializer: Application-owned safe Agent blueprint encoder.
            callback_serializer: Optional stable-ID encoder for custom mapper
                or router callbacks; declarative dynamic callbacks need none.

        Returns:
            The written snapshot path.

        Raises:
            GraphPersistenceError: If an Agent or custom callback cannot be
                represented safely.
        """
        return self._graph.save(
            path,
            agent_serializer=agent_serializer,
            callback_serializer=callback_serializer,
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        agent_resolver: AgentResolver | None = None,
        callback_resolver: CallbackResolver | None = None,
    ) -> "AgentSwarm":
        """Restore a quiescent Swarm without exposing its private graph field.

        Args:
            path: Snapshot written by :meth:`save`.
            agent_resolver: Application-owned Agent blueprint decoder.
            callback_resolver: Resolver for any custom mapper/router callback.

        Returns:
            A Swarm with restored topology, task mailbox, and Agent instances.

        Raises:
            GraphPersistenceError: If the snapshot is invalid or requires a
                missing resolver.
        """
        swarm = cls.__new__(cls)
        swarm._graph = ExecutionGraph.load(
            path,
            agent_resolver=agent_resolver,
            callback_resolver=callback_resolver,
        )
        return swarm

    def add_routing_node(self, name: str, router: RouterFn) -> bool:
        """Register a lightweight non-LLM routing node."""
        return self._graph.add_routing_node(name, router)

    def remove_agent(self, agent_name: str) -> bool:
        """Remove a registered agent and every edge connected to it."""
        return self._graph.remove_agent(agent_name)

    # ------------------------------------------------------------------
    # Graph construction  —  edges
    # ------------------------------------------------------------------

    def add_connection(self, source: str, target: str) -> bool:
        """Add a directed dependency edge from *source* to *target*."""
        return self._graph.add_connection(source, target)

    def add_split(self, source: str, targets: list[str]) -> None:
        """Broadcast one agent's output to multiple successors."""
        self._graph.add_split(source, targets)

    def add_gather(
        self,
        sources: list[str],
        target: str,
        mapper: MapperFn | None = None,
    ) -> None:
        """Make *target* depend on and aggregate outputs from *sources*."""
        self._graph.add_gather(sources, target, mapper)

    # ------------------------------------------------------------------
    # Graph construction  —  mappers (node-level)
    # ------------------------------------------------------------------

    def set_mapper(self, agent_name: str, mapper: MapperFn) -> None:
        """Set a node-level mapper that converts predecessor outputs into
        the agent's input message."""
        self._graph.set_mapper(agent_name, mapper)

    # ------------------------------------------------------------------
    # Graph construction  —  routers (dynamic successor selection)
    # ------------------------------------------------------------------

    def set_router(self, agent_name: str, router: RouterFn) -> None:
        """Attach a post-completion router to an existing agent."""
        self._graph.set_router(agent_name, router)

    def remove_router(self, agent_name: str) -> bool:
        """Remove a post-completion router from an agent."""
        return self._graph.remove_router(agent_name)

    # ------------------------------------------------------------------
    # Dynamic mutation  —  thread-safe, usable during run()
    # ------------------------------------------------------------------

    def dynamic_add_agent(
        self, agent_name: str, agent_instance: Agent,
    ) -> str:
        """Dynamically register an ``Agent`` instance during execution."""
        return self._graph.dynamic_add_agent(agent_name, agent_instance)

    def dispatch_task(
        self,
        *,
        agent_name: str,
        agent_instance: Agent,
        objective: str,
        handoff: str,
        reply_to: str,
        expected_artifacts: Iterable[str] = (),
        task_id: str = "",
        plan_task_id: str = "",
    ) -> TaskAssignment:
        """Create and immediately schedule a task-addressed subagent.

        Args:
            agent_name: Unique graph name for the worker.
            agent_instance: Worker configured with task-report tools.
            objective: Concrete task delivered to the worker inbox.
            handoff: Bounded coordinator state relevant to the task.
            reply_to: Coordinator Agent that receives the final report.
            expected_artifacts: Optional detailed-output references expected.
            task_id: Optional stable task identifier.
            plan_task_id: Optional external leaf-plan ID for browser plan
                synchronization. It does not alter graph scheduling.

        Returns:
            Immutable task assignment accepted by the graph task bus.
        """
        return self._graph.dispatch_task(
            agent_name=agent_name,
            agent_instance=agent_instance,
            objective=objective,
            handoff=handoff,
            reply_to=reply_to,
            expected_artifacts=expected_artifacts,
            task_id=task_id,
            plan_task_id=plan_task_id,
        )

    def task_id_for_agent(self, agent_name: str) -> str:
        """Return the latest TaskBus assignment for a dispatched worker.

        Args:
            agent_name: Existing worker graph identity.

        Returns:
            Current assignment ID used when the worker reports completion.
        """
        return self._graph.task_id_for_agent(agent_name)

    def get_agent(self, agent_name: str) -> Agent | None:
        """Return one restored or live Agent without exposing topology maps.

        Args:
            agent_name: Registered graph identity.

        Returns:
            The Agent instance, or ``None`` for unknown/routing-only nodes.
        """
        return self._graph.agent_dict.get(agent_name)

    def dispatched_agent_names(self) -> tuple[str, ...]:
        """Return worker identities that own TaskBus assignments.

        Returns:
            Stable tuple of dispatched worker names, including terminal workers
            intentionally retained for inspection or later revival.
        """
        return tuple(sorted(self._graph._task_by_agent))

    def redispatch_task(
        self,
        *,
        agent_name: str,
        objective: str,
        handoff: str,
        reply_to: str,
        expected_artifacts: Iterable[str] = (),
        task_id: str = "",
        plan_task_id: str = "",
    ) -> TaskAssignment:
        """Reactivate one terminal dispatched worker with a new task record.

        Args:
            agent_name: Existing terminal worker to reuse.
            objective: New concrete task objective.
            handoff: Bounded coordinator state for that task.
            reply_to: Agent receiving the next structured report.
            expected_artifacts: Optional expected detailed outputs.
            task_id: Optional new task identity.
            plan_task_id: Optional external leaf-plan ID for the new work.

        Returns:
            Fresh queued TaskBus assignment; prior assignments remain visible.
        """
        return self._graph.redispatch_task(
            agent_name=agent_name,
            objective=objective,
            handoff=handoff,
            reply_to=reply_to,
            expected_artifacts=expected_artifacts,
            task_id=task_id,
            plan_task_id=plan_task_id,
        )

    def report_task(
        self,
        *,
        task_id: str,
        reporter: str,
        status: str,
        summary: str,
        findings: Iterable[str] = (),
        evidence: Iterable[str] = (),
        artifacts: Iterable[str] = (),
        open_questions: Iterable[str] = (),
        recommended_next_action: str = "",
    ) -> TaskReport:
        """Submit one structured worker report to the assigned coordinator.

        Args:
            task_id: Correlation identifier from the assignment.
            reporter: Reporting worker name.
            status: Terminal task status.
            summary: Bounded conclusion.
            findings: Key claims or observations.
            evidence: Source or evidence references.
            artifacts: Persisted detailed-output references.
            open_questions: Remaining uncertainties.
            recommended_next_action: Suggested follow-up.

        Returns:
            Accepted immutable report.
        """
        return self._graph.report_task(
            task_id=task_id,
            reporter=reporter,
            status=status,
            summary=summary,
            findings=findings,
            evidence=evidence,
            artifacts=artifacts,
            open_questions=open_questions,
            recommended_next_action=recommended_next_action,
        )

    def wait_for_reports(
        self,
        task_ids: Iterable[str],
        timeout_seconds: float,
    ) -> list[TaskReport]:
        """Wait for reports from explicitly dispatched subagent tasks.

        Args:
            task_ids: Task identifiers expected by a coordinator.
            timeout_seconds: Maximum wait duration in seconds.

        Returns:
            Available reports in requested task order.
        """
        return self._graph.wait_for_reports(task_ids, timeout_seconds)

    def dynamic_remove_agent(self, agent_name: str) -> str:
        """Dynamically remove an agent and its edges during execution."""
        return self._graph.dynamic_remove_agent(agent_name)

    def dynamic_add_connection(self, source: str, target: str) -> str:
        """Dynamically add a dependency edge during execution."""
        return self._graph.dynamic_add_connection(source, target)

    def dynamic_remove_connection(self, source: str, target: str) -> str:
        """Dynamically remove a dependency edge during execution."""
        return self._graph.dynamic_remove_connection(source, target)

    def dynamic_set_mapper(self, agent_name: str, mode: str) -> str:
        """Dynamically set a declarative predecessor-output mapper."""
        return self._graph.dynamic_set_mapper(agent_name, mode)

    def dynamic_set_router(self, agent_name: str, targets: list[str]) -> str:
        """Dynamically set a fixed successor router."""
        return self._graph.dynamic_set_router(agent_name, targets)

    def dynamic_get_info(self) -> str:
        """Return current graph state as a structured string."""
        return self._graph.dynamic_get_info()

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def add_hook(self, hook: ExecutionHook) -> None:
        """Register a hook that receives every :class:`ExecutionEvent`.

        The hook is forwarded to the underlying :class:`ExecutionGraph`.
        """
        self._graph.add_hook(hook)

    def view_snapshot(self) -> dict[str, Any]:
        """Return a safe, UI-oriented snapshot of the active graph topology.

        Returns:
            JSON-compatible node, edge, assignment, and task-state data from
            the underlying :class:`ExecutionGraph`.
        """
        return self._graph.view_snapshot()

    def finalize_tasks(self) -> dict[str, str]:
        """Close unfinished dynamic tasks after any terminal run outcome.

        Returns:
            Mapping of changed task identifiers to ``interrupted`` or
            ``cancelled``.

        Side Effects:
            Emits terminal task lifecycle events through registered hooks.
        """
        return self._graph.finalize_tasks()

    def request_shutdown(self) -> None:
        """Stop scheduling further runnable Agents in the active graph.

        Already-running Agents finish their current work according to their
        own cooperative controls.

        Returns:
            None.
        """
        self._graph.request_shutdown()

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def total_usage(self) -> dict[str, int]:
        """Aggregate token usage across every registered Agent.

        Each Agent accumulates its own per-round usage plus internal
        compaction / graph-memory LLM usage in ``Agent.usage`` after
        ``run`` completes. This sums them across the coordinator and all
        (dynamically dispatched) workers.

        Returns:
            Dict with ``input``, ``output``, ``total``, ``cached`` and
            ``reasoning`` keys, all non-negative.
        """
        totals = {"input": 0, "output": 0, "total": 0, "cached": 0, "reasoning": 0}
        with self._graph._topology_lock:
            for agent in self._graph.agent_dict.values():
                if agent is None:
                    continue
                usage = getattr(agent, "usage", None)
                if usage is None:
                    continue
                totals["input"] += usage.input_tokens or 0
                totals["output"] += usage.output_tokens or 0
                totals["total"] += usage.total_tokens or 0
                totals["cached"] += usage.cached_tokens or 0
                totals["reasoning"] += usage.reasoning_tokens or 0
        return totals

    def run(
        self,
        message: str,
        max_rounds: int | None = None,
        control: AgentRunControl | None = None,
    ) -> dict[str, Any]:
        """Execute the graph with an optional cooperative Agent control.

        Args:
            message: Initial input supplied to every root Agent.
            max_rounds: Maximum rounds passed to every Agent; ``0`` means
                unlimited and ``None`` uses each Agent's default.
            control: Optional stop and steering source shared by graph Agents.

        Returns:
            Mapping of agent name to its raw output; a failed agent maps to an
            :class:`AgentFailure` marker (failures do not abort the swarm).

        Side Effects:
            Finalizes every unfinished dynamic assignment before returning or
            propagating a scheduler exception.
        """
        try:
            return self._graph.run(message, max_rounds=max_rounds, control=control)
        finally:
            self._graph.finalize_tasks()
