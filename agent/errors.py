from __future__ import annotations

from ..llm_types import LLMOutput


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


class ContextLoadError(RuntimeError):
    """Signal that an existing Agent checkpoint could not be restored."""


class ContextSaveError(RuntimeError):
    """Signal that a configured Agent checkpoint could not be committed."""
