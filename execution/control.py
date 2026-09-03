"""One cooperative and forceful stop controller per execution."""

from __future__ import annotations

import queue
import threading
import time
import uuid
from contextlib import contextmanager
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass
from enum import StrEnum


_active_controller: ContextVar["ExecutionController | None"] = ContextVar(
    "llmfetcher_active_execution_controller",
    default=None,
)


class StopMode(StrEnum):
    """The strategy used to reach the single ``stopped`` terminal result."""

    GRACEFUL = "graceful"
    FORCE = "force"


@dataclass(frozen=True)
class StopRequest:
    """Immutable stop intent shared by every execution boundary.

    Args:
        mode: ``GRACEFUL`` waits for a committed safe boundary; ``FORCE`` also
            closes registered active resources.
        reason: Host-provided human-readable reason for observability.
        requested_at: UNIX timestamp at the first request for this mode.
    """

    mode: StopMode
    reason: str
    requested_at: float


class ExecutionController:
    """Coordinate one execution's stop strategy, steering, and live resources.

    Normal and forced stopping share the same ``StopRequest``. A force request
    upgrades a prior graceful request and synchronously invokes every resource
    canceller registered by model, streaming, tool, or scheduler code. The
    controller does not decide the terminal state; an execution runner observes
    the request, commits or abandons its current boundary, then emits one
    ``stopped`` result.
    """

    def __init__(self) -> None:
        """Create an execution-local controller with no request or resources."""
        self._lock = threading.RLock()
        self._stop_changed = threading.Event()
        self._force_changed = threading.Event()
        self._request: StopRequest | None = None
        self._cancellers: dict[str, Callable[[StopRequest], None]] = {}
        self._steers: queue.Queue[str] = queue.Queue()

    @property
    def stop_request(self) -> StopRequest | None:
        """Return the current request, if any, without mutating its state."""
        with self._lock:
            return self._request

    def request_stop(
        self,
        mode: StopMode = StopMode.GRACEFUL,
        *,
        reason: str = "user_requested",
    ) -> StopRequest:
        """Request graceful stop or escalate it to forced resource cancellation.

        Args:
            mode: Requested stop strategy. A force request permanently wins
                over a prior graceful request for this execution.
            reason: Diagnostic reason retained exactly as supplied.

        Returns:
            The effective immutable request after deduplication or escalation.

        Side Effects:
            Sets the stop wake-up event. On first force escalation, invokes
            every currently registered canceller outside the controller lock.
            Canceller failures are isolated because one bad client must not
            prevent remaining HTTP streams, processes, or tools from closing.
        """
        callbacks: tuple[Callable[[StopRequest], None], ...] = ()
        with self._lock:
            current = self._request
            must_upgrade = current is None or (
                mode is StopMode.FORCE and current.mode is StopMode.GRACEFUL
            )
            if must_upgrade:
                self._request = StopRequest(mode, reason, time.time())
                self._stop_changed.set()
                if mode is StopMode.FORCE:
                    self._force_changed.set()
                    callbacks = tuple(self._cancellers.values())
            effective = self._request

        # Resource owners decide how to abort their own I/O. They run outside
        # the lock so a close callback may safely unregister itself.
        if effective is not None and effective.mode is StopMode.FORCE:
            for cancel in callbacks:
                try:
                    cancel(effective)
                except Exception:
                    pass
        assert effective is not None
        return effective

    def register_force_canceller(
        self,
        cancel: Callable[[StopRequest], None],
    ) -> Callable[[], None]:
        """Register one active resource closer and return its unregister handle.

        Args:
            cancel: Callable that closes one active resource when a force-stop
                request is received. It receives the effective force request.

        Returns:
            Idempotent callback that removes this resource from the registry.

        Side Effects:
            If force-stop already won, invokes ``cancel`` immediately so a
            resource opened during a cancellation race cannot escape closure.
        """
        token = uuid.uuid4().hex
        immediate_request: StopRequest | None = None
        with self._lock:
            self._cancellers[token] = cancel
            if self._request is not None and self._request.mode is StopMode.FORCE:
                immediate_request = self._request

        if immediate_request is not None:
            try:
                cancel(immediate_request)
            except Exception:
                pass

        def unregister() -> None:
            """Remove this resource closer after its I/O has completed."""
            with self._lock:
                self._cancellers.pop(token, None)

        return unregister

    def wait_for_stop(self, timeout: float | None = None) -> StopRequest | None:
        """Wait for a stop request and return the current request when present.

        Args:
            timeout: Maximum seconds to wait; ``None`` waits indefinitely.

        Returns:
            Current request, or ``None`` if the timeout expired first.
        """
        if not self._stop_changed.wait(timeout):
            return None
        return self.stop_request

    def should_stop(self) -> bool:
        """Return whether any stop strategy has been requested.

        This compatibility-shaped query deliberately has no Agent-specific
        semantics; future Agent and graph loops consume the same request.
        """
        return self.stop_request is not None

    @property
    def force_stopped(self) -> threading.Event:
        """Expose an event for existing streaming loops during migration.

        New code should inspect ``stop_request.mode``. This event stays unset
        for graceful stop and is set only once force cancellation is requested.
        """
        return self._force_changed

    def steer(self, message: str) -> None:
        """Queue one non-empty steering message for the next safe boundary."""
        if message.strip():
            self._steers.put(message)

    def drain_steers(self) -> list[str]:
        """Return and consume queued steering messages in FIFO order."""
        messages: list[str] = []
        while True:
            try:
                messages.append(self._steers.get_nowait())
            except queue.Empty:
                return messages


def current_execution_controller() -> ExecutionController | None:
    """Return the controller bound to the currently executing tool worker."""
    return _active_controller.get()


@contextmanager
def bind_execution_controller(controller: ExecutionController | None):
    """Bind one controller to a worker without exposing it as tool input."""
    token = _active_controller.set(controller)
    try:
        yield
    finally:
        _active_controller.reset(token)
