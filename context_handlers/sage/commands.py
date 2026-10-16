"""Deferred worktree mutations requested by Sage tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class SageBranchCommand:
    """One mutation applied at the next completed agent round."""

    kind: str
    branch_id: Optional[UUID] = None
    description: str = ""
    verdict: Optional[str] = None
    reason: str = ""


__all__ = ["SageBranchCommand"]
