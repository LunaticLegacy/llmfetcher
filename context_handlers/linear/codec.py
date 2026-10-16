"""Serialization between durable row payloads and context models.

The durable store exchanges plain JSON dictionaries. This module is the one
place that knows how ``LLMContext`` / ``LLMContextCompacted`` map onto them, so
persistence, paging and host readers share a single representation.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from ...llm_types import LLMContext, LLMContextCompacted, LLMToolCall, ToolInfo
from ...multimodal import validate_images


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
    return LLMContext(
        role=data["role"],
        timeline=data["timeline"],
        content=data.get("content", ""),
        images=validate_images(data.get('images', [])),
        content_reasoning=data.get("content_reasoning", ""),
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


__all__ = [
    "context_to_dict",
    "context_from_dict",
    "compacted_to_dict",
    "compacted_from_dict",
]
