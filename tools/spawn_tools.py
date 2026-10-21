"""Tool factory: expose swarm graph mutation as Agent-callable tools.

Usage
-----
These tools are given to a **coordinator** agent so it can dynamically spawn
worker agents, wire them into the execution graph, and inspect topology at
runtime::

    from modules.llmfetcher.tools.spawn_tools import create_swarm_tools

    coordinator.add_tools(
        create_swarm_tools(
            swarm=my_swarm,
            llm_fetcher=llm_fetcher,
            worker_tool_pool=global_tools,
        )
    )
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ..agent import Agent
from ..llm_fetcher import LLMFetcher
from ..graph_memory import GraphContextHandler, SemanticGraphWorker
from ..llm_types import Tool, ToolParameter, ToolSchema
from ..swarm_module.swarm import AgentSwarm
from ..swarm_module.task_bus import TaskAssignment, append_subagent_report_instruction


def _text(arguments: Mapping[str, object], key: str, default: str = "") -> str:
    """Return one string argument, treating JSON null as absent."""
    value = arguments.get(key, default)
    if value is None:
        return default
    return value if isinstance(value, str) else str(value)


def _string_list(value: object) -> tuple[str, ...]:
    """Normalize one model-provided scalar or array into string values."""
    if isinstance(value, list):
        return tuple(str(item) for item in cast("list[object]", value))
    return (str(value),) if value else ()


def _artifact_list(value: object) -> tuple[str, ...]:
    """Normalize expected artifact names, rejecting non-array scalars."""
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, list):
        raise ValueError("expected_artifacts must be an array")
    return tuple(str(item) for item in cast("list[object]", value))


def _as_int(value: object, field: str) -> int:
    """Coerce a model-provided integer without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field} must be an integer.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer.") from exc


def _as_float(value: object, field: str) -> float:
    """Coerce a model-provided number without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field} must be a number.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number.") from exc


@dataclass(frozen=True)
class DispatchSpecification:
    """One coordinator request to dispatch a fresh worker."""

    name: str
    system_prompt: str
    objective: str
    handoff: str
    reply_to: str
    expected_artifacts: tuple[str, ...]
    plan_task_id: str

    @classmethod
    def from_arguments(
        cls, arguments: Mapping[str, object], *, default_reply_to: str
    ) -> "DispatchSpecification":
        """Decode one tool call, rejecting missing required fields."""
        name = _text(arguments, "name").strip()
        system_prompt = _text(arguments, "system_prompt").strip()
        objective = _text(arguments, "objective").strip()
        if not name or not system_prompt or not objective:
            raise ValueError("name, system_prompt, and objective are required")
        return cls(
            name=name,
            system_prompt=system_prompt,
            objective=objective,
            handoff=_text(arguments, "handoff").strip(),
            reply_to=(
                _text(arguments, "reply_to", default_reply_to).strip()
                or default_reply_to
            ),
            expected_artifacts=_artifact_list(
                arguments.get("expected_artifacts", [])
            ),
            plan_task_id=_text(arguments, "plan_task_id").strip(),
        )


@dataclass(frozen=True)
class ReviveSpecification:
    """One coordinator request to reuse a terminal worker."""

    name: str
    objective: str
    handoff: str
    reply_to: str
    expected_artifacts: tuple[str, ...]
    plan_task_id: str

    @classmethod
    def from_arguments(
        cls, arguments: Mapping[str, object], *, default_reply_to: str
    ) -> "ReviveSpecification":
        """Decode one revive tool call, rejecting missing required fields."""
        name = _text(arguments, "name").strip()
        objective = _text(arguments, "objective").strip()
        if not name or not objective:
            raise ValueError("name and objective are required")
        return cls(
            name=name,
            objective=objective,
            handoff=_text(arguments, "handoff").strip(),
            reply_to=(
                _text(arguments, "reply_to", default_reply_to).strip()
                or default_reply_to
            ),
            expected_artifacts=_artifact_list(
                arguments.get("expected_artifacts", [])
            ),
            plan_task_id=_text(arguments, "plan_task_id").strip(),
        )


@dataclass(frozen=True)
class TaskReport:
    """One worker's terminal structured report."""

    status: str
    summary: str
    findings: tuple[str, ...]
    evidence: tuple[str, ...]
    artifacts: tuple[str, ...]
    open_questions: tuple[str, ...]
    recommended_next_action: str

    @classmethod
    def from_arguments(cls, arguments: Mapping[str, object]) -> "TaskReport":
        """Decode one report tool call with the documented defaults."""
        return cls(
            status=_text(arguments, "status", "completed") or "completed",
            summary=_text(arguments, "summary"),
            findings=_string_list(arguments.get("findings", [])),
            evidence=_string_list(arguments.get("evidence", [])),
            artifacts=_string_list(arguments.get("artifacts", [])),
            open_questions=_string_list(arguments.get("open_questions", [])),
            recommended_next_action=_text(arguments, "recommended_next_action"),
        )


