"""Regression coverage for execution-wide graceful and forced stop control."""

from __future__ import annotations

import unittest
import threading
import shlex
import sys

from llmfetcher.execution import ExecutionController, StopMode
from llmfetcher.execution import current_execution_controller
from llmfetcher.llm_fetcher import LLMFetcher
from llmfetcher.llm_types import LLMBackendConfig, LLMRequestCancelled
from llmfetcher.tool_executor import ToolBatchCancelled, ToolExecutor
from llmfetcher.tools.shell_tools import create_shell_tools


class ExecutionControllerTests(unittest.TestCase):
    """Verify one stop request governs resource cancellation and observation."""

    def test_graceful_stop_wakes_waiters_without_closing_resources(self) -> None:
        """Graceful mode shares the request path but preserves active I/O."""
        controller = ExecutionController()
        cancelled: list[str] = []
        controller.register_force_canceller(lambda request: cancelled.append(request.mode))

        request = controller.request_stop(reason="user")

        self.assertIs(request.mode, StopMode.GRACEFUL)
        self.assertIs(controller.wait_for_stop(0), request)
        self.assertEqual(cancelled, [])

    def test_force_stop_escalates_and_closes_existing_and_late_resources(self) -> None:
        """Force mode upgrades graceful intent and closes every registered resource."""
        controller = ExecutionController()
        cancelled: list[StopMode] = []
        controller.register_force_canceller(lambda request: cancelled.append(request.mode))
        controller.request_stop(StopMode.GRACEFUL)

        request = controller.request_stop(StopMode.FORCE, reason="force")
        controller.register_force_canceller(lambda late: cancelled.append(late.mode))

        self.assertIs(request.mode, StopMode.FORCE)
        self.assertEqual(cancelled, [StopMode.FORCE, StopMode.FORCE])

    def test_force_stop_closes_active_fetcher_transport(self) -> None:
        """A fetch request registers its transport and exits as cancellation."""
        backend = LLMBackendConfig(name="test", provider="test", model="test")
        handler = _BlockingHandler()
        fetcher = object.__new__(LLMFetcher)
        fetcher.backends = {backend.name: backend}
        fetcher.backend_order = [backend.name]
        fetcher.default_backend = backend.name
        fetcher.handlers = {backend.name: handler}
        controller = ExecutionController()
        errors: list[BaseException] = []

        worker = threading.Thread(
            target=lambda: _fetch_in_thread(fetcher, controller, errors),
        )
        worker.start()
        self.assertTrue(handler.started.wait(1))
        controller.request_stop(StopMode.FORCE, reason="test")
        worker.join(1)

        self.assertFalse(worker.is_alive())
        self.assertTrue(handler.aborted.is_set())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], LLMRequestCancelled)

    def test_force_stop_closes_an_active_stream(self) -> None:
        """The stream keeps its registration until its generator is closed."""
        backend = LLMBackendConfig(name="test", provider="test", model="test")
        handler = _StreamingHandler()
        fetcher = object.__new__(LLMFetcher)
        fetcher.backends = {backend.name: backend}
        fetcher.backend_order = [backend.name]
        fetcher.default_backend = backend.name
        fetcher.handlers = {backend.name: handler}
        controller = ExecutionController()
        stream = fetcher.fetch_stream(msg="test", controller=controller)

        self.assertEqual(next(stream), "first")
        errors: list[BaseException] = []
        worker = threading.Thread(target=lambda: _advance_stream(stream, errors))
        worker.start()
        self.assertTrue(handler.waiting.wait(1))
        controller.request_stop(StopMode.FORCE, reason="test")
        worker.join(1)

        self.assertFalse(worker.is_alive())
        self.assertTrue(handler.aborted.is_set())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], LLMRequestCancelled)

    def test_force_stop_cancels_a_tool_batch_and_binds_its_controller(self) -> None:
        """A running tool can close its resource through the bound controller."""
        controller = ExecutionController()
        executor = ToolExecutor(max_concurrency=1)
        resource_started = threading.Event()
        resource_closed = threading.Event()
        errors: list[BaseException] = []

        def blocking_tool() -> str:
            active = current_execution_controller()
            assert active is controller
            unregister = active.register_force_canceller(
                lambda _request: resource_closed.set()
            )
            resource_started.set()
            try:
                resource_closed.wait(5)
                return "closed"
            finally:
                unregister()

        worker = threading.Thread(
            target=lambda: _run_tool_batch(executor, controller, blocking_tool, errors),
        )
        worker.start()
        self.assertTrue(resource_started.wait(1))
        controller.request_stop(StopMode.FORCE, reason="test")
        worker.join(1)

        self.assertFalse(worker.is_alive())
        self.assertTrue(resource_closed.is_set())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ToolBatchCancelled)

    def test_force_stop_kills_a_shell_tool_process_group(self) -> None:
        """Shell tools register their spawned process group with the controller."""
        controller = ExecutionController()
        executor = ToolExecutor(max_concurrency=1)
        process_started = threading.Event()
        errors: list[BaseException] = []
        shell = create_shell_tools(
            register_process=lambda _process: process_started.set(),
        )[0].handler
        command = f'{shlex.quote(sys.executable)} -c "import time; time.sleep(5)"'

        worker = threading.Thread(
            target=lambda: _run_tool_batch(
                executor,
                controller,
                shell,
                errors,
                arguments={"command": command, "timeout": 10},
            ),
        )
        worker.start()
        self.assertTrue(process_started.wait(1))
        controller.request_stop(StopMode.FORCE, reason="test")
        worker.join(1)

        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ToolBatchCancelled)


class _BlockingHandler:
    """Minimal provider double whose close wakes a blocked completion call."""

    def __init__(self) -> None:
        self.started = threading.Event()
        self.aborted = threading.Event()

    def prepare_tools(self, tools: object) -> object:
        return tools

    def create_completion(self, **_kwargs: object) -> object:
        self.started.set()
        self.aborted.wait(5)
        raise RuntimeError("transport closed")

    def abort_active_request(self) -> int:
        self.aborted.set()
        return 1


class _StreamingHandler(_BlockingHandler):
    """Provider double that emits one chunk then blocks on the transport."""

    def __init__(self) -> None:
        super().__init__()
        self.waiting = threading.Event()

    def create_completion(self, **_kwargs: object) -> object:
        return object()

    def iter_stream_text(self, _raw: object, **_kwargs: object):
        yield "first"
        self.waiting.set()
        self.aborted.wait(5)
        raise RuntimeError("transport closed")


def _fetch_in_thread(
    fetcher: LLMFetcher,
    controller: ExecutionController,
    errors: list[BaseException],
) -> None:
    try:
        fetcher.fetch(msg="test", controller=controller)
    except BaseException as exc:
        errors.append(exc)


def _advance_stream(stream: object, errors: list[BaseException]) -> None:
    try:
        next(stream)  # type: ignore[arg-type]
    except BaseException as exc:
        errors.append(exc)


def _run_tool_batch(
    executor: ToolExecutor,
    controller: ExecutionController,
    handler: object,
    errors: list[BaseException],
    arguments: dict[str, object] | None = None,
) -> None:
    try:
        executor.execute_batch_timed(
            [handler],
            [arguments or {}],
            controller=controller,
        )
    except BaseException as exc:
        errors.append(exc)
