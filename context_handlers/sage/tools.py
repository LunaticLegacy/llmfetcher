"""Agent-facing tools for Sage worktree navigation.

Handlers only enqueue mutations.  The Agent applies the queue after the model
turn and its tool results have been durably recorded, which keeps parallel tool
execution from racing on the worktree stack.
"""

from __future__ import annotations

import json
from typing import Any, Callable
from uuid import UUID

from ...llm_types import Tool, ToolParameter, ToolSchema
from .commands import SageBranchCommand
from .status import BranchPhase, BranchVerdict


class SageToolProvider:
    """Bind Sage coordination tools to one context handler instance."""

    def __init__(self, context: Any) -> None:
        self.context = context

    def tools(self) -> list[Tool]:
        return [
            Tool("sage_get_worktree", "Inspect the current Sage worktree path and branch statuses.", ToolSchema(), self.get_worktree),
            Tool("sage_fork_branch", "Queue a child branch from the current Sage branch.", ToolSchema(properties=[
                ToolParameter("description", description="The question or hypothesis this branch will investigate."),
                ToolParameter("checkout", type="boolean", description="Switch to the new branch after this turn.", required=False, default=False),
            ]), self.fork_branch),
            Tool("sage_checkout_branch", "Queue a switch to an existing Sage branch by UUID.", ToolSchema(properties=[
                ToolParameter("branch_id", description="UUID of the branch to activate."),
            ]), self.checkout_branch),
            Tool("sage_pause_branch", "Pause the current Sage branch.", ToolSchema(properties=[
                ToolParameter("reason", description="Why this branch is paused.", required=False, default=""),
            ]), self.pause_branch),
            Tool("sage_resume_branch", "Resume the current Sage branch.", ToolSchema(), self.resume_branch),
            Tool("sage_finish_branch", "Finish the current Sage branch with a verdict.", ToolSchema(properties=[
                ToolParameter("verdict", enum=[v.value for v in BranchVerdict if v != BranchVerdict.UNKNOWN], description="The branch result."),
            ]), self.finish_branch),
        ]

    def get_worktree(self, **_: Any) -> str:
        return json.dumps(self.context.worktree_snapshot(), ensure_ascii=False)

    def fork_branch(self, description: str, checkout: bool = False, **_: Any) -> str:
        if not str(description).strip():
            raise ValueError("description must not be empty")
        self.context.queue_branch_command(SageBranchCommand(
            "fork", description=str(description), reason="checkout" if checkout else ""
        ))
        return json.dumps({"queued": True, "operation": "fork", "checkout": bool(checkout)})

    def checkout_branch(self, branch_id: str, **_: Any) -> str:
        branch = UUID(str(branch_id))
        self.context.queue_branch_command(SageBranchCommand("checkout", branch_id=branch))
        return json.dumps({"queued": True, "operation": "checkout", "branch_id": str(branch)})

    def pause_branch(self, reason: str = "", **_: Any) -> str:
        self.context.queue_branch_command(SageBranchCommand("pause", reason=str(reason)))
        return json.dumps({"queued": True, "operation": "pause"})

    def resume_branch(self, **_: Any) -> str:
        self.context.queue_branch_command(SageBranchCommand("resume"))
        return json.dumps({"queued": True, "operation": "resume"})

    def finish_branch(self, verdict: str, **_: Any) -> str:
        BranchVerdict(str(verdict))
        self.context.queue_branch_command(SageBranchCommand("finish", verdict=str(verdict)))
        return json.dumps({"queued": True, "operation": "finish", "verdict": str(verdict)})


def create_sage_tools(context: Any) -> list[Tool]:
    """Return tools bound to *context* for an Angelus Agent."""
    return SageToolProvider(context).tools()


__all__ = ["SageToolProvider", "create_sage_tools"]
