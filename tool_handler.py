from __future__ import annotations

from typing import Any, Dict, List

from .llm_types import LLMToolCall, Tool


class ToolCallValidationError(ValueError):
    """A model-requested tool call does not match a registered Tool contract."""


class ToolHandler:
    """Register, look up, and describe ``Tool`` objects.

    This is a pure **registry** — it tracks what tools exist and how to
    describe them.  Execution is delegated to ``ToolExecutor`` so that
    the two concerns (registration vs. execution) can evolve independently.
    """

    def __init__(self) -> None:
        self.tool_dict: Dict[str, Tool] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add_tool(self, tool: Tool) -> bool:
        """Register a tool.  No-op if a tool with the same name exists.

        Returns:
            ``True`` if the tool was added, ``False`` if a tool with
            the same name was already registered.
        """
        if tool.name in self.tool_dict:
            return False
        self.tool_dict[tool.name] = tool
        return True

    def remove_tool(self, name: str) -> bool:
        """Unregister a tool by name.

        Returns:
            ``True`` if the tool was removed, ``False`` if no tool
        """
        if name not in self.tool_dict:
            return False
        del self.tool_dict[name]
        return True

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> Tool | None:
        """Look up a tool by name.

        Returns:
            The ``Tool`` instance, or ``None`` if not found.
        """
        return self.tool_dict.get(name)

    def get_handler(self, name: str) -> Any | None:
        """Return the callable handler for a named tool.

        Returns:
            The handler callable, or ``None`` if not found.
        """
        tool = self.tool_dict.get(name)
        return tool.handler if tool else None

    def get_handlers_and_arguments(
        self,
        calls: List[LLMToolCall],
    ) -> tuple[List[Any | None], List[Dict[str, Any]]]:
        """Resolve a list of tool calls into (handlers, arguments).

        Handlers for unknown tool names are set to ``None``.

        Args:
            calls: Tool calls to resolve.

        Returns:
            A ``(handlers, arguments_list)`` tuple suitable for passing
            directly to ``ToolExecutor.execute_batch``.
        """
        handlers: List[Any | None] = []
        arguments_list: List[Dict[str, Any]] = []
        for tc in calls:
            tool = self.tool_dict.get(tc.name)
            error = _validate_tool_call(tool, tc)
            handlers.append(tool.handler if error is None else _reject_tool_call(error))
            arguments_list.append(tc.arguments)
        return handlers, arguments_list

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_all_tool_description(self) -> str:
        """Concatenated ``__str__`` of all registered tools, newline-separated."""
        return "\n".join(str(v) for v in self.tool_dict.values())

    def get_all_tools(self) -> List[Tool]:
        """Return all registered tools as a list."""
        return list(self.tool_dict.values())


def _reject_tool_call(message: str) -> Any:
    """Return a handler that reports one validation failure to the model."""
    def reject(**_arguments: Any) -> None:
        raise ToolCallValidationError(message)
    return reject


def _validate_tool_call(tool: Tool | None, call: LLMToolCall) -> str | None:
    """Validate one model call before a local handler can observe it.

    This deliberately supports the object/required/properties/type/enum
    subset common to first-party and MCP tool schemas.  Unsupported JSON
    Schema keywords remain the tool owner's responsibility, while malformed
    schemas fail closed instead of passing arbitrary model data to Python.
    """
    if tool is None:
        return f"Unknown tool: {call.name}"
    if not isinstance(call.arguments, dict):
        return f"Invalid arguments for {call.name}: expected a JSON object"
    schema = tool.schemas.to_dict()
    if not isinstance(schema, dict) or schema.get("type", "object") != "object":
        return f"Tool {call.name} has an invalid input schema"
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if not isinstance(properties, dict) or not isinstance(required, list) or any(not isinstance(key, str) for key in required):
        return f"Tool {call.name} has an invalid input schema"
    missing = [key for key in required if key not in call.arguments]
    if missing:
        return f"Invalid arguments for {call.name}: missing required field(s): {', '.join(missing)}"
    # Compact first-party schemas enumerate the complete Python callable
    # contract, so extra model fields must not reach ``handler(**kwargs)``.
    # Raw external schemas retain JSON Schema's default permissiveness unless
    # their owner explicitly sets ``additionalProperties: false``.
    allow_extra = tool.schemas.raw_schema is not None and schema.get("additionalProperties") is not False
    for key, value in call.arguments.items():
        definition = properties.get(key)
        if definition is None:
            if not allow_extra:
                return f"Invalid arguments for {call.name}: unexpected field: {key}"
            continue
        if not isinstance(definition, dict):
            return f"Tool {call.name} has an invalid schema for field: {key}"
        expected = definition.get("type")
        if isinstance(expected, str) and not _matches_json_type(value, expected):
            return f"Invalid arguments for {call.name}: {key} must be {expected}"
        allowed = definition.get("enum")
        if isinstance(allowed, list) and value not in allowed:
            return f"Invalid arguments for {call.name}: {key} must be one of {allowed}"
    return None


def _matches_json_type(value: Any, expected: str) -> bool:
    """Return whether a JSON-compatible value matches one primitive type."""
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "null":
        return value is None
    return False
