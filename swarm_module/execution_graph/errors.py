"""Exceptions and non-fatal markers raised by the execution graph."""

from __future__ import annotations

from dataclasses import dataclass


class GraphPersistenceError(ValueError):
    """Raised when an ExecutionGraph cannot be safely saved or restored."""


@dataclass
class AgentFailure:
    """Non-fatal marker placed in :meth:`ExecutionGraph.run` outputs when an
    Agent raises during execution.

    The graph keeps running: independent Agents are unaffected, the failure
    is delivered to the coordinator through the task bus (``status="failed"``
    report) and to observers through the ``agent:failed`` event, and the
    failed Agent's downstream dependents are skipped.

    Attributes:
        agent_name: Graph name of the Agent that raised.
        error: Bounded error message.
        exception: The original exception, when available.
    """

    agent_name: str
    error: str
    exception: Exception | None = None

    def __str__(self) -> str:
        return f"[{self.agent_name} failed] {self.error}"


__all__ = ["AgentFailure", "GraphPersistenceError"]
