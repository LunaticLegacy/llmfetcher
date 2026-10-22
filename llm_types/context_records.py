"""Explicit durable context records and their reference contract.

A context item is one ordered entry of the durable transcript.  Assistant
items never embed tool output: each tool call carries a
:class:`ToolResultId`, and the complete output lives in a separate
:class:`ToolResultRecord` resolved through :class:`ContextStore`.

Identifiers are minted once, when the record is first written, and are never
derived from a timeline, an array index or a page position.  Timeline values
may be renumbered by context editing; item and result identities may not.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol, TypeAlias
from uuid import uuid4

from ..multimodal import ImageReference
from .json import JsonObject
from .messages import TokenUsage


@dataclass(frozen=True)
class ContextItemId:
    """Stable identity of one durable context item.

    Attributes:
        value: Opaque identifier assigned when the item is first written.
    """

    value: str

    def __post_init__(self) -> None:
        """Reject an empty identity instead of accepting an unusable record.

        Raises:
            ValueError: If ``value`` is empty or whitespace.
        """
        if not self.value or not self.value.strip():
            raise ValueError("context item id must be a non-empty string")

    @classmethod
    def new(cls) -> "ContextItemId":
        """Mint a fresh identity for a newly written context item."""
        return cls(uuid4().hex)


@dataclass(frozen=True)
class ToolResultId:
    """Stable identity of one durable tool result.

    Attributes:
        value: Opaque identifier assigned when the result is first written.
    """

    value: str

    def __post_init__(self) -> None:
        """Reject an empty identity instead of accepting an unusable reference.

        Raises:
            ValueError: If ``value`` is empty or whitespace.
        """
        if not self.value or not self.value.strip():
            raise ValueError("tool result id must be a non-empty string")

    @classmethod
    def new(cls) -> "ToolResultId":
        """Mint a fresh identity for a newly written tool result."""
        return cls(uuid4().hex)


@dataclass(frozen=True)
class ToolCallRecord:
    """One tool invocation requested by an assistant turn.

    Attributes:
        call_id: Correlation identifier the tool result answers.
        name: Tool name the model asked for.
        arguments: Parsed arguments exactly as the model supplied them.
        result_id: Reference to the stored result, or ``None`` when the call
            produced no result.
    """

    call_id: str
    name: str
    arguments: JsonObject
    result_id: ToolResultId | None


@dataclass(frozen=True)
class ToolResultRecord:
    """One complete tool execution result, stored outside the transcript.

    Attributes:
        result_id: Stable identity the assistant item references.
        call_id: Correlation identifier of the originating tool call.
        tool_name: Tool name that produced this result.
        output: Complete result text.
        images: Durable image references the tool returned.
        ok: Whether execution succeeded, or ``None`` when the producer did
            not report a status.
        duration_ms: Execution wall time in milliseconds, or ``None``.
        created_at: Unix timestamp when the result completed, or ``None``.
    """

    result_id: ToolResultId
    call_id: str
    tool_name: str
    output: str
    images: tuple[ImageReference, ...]
    ok: bool | None
    duration_ms: int | None
    created_at: float | None


@dataclass(frozen=True)
class ToolCallInput:
    """One tool call as the model produced it, before a result is stored.

    Attributes:
        call_id: Provider correlation identifier; required so the durable
            turn can pair its result without inventing an index-based ID.
        name: Tool name the model asked for.
        arguments: Parsed arguments exactly as the model supplied them.
    """

    call_id: str
    name: str
    arguments: JsonObject

    def __post_init__(self) -> None:
        """Reject a call that cannot be correlated with its result.

        Raises:
            ValueError: If ``call_id`` is empty or whitespace.
        """
        if not self.call_id or not self.call_id.strip():
            raise ValueError("tool call requires a non-empty call_id")


@dataclass(frozen=True)
class ToolResultInput:
    """One completed tool execution offered to a context handler.

    Attributes:
        call_id: Correlation identifier of the originating tool call.
        tool_name: Tool name that produced this result.
        output: Complete result text.
        images: Durable image references the tool returned.
        ok: Whether execution succeeded, or ``None`` when unreported.
        duration_ms: Execution wall time in milliseconds, or ``None``.
        created_at: Unix timestamp when the result completed, or ``None``.
    """

    call_id: str
    tool_name: str
    output: str
    images: tuple[ImageReference, ...]
    ok: bool | None
    duration_ms: int | None
    created_at: float | None

    def __post_init__(self) -> None:
        """Reject a result that cannot be paired with a tool call.

        Raises:
            ValueError: If ``call_id`` or ``tool_name`` is empty.
        """
        if not self.call_id or not self.call_id.strip():
            raise ValueError("tool result requires a non-empty call_id")
        if not self.tool_name or not self.tool_name.strip():
            raise ValueError("tool result requires a non-empty tool_name")


@dataclass(frozen=True)
class AssistantTurnInput:
    """Complete input for one durable assistant turn.

    The agent boundary builds this from the model output plus the tool batch,
    so a handler never has to infer duration, status or usage from side
    channels.

    Attributes:
        content: Assistant text content.
        reasoning: Native reasoning text, kept separate from content.
        tool_calls: Tool calls this turn requested.
        usage: Token usage of the model call that produced this turn.
        model_duration_ms: Wall time spent generating this output.
        round_duration_ms: Whole round wall time, including tool execution.
        created_at: Unix timestamp when this turn completed.
    """

    content: str
    reasoning: str
    tool_calls: tuple[ToolCallInput, ...]
    usage: TokenUsage
    model_duration_ms: int | None
    round_duration_ms: int | None
    created_at: float | None

    def __post_init__(self) -> None:
        """Reject duplicate call identities in one turn.

        Raises:
            ValueError: If two tool calls share a ``call_id``.
        """
        call_ids = [call.call_id for call in self.tool_calls]
        if len(call_ids) != len(set(call_ids)):
            raise ValueError("assistant turn contains duplicate tool call ids")


@dataclass(frozen=True)
class UserContextItem:
    """One durable user input entry.

    Attributes:
        item_id: Stable identity of this entry.
        timeline: Ordering position in the active transcript.
        content: User input text.
        images: Durable image references the input carried.
    """

    kind: ClassVar[str] = "user"

    item_id: ContextItemId
    timeline: int
    content: str
    images: tuple[ImageReference, ...]


@dataclass(frozen=True)
class AssistantContextItem:
    """One durable assistant turn.

    The turn carries tool-call references only; resolving them is the
    store's job, so a reader can never mistake a missing result for an empty
    one.

    Attributes:
        item_id: Stable identity of this entry.
        timeline: Ordering position in the active transcript.
        content: Assistant text content.
        reasoning: Native reasoning text, kept separate from content.
        tool_calls: Tool calls this turn requested.
        usage: Token usage of the model call that produced this turn.
        model_duration_ms: Wall time spent generating this output.
        round_duration_ms: Whole round wall time, including tool execution.
        created_at: Unix timestamp when this turn completed.
    """

    kind: ClassVar[str] = "assistant"

    item_id: ContextItemId
    timeline: int
    content: str
    reasoning: str
    tool_calls: tuple[ToolCallRecord, ...]
    usage: TokenUsage
    model_duration_ms: int | None
    round_duration_ms: int | None
    created_at: float | None


@dataclass(frozen=True)
class ContextSummaryItem:
    """One compacted summary that replaced a contiguous transcript range.

    Attributes:
        item_id: Stable identity of the summary entry itself.
        timeline: Ordering position of the summary in the active transcript.
        abstract: Summary text that stands in for the collapsed entries.
        source_item_ids: Identities of the collapsed context items.
        source_timeline: Timeline values of the collapsed entries.
        source_result_ids: Tool results referenced by the collapsed entries.
    """

    kind: ClassVar[str] = "summary"

    item_id: ContextItemId
    timeline: int
    abstract: str
    source_item_ids: tuple[ContextItemId, ...]
    source_timeline: tuple[int, ...]
    source_result_ids: tuple[ToolResultId, ...]


ContextItem: TypeAlias = UserContextItem | AssistantContextItem | ContextSummaryItem
"""Every record that can occupy one position in the durable transcript."""


class ContextStore(Protocol):
    """Resolve durable references held by context items.

    A reader that receives a :class:`ToolResultId` must call this method and
    fail when the store cannot produce the record; it must never substitute
    an empty string or a placeholder.
    """

    def resolve_tool_result(self, result_id: ToolResultId) -> ToolResultRecord:
        """Return the complete result a context item references.

        Args:
            result_id: Reference carried by an assistant tool call.

        Returns:
            The stored result record.

        Raises:
            KeyError: When the reference has no stored result.
        """
        ...


__all__ = [
    "AssistantContextItem",
    "ContextItem",
    "ContextItemId",
    "ContextStore",
    "ContextSummaryItem",
    "ToolCallRecord",
    "ToolResultId",
    "ToolResultRecord",
    "UserContextItem",
]
