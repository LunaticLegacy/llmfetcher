from __future__ import annotations

from typing import Protocol

from ..execution import ExecutionController


def _supports_force_control(control: object) -> bool:
    """Return whether one cooperative control can cancel provider resources.

    Args:
        control: Candidate global or Agent-scoped execution control.

    Returns:
        ``True`` when the object exposes the force-cancellation contract used
        by ``LLMFetcher`` and tool execution.
    """
    return (
        isinstance(control, ExecutionController)
        or (
            control is not None
            and callable(getattr(control, "register_force_canceller", None))
            and hasattr(control, "force_stopped")
        )
    )


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
