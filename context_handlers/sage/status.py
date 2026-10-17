"""
Status for definitoin of work graph.
A work graph is included the branches. For each branches, there are multiply status for it.
Sage may need to maintain an explicit workgraph inside the context.
"""
from enum import StrEnum
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import List, Optional

class BranchPhase(StrEnum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    ABANDONED = "abandoned"


class BranchVerdict(StrEnum):
    UNKNOWN = "unknown"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    SOLVED = "solved"


@dataclass
class SageWorkTreeBranch:
    """
    The metadata about the branch. A branch can be the root of the subtree.

    Things will be injected to Agent are:
    - Description.
    - Phase
    - Verdict
    """
    id: UUID
    description: str

    # Branching relationship
    branches_id: List[UUID] = field(default_factory=list)
    parent_branch_id: Optional[UUID] = None

    # Stable references, not copied messages
    root_context_id: Optional[int] = None
    holding_context_ids: List[int] = field(
        default_factory=list
    )
    summary_context_id: Optional[int] = None

    # Phase and verdict. This will be injected into context.
    phase: BranchPhase = BranchPhase.NOT_STARTED
    verdict: BranchVerdict = BranchVerdict.UNKNOWN

    
