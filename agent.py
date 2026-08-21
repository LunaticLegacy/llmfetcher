from __future__ import annotations

import threading
import time
import queue
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Any, Optional, Dict, Protocol
from pathlib import Path

from .llm_fetcher import LLMBackendConfig, LLMFetcher, LLMBackendHandler
from .llm_types import Tool, ToolParameter, ToolSchema, LLMOutput, LLMToolCall, TokenUsage
from .tool_handler import ToolHandler
from .tool_executor import ToolExecutor
from .context_handlers import ContextHandlerLinear, ContextHandler
from .events import ExecutionEvent, ExecutionHook
from .usage_ledger import UsageRecord, add_usage, copy_usage


class AgentRunControl(Protocol):
    """Describe cooperative controls read between completed Agent steps.

    Implementations may persist requests in a database or keep them in an
    application-specific queue. Methods are deliberately only called after a
    model response and its tool batch have completed.
    """

    def should_stop(self) -> bool:
        """Return whether the Agent should stop at the current safe boundary."""
        ...

    def drain_steers(self) -> list[str]:
        """Return and consume queued user steering messages in FIFO order."""
        ...


class AgentRunStopped(RuntimeError):
    """Signal a cooperative stop after durable completion of one Agent step.

    Args:
        message: Human-readable reason for ending the current run.
        last_output: Model result from the completed boundary. It is ``None``
            only when no model round completed before the stop was observed.

    The exception is raised only after the latest assistant message has been
    added to the context and that context has been saved. Browser callers use
    ``last_output`` to persist the matching display transcript.
    """

    def __init__(self, message: str, *, last_output: LLMOutput | None = None) -> None:
        super().__init__(message)
        self.last_output = last_output


class AgentRunLimitReached(RuntimeError):
    """Signal that an Agent exhausted its round budget before a terminal result.

    The last response requested tools, so returning it as a user-facing answer
    would silently discard the required next model step.
    """


class AgentRunTermination(str, Enum):
    """Explicit terminal classifications for one completed Agent invocation."""

    FINAL_RESPONSE = "final_response"
    STOP_TURN = "stop_turn"
    WORKFLOW_COMPLETION = "workflow_completion"
    USER_STOPPED = "user_stopped"
    EMPTY_RESPONSE = "empty_response"
    ROUND_LIMIT = "round_limit"


