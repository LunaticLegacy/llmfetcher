"""Provider-neutral messages, model output, and conversation entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, TypeAlias, cast

from ..multimodal import ImageReference
from .json import JsonObject, JsonValue

MessageRole: TypeAlias = Literal["system", "user", "assistant", "tool"]
"""The four roles a provider-neutral request message can carry."""


@dataclass(frozen=True)
class ToolCallPayload:
    """One tool call as a provider-neutral request message carries it.

    Attributes:
        id: Correlation identifier the matching tool result refers to.
        name: Tool name the model asked for.
        arguments: Parsed arguments exactly as the model supplied them.
    """

    id: str
    name: str
    arguments: JsonObject

    def to_dict(self) -> JsonObject:
        """Return this tool call as the provider-neutral wire mapping.

        Returns:
            A fresh mapping whose ``arguments`` pass through unchanged.
        """
        return {"id": self.id, "name": self.name, "arguments": self.arguments}


@dataclass(frozen=True)
class RequestMessage:
    """One provider-neutral message of a dispatch-ready request.

    The rendered counterpart of :class:`LLMContext`: ``role`` decides which of
    the remaining fields carry meaning, so ``tool_calls`` describes an
    assistant turn that requested tools, ``tool_call_id`` correlates the
    ``tool`` turn answering one, and ``images`` travels with an entry that had
    image references. Reasoning is deliberately not a field of its own: the
    render layer folds it into ``content`` inside a ``<think>`` block.

    Attributes:
        role: Conversation role this message plays.
        content: Message text, or ``None`` for an assistant turn whose only
            output was a tool request.
        tool_calls: Tool calls requested by an assistant turn.
        tool_call_id: Identifier of the tool call a ``tool`` message answers.
        images: Durable image references the source entry carried.
    """

    role: MessageRole
    content: Optional[str] = None
    tool_calls: List[ToolCallPayload] = field(default_factory=list)
    tool_call_id: Optional[str] = None
    images: List[ImageReference] = field(default_factory=list)

    def to_dict(self) -> JsonObject:
        """Return this message as the wire mapping a provider adapter reads.

        Only the fields the role actually uses are present, so the mapping is
        identical to the one the render layer used to assemble by hand.
        ``images`` carries :class:`~llmfetcher.multimodal.ImageReference`
        objects rather than serialized data — the provider adapters resolve
        them — so that single value is cast into the JSON mapping the dispatch
        layer expects.

        Returns:
            A fresh mapping containing this message's populated fields.
        """
        payload: JsonObject = {"role": self.role, "content": self.content}
        if self.tool_calls:
            payload["tool_calls"] = [call.to_dict() for call in self.tool_calls]
        if self.tool_call_id is not None:
            payload["tool_call_id"] = self.tool_call_id
        if self.images:
            payload["images"] = cast(JsonValue, self.images)
        return payload


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
    images: list[ImageReference] = field(default_factory=list)


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
    # Observability belongs to the durable assistant turn, rather than to an
    # ephemeral execution event.  Keys use the console/API names so this
    # record remains provider-neutral and JSON-safe.
    usage: Dict[str, int] = field(default_factory=dict)
    model_duration_ms: Optional[int] = None
    round_duration_ms: Optional[int] = None
    created_at: Optional[float] = None
    images: list[ImageReference] = field(default_factory=list)


@dataclass
class LLMContextCompacted:
    """Summarised representation of one or more LLMContext entries."""

    abstract_msg: str                               # compacted summary text
    source_timeline: List[int] = field(default_factory=list)  # source timeline IDs
    source_uuid: List[str] = field(default_factory=list)      # source UUIDs
    tags: List[str] = field(default_factory=list)             # optional tags

    def __str__(self) -> str:
        return self.abstract_msg


__all__ = [
    "LLMContext",
    "LLMContextCompacted",
    "LLMOutput",
    "LLMToolCall",
    "MessageRole",
    "RequestMessage",
    "TokenUsage",
    "ToolCallPayload",
    "ToolInfo",
]
