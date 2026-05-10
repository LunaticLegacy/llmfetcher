"""Built-in tools for Agent lifecycle management."""

from typing import Any, List

from ..tool import Tool


def create_builtin_tools() -> List[Tool]:
    """Create Agent built-in meta-tools (e.g., round_end)."""

    async def _round_end(**kwargs: Any) -> str:
        """结束当前 round_call。"""
        return "Round ended."

    return [
        Tool(
            name="round_end",
            description=(
                "结束当前轮次。当你认为已经完成了本轮所有必要的思考、"
                "工具调用和论点记录后，调用此工具来明确结束本轮对话。"
            ),
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            handler=_round_end,
        ),
    ]
