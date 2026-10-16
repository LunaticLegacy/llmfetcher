"""Render durable context entries into provider-neutral request messages.

Tool-call shaping, image attachment and the post-compaction resume turn live
here, so ``ContextHandlerLinear`` only decides what to store, not how a
provider should receive it.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ...llm_types import LLMContext, LLMContextCompacted
from ...multimodal import validate_images

# Appended once after a successful compaction so the next request still has an
# explicit user turn; some providers reject a request without one.
_RESUME_PROMPT = "Continue user's job from your checkpoint, now."


def append_context_entry(messages: List[Dict[str, Any]], item: LLMContext) -> None:
    """Append backend-neutral messages for a single context entry.

    For assistant entries with tool calls this emits:
    1. An assistant message with ``tool_calls`` as a list of
       flat ``{"id", "name", "arguments"}`` dicts.
    2. A ``{"role": "tool", ...}`` message per tool call that has
       a result.

    This layer preserves every supplied tool result verbatim. A host may
    replace a large result with a stable artifact reference before it is
    recorded, but context reconstruction itself never truncates it.

    Args:
        messages: The message list being built (mutated in place).
        item: The context entry to convert.
    """
    role = item.role
    content = item.content

    # Prepend reasoning block when present.
    if item.content_reasoning.strip():
        reasoning_block = (
            f"<think>\n{item.content_reasoning.strip()}\n</think>"
        )
        content = (
            f"{reasoning_block}\n{content}"
            if content
            else reasoning_block
        )

    # Assistant turn with tool calls.
    if role == "assistant" and item.tool_calls:
        messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": [
                {
                    "id": ti.call.call_id or f"call_{i}",
                    "name": ti.call.name,
                    "arguments": ti.call.arguments,
                }
                for i, ti in enumerate(item.tool_calls)
            ],
        })
        for i, ti in enumerate(item.tool_calls):
            if ti.result is not None:
                call_id = ti.call.call_id or f"call_{i}"
                messages.append({
                    "role": "tool",
                    "content": str(ti.result),
                    "tool_call_id": call_id,
                    **({'images': validate_images(ti.images)} if ti.images else {}),
                })
        return

    messages.append({"role": role, "content": content or "",
                     **({'images': validate_images(item.images)} if item.images else {})})


def render_messages(
    history: List[LLMContext | LLMContextCompacted],
    *,
    pending_resume: bool,
) -> List[Dict[str, Any]]:
    """Render stored history into the message list for one request.

    Tool call data uses a flat structure:
    ``{"id": ..., "name": ..., "arguments": {...}}`` — no provider-specific
    wrapping. Compacted summaries (``LLMContextCompacted``) are emitted with
    ``role: "system"``.

    After a successful compaction the active buffer is empty, so the request
    would otherwise be system-only. ``pending_resume`` appends the derived
    resume user turn; it is intentionally ephemeral (never stored, never
    persisted, consumes no timeline slot).

    Args:
        history: Stored entries, compacted abstract first when present.
        pending_resume: Whether to append the derived resume user turn.

    Returns:
        A list of message dicts.
    """
    messages: List[Dict[str, Any]] = []
    for item in history:
        if isinstance(item, LLMContext):
            append_context_entry(messages, item)
        elif isinstance(item, LLMContextCompacted):
            messages.append({
                "role": "system",
                "content": str(item),
            })

    if pending_resume:
        messages.append({
            "role": "user",
            "content": _RESUME_PROMPT,
        })

    return messages


__all__ = ["append_context_entry", "render_messages"]
