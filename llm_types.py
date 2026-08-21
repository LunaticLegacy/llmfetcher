import asyncio
import inspect
from dataclasses import dataclass, field
from typing import List, Dict, Literal, Optional, Tuple, Union, Set, Any, Callable, overload, override

from typing import TypeAlias
from uuid import UUID, uuid4
import json

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
JsonArray: TypeAlias = list[JsonValue]


@dataclass(frozen=True)
class RemoteRequestSnapshot:
    """Credential-free schema for one dispatch-ready remote model request.

    The dispatcher builds this object after a provider handler has prepared
    its tool schemas and immediately before it starts provider I/O.  It is a
    stable observability contract shared with application hosts; provider
    adapters may still use additional wire-only fields internally.

    Attributes:
        model: Provider model identifier selected for this attempt.
        messages: Complete provider-neutral message sequence sent to the
            handler before any provider-local message normalization.
        temperature: Sampling temperature for this request.
        max_tokens: Maximum completion tokens requested from the provider.
        stream: Whether the request asks for streamed output.
        tools: Provider-prepared JSON tool schemas exposed for this attempt.
    """

    model: str
    messages: list[JsonObject]
    temperature: float
    max_tokens: int
    stream: bool
    tools: list[JsonObject] = field(default_factory=list)

    def to_dict(self) -> JsonObject:
        """Return the JSON-safe event payload used by application hosts.

        Returns:
            A fresh top-level mapping containing only request fields that are
            safe to persist or render. Credentials and endpoint URLs are not
            part of this schema.
        """
        return {
            "model": self.model,
            "messages": self.messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
            "tools": self.tools,
        }

# --------------------------
# Exception hierarchy
# --------------------------


class LLMError(Exception):
    """Base exception for all LLM-related errors."""


class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""


class LLMBackendError(LLMError):
    """Raised when all candidate backends fail."""


class LLMRequestCancelled(LLMError):
    """Raised when a terminal force-stop cancels an in-flight LLM request."""


# --------------------------
# LLM API-level objects
# --------------------------

@dataclass
class LLMBackendConfig:
    """Configuration for one routable LLM backend."""

    name: str
    provider: str
    model: str
    api_key: str = ""
    api_url: Optional[str] = None
    timeout: float = 60.0
    # Additional attempts after the initial request. A value of ``3`` allows
    # at most four total requests when the failure is retryable.
    max_retries: int = 0
    # Selects provider-specific behaviour for an otherwise compatible API.
    # For example, an OpenAI-compatible DeepSeek gateway can set this to
    # ``"deepseek"`` while keeping ``provider="openai"`` for its wire API.
    # When omitted, handlers may still identify well-known provider URLs or
    # model families.
    compatibility_profile: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Render the backend config in a compact human-readable form."""
        return f"""
        LLMBackendConfig(
            Name: {self.name},
            Provider: {self.provider},
            Model: {self.model},
            API Key: {self.api_key},
            API URL: {self.api_url},
            Timeout: {self.timeout} secs,
            Max retries: {self.max_retries},
            Compatibility profile: {self.compatibility_profile},
            Extra args: {self.extra}
        )
        """


@dataclass
class LLMToolCall:
    """Backend-neutral tool call emitted by a model."""

    name: str
    arguments: JsonObject = field(default_factory=dict)
    call_id: Optional[str] = None
    source: Optional[str] = None


@dataclass
class ToolInfo:
    """A tool call paired with its execution result.

    Used in ``LLMContext`` to preserve both what the model requested
    and what the local execution produced, so that message reconstruction
    can emit the ``{"role": "tool", ...}`` feedback turn.
    """

    call: LLMToolCall
    result: Optional[str] = None  # execution result text, if available


@dataclass
class TokenUsage:
    """Platform-irrelevant token usage summary produced by every LLM handler.

    Each handler normalizes its provider-specific usage response into this
    type so downstream consumers never need provider aliases or flattening.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """Fraction of input tokens served from the provider's prompt cache."""
        denominator = max(1, self.input_tokens)
        return round(min(100.0, self.cached_tokens / denominator * 100.0), 1)


@dataclass
class LLMOutput:
    """
    Backend-neutral non-streaming model output.
    this class will be created by handlers that handle the LLM call.
    """

    content: str                # 内容
    provider: str               # 模型提供者
    backend_name: str           # 后端名称
    model: str                  # 模型名称
    role: str = "assistant"     # 角色，支持 "assistant"、"system" 和 "user"
    reasoning_content: str = "" # 思考过程内容……
    tool_calls: List[LLMToolCall] = field(default_factory=list)
    stop_reason: Optional[str] = None
    usage: TokenUsage = field(default_factory=TokenUsage)

    @property
    def text(self) -> str:
        """Alias for assistant text content."""
        return self.content

    def __str__(self) -> str:
        """Return the assistant content for debug printing and logging."""
        return self.content



@dataclass
class LLMContext:
    """A single message in the conversation timeline."""

    role: str                                       # "assistant", "user", "system"
    timeline: int                                   # timeline
    content: str                                    # text content
    content_reasoning: str = ""                     # reasoning content (e.g. <think>...</think>)
    tool_calls: List[ToolInfo] = field(default_factory=list)  # tool calls + their results
    tags: List[str] = field(default_factory=list)             # optional tags


@dataclass
class LLMContextCompacted:
    """Summarised representation of one or more LLMContext entries."""

    abstract_msg: str                               # compacted summary text
    source_timeline: List[int] = field(default_factory=list)  # source timeline IDs
    source_uuid: List[str] = field(default_factory=list)      # source UUIDs
    tags: List[str] = field(default_factory=list)             # optional tags

    def __str__(self) -> str:
        return self.abstract_msg


# --------------------------
# Tool
# --------------------------

@dataclass
class ToolParameter:
    """A single parameter in a tool's JSON Schema."""

    name: str                           # 参数名
    type: str = "string"                # JSON Schema 类型
    description: str = ""               # 参数描述
    required: bool = True               # 是否必需
    enum: Optional[List[str]] = None    # 可选值枚举
    default: Optional[Any] = None       # 默认值


@dataclass
class ToolSchema:
    """Structured JSON Schema for tool parameters, replacing raw dicts."""

    type: str = "object"
    properties: List[ToolParameter] = field(default_factory=list)
    # External tool protocols such as MCP can provide nested JSON Schema that
    # cannot be represented by the compact ToolParameter model alone.  When
    # supplied, preserve that validated object verbatim for the LLM backend.
    raw_schema: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain JSON Schema dict for LLM API payloads."""
        if self.raw_schema is not None:
            return dict(self.raw_schema)
        required: List[str] = []
        props: Dict[str, Any] = {}
        for p in self.properties:
            prop: Dict[str, Any] = {"type": p.type}
            if p.description:
                prop["description"] = p.description
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            props[p.name] = prop
            if p.required:
                required.append(p.name)

        result: Dict[str, Any] = {"type": self.type, "properties": props}
        if required:
            result["required"] = required
        return result


@dataclass
class Tool:
    """A single tool that an Agent can call."""

    name: str                           # 工具名
    description: str                    # 工具描述
    schemas: ToolSchema                 # 工具入参 schemas
    handler: Callable[..., Any]         # sync or async callable

    def __str__(self):
        return f"""
        Tool name: {self.name}
        Tool description: {self.description}
        Tool schemas: {self.schemas.to_dict()}
    """
    
@dataclass
class ToolBatch:
    pass
