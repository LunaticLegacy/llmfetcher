"""Small, drainable ledger for non-primary LLM calls.

Context helpers can make LLM calls outside an Agent's visible model round.
Keeping those calls as individual records lets the Agent publish durable
accounting events without treating a cumulative counter as an event source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .llm_types import TokenUsage


@dataclass(frozen=True)
class UsageRecord:
    """Usage reported by one completed LLM call."""

    kind: str
    usage: TokenUsage


def copy_usage(usage: Optional[TokenUsage]) -> TokenUsage:
    """Copy provider usage, representing a missing provider report as zero."""
    if usage is None:
        return TokenUsage()
    return TokenUsage(
        input_tokens=usage.input_tokens or 0,
        output_tokens=usage.output_tokens or 0,
        total_tokens=usage.total_tokens or 0,
        cached_tokens=usage.cached_tokens or 0,
        reasoning_tokens=usage.reasoning_tokens or 0,
    )


def add_usage(total: TokenUsage, usage: TokenUsage) -> None:
    """Add all dimensions without deriving total from its subdimensions."""
    total.input_tokens += usage.input_tokens
    total.output_tokens += usage.output_tokens
    total.total_tokens += usage.total_tokens
    total.cached_tokens += usage.cached_tokens
    total.reasoning_tokens += usage.reasoning_tokens


def drain_records(records: list[UsageRecord]) -> list[UsageRecord]:
    """Return and consume records in their completed-call order."""
    drained = list(records)
    records.clear()
    return drained
