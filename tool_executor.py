from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from .llm_types import LLMToolCall, Tool


@dataclass
class ToolExecution:
    """One tool handler execution: its result and wall-clock duration.

    Attributes:
        result: Handler return value, or the ``Exception`` instance raised
            by the handler (never propagated).
        duration_ms: Wall-clock time spent in the handler, in milliseconds.
    """

    result: Any
    duration_ms: int


class ToolExecutor:
    """Execute tool handlers in parallel using a thread pool.

    All tools in this system are I/O-bound (HTTP requests, subprocess,
    file I/O) — the GIL is released during the actual I/O wait, so
    ``ThreadPoolExecutor`` provides effective parallelism without the
    complexity of sub-interpreters.

    Benefits over sub-interpreters:
    - ``KeyboardInterrupt`` propagates correctly (Ctrl+C works).
    - Closures and lambdas work without fallback.
    - No pickle/serialisation boundary.
    - Full Python version compatibility.

    Single tools run in the calling thread.  Batches are dispatched across
    the thread pool.
    """

    def __init__(
        self,
        max_concurrency: int = 3,
    ) -> None:
        self._max_concurrency = max(max_concurrency, 1)

    # ------------------------------------------------------------------
    # Single execution
    # ------------------------------------------------------------------

    def execute(
        self,
        handler: Callable[..., Any],
        arguments: Dict[str, Any],
    ) -> Any:
        """Run a single tool handler in the calling thread."""
        return handler(**arguments)

    def execute_timed(
        self,
        handler: Callable[..., Any],
        arguments: Dict[str, Any],
    ) -> ToolExecution:
        """Run a single tool handler in the calling thread with timing.

        Unlike :meth:`execute`, exceptions are caught and stored in the
        returned record's ``result`` so callers can pair the failure with its
        duration without a try/except around the call.

        Args:
            handler: Tool callable to invoke.
            arguments: Keyword arguments passed to *handler*.

        Returns:
            A :class:`ToolExecution` record with the handler's result (or the
            raised ``Exception``) and its wall-clock duration in milliseconds.
        """
        started_at = time.perf_counter()
        try:
            result = handler(**arguments)
        except Exception as exc:
            result = exc
        duration_ms = round((time.perf_counter() - started_at) * 1000)
        return ToolExecution(result=result, duration_ms=duration_ms)

    # ------------------------------------------------------------------
    # Batch (parallel) execution
    # ------------------------------------------------------------------

    def execute_batch(
        self,
        handlers: List[Callable[..., Any] | None],
        arguments_list: List[Dict[str, Any]],
    ) -> List[Any]:
        """Execute tool handlers in parallel using a thread pool.

        Results are returned in the same order as the input lists.
        Handlers that are ``None`` are skipped (result remains ``None``).
        Exceptions raised by a handler are caught and stored in the
        results list as ``Exception`` instances.

        Args:
            handlers:
                List of callables (or ``None``), one per batch item.
            arguments_list:
                List of argument dicts, one per batch item.  Must be
                the same length as *handlers*.

        Returns:
            Results in the same order as inputs.
        """
        return [
            execution.result
            for execution in self.execute_batch_timed(handlers, arguments_list)
        ]

    def execute_batch_timed(
        self,
        handlers: List[Callable[..., Any] | None],
        arguments_list: List[Dict[str, Any]],
    ) -> List[ToolExecution]:
        """Execute tool handlers in parallel, measuring each one's duration.

        Results are returned in the same order as the input lists, wrapped in
        :class:`ToolExecution` records that also carry each handler's
        wall-clock time.  Handlers that are ``None`` are skipped (result stays
        ``None`` with a zero duration).  Exceptions raised by a handler are
        caught and stored in the record's ``result`` as ``Exception``
        instances.

        Args:
            handlers:
                List of callables (or ``None``), one per batch item.
            arguments_list:
                List of argument dicts, one per batch item.  Must be
                the same length as *handlers*.

        Returns:
            :class:`ToolExecution` records in the same order as the inputs.
        """
        n = len(handlers)
        if n == 0:
            return []

        results: List[Any] = [None] * n
        durations: List[int] = [0] * n
        lock = threading.Lock()

        with ThreadPoolExecutor(
            max_workers=self._max_concurrency,
        ) as executor:
            futures = []

            for idx in range(n):
                fn = handlers[idx]
                if fn is None:
                    continue

                def submit_one(
                    i: int,
                    handler: Callable[..., Any],
                    kwargs: Dict[str, Any],
                ) -> None:
                    started_at = time.perf_counter()
                    try:
                        result = handler(**kwargs)
                    except Exception as exc:
                        result = exc
                    duration_ms = round((time.perf_counter() - started_at) * 1000)
                    with lock:
                        results[i] = result
                        durations[i] = duration_ms

                futures.append(
                    executor.submit(submit_one, idx, fn, arguments_list[idx])
                )

            for _ in as_completed(futures):
                pass

        return [
            ToolExecution(result=results[i], duration_ms=durations[i])
            for i in range(n)
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release resources.  (No-op — threads clean up on exit.)"""
        pass
