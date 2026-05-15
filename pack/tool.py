import asyncio
import json
from dataclasses import dataclass
from re import I
from typing import Any, Callable, Dict, List

from .types import Tool


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
        """Return tool metadata in OpenAI-compatible format.
        
        This is the default format used by OpenAI and many compatible providers.
        """
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
    
    def get_schemas_for_provider(self, provider: str = "openai") -> List[Dict[str, Any]]:
        """Return tool schemas formatted for a specific LLM provider.
        
        Args:
            provider: Target provider name. Supported: "openai", "anthropic", "custom_json"
            
        Returns:
            List of tool definitions in provider-specific format
            
        Examples:
            OpenAI format:
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "...",
                    "parameters": {...}
                }
            }
            
            Anthropic format:
            {
                "name": "search",
                "description": "...",
                "input_schema": {...}  # Note: different key name
            }
        """
        if provider == "openai":
            return self.schemas  # Already OpenAI-compatible
        
        elif provider == "anthropic":
            return self._to_anthropic_format()
        
        elif provider == "custom_json":
            # For custom JSON parsing, we don't send schemas to LLM
            # Tools are described in system prompt instead
            return []
        
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai', 'anthropic', or 'custom_json'.")
    
    def _to_anthropic_format(self) -> List[Dict[str, Any]]:
        """Convert internal tool definitions to Anthropic Claude format.
        
        Anthropic uses a slightly different schema:
        - No "type": "function" wrapper
        - Uses "input_schema" instead of "parameters"
        """
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,  # Anthropic uses input_schema
            }
            for t in self._tools.values()
        ]

    def get_prompt_hint(self) -> str:
        """Return a prompt snippet that instructs the LLM how to call tools."""
        if not self._tools: # 没有工具，不返回任何东西
            return ""

        lines: List[str] = [    # 工具文本。
            "",
            "=== AVAILABLE TOOLS ===",
            "When you need a tool, respond with ONE valid JSON object and nothing else.",
            "Use one of these shapes:",
            '  {"tool": "<tool_name>", "arguments": {<key>: <value>, ...}}',
            '  {"tool_calls": [{"tool": "<tool_name>", "arguments": {...}}, ...]}',
            "If you do not need any tool, answer normally in natural language.",
            ""
        ]  # 对每一个工具，加入这些东西。
        for t in self._tools.values():
            lines.append(f"Tool: {t.name}")
            lines.append(f"  Description: {t.description}")
            params = json.dumps(t.parameters, ensure_ascii=False)
            lines.append(f"  Parameters: {params}")
            lines.append("")
        lines.append("=== END TOOLS ===")
        return "\n".join(lines)