def create_task_report_tool(
    swarm: AgentSwarm,
    reporter: str,
    on_report: Callable[[], None],
) -> Tool:
    """Build the terminal report tool for one dispatched or restored worker.

    Args:
        swarm: Owning Swarm whose TaskBus resolves the worker's current task.
        reporter: Stable graph identity of the reporting worker.
        on_report: Callback requesting completion after the report is accepted.

    Returns:
        A ``report_task`` tool that always resolves the worker's latest task
        ID, including after an explicit revival or process-restart restore.
    """
    def _report_task(
        status: str = "completed",
        summary: str = "",
        findings: list[str] | None = None,
        evidence: list[str] | None = None,
        artifacts: list[str] | None = None,
        open_questions: list[str] | None = None,
        recommended_next_action: str = "",
    ) -> str:
        """Submit a bounded structured report to the worker's current task."""
        specification = TaskReport(
            status=status or "completed",
            summary=summary,
            findings=tuple(findings or ()),
            evidence=tuple(evidence or ()),
            artifacts=tuple(artifacts or ()),
            open_questions=tuple(open_questions or ()),
            recommended_next_action=recommended_next_action,
        )
        report = swarm.report_task(
            task_id=swarm.task_id_for_agent(reporter),
            reporter=reporter,
            status=specification.status,
            summary=specification.summary,
            findings=list(specification.findings),
            evidence=list(specification.evidence),
            artifacts=list(specification.artifacts),
            open_questions=list(specification.open_questions),
            recommended_next_action=specification.recommended_next_action,
        )
        on_report()
        return f"Report submitted for task {report.task_id} to {report.recipient}."

    return Tool(
        name="report_task",
        description=(
            "Submit the final structured task report. Do not paste raw tool "
            "output or reasoning; reference detailed files in artifacts. "
            "This is terminal: the worker stops after this tool batch."
        ),
        schemas=ToolSchema(properties=[
            ToolParameter(name="status", type="string", enum=["completed", "failed", "partial"], default="completed", description="Terminal task status."),
            ToolParameter(name="summary", type="string", description="Concise conclusion for the coordinator."),
            ToolParameter(name="findings", type="array", description="Key claims or observations."),
            ToolParameter(name="evidence", type="array", description="URLs or concise evidence references."),
            ToolParameter(name="artifacts", type="array", description="Paths or IDs of persisted detailed output."),
            ToolParameter(name="open_questions", type="array", description="Unresolved follow-up questions."),
            ToolParameter(name="recommended_next_action", type="string", description="Suggested coordinator follow-up."),
        ]),
        handler=_report_task,
    )


