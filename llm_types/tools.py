"""Tool declarations, JSON schemas, and the handler call contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, TypeAlias, cast

from .json import JsonObject, JsonValue

ToolCallable: TypeAlias = Callable[..., object]
"""A tool callable with an open but JSON-serializable return contract."""


@dataclass
class ToolParameter:
    """A single parameter in a tool's JSON Schema."""

    name: str                           # 参数名
    type: str = "string"                # JSON Schema 类型
    description: str = ""               # 参数描述
    required: bool = True               # 是否必需
    enum: Optional[List[str]] = None    # 可选值枚举
    default: JsonValue = None       # 默认值


@dataclass
class ToolSchema:
    """Structured JSON Schema for tool parameters and external tool protocols.

    Args:
        type: Root JSON Schema type used by compact ``ToolParameter`` schemas.
        properties: Flat first-party parameter declarations.
        raw_schema: Validated complete JSON Schema from an external protocol
            such as MCP. When present, it takes precedence so nested objects,
            arrays, and protocol-specific constraints are retained verbatim.
    """

    type: str = "object"
    properties: List[ToolParameter] = field(default_factory=list)
    raw_schema: Optional[JsonObject] = None

    def to_dict(self) -> JsonObject:
        """Convert this schema to an isolated JSON-ready mapping.

        Returns:
            A shallow copy of ``raw_schema`` for external tools, or a JSON
            Schema generated from the compact first-party parameter model.
        """
        # MCP input schemas may contain nested constraints unavailable in the
        # compact ToolParameter representation, so preserve that contract.
        if self.raw_schema is not None:
            return dict(self.raw_schema)
        required: List[str] = []
        props: JsonObject = {}
        for p in self.properties:
            prop: JsonObject = {"type": p.type}
            if p.description:
                prop["description"] = p.description
            if p.enum:
                prop["enum"] = cast("JsonValue", p.enum)
            if p.default is not None:
                prop["default"] = p.default
            props[p.name] = prop
            if p.required:
                required.append(p.name)

        result: JsonObject = {"type": self.type, "properties": props}
        if required:
            result["required"] = cast("JsonValue", required)
        return result


@dataclass
class Tool:
    """A single tool that an Agent can call."""

    name: str                           # 工具名
    description: str                    # 工具描述
    schemas: ToolSchema                 # 工具入参 schemas
    handler: ToolCallable            # sync or async callable

    def __str__(self):
        return f"""
        Tool name: {self.name}
        Tool description: {self.description}
        Tool schemas: {self.schemas.to_dict()}
        """


@dataclass
class ToolBatch:
    pass


__all__ = [
    "Tool",
    "ToolBatch",
    "ToolCallable",
    "ToolParameter",
    "ToolSchema",
]
