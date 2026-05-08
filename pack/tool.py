import asyncio
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class Tool:
    """A single tool that an Agent can call."""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable[..., Any]  # sync or async callable

    async def execute(self, **kwargs: Any) -> Any:
        """
        Invoke the tool handler, awaiting if necessary.

        要求所有工具均使用异步模式。
        """
        if asyncio.iscoroutinefunction(self.handler):
            return await self.handler(**kwargs)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.handler(**kwargs))


class ToolRegistry:
    """Registers and executes tools, and produces LLM-compatible schemas."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        """Register a tool. Returns the tool for decorator usage."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool
        return tool

    def unregister(self, name: str) -> Tool:
        """Unregister a tool by name. Returns the removed tool."""
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools.pop(name)

    def get(self, name: str) -> Tool:
        """Retrieve a registered tool by name."""
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered tool by name."""
        tool = self.get(name)
        return await tool.execute(**arguments)

    @property
    def schemas(self) -> List[Dict[str, Any]]:
        """Return tool metadata for prompt injection or future adapters."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def get_prompt_hint(self) -> str:
        """Return a prompt snippet that instructs the LLM how to call tools."""
        if not self._tools:
            return ""

        lines: List[str] = [
            "",
            "=== AVAILABLE TOOLS ===",
            "When you need a tool, respond with ONE valid JSON object and nothing else.",
            "Use one of these shapes:",
            '  {"tool": "<tool_name>", "arguments": {<key>: <value>, ...}}',
            '  {"tool_calls": [{"tool": "<tool_name>", "arguments": {...}}, ...]}',
            "If you do not need any tool, answer normally in natural language.",
            ""
        ]
        for t in self._tools.values():
            lines.append(f"Tool: {t.name}")
            lines.append(f"  Description: {t.description}")
            params = json.dumps(t.parameters, ensure_ascii=False)
            lines.append(f"  Parameters: {params}")
            lines.append("")
        lines.append("=== END TOOLS ===")
        return "\n".join(lines)
