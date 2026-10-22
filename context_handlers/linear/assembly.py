"""Assemble context items and resolved tool results into one request.

The assembler is the only place that joins the two durable collections. It
walks the ordered items, resolves every ``result_id`` through the store, and
emits both projections from that single walk:

- the model projection, strictly ordered ``RequestMessage`` values;
- the observation projection, one row per source fragment, used by previews.

``INTERLEAVED`` places each result directly after its assistant turn;
``DEFERRED`` emits no ``tool`` message and merges every result into one
``system`` block whose entries carry the ``call_id`` they answer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, Sequence, TypeAlias, cast

from ..placement import RESUME_PROMPT, ToolResultPlacement
from ...llm_types import (
    AssistantContextItem,
    ContextItem,
    ContextItemId,
    ContextStore,
    ContextSummaryItem,
    JsonObject,
    JsonValue,
    RequestMessage,
    ToolCallPayload,
    ToolResultId,
    ToolResultRecord,
    UserContextItem,
)

ObservationKind: TypeAlias = Literal[
    "user",
    "assistant",
    "reasoning",
    "tool_call",
    "tool_result",
    "tool_results",
    "summary",
]
"""Every independently inspectable fragment the assembler can emit."""


class ContextAssemblyError(RuntimeError):
    """Raised when a transcript cannot produce a valid model request."""


@dataclass(frozen=True)
class ContextObservation:
    """One source fragment of an assembled request.

    Attributes:
        kind: Fragment kind that decides how a preview renders it.
        source: Stable provenance label for the fragment.
        item_id: Context item that owns the fragment, when it has one.
        timeline: Owning item's ordering position, when it has one.
        call_id: Tool call the fragment describes, when applicable.
        result_id: Stored result the fragment describes, when applicable.
        characters: Rendered character count of the fragment.
        truncated: Whether the request projection trimmed this fragment.
        ok: Tool status, when the producer reported it.
        duration_ms: Tool wall time, when the producer reported it.
    """

    kind: ObservationKind
    source: str
    item_id: ContextItemId | None
    timeline: int | None
    call_id: str | None
    result_id: ToolResultId | None
    characters: int
    truncated: bool
    ok: bool | None
    duration_ms: int | None


@dataclass(frozen=True)
class AssembledContext:
    """The model and observation projections of one request.

    Attributes:
        messages: Exact provider-neutral request sequence.
        observations: Source fragments produced by the same walk.
    """

    messages: tuple[RequestMessage, ...]
    observations: tuple[ContextObservation, ...]


class ContextAssembler:
    """Join ordered context items with the results they reference.

    Args:
        store: Resolver for every ``ToolResultId`` a transcript carries.
    """

    def __init__(self, store: ContextStore) -> None:
        self._store = store

    def assemble(
        self,
        items: Sequence[ContextItem],
        *,
        placement: ToolResultPlacement = ToolResultPlacement.INTERLEAVED,
        pending_resume: bool = False,
    ) -> AssembledContext:
        """Build both projections for one model request.

        Args:
            items: Ordered active context items, oldest first.
            placement: How tool results are placed relative to their calls.
            pending_resume: Whether to append the derived post-compaction turn.

        Returns:
            The assembled request and its observation rows.

        Raises:
            ContextAssemblyError: If the transcript cannot be paired, or an
                unsupported item kind is supplied.
            KeyError: If the store cannot resolve a referenced result.
        """
        messages: list[RequestMessage] = []
        observations: list[ContextObservation] = []
        deferred: list[tuple[str, ToolResultRecord]] = []
        last_user_index: int | None = None

        for item in items:
            match item.kind:
                case "summary":
                    summary = cast(ContextSummaryItem, item)
                    messages.append(RequestMessage(role="system", content=summary.abstract))
                    observations.append(ContextObservation(
                        kind="summary",
                        source="linear.summary",
                        item_id=summary.item_id,
                        timeline=summary.timeline,
                        call_id=None,
                        result_id=None,
                        characters=len(summary.abstract),
                        truncated=False,
                        ok=None,
                        duration_ms=None,
                    ))
                case "user":
                    user = cast(UserContextItem, item)
                    last_user_index = len(messages)
                    messages.append(RequestMessage(
                        role="user",
                        content=user.content,
                        images=list(user.images),
                    ))
                    observations.append(ContextObservation(
                        kind="user",
                        source="linear.user",
                        item_id=user.item_id,
                        timeline=user.timeline,
                        call_id=None,
                        result_id=None,
                        characters=len(user.content),
                        truncated=False,
                        ok=None,
                        duration_ms=None,
                    ))
                case "assistant":
                    assistant = cast(AssistantContextItem, item)
                    messages.append(RequestMessage(
                        role="assistant",
                        content=_fold_reasoning(assistant.reasoning, assistant.content) or None,
                        tool_calls=[
                            ToolCallPayload(
                                id=call.call_id,
                                name=call.name,
                                arguments=call.arguments,
                            )
                            for call in assistant.tool_calls
                        ],
                    ))
                    observations.append(ContextObservation(
                        kind="assistant",
                        source="linear.assistant",
                        item_id=assistant.item_id,
                        timeline=assistant.timeline,
                        call_id=None,
                        result_id=None,
                        characters=len(assistant.content),
                        truncated=False,
                        ok=None,
                        duration_ms=None,
                    ))
                    if assistant.reasoning.strip():
                        observations.append(ContextObservation(
                            kind="reasoning",
                            source="linear.assistant",
                            item_id=assistant.item_id,
                            timeline=assistant.timeline,
                            call_id=None,
                            result_id=None,
                            characters=len(assistant.reasoning),
                            truncated=False,
                            ok=None,
                            duration_ms=None,
                        ))
                    for call in assistant.tool_calls:
                        observations.append(ContextObservation(
                            kind="tool_call",
                            source="linear.tool_call",
                            item_id=assistant.item_id,
                            timeline=assistant.timeline,
                            call_id=call.call_id,
                            result_id=call.result_id,
                            characters=len(json.dumps(call.arguments, ensure_ascii=False)),
                            truncated=False,
                            ok=None,
                            duration_ms=None,
                        ))
                        if call.result_id is None:
                            continue
                        result = self._store.resolve_tool_result(call.result_id)
                        if placement is ToolResultPlacement.INTERLEAVED:
                            messages.append(RequestMessage(
                                role="tool",
                                content=result.output,
                                tool_call_id=call.call_id,
                                images=list(result.images),
                            ))
                        else:
                            deferred.append((call.call_id, result))
                        observations.append(ContextObservation(
                            kind="tool_result",
                            source=(
                                "linear.tool_result"
                                if placement is ToolResultPlacement.INTERLEAVED
                                else "linear.system.tool_results"
                            ),
                            item_id=assistant.item_id,
                            timeline=assistant.timeline,
                            call_id=call.call_id,
                            result_id=call.result_id,
                            characters=len(result.output),
                            truncated=False,
                            ok=result.ok,
                            duration_ms=result.duration_ms,
                        ))
                case _:
                    raise ContextAssemblyError(
                        f"unsupported context item kind: {item.kind!r}"
                    )

        if placement is ToolResultPlacement.INTERLEAVED:
            _validate_interleaved(messages)
        else:
            block = _deferred_message(deferred)
            if block is not None:
                insert_at = last_user_index if last_user_index is not None else len(messages)
                messages.insert(insert_at, block)
                observations.append(ContextObservation(
                    kind="tool_results",
                    source="linear.system.tool_results",
                    item_id=None,
                    timeline=None,
                    call_id=None,
                    result_id=None,
                    characters=len(block.content or ""),
                    truncated=False,
                    ok=None,
                    duration_ms=None,
                ))

        if pending_resume:
            messages.append(RequestMessage(role="user", content=RESUME_PROMPT))

        return AssembledContext(tuple(messages), tuple(observations))


def _fold_reasoning(reasoning: str, content: str) -> str:
    """Fold native reasoning into content inside a ``<think>`` block."""
    if not reasoning.strip():
        return content
    block = f"<think>\n{reasoning.strip()}\n</think>"
    return f"{block}\n{content}" if content else block


def _deferred_message(entries: Sequence[tuple[str, ToolResultRecord]]) -> RequestMessage | None:
    """Merge every deferred result into one system message."""
    if not entries:
        return None
    seen: set[str] = set()
    payload: list[JsonValue] = []
    for call_id, result in entries:
        if call_id in seen:
            raise ContextAssemblyError(
                f"deferred tool results repeat call_id {call_id!r}"
            )
        seen.add(call_id)
        entry: JsonObject = {
            "call_id": call_id,
            "result_id": result.result_id.value,
            "name": result.tool_name,
            "ok": result.ok,
            "duration_ms": result.duration_ms,
            "output": result.output,
        }
        payload.append(entry)
    return RequestMessage(
        role="system",
        content=json.dumps({"tool_results": payload}, ensure_ascii=False),
    )


def _validate_interleaved(messages: Sequence[RequestMessage]) -> None:
    """Reject a tool message that does not answer the preceding assistant turn."""
    open_calls: set[str] = set()
    for message in messages:
        if message.role == "assistant":
            open_calls = {call.id for call in message.tool_calls}
        elif message.role == "tool":
            if message.tool_call_id not in open_calls:
                raise ContextAssemblyError(
                    f"tool result {message.tool_call_id!r} does not answer the "
                    "preceding assistant turn"
                )
            open_calls.remove(cast(str, message.tool_call_id))
        else:
            open_calls = set()


__all__ = [
    "AssembledContext",
    "ContextAssembler",
    "ContextAssemblyError",
    "ContextObservation",
    "ObservationKind",
]
