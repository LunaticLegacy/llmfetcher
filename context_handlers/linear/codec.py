"""Serialization between durable row payloads and context models.

The durable store exchanges plain JSON dictionaries. This module is the one
place that knows how context records map onto them, so persistence, paging
and host readers share a single representation.

The ``LLMContext`` helpers are retained only until the linear handler finishes
moving to the explicit record model; the v2 helpers below are the contract the
new store uses.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Literal, Optional, cast

from ...llm_types import (
    AssistantContextItem,
    ContextItem,
    ContextItemId,
    ContextSummaryItem,
    JsonObject,
    JsonValue,
    LLMContext,
    LLMContextCompacted,
    LLMToolCall,
    TokenUsage,
    ToolCallRecord,
    ToolInfo,
    ToolResultId,
    ToolResultRecord,
    UserContextItem,
)
from ...multimodal import ImageReference, validate_images


def context_to_dict(ctx: LLMContext) -> Dict[str, Any]:
    """Serialize one durable context entry into its persisted row payload."""
    return asdict(ctx)


def context_from_dict(data: Dict[str, Any]) -> LLMContext:
    """Rebuild one durable context entry from a persisted row payload."""
    tool_calls: List[ToolInfo] = []
    for tc in data.get("tool_calls", []):
        call = LLMToolCall(
            name=tc["call"]["name"],
            arguments=tc["call"].get("arguments", {}),
            call_id=tc["call"].get("call_id"),
            source=tc["call"].get("source"),
        )
        tool_calls.append(ToolInfo(call=call, result=tc.get("result"), images=validate_images(tc.get('images', []))))
    # Older Session/context projections used ``reasoning`` or
    # ``reasoning_content`` for the same durable value.  Keep those records
    # usable after restart; otherwise DeepSeek history is rebuilt without the
    # native reasoning it requires on the next request.
    content_reasoning = data.get("content_reasoning")
    if not isinstance(content_reasoning, str):
        content_reasoning = data.get("reasoning_content")
    if not isinstance(content_reasoning, str):
        content_reasoning = data.get("reasoning", "")
    if not isinstance(content_reasoning, str):
        content_reasoning = ""
    return LLMContext(
        role=data["role"],
        timeline=data["timeline"],
        content=data.get("content", ""),
        images=validate_images(data.get('images', [])),
        content_reasoning=content_reasoning,
        tool_calls=tool_calls,
        tags=data.get("tags", []),
        usage=dict(data.get("usage") or {}),
        model_duration_ms=data.get("model_duration_ms"),
        round_duration_ms=data.get("round_duration_ms"),
        created_at=data.get("created_at"),
    )


def compacted_to_dict(
    comp: Optional[LLMContextCompacted],
) -> Optional[Dict[str, Any]]:
    """Serialize a compacted abstract, preserving ``None``."""
    if comp is None:
        return None
    return asdict(comp)


def compacted_from_dict(
    data: Optional[Dict[str, Any]],
) -> Optional[LLMContextCompacted]:
    """Rebuild a compacted abstract from its pointer payload."""
    if data is None:
        return None
    return LLMContextCompacted(
        abstract_msg=data["abstract_msg"],
        source_timeline=data.get("source_timeline", []),
        source_uuid=data.get("source_uuid", []),
        tags=data.get("tags", []),
    )


# -- v2 record codec -------------------------------------------------------


def _field(data: JsonObject, key: str) -> JsonValue:
    """Return one required payload field.

    Raises:
        ValueError: If the field is absent.
    """
    if key not in data:
        raise ValueError(f"context payload is missing {key!r}")
    return data[key]


def _text(data: JsonObject, key: str) -> str:
    """Return one required string field."""
    value = _field(data, key)
    if not isinstance(value, str):
        raise ValueError(f"context payload field {key!r} must be a string")
    return value


def _number(data: JsonObject, key: str) -> int:
    """Return one required integer field."""
    value = _field(data, key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"context payload field {key!r} must be an integer")
    return value


def _optional_int(data: JsonObject, key: str) -> int | None:
    """Return an optional integer field, rejecting wrong types."""
    value = _field(data, key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"context payload field {key!r} must be an integer or null")
    return value


def _optional_float(data: JsonObject, key: str) -> float | None:
    """Return an optional numeric field, rejecting wrong types."""
    value = _field(data, key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"context payload field {key!r} must be a number or null")
    return float(value)


def _objects(data: JsonObject, key: str) -> list[JsonObject]:
    """Return one required list of JSON objects."""
    value = _field(data, key)
    if not isinstance(value, list):
        raise ValueError(f"context payload field {key!r} must be a list")
    result: list[JsonObject] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError(f"context payload field {key!r} must contain objects")
        result.append(cast(JsonObject, entry))
    return result


def _texts(data: JsonObject, key: str) -> tuple[str, ...]:
    """Return one required list of strings."""
    value = _field(data, key)
    if not isinstance(value, list):
        raise ValueError(f"context payload field {key!r} must be a list")
    return tuple(_as_text(entry, key) for entry in value)


def _as_text(value: JsonValue, key: str) -> str:
    """Return one string list entry."""
    if not isinstance(value, str):
        raise ValueError(f"context payload field {key!r} must contain strings")
    return value


def _images_to_json(images: tuple[ImageReference, ...]) -> list[JsonValue]:
    """Encode durable image references without any image bytes."""
    result: list[JsonValue] = []
    for ref in images:
        payload: JsonObject = {
            "attachment_id": ref["attachment_id"],
            "media_type": ref["media_type"],
        }
        if "detail" in ref:
            payload["detail"] = ref["detail"]
        result.append(payload)
    return result


def _images_from_json(value: JsonValue) -> tuple[ImageReference, ...]:
    """Decode image references through the shared validator."""
    if not isinstance(value, list):
        raise ValueError("context payload field 'images' must be a list")
    refs: list[ImageReference] = []
    for entry in value:
        if not isinstance(entry, dict):
            raise ValueError("context payload field 'images' must contain objects")
        data = cast(JsonObject, entry)
        ref: ImageReference = {
            "attachment_id": _text(data, "attachment_id"),
            "media_type": _text(data, "media_type"),
        }
        detail = data.get("detail")
        if detail is not None:
            if not isinstance(detail, str) or detail not in {"auto", "low", "high"}:
                raise ValueError("context payload image detail is invalid")
            ref["detail"] = cast(Literal["auto", "low", "high"], detail)
        refs.append(ref)
    return tuple(validate_images(refs))


def _usage_to_json(usage: TokenUsage) -> JsonObject:
    """Encode one token-usage snapshot."""
    return {
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "cached_tokens": usage.cached_tokens,
        "reasoning_tokens": usage.reasoning_tokens,
    }


def _usage_from_json(value: JsonValue) -> TokenUsage:
    """Decode one token-usage snapshot."""
    if not isinstance(value, dict):
        raise ValueError("context payload field 'usage' must be an object")
    data = cast(JsonObject, value)
    return TokenUsage(
        input_tokens=_number(data, "input_tokens"),
        output_tokens=_number(data, "output_tokens"),
        total_tokens=_number(data, "total_tokens"),
        cached_tokens=_number(data, "cached_tokens"),
        reasoning_tokens=_number(data, "reasoning_tokens"),
    )


def _tool_call_to_json(call: ToolCallRecord) -> JsonObject:
    """Encode one tool-call reference."""
    return {
        "call_id": call.call_id,
        "name": call.name,
        "arguments": call.arguments,
        "result_id": call.result_id.value if call.result_id is not None else None,
    }


def _tool_call_from_json(data: JsonObject) -> ToolCallRecord:
    """Decode one tool-call reference without inventing an ID."""
    arguments = _field(data, "arguments")
    if not isinstance(arguments, dict):
        raise ValueError("tool call arguments must be an object")
    result_id_raw = _field(data, "result_id")
    if result_id_raw is None:
        result_id = None
    elif isinstance(result_id_raw, str):
        result_id = ToolResultId(result_id_raw)
    else:
        raise ValueError("tool call result_id must be a string or null")
    return ToolCallRecord(
        call_id=_text(data, "call_id"),
        name=_text(data, "name"),
        arguments=cast(JsonObject, arguments),
        result_id=result_id,
    )


def tool_result_to_dict(record: ToolResultRecord) -> JsonObject:
    """Serialize one complete tool result for its own storage row."""
    return {
        "result_id": record.result_id.value,
        "call_id": record.call_id,
        "tool_name": record.tool_name,
        "output": record.output,
        "images": _images_to_json(record.images),
        "ok": record.ok,
        "duration_ms": record.duration_ms,
        "created_at": record.created_at,
    }


def tool_result_from_dict(data: JsonObject) -> ToolResultRecord:
    """Rebuild one complete tool result from its storage row."""
    ok = _field(data, "ok")
    if ok is not None and not isinstance(ok, bool):
        raise ValueError("tool result ok must be a boolean or null")
    return ToolResultRecord(
        result_id=ToolResultId(_text(data, "result_id")),
        call_id=_text(data, "call_id"),
        tool_name=_text(data, "tool_name"),
        output=_text(data, "output"),
        images=_images_from_json(_field(data, "images")),
        ok=ok,
        duration_ms=_optional_int(data, "duration_ms"),
        created_at=_optional_float(data, "created_at"),
    )


def context_item_to_dict(item: ContextItem) -> JsonObject:
    """Serialize one ordered context item.

    The ``kind`` discriminator is the only dispatch key; the union is closed,
    so an unknown kind is a corrupt payload rather than a fallback path.
    """
    match item.kind:
        case "user":
            user = cast(UserContextItem, item)
            return {
                "kind": "user",
                "item_id": user.item_id.value,
                "timeline": user.timeline,
                "content": user.content,
                "images": _images_to_json(user.images),
            }
        case "assistant":
            assistant = cast(AssistantContextItem, item)
            return {
                "kind": "assistant",
                "item_id": assistant.item_id.value,
                "timeline": assistant.timeline,
                "content": assistant.content,
                "reasoning": assistant.reasoning,
                "tool_calls": [
                    _tool_call_to_json(call) for call in assistant.tool_calls
                ],
                "usage": _usage_to_json(assistant.usage),
                "model_duration_ms": assistant.model_duration_ms,
                "round_duration_ms": assistant.round_duration_ms,
                "created_at": assistant.created_at,
            }
        case "summary":
            summary = cast(ContextSummaryItem, item)
            return {
                "kind": "summary",
                "item_id": summary.item_id.value,
                "timeline": summary.timeline,
                "abstract": summary.abstract,
                "source_item_ids": [
                    value.value for value in summary.source_item_ids
                ],
                "source_timeline": list(summary.source_timeline),
                "source_result_ids": [
                    value.value for value in summary.source_result_ids
                ],
            }
        case _:
            raise ValueError(f"unsupported context item kind: {item.kind!r}")


def context_item_from_dict(data: JsonObject) -> ContextItem:
    """Rebuild one ordered context item from its storage row."""
    kind = _text(data, "kind")
    match kind:
        case "user":
            return UserContextItem(
                item_id=ContextItemId(_text(data, "item_id")),
                timeline=_number(data, "timeline"),
                content=_text(data, "content"),
                images=_images_from_json(_field(data, "images")),
            )
        case "assistant":
            return AssistantContextItem(
                item_id=ContextItemId(_text(data, "item_id")),
                timeline=_number(data, "timeline"),
                content=_text(data, "content"),
                reasoning=_text(data, "reasoning"),
                tool_calls=tuple(
                    _tool_call_from_json(entry)
                    for entry in _objects(data, "tool_calls")
                ),
                usage=_usage_from_json(_field(data, "usage")),
                model_duration_ms=_optional_int(data, "model_duration_ms"),
                round_duration_ms=_optional_int(data, "round_duration_ms"),
                created_at=_optional_float(data, "created_at"),
            )
        case "summary":
            return ContextSummaryItem(
                item_id=ContextItemId(_text(data, "item_id")),
                timeline=_number(data, "timeline"),
                abstract=_text(data, "abstract"),
                source_item_ids=tuple(
                    ContextItemId(value) for value in _texts(data, "source_item_ids")
                ),
                source_timeline=tuple(
                    _number_entry(value)
                    for value in _field_list(data, "source_timeline")
                ),
                source_result_ids=tuple(
                    ToolResultId(value) for value in _texts(data, "source_result_ids")
                ),
            )
        case _:
            raise ValueError(f"unsupported context item kind: {kind!r}")


def _field_list(data: JsonObject, key: str) -> list[JsonValue]:
    """Return one required generic list field."""
    value = _field(data, key)
    if not isinstance(value, list):
        raise ValueError(f"context payload field {key!r} must be a list")
    return value


def _number_entry(value: JsonValue) -> int:
    """Return one integer list entry."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("context payload list must contain integers")
    return value


__all__ = [
    "context_to_dict",
    "context_from_dict",
    "compacted_to_dict",
    "compacted_from_dict",
    "context_item_to_dict",
    "context_item_from_dict",
    "tool_result_to_dict",
    "tool_result_from_dict",
]