def create_swarm_tools(
    swarm: AgentSwarm,
    llm_fetcher: LLMFetcher,
    worker_tool_pool: list[Tool],
    worker_tool_factory: Callable[[str], list[Tool]] | None = None,
    worker_tool_binder: Callable[[str, Agent, list[Tool]], list[Tool]] | None = None,
    coordinator_name: str = "main_agent",
    worker_max_rounds: int = 30,
    worker_max_tokens: int = 32768,
    worker_max_context_threshold: int = 262144,
    worker_enable_stop_turn: bool = False,
    worker_default_stream: bool = False,
    context_path_factory: Callable[[str], str | Path | None] | None = None,
    require_plan_task_id: bool = False,
    plan_task_validator: Callable[[str], bool] | None = None,
) -> list[Tool]:
    """Create tools that let a coordinator LLM manipulate the swarm at runtime.

    Args:
        swarm:
            The running swarm instance. The coordinator must be registered
            in this swarm so its tool calls can mutate the graph.
        llm_fetcher:
            Shared ``LLMFetcher`` used to create new worker ``Agent``
            instances.
        worker_tool_pool:
            Tools that are registered on every worker created by the
            coordinator when ``worker_tool_factory`` is not supplied.
        worker_tool_factory:
            Optional callback that receives the new worker name and returns
            its isolated tool collection. When supplied, this takes priority
            over ``worker_tool_pool``. Use it for tools whose handlers close
            over worker-specific state, such as plans or process controls.
        worker_tool_binder:
            Optional post-construction adapter receiving the worker name, live
            ``Agent``, and factory-produced tools. Use it for handlers that
            must flush or reload the newly created Agent's live context.
        coordinator_name:
            Logical coordinator name used as the default structured-report
            recipient for ``dispatch_subagent``.
        worker_max_rounds:
            Default model-and-tool step budget for every worker created by
            these tools.
        worker_max_tokens:
            Default generated-token budget per worker model step.
        worker_max_context_threshold:
            Character count at which every dynamically created worker
            compacts its older conversation history.
        worker_enable_stop_turn:
            Whether dynamically created workers receive the reserved native
            ``stop_turn`` control tool.
        worker_default_stream:
            Whether dynamically created workers emit incremental lifecycle
            events for provider text and reasoning.
        context_path_factory:
            Optional callback returning a durable context path for each
            dynamically created worker Agent.
        require_plan_task_id:
            Require every dispatched or revived assignment to name an external
            plan leaf. Generic library users keep the permissive default.
        plan_task_validator:
            Optional predicate used with ``require_plan_task_id`` to verify a
            caller-supplied external task ID before scheduling work.

    Returns:
        A list of ``Tool`` instances the coordinator can call.

    Raises:
        ValueError: If the worker execution budgets or context threshold are
            outside their supported ranges.
    """
    if worker_max_rounds < 0:
        raise ValueError("worker_max_rounds must be zero or greater")
    if worker_max_tokens <= 0:
        raise ValueError("worker_max_tokens must be greater than zero")
    if worker_max_context_threshold < 1024:
        raise ValueError("worker_max_context_threshold must be at least 1024")

    def _tools_for_worker(name: str) -> list[Tool]:
        """Return the static or freshly built tools for one named worker.

        Args:
            name: Unique identity of the Agent being created.

        Returns:
            A new list of tools. Factory-created tools supersede the shared
            fallback pool so handlers can safely retain worker-local state.
        """
        if worker_tool_factory is not None:
            return list(worker_tool_factory(name))
        return list(worker_tool_pool)

    def _bind_tools_for_worker(name: str, agent: Agent) -> list[Tool]:
        """Bind worker tools after the live Agent exists.

        Args:
            name: Unique worker identity selected by the coordinator.
            agent: Fully constructed worker whose live state may be captured.

        Returns:
            Deterministic tool collection to register on this worker.
        """
        tools = _tools_for_worker(name)
        if worker_tool_binder is not None:
            return list(worker_tool_binder(name, agent, tools))
        return tools

    def _dynamic_add_agent(name: str = "", system_prompt: str = "") -> str:
        """Create and register a new worker agent in the swarm.

        Each new agent receives the configured shared pool or a fresh
        name-specific tool collection, plus a customized system *prompt*.

        Required parameters: ``name`` (unique agent name), ``system_prompt``.
        """
        name = name.strip()
        system_prompt = system_prompt.strip()

        if not name or not system_prompt:
            return "Error: both 'name' and 'system_prompt' are required."

        agent = Agent(
            llm_fetcher=llm_fetcher,
            system_prompt=system_prompt,
            max_context_threshold=worker_max_context_threshold,
            context_path=context_path_factory(name) if context_path_factory else None,
            default_max_rounds=worker_max_rounds,
            default_max_tokens=worker_max_tokens,
            enable_stop_turn=worker_enable_stop_turn,
            default_stream=worker_default_stream,
            # Graph long-term memory for the dynamically created worker,
            # persisted as ``<context_path>.graph.json`` when a path exists.
            context_handler=GraphContextHandler(
                compacting_fetcher=llm_fetcher,
                extraction_fetcher=SemanticGraphWorker(llm_fetcher),
                query_fetcher=SemanticGraphWorker(llm_fetcher),
                max_context_threshold=worker_max_context_threshold,
            ),
            context_providers=(),
        )
        agent.add_tools(_bind_tools_for_worker(name, agent))

        return swarm.dynamic_add_agent(name, agent)

    def _dispatch_subagent(
        name: str = "", system_prompt: str = "", objective: str = "",
        handoff: str = "", reply_to: str = "", expected_artifacts: list[str] | None = None,
        plan_task_id: str = "",
    ) -> str:
        """Create, task, and immediately schedule one independent worker.

        Args:
            **kwargs: Worker identity, system prompt, objective, handoff, and
                optional report-recipient fields supplied by the coordinator.

        Returns:
            Task identifier and worker name for a later ``wait_for_reports`` call.
        """
        try:
            specification = DispatchSpecification(
                name=name.strip(), system_prompt=system_prompt.strip(), objective=objective.strip(),
                handoff=handoff.strip(), reply_to=reply_to.strip() or coordinator_name,
                expected_artifacts=tuple(expected_artifacts or ()), plan_task_id=plan_task_id.strip(),
            )
            if not specification.name or not specification.system_prompt or not specification.objective:
                raise ValueError("name, system_prompt, and objective are required")
            assignment = _create_assignment(specification)
        except ValueError as exc:
            return f"Error: {exc}"
        return (
            f"Dispatched {assignment.recipient} with task_id={assignment.id}. "
            "Call wait_for_reports with this task_id before synthesizing results."
        )

    def _create_assignment(specification: DispatchSpecification) -> TaskAssignment:
        """Create one worker and its explicit task assignment from a tool spec.

        Args:
            specification: Validated worker name, prompt, objective, handoff,
                report recipient, and artifact expectations.

        Returns:
            Accepted task assignment from the shared swarm task bus.

        Raises:
            ValueError: If the plan task is required but missing, or the graph
                rejects the requested worker identity.
        """
        if require_plan_task_id and not specification.plan_task_id:
            raise ValueError("plan_task_id is required for dispatched work")
        if (
            specification.plan_task_id
            and plan_task_validator is not None
            and not plan_task_validator(specification.plan_task_id)
        ):
            raise ValueError("plan_task_id must identify an existing leaf task")
        task_id = uuid.uuid4().hex
        worker_prompt = append_subagent_report_instruction(specification.system_prompt)
        worker = Agent(
            llm_fetcher=llm_fetcher,
            system_prompt=worker_prompt,
            max_context_threshold=worker_max_context_threshold,
            context_path=(
                context_path_factory(specification.name)
                if context_path_factory
                else None
            ),
            default_max_rounds=worker_max_rounds,
            default_max_tokens=worker_max_tokens,
            enable_stop_turn=worker_enable_stop_turn,
            default_stream=worker_default_stream,
            # Graph long-term memory for the dispatched worker.
            context_handler=GraphContextHandler(
                compacting_fetcher=llm_fetcher,
                extraction_fetcher=SemanticGraphWorker(llm_fetcher),
                query_fetcher=SemanticGraphWorker(llm_fetcher),
                max_context_threshold=worker_max_context_threshold,
            ),
            context_providers=(),
        )
        worker.add_tools(_bind_tools_for_worker(specification.name, worker) + [
            create_task_report_tool(
                swarm, specification.name, worker.request_completion
            ),
        ])
        return swarm.dispatch_task(
            agent_name=specification.name,
            agent_instance=worker,
            objective=specification.objective,
            handoff=specification.handoff,
            reply_to=specification.reply_to,
            expected_artifacts=list(specification.expected_artifacts),
            task_id=task_id,
            plan_task_id=specification.plan_task_id,
        )

    def _dispatch_subagents(assignments: list[Mapping[str, object]] | None = None, expected_count: int = 0) -> str:
        """Dispatch a complete independent worker group in one tool call.

        Args:
            **kwargs: ``assignments`` array containing one task specification
                per worker, plus an optional expected worker count.

        Returns:
            JSON containing every worker name and task ID for one subsequent
            ``wait_for_reports`` call.
        """
        raw_specifications = assignments or []
        try:
            expected_count = _as_int(
                expected_count, "expected_count"
            )
        except ValueError as exc:
            return f"Error: {exc}"
        if not isinstance(raw_specifications, list) or not raw_specifications:
            return "Error: assignments must be a non-empty array."
        specifications_value = cast("list[object]", raw_specifications)
        if expected_count and len(specifications_value) != expected_count:
            return f"Error: expected exactly {expected_count} assignments."
        specifications: list[DispatchSpecification] = []
        for item in specifications_value:
            if not isinstance(item, dict):
                return "Error: every assignment must be an object."
            try:
                specifications.append(
                    DispatchSpecification.from_arguments(
                        cast("Mapping[str, object]", item),
                        default_reply_to=coordinator_name,
                    )
                )
            except ValueError as exc:
                return f"Error: {exc}"
        names = [specification.name for specification in specifications]
        if len(names) != len(set(names)):
            return "Error: every assignment needs a unique non-empty name."
        try:
            assignments = [
                _create_assignment(specification)
                for specification in specifications
            ]
        except ValueError as exc:
            return f"Error: {exc}"
        return json.dumps(
            {
                "tasks": [
                    {"agent_name": assignment.recipient, "task_id": assignment.id}
                    for assignment in assignments
                ],
            },
            ensure_ascii=False,
        )

    def _revive_agent(
        name: str = "", objective: str = "", handoff: str = "", reply_to: str = "",
        expected_artifacts: list[str] | None = None, plan_task_id: str = "",
    ) -> str:
        """Queue a fresh task for an existing terminal dispatched worker.

        Args:
            **kwargs: Worker name, new objective/handoff, report recipient,
                and expected artifacts supplied by the coordinator.

        Returns:
            New task ID on success, or a safe validation message on failure.
        """
        try:
            specification = ReviveSpecification(
                name=name.strip(), objective=objective.strip(), handoff=handoff.strip(),
                reply_to=reply_to.strip() or coordinator_name,
                expected_artifacts=tuple(expected_artifacts or ()), plan_task_id=plan_task_id.strip(),
            )
            if not specification.name or not specification.objective:
                raise ValueError("name and objective are required")
        except ValueError as exc:
            return f"Error: {exc}"
        if require_plan_task_id and not specification.plan_task_id:
            return "Error: plan_task_id is required for revived work."
        if (
            specification.plan_task_id
            and plan_task_validator is not None
            and not plan_task_validator(specification.plan_task_id)
        ):
            return "Error: plan_task_id must identify an existing leaf task."
        try:
            assignment = swarm.redispatch_task(
                agent_name=specification.name,
                objective=specification.objective,
                handoff=specification.handoff,
                reply_to=specification.reply_to,
                expected_artifacts=list(specification.expected_artifacts),
                plan_task_id=specification.plan_task_id,
            )
        except (KeyError, ValueError) as exc:
            return f"Error: {exc}"
        return (
            f"Revived {assignment.recipient} with task_id={assignment.id}. "
            "Wait for its new report with wait_for_reports."
        )

    def _wait_for_reports(task_ids: list[str] | str | None = None, timeout_seconds: float = 120.0) -> str:
        """Wait for selected worker reports and return their bounded JSON form.

        Args:
            **kwargs: Task ID list and bounded timeout supplied by coordinator.

        Returns:
            JSON object containing received structured reports only.
        """
        raw_task_ids = task_ids or []
        if isinstance(raw_task_ids, str):
            task_ids = [raw_task_ids]
        elif isinstance(raw_task_ids, list):
            task_ids = [
                str(item) for item in cast("list[object]", raw_task_ids)
            ]
        else:
            task_ids = []
        try:
            timeout_seconds = _as_float(
                timeout_seconds, "timeout_seconds"
            )
        except ValueError as exc:
            return f"Error: {exc}"
        timeout_seconds = max(1.0, min(timeout_seconds, 900.0))
        reports = swarm.wait_for_reports(task_ids, timeout_seconds)
        return json.dumps(
            {"requested_task_ids": task_ids, "reports": [report.as_dict() for report in reports]},
            ensure_ascii=False,
        )

    def _dynamic_add_connection(source: str = "", target: str = "") -> str:
        """Add a directed dependency edge between two agents.

        After this call, *target* waits for *source* to complete before
        it may execute.  The source must not have finished yet.

        Required: ``source``, ``target``.
        """
        source = source.strip()
        target = target.strip()

        if not source or not target:
            return "Error: both 'source' and 'target' are required."

        return swarm.dynamic_add_connection(source, target)

    def _dynamic_remove_agent(name: str = "") -> str:
        """Remove an agent and every edge connected to it."""
        name = name.strip()
        if not name:
            return "Error: 'name' is required."
        return swarm.dynamic_remove_agent(name)

    def _dynamic_remove_connection(source: str = "", target: str = "") -> str:
        """Remove a dependency edge from the editable graph."""
        source = source.strip()
        target = target.strip()
        if not source or not target:
            return "Error: both 'source' and 'target' are required."
        return swarm.dynamic_remove_connection(source, target)

    def _dynamic_set_mapper(agent_name: str = "", mode: str = "labelled") -> str:
        """Set a declarative fan-in mapper on a target Agent."""
        agent_name = agent_name.strip()
        mode = mode.strip() or "labelled"
        if not agent_name:
            return "Error: 'agent_name' is required."
        return swarm.dynamic_set_mapper(agent_name, mode)

    def _dynamic_set_router(agent_name: str = "", targets: list[str] | str | None = None) -> str:
        """Set a fixed successor subset for a source Agent."""
        agent_name = agent_name.strip()
        raw_targets = targets or []
        if isinstance(raw_targets, str):
            raw_targets = [raw_targets]
        targets = (
            [str(target) for target in cast("list[object]", raw_targets)]
            if isinstance(raw_targets, list)
            else []
        )
        if not agent_name:
            return "Error: 'agent_name' is required."
        return swarm.dynamic_set_router(agent_name, targets)

    def _dynamic_get_info() -> str:
        """Return the current graph topology as structured text.

        Useful for inspecting which agents are registered and how they
        are connected before deciding on next steps.
        """
        return swarm.dynamic_get_info()

    return [
        Tool(
            name="dispatch_subagents",
            description=(
                "Dispatch a complete group of independent workers in one call. "
                "Use this for a fixed task list, then pass every returned task "
                "ID to wait_for_reports. Do not wait after dispatching only one worker."
            ),
            schemas=ToolSchema(properties=[
                ToolParameter(name="assignments", type="array", description="Worker task objects: name, system_prompt, objective, handoff, reply_to, expected_artifacts, and optional plan_task_id for a coordinator-plan leaf."),
                ToolParameter(name="expected_count", type="integer", default=0, description="Exact required worker count; use it to prevent partial groups."),
            ]),
            handler=_dispatch_subagents,
        ),
        Tool(
            name="dispatch_subagent",
            description=(
                "Dispatch an independent subagent with an explicit objective and "
                "bounded handoff. It runs immediately and returns only a structured "
                "report through wait_for_reports; do not add a dependency edge."
            ),
            schemas=ToolSchema(properties=[
                ToolParameter(name="name", type="string", description="Unique worker name."),
                ToolParameter(name="system_prompt", type="string", description="Worker role and quality constraints."),
                ToolParameter(name="objective", type="string", description="Concrete task assigned only to this worker."),
                ToolParameter(name="handoff", type="string", description="Compact coordinator state relevant to the task."),
                ToolParameter(name="reply_to", type="string", default=coordinator_name, description="Coordinator receiving the structured report."),
                ToolParameter(name="expected_artifacts", type="array", description="Expected detailed-output paths or names."),
                ToolParameter(name="plan_task_id", type="string", description="Optional coordinator-plan leaf task ID to synchronize with this assignment."),
            ]),
            handler=_dispatch_subagent,
        ),
        Tool(
            name="revive_agent",
            description=(
                "Reuse an existing terminal dispatched worker with a fresh task ID, "
                "objective, and handoff. Its Agent instance, tools, and persisted "
                "context are retained; its earlier task report remains immutable."
            ),
            schemas=ToolSchema(properties=[
                ToolParameter(name="name", type="string", description="Existing terminal worker name to reactivate."),
                ToolParameter(name="objective", type="string", description="New concrete task assigned to that worker."),
                ToolParameter(name="handoff", type="string", description="Bounded coordinator context for the revived task."),
                ToolParameter(name="reply_to", type="string", default=coordinator_name, description="Agent that receives the new structured report."),
                ToolParameter(name="expected_artifacts", type="array", description="Expected detailed-output paths or names."),
                ToolParameter(name="plan_task_id", type="string", description="Optional coordinator-plan leaf task ID to synchronize with this revived assignment."),
            ]),
            handler=_revive_agent,
        ),
        Tool(
            name="wait_for_reports",
            description=(
                "Wait for structured reports from dispatched task IDs. Use this "
                "instead of inspecting subagent raw run output."
            ),
            schemas=ToolSchema(properties=[
                ToolParameter(name="task_ids", type="array", description="Task IDs returned by dispatch_subagent."),
                ToolParameter(name="timeout_seconds", type="number", default=120, description="Maximum wait duration in seconds."),
            ]),
            handler=_wait_for_reports,
        ),
        Tool(
            name="dynamic_add_agent",
            description=(
                "Create and register a new worker agent in the execution graph. "
                "The new agent will receive the shared worker tools (web fetch, "
                "KB read/write, clock).  After creation, connect it to the graph "
                "with dynamic_add_connection."
            ),
            schemas=ToolSchema(
                properties=[
                    ToolParameter(
                        name="name",
                        type="string",
                        description="Unique name for the new agent (e.g. 'worker_mexico'). Must not conflict with existing names.",
                    ),
                    ToolParameter(
                        name="system_prompt",
                        type="string",
                        description="Full system prompt for the new worker agent.",
                    ),
                ],
            ),
            handler=_dynamic_add_agent,
        ),
        Tool(
            name="dynamic_add_connection",
            description=(
                "Add a dependency edge from source to target. "
                "The target agent will not execute until the source has completed. "
                "Connect workers to the coordinator AFTER creating them, so they "
                "run when the coordinator finishes."
            ),
            schemas=ToolSchema(
                properties=[
                    ToolParameter(
                        name="source",
                        type="string",
                        description="Name of the predecessor agent (e.g. 'coordinator').",
                    ),
                    ToolParameter(
                        name="target",
                        type="string",
                        description="Name of the successor agent (e.g. 'worker_mexico').",
                    ),
                ],
            ),
            handler=_dynamic_add_connection,
        ),
        Tool(
            name="dynamic_remove_agent",
            description=(
                "Remove an agent and every edge connected to it from the graph. "
                "Useful to clean up failed or misconfigured workers."
            ),
            schemas=ToolSchema(
                properties=[
                    ToolParameter(
                        name="name",
                        type="string",
                        description="Name of the agent to remove.",
                    ),
                ],
            ),
            handler=_dynamic_remove_agent,
        ),
        Tool(
            name="dynamic_remove_connection",
            description="Remove an existing dependency edge before the graph source completes.",
            schemas=ToolSchema(properties=[
                ToolParameter(name="source", type="string", description="Predecessor Agent name."),
                ToolParameter(name="target", type="string", description="Successor Agent name."),
            ]),
            handler=_dynamic_remove_connection,
        ),
        Tool(
            name="dynamic_set_mapper",
            description=(
                "Configure how a fan-in Agent receives predecessor outputs. "
                "Use labelled for readable evidence, concat for plain text, or json for structured aggregation."
            ),
            schemas=ToolSchema(properties=[
                ToolParameter(name="agent_name", type="string", description="Target Agent receiving gathered outputs."),
                ToolParameter(name="mode", type="string", enum=["labelled", "concat", "json"], default="labelled", description="Declarative aggregation mode."),
            ]),
            handler=_dynamic_set_mapper,
        ),
        Tool(
            name="dynamic_set_router",
            description="Configure a source Agent to activate only the listed successor Agents after completion.",
            schemas=ToolSchema(properties=[
                ToolParameter(name="agent_name", type="string", description="Source Agent name."),
                ToolParameter(name="targets", type="array", description="Successor Agent names to activate."),
            ]),
            handler=_dynamic_set_router,
        ),
        Tool(
            name="dynamic_get_info",
            description=(
                "Inspect the current execution graph: list registered agents, "
                "their connections, and concurrency limits. Useful before "
                "creating or removing workers."
            ),
            schemas=ToolSchema(properties=[]),
            handler=_dynamic_get_info,
        ),
    ]
