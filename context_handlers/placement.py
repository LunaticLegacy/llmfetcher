"""Request-assembly policy shared by the context handler hierarchy."""

from __future__ import annotations

from enum import StrEnum

RESUME_PROMPT = "Continue user's job from your checkpoint, now."
"""Derived user turn appended when compaction left no usable user input."""


class ToolResultPlacement(StrEnum):
    """Where an assembled request places the results of a tool batch.

    ``INTERLEAVED`` is the provider-compliant default: each result is its own
    ``tool`` message immediately after the assistant turn that requested it.
    ``DEFERRED`` emits no ``tool`` message at all and merges every result into
    one ``system`` block, each entry carrying the ``call_id`` its assistant
    turn points at.
    """

    INTERLEAVED = "interleaved"
    DEFERRED = "deferred"


__all__ = ["RESUME_PROMPT", "ToolResultPlacement"]