@dataclass(frozen=True)
class AgentRunOutcome:
    """Inspectable terminal state for an Agent run.

    Args:
        termination: Explicit reason the run stopped progressing.
        rounds: Number of completed model rounds.
        detail: Optional model- or control-provided terminal explanation.
        output: Last completed model response, if one exists.

    ``output`` is retained in-process for hosts that need the exact response;
    lifecycle events use :meth:`to_dict` and therefore never serialize it.
    """

    termination: AgentRunTermination
    rounds: int
    detail: str = ""
    output: LLMOutput | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the credential-free terminal fields for lifecycle events."""
        return {
            "termination": self.termination.value,
            "rounds": self.rounds,
            "detail": self.detail,
            "has_output": self.output is not None,
        }


def _tool_result_text(value: Any) -> str:
    """Return the complete tool-result string supplied back to the model.

    Args:
        value: Raw value returned by a tool handler.
    Returns:
        Complete string form of ``value`` without a display or persistence limit.

    Notes:
        This model-facing conversion is intentionally separate from lifecycle
        events, which retain their raw value so JSON results reach the UI as
        structured data rather than Python's escaped representation.
    """
    return str(value)


class Agent:
    def __init__(
        self,
        llm_fetcher: LLMFetcher,
        *,
        system_prompt: str,
        max_concurrency: int = 3,
        max_context_threshold: int = 262144,
        context_path: Optional[str | Path] = "",
        context_handler: Optional[ContextHandler] = None,
        default_max_rounds: int = 30,
        default_max_tokens: int = 32768,
        enable_stop_turn: bool = False,
        default_stream: bool = False,
    ):
        """Initialize one tool-using Agent.

        Args:
            llm_fetcher: Backend dispatcher used for model rounds.
            system_prompt: Instructions supplied to the model.
            max_concurrency: Maximum concurrent tool handlers.
            max_context_threshold: Context size at which compaction starts.
            context_path: Optional persisted context file path.
            context_handler: Optional custom context implementation, such as
                ``RetrievedContextHandler``.
            default_max_rounds: Default maximum model-and-tool steps for a
                ``run`` call that omits ``max_rounds``. ``0`` means unlimited.
            default_max_tokens: Default maximum generated tokens per model
                step for a ``run`` call that omits ``max_tokens``.
            enable_stop_turn: Whether to register the reserved native
                ``stop_turn`` control tool. Hosts enable it when their user
                workflow needs a model-visible non-text terminal boundary.
            default_stream: Whether calls omitting ``stream`` should emit
                incremental lifecycle events while preserving final results.

        Returns:
            None.

        Raises:
            ValueError: If either default execution budget is negative or the
                token budget is not positive.
        """
        if default_max_rounds < 0:
            raise ValueError("default_max_rounds must be zero or greater")
        if default_max_tokens <= 0:
            raise ValueError("default_max_tokens must be greater than zero")
        self.llm_fetcher = llm_fetcher
        self.system_prompt = system_prompt
        self.max_concurrency = max_concurrency
        self.max_context_threshold = max_context_threshold
        self.context_path = Path(context_path) if context_path else None
        self.default_max_rounds = default_max_rounds
        self.default_max_tokens = default_max_tokens
        self.default_stream = default_stream

        self.tool_handler: ToolHandler = ToolHandler()
        self.tool_executor: ToolExecutor = ToolExecutor(
            max_concurrency=self.max_concurrency,
        )
        self.context_handler: ContextHandler = context_handler or ContextHandlerLinear(
            compacting_llmfetcher_handler=self.llm_fetcher,
            max_context_threshold=self.max_context_threshold,
        )

        # This attribute will be assigned by ExecutionGraph so Agent-level events retain their node.
        self._agent_name_in_graph: str = ""

        # Cumulative token usage across all rounds of the most recent run.
        self.usage: TokenUsage = TokenUsage()

        # hook system
        self.hooks: list[ExecutionHook] = []

        # Terminal workflow tools request this event after persisting their
        # result. ``run`` observes it only at a complete step boundary.
        self._completion_requested = threading.Event()
        self._stop_turn_requested = threading.Event()
        self._stop_turn_reason = ""
        self._termination_lock = threading.Lock()
        self.last_outcome: AgentRunOutcome | None = None

        if enable_stop_turn:
            # This reserved tool is a control signal, not a business
            # capability. It travels through the native tool channel and
            # never enters system text.
            self.add_stop_turn_tool()

    # -- hooks ----------------------------------------------------------

    def add_hook(self, hook: ExecutionHook) -> None:
        """Register an execution-event receiver.

        Args:
            hook: Callback invoked synchronously for each agent event.

        Returns:
            None.
        """
        self.hooks.append(hook)

    def remove_hook(self, hook: ExecutionHook) -> bool:
        """Unregister one execution-event receiver.

        Args:
            hook: Previously registered callback.

        Returns:
            ``True`` when the callback was removed, otherwise ``False``.
        """
        try:
            self.hooks.remove(hook)
        except ValueError:
            return False
        return True

    def request_completion(self) -> None:
        """Request completion after the active model-and-tool step finishes.

        Terminal workflow tools, such as a dispatched worker's
        ``report_task``, call this method after writing their durable result.
        The request never interrupts model inference or a parallel tool batch;
        ``run`` observes it only after that complete step is stored.

        Returns:
            None.
        """
        self._completion_requested.set()

    def request_turn_stop(self, reason: str = "") -> None:
        """Request a normal boundary from the reserved ``stop_turn`` tool.

        Args:
            reason: Optional model-provided explanation retained in the
                outcome and lifecycle event, not as a final user answer.

        Side Effects:
            Marks the current model-and-tool batch terminal. The Agent waits
            for every concurrently requested tool to finish first.
        """
        with self._termination_lock:
            self._stop_turn_reason = reason.strip()
        self._stop_turn_requested.set()

    def add_stop_turn_tool(self) -> bool:
        """Register the reserved model-visible control tool for ending a turn.

        Returns:
            ``True`` when ``stop_turn`` was newly registered. ``False`` means
            this Agent already has a tool with that reserved name.
        """
        return self.add_tool(self._create_stop_turn_tool())

    def _create_stop_turn_tool(self) -> Tool:
        """Create the reserved model-visible control tool for ending a turn.

        Returns:
            A native ``stop_turn`` tool. Its handler records a request and
            :meth:`run` applies the result at the completed batch boundary.
        """
        def stop_turn(reason: str = "") -> str:
            """Record a requested turn stop without interrupting sibling tools."""
            self.request_turn_stop(reason)
            return "Turn completion requested."

        return Tool(
            name="stop_turn",
            description=(
                "End the current Agent turn after this complete tool batch. "
                "Use only when no final user-facing answer should be emitted."
            ),
            schemas=ToolSchema(properties=[
                ToolParameter(
                    name="reason",
                    required=False,
                    description="Optional concise reason for ending this turn.",
                ),
            ]),
            handler=stop_turn,
        )

    def _set_outcome(
        self,
        termination: AgentRunTermination,
        rounds: int,
        *,
        detail: str = "",
        output: LLMOutput | None = None,
    ) -> AgentRunOutcome:
        """Record and publish the single explicit terminal result of this run.

        Args:
            termination: Classification selected at a safe Agent boundary.
            rounds: Number of model rounds completed before the boundary.
            detail: Optional concise explanation of that boundary.
            output: Last completed model response, if available.

        Returns:
            The stored outcome for in-process hosts.
        """
        outcome = AgentRunOutcome(termination, rounds, detail, output)
        self.last_outcome = outcome
        self._emit(
            "agent", self._agent_name_in_graph, "agent:termination",
            f"Terminated as {termination.value}", data=outcome.to_dict(),
        )
        return outcome

    def set_context_threshold(
        self,
        max_context_threshold: int,
        *,
        persist: bool = False,
    ) -> bool:
        """Update the compaction threshold used by this Agent's context.

        Args:
            max_context_threshold: Character count that triggers context
                compaction. It must be at least ``1024``.
            persist: Whether to immediately save the updated handler at
                ``context_path`` so a following :meth:`run` load observes the
                new value.

        Returns:
            ``True`` when the active handler exposes a mutable compression
            threshold and, when requested, saving succeeds. ``False`` means a
            custom handler does not support threshold synchronization or its
            persistence failed.

        Raises:
            ValueError: If ``max_context_threshold`` is below ``1024``.

        Side Effects:
            Updates ``self.max_context_threshold``. Graph context handlers are
            synchronized through their embedded linear handler.
        """
        if max_context_threshold < 1024:
            raise ValueError("max_context_threshold must be at least 1024")
        self.max_context_threshold = max_context_threshold
        handler = self.context_handler
        linear = getattr(handler, "linear", handler)
        if not hasattr(linear, "compress_threshold"):
            return False
        linear.compress_threshold = max_context_threshold
        if persist and self.context_path is not None:
            return bool(handler.save(self.context_path))
        return True

    def _emit(
        self,
        source: str,
        agent_name: str,
        event_type: str,
        message: str = "",
        data: Any = None,
    ) -> None:
        """Send one event to each registered hook, isolating hook failures.

        Args:
            source: Event source identifier.
            agent_name: Stable graph name of the emitting Agent.
            event_type: Machine-readable lifecycle event name.
            message: Human-readable event description.
            data: Optional structured event payload.

        Returns:
            None.
        """
        event = ExecutionEvent(
            source=source,
            agent_name=agent_name,
            event_type=event_type,
            message=message,
            data=data,
        )
        for hook in self.hooks:
            try:
                hook(event)
            except Exception:
                pass

    @staticmethod
    def _usage_data(usage: TokenUsage) -> dict[str, int]:
        """Serialize every normalized usage dimension for durable events."""
        return {
            "input": usage.input_tokens or 0,
            "output": usage.output_tokens or 0,
            "total": usage.total_tokens or 0,
            "cached": usage.cached_tokens or 0,
            "reasoning": usage.reasoning_tokens or 0,
        }

    def _drain_internal_usage(self, name: str) -> None:
        """Publish and aggregate each hidden LLM call once, if supported."""
        drain = getattr(self.context_handler, "drain_usage_records", None)
        if drain is None:
            return
        for record in drain():
            if not isinstance(record, UsageRecord):
                continue
            add_usage(self.usage, record.usage)
            self._emit(
                "agent", name, "agent:internal_usage",
                f"Internal {record.kind} LLM call",
                data={"kind": record.kind, "usage": self._usage_data(record.usage)},
            )

    # -- tool registration ----------------------------------------------

    def add_tool(self, tool: Tool) -> bool:
        """Register one callable tool on this Agent.

        Args:
            tool: Tool schema and handler exposed to the model.

        Returns:
            ``True`` when registration succeeds, otherwise ``False``.
        """
        return self.tool_handler.add_tool(tool=tool)

    def add_tools(self, tools: List[Tool]) -> bool:
        """Register a batch of tools in the supplied order.

        Args:
            tools: Tool definitions to register.

        Returns:
            ``True`` only when every registration succeeds.
        """
        results: List[bool] = [False for _ in range(len(tools))]
        for idx, tool in enumerate(tools):
            results[idx] = self.add_tool(tool=tool)

        out = True
        for r in results:
            out *= r
        return bool(out)

    # -- internal --------------------------------------------------------

    def _build_prompt(self) -> str:
        """Return the system prompt without serializing registered tools into it.

        Tool definitions travel only through ``LLMFetcher.fetch(..., tools=)``.
        The provider handler converts that collection to its native wire schema.
        Keeping the textual ``Tool.__str__`` fallback out of this message avoids
        sending the same schemas both in ``messages`` and in the provider's
        top-level ``tools`` field.

        Returns:
            Exact system-role instruction text for the next model request.
        """
        return self.system_prompt

    def _save_context(self) -> bool:
        """Persist the current context when this Agent has a storage path.

        Returns:
            ``True`` when a configured context was saved successfully;
            ``False`` when persistence is disabled or the handler reports a
            write failure.

        This helper is called for both ordinary completion and cooperative
        stops so a completed model-and-tool boundary is never lost merely
        because execution will not enter another round.
        """
        if self.context_path is None:
            return False
        return self.context_handler.save(self.context_path)

    def _fetch_model_with_force_stop(
        self,
        *,
        control: AgentRunControl | None,
        **fetch_kwargs: Any,
    ) -> LLMOutput:
        """Fetch one model response, allowing a terminal browser force-stop.

        Args:
            control: Optional cooperative controller.  A controller may also
                expose a ``force_stopped`` ``threading.Event`` for immediate
                cancellation; that optional extension is intentionally not
                required for library-only controllers.
            **fetch_kwargs: Keyword arguments forwarded unchanged to
                ``LLMFetcher.fetch``.

        Returns:
            The completed normalized model response.

        Raises:
            AgentRunStopped: If ``force_stopped`` is set before the provider
                call completes.  No incomplete model response is persisted.
            Exception: Any provider exception raised by ``LLMFetcher.fetch``.

        Side Effects:
            Uses a daemon worker while a force-stop event is available.  On a
            force-stop it asks the fetcher to close provider transports before
            ending the Agent thread; the worker cannot mutate Agent context.
        """
        force_event = getattr(control, "force_stopped", None)
        if force_event is None:
            return self.llm_fetcher.fetch(**fetch_kwargs)

        result_queue: queue.Queue[tuple[bool, LLMOutput | BaseException]] = queue.Queue(maxsize=1)

        def fetch_in_background() -> None:
            """Keep blocking provider I/O isolated from the Agent worker."""
            try:
                result_queue.put((True, self.llm_fetcher.fetch(**fetch_kwargs)))
            except BaseException as exc:
                result_queue.put((False, exc))

        threading.Thread(
            target=fetch_in_background,
            name="llmfetcher-model-request",
            daemon=True,
        ).start()
        while True:
            if force_event.wait(timeout=0.05):
                # Closing SDK transports interrupts providers such as OpenAI
                # and Anthropic.  Regardless of SDK support, do not let the
                # detached request resume this terminal Agent invocation.
                abort_requests = getattr(self.llm_fetcher, "abort_active_requests", None)
                if callable(abort_requests):
                    abort_requests()
                raise AgentRunStopped("Agent force-stopped during model request")
            try:
                completed, value = result_queue.get_nowait()
            except queue.Empty:
                continue
            if completed:
                return value  # type: ignore[return-value]
            raise value  # type: ignore[misc]

    def _stream_model_response(
        self,
        *,
        name: str,
        round_idx: int,
        control: AgentRunControl | None,
        **fetch_kwargs: Any,
    ) -> LLMOutput:
        """Stream one provider response, emit deltas, and rebuild its final form.

        Args:
            name: Stable emitting Agent identity.
            round_idx: Current model round for SSE correlation.
            control: Optional control whose force-stop event is checked between
                received chunks.
            **fetch_kwargs: Arguments forwarded to ``LLMFetcher.fetch_stream``.

        Returns:
            A complete backend-neutral output suitable for the normal tool and
            context pipeline.
        """
        content: list[str] = []
        reasoning: list[str] = []
        calls: list[LLMToolCall] = []
        channel = "content"
        tool_payload: list[str] = []
        force_event = getattr(control, "force_stopped", None)
        backend = self.llm_fetcher.default_backend_config
        # The fetcher fills this per-call accumulator with the provider's
        # streamed usage so streamed rounds carry the same token accounting
        # as non-streamed rounds (agent:usage ledger, round_usage, totals).
        stream_usage = TokenUsage()

        for chunk in self.llm_fetcher.fetch_stream(
            usage_sink=stream_usage, **fetch_kwargs
        ):
            if force_event is not None and force_event.is_set():
                abort = getattr(self.llm_fetcher, "abort_active_requests", None)
                if callable(abort):
                    abort()
                raise AgentRunStopped("Agent force-stopped during streamed model request")
            if chunk == "\n<think>\n":
                channel = "reasoning"
                continue
            if chunk == "\n</think>\n":
                channel = "content"
                continue
            if chunk == "\n<tool_call>\n":
                channel = "tool_call"
                tool_payload = []
                continue
            if chunk == "\n</tool_call>\n":
                channel = "content"
                try:
                    payload = json.loads("".join(tool_payload))
                except json.JSONDecodeError:
                    payload = {}
                if isinstance(payload, dict) and isinstance(payload.get("name"), str):
                    arguments = payload.get("arguments", {})
                    calls.append(LLMToolCall(
                        name=payload["name"],
                        arguments=arguments if isinstance(arguments, dict) else {},
                        call_id=str(payload["call_id"]) if payload.get("call_id") else None,
                    ))
                continue
            if channel == "tool_call":
                tool_payload.append(chunk)
                continue
            target = reasoning if channel == "reasoning" else content
            target.append(chunk)
            self._emit(
                "agent", name, "agent:stream_delta", "Streamed model delta",
                data={"round": round_idx, "channel": channel, "delta": chunk},
            )

        return LLMOutput(
            content="".join(content),
            provider=backend.provider,
            backend_name=backend.name,
            model=backend.model,
            reasoning_content="".join(reasoning),
            tool_calls=calls,
            usage=stream_usage,
        )

    # -- run ------------------------------------------------------------

    def run(
        self,
        message: str,
        max_rounds: int | None = None,
        temperature: float = 0.4,
        max_tokens: int | None = None,
        verbose: bool = False,
        control: AgentRunControl | None = None,
        stream: bool | None = None,
    ) -> LLMOutput:
        """Run the Agent until one explicit terminal outcome is reached.

        Args:
            message: User request or explicit task package for this run.
            max_rounds: Maximum model-and-tool steps. ``None`` uses the
                Agent's ``default_max_rounds``; ``0`` means unlimited.
            temperature: Model sampling temperature.
            max_tokens: Maximum generated tokens per model step. ``None``
                uses the Agent's ``default_max_tokens``.
            verbose: Whether to print per-round diagnostic output.
            control: Optional cooperative stop and steering source. It is read
                after each completed model-and-tool step, never mid-step.
            stream: Whether to emit provider text/thinking deltas. ``None``
                uses ``default_stream``.

        Returns:
            Last model output produced by the Agent.

        Raises:
            ValueError: If a resolved execution budget is negative or the
                token budget is not positive.
            AgentRunStopped: If ``control`` requests a stop after a completed
                model-and-tool boundary. That boundary is persisted before
                the exception is raised.
            AgentRunLimitReached: If the last permitted response still
                requests tools and therefore cannot be a final answer.
            RuntimeError: If a model returns neither tool calls nor formal
                answer content; this is an invalid empty response rather than
                a successful completion.
        """
        resolved_max_rounds = self.default_max_rounds if max_rounds is None else max_rounds
        resolved_max_tokens = (
            self.default_max_tokens if max_tokens is None else max_tokens
        )
        resolved_stream = self.default_stream if stream is None else stream
        if resolved_max_rounds < 0:
            raise ValueError("max_rounds must be zero or greater")
        if resolved_max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero")
        self._completion_requested.clear()
        self._stop_turn_requested.clear()
        with self._termination_lock:
            self._stop_turn_reason = ""
        self.last_outcome = None
        name = self._agent_name_in_graph

        backend = self.llm_fetcher.default_backend_config
        self._emit(
            "agent",
            name,
            "agent:start",
            message,
            data={
                "backend": {
                    "name": backend.name,
                    "provider": backend.provider,
                    "model": backend.model,
                },
                "tools": [
                    {"name": tool.name, "description": tool.description}
                    for tool in self.tool_handler.get_all_tools()
                ],
            },
        )

        prompt: str = self._build_prompt()
        tool_results: Optional[Dict[str, str]] = None
        have_tool_call: bool = False

        load_result = (
            self.context_handler.load(self.context_path)
            if self.context_path is not None
            else False
        )
        if verbose:
            if not load_result:
                print(
                    "Context not loaded, check for whether file not exist "
                    "or else issues."
                )
            else:
                print("Context loaded: ", self.context_path)

        self.context_handler.add_user_message(message=message)
        self.usage = TokenUsage()
        self._drain_internal_usage(name)

        result: LLMOutput | None = None
        round_idx = 0

        while resolved_max_rounds == 0 or round_idx < resolved_max_rounds:
            round_idx += 1
            if verbose:
                print("=" * 10 + "  ROUND " + str(round_idx) + "=" * 10)

            round_started_at = time.perf_counter()
            message_input: str = ""
            if round_idx == 0:
                message_input = message

            self._emit(
                "agent",
                name,
                "agent:llm_request",
                f"LLM request round {round_idx}",
                data={
                    "round": round_idx,
                    "message": message,
                    "msg": message_input,
                    "system_prompt": prompt,
                    "temperature": temperature,
                    "max_tokens": resolved_max_tokens,
                    "backend": {
                        "name": backend.name,
                        "provider": backend.provider,
                        "model": backend.model,
                    },
                    "tools": [
                        {"name": tool.name, "description": tool.description}
                        for tool in self.tool_handler.get_all_tools()
                    ],
                },
            )

            try:
                fetch_kwargs = dict(
                    control=control,
                    msg=message_input,
                    system_prompt=prompt,
                    temperature=temperature,
                    context_handler=self.context_handler,
                    max_tokens=resolved_max_tokens,
                    tools=self.tool_handler.get_all_tools(),
                    on_request=lambda request: self._emit(
                        "agent", name, "agent:remote_request",
                        f"Remote request prepared for round {round_idx}",
                        data={"round": round_idx, "request": request.to_dict()},
                    ),
                )
                result = (
                    self._stream_model_response(name=name, round_idx=round_idx, **fetch_kwargs)
                    if resolved_stream else self._fetch_model_with_force_stop(**fetch_kwargs)
                )
            except AgentRunStopped:
                self._set_outcome(AgentRunTermination.USER_STOPPED, round_idx)
                raise

            # Accumulate token usage across rounds.
            add_usage(self.usage, copy_usage(result.usage))
            # ``agent:round`` remains the lifecycle/transcript event.  This
            # separate record is the canonical per-call usage ledger entry,
            # so consumers need not infer hidden calls from round payloads.
            self._emit(
                "agent", name, "agent:usage",
                f"Primary LLM usage for round {round_idx}",
                data={
                    "kind": "primary",
                    "round": round_idx,
                    "usage": self._usage_data(copy_usage(result.usage)),
                },
            )

            if verbose:
                print(str(result))
                print("")
                print("Tool calls: ", result.tool_calls)
                print("Tool calls nums: ", len(result.tool_calls))

            # parse for tool call. batch execution.
            if result.tool_calls:
                requested_calls = [
                    {
                        "call_id": tool_call.call_id or f"call_{index}",
                        "name": tool_call.name,
                        "args": tool_call.arguments,
                    }
                    for index, tool_call in enumerate(result.tool_calls)
                ]
                self._emit(
                    "agent",
                    name,
                    "agent:tools_requested",
                    f"Requested {len(requested_calls)} tool call(s)",
                    data={"round": round_idx, "tool_calls": requested_calls},
                )

                handlers, arguments = (
                    self.tool_handler.get_handlers_and_arguments(
                        list(result.tool_calls),
                    )
                )
                tool_started_at = time.perf_counter()
                results_list: List[Any] = self.tool_executor.execute_batch(
                    handlers, arguments,
                )
                tool_results = dict([
                    (tc.call_id or f"call_{i}", str(r))
                    for i, (tc, r) in enumerate(
                        zip(result.tool_calls, results_list),
                    )
                ])
                have_tool_call = True

                # Preserve typed outcomes for event consumers while the model
                # receives the string map above on its next round.
                completed_calls = []
                for call, raw_result in zip(requested_calls, results_list):
                    result_ok = not isinstance(raw_result, Exception)
                    if isinstance(raw_result, dict) and raw_result.get("ok") is False:
                        result_ok = False
                    completed_calls.append({
                        **call,
                        "ok": result_ok,
                        "result": raw_result,
                    })
                self._emit(
                    "agent",
                    name,
                    "agent:tools_completed",
                    f"Completed {len(completed_calls)} tool call(s)",
                    data={
                        "round": round_idx,
                        "duration_ms": round((time.perf_counter() - tool_started_at) * 1000),
                        "tool_calls": completed_calls,
                    },
                )
            else:
                tool_results = None
                have_tool_call = False

            if not have_tool_call and not result.content.strip():
                # Empty provider turns are neither a final answer nor an
                # action. Do not checkpoint an unusable blank assistant turn.
                outcome = self._set_outcome(
                    AgentRunTermination.EMPTY_RESPONSE,
                    round_idx,
                    detail="Model returned no tool calls and no formal content.",
                    output=result,
                )
                self._emit(
                    "agent", name, "agent:invalid_response",
                    "Model returned an empty response without tool calls",
                    data=outcome.to_dict(),
                )
                raise RuntimeError(outcome.detail)

            self._emit(
                "agent", name, "agent:round",
                f"Round {round_idx}, {len(result.tool_calls)} tool call(s)",
                data={
                    "round": round_idx,
                    "tool_call_count": len(result.tool_calls),
                    "tool_calls": [
                        {"name": tc.name, "args": tc.arguments}
                        for tc in result.tool_calls
                    ],
                    "usage": self._usage_data(self.usage),
                    "round_usage": self._usage_data(copy_usage(result.usage)),
                    "duration_ms": round((time.perf_counter() - round_started_at) * 1000),
                    "assistant_content": result.content,
                    "reasoning_content": result.reasoning_content,
                },
            )

            if verbose:
                print("\n", tool_results, "\n")

            self.context_handler.add_assistant_message(
                message=result,
                tool_results=tool_results,
            )
            self._drain_internal_usage(name)

            # A completed model response and its complete tool batch form the
            # smallest safe resume boundary.  Checkpoint it immediately so a
            # process crash, force-stop, or later model failure cannot erase
            # every turn produced by a long-running Agent invocation.
            self._save_context()

            if self._completion_requested.is_set():
                outcome = self._set_outcome(
                    AgentRunTermination.WORKFLOW_COMPLETION,
                    round_idx,
                    output=result,
                )
                self._emit(
                    "agent", name, "agent:completion_requested",
                    f"Completed after terminal tool in round {round_idx}",
                    data=outcome.to_dict(),
                )
                break

            if self._stop_turn_requested.is_set():
                with self._termination_lock:
                    stop_reason = self._stop_turn_reason
                outcome = self._set_outcome(
                    AgentRunTermination.STOP_TURN,
                    round_idx,
                    detail=stop_reason,
                    output=result,
                )
                self._emit(
                    "agent", name, "agent:stop_turn",
                    "Stopped after reserved stop_turn tool",
                    data=outcome.to_dict(),
                )
                break

            # Persist before checking controls because stops are observed only
            # after a completed response and its complete tool batch.
            if control is not None and control.should_stop():
                self._save_context()
                outcome = self._set_outcome(
                    AgentRunTermination.USER_STOPPED,
                    round_idx,
                    output=result,
                )
                self._emit(
                    "agent", name, "agent:stopped",
                    f"Stopped after round {round_idx}",
                    data=outcome.to_dict(),
                )
                raise AgentRunStopped(
                    "Agent stopped after the current step",
                    last_output=result,
                )

            # Safe controls are intentionally observed after response
            # persistence and the complete tool batch, preserving one step.
            steers = control.drain_steers() if control is not None else []
            if steers:
                for steer in steers:
                    self.context_handler.add_user_message(message=steer)
                self._drain_internal_usage(name)
                message = steers[-1]
                self._emit(
                    "agent", name, "agent:steer_applied",
                    f"Applied {len(steers)} steering message(s)",
                    data={"round": round_idx, "messages": steers},
                )

            if not have_tool_call and not steers:
                self._set_outcome(
                    AgentRunTermination.FINAL_RESPONSE,
                    round_idx,
                    output=result,
                )
                break

        if result is not None and self.last_outcome is None:
            outcome = self._set_outcome(
                AgentRunTermination.ROUND_LIMIT,
                round_idx,
                detail="Maximum model-and-tool rounds reached before a terminal response.",
                output=result,
            )
            self._save_context()
            raise AgentRunLimitReached(outcome.detail)

        save_result = self._save_context()
        if verbose:
            if not save_result:
                print("Context saving failed.")
            else:
                print("Context saved at: ", self.context_path)

        self._drain_internal_usage(name)

        self._emit(
            "agent", name, "agent:complete",
            f"Completed in {round_idx} round(s), "
            f"{self.usage.total_tokens} total tokens",
            data={
                "rounds": round_idx,
                "usage": self._usage_data(self.usage),
                "output_len": len(result.content) if result else 0,
                "outcome": self.last_outcome.to_dict() if self.last_outcome else None,
            },
        )

        if result is None:
            raise RuntimeError("Agent completed without a model response")
        return result

    def close(self) -> None:
        """Release sub-interpreter resources held by the tool executor."""
        self.tool_executor.close()

    def clear_context(self) -> None:
        """
        Clear context.
        """
        self.context_handler.clear_context()
