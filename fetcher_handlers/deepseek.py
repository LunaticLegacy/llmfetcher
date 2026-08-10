"""DeepSeek platform-specialised backend handler.

DeepSeek serves an OpenAI-compatible chat-completions endpoint, so
``DeepSeekHandler`` reuses the request construction, tool-call streaming
and tool-schema machinery of :class:`OpenAIHandler`. Two provider surfaces
are specialised here:

Reasoning field
    DeepSeek reasoner models (``deepseek-reasoner``) return their chain of
    thought in a dedicated ``reasoning_content`` field on the assistant
    message and on every streamed delta. Unlike the generic
    OpenAI-compatible handler, DeepSeek never falls back to the
    ``reasoning``/``thinking`` aliases used by other providers — those
    aliases can carry unrelated payloads and caused thinking leakage when
    DeepSeek traffic was routed through the generic handler.

Cache accounting
    DeepSeek reports prompt-cache economics as
    ``prompt_cache_hit_tokens`` / ``prompt_cache_miss_tokens`` on the usage
    object instead of OpenAI's ``prompt_tokens_details.cached_tokens`` or
    Anthropic's ``cache_read_input_tokens``. ``normalize_usage`` maps the
    hit counter onto :class:`TokenUsage.cached_tokens`.
"""

from __future__ import annotations

from typing import Mapping, Optional

from ..llm_types import TokenUsage
from .openai import OpenAIHandler


class DeepSeekHandler(OpenAIHandler):
    """OpenAI-compatible chat-completions handler specialised for DeepSeek."""

    provider_names = frozenset({"deepseek"})

    def _message_reasoning(
        self,
        message: object | Mapping[str, object] | None,
    ) -> str:
        """DeepSeek exposes reasoning exclusively via ``reasoning_content``.

        No fallback to ``reasoning``/``thinking``: those aliases belong to
        other platforms and could misclassify unrelated payloads.
        """
        reasoning = self._read_field(message, "reasoning_content", None)
        return str(reasoning or "")

    def _delta_reasoning(
        self,
        delta: object | Mapping[str, object] | None,
    ) -> Optional[str]:
        """Read ``reasoning_content`` from one streamed delta (and only that)."""
        if delta is None:
            return None
        if isinstance(delta, dict):
            reasoning = delta.get("reasoning_content")
        else:
            reasoning = getattr(delta, "reasoning_content", None)
        return str(reasoning) if reasoning else None

    def normalize_usage(
        self,
        usage: object | Mapping[str, object] | None,
    ) -> TokenUsage:
        """Map DeepSeek's ``prompt_cache_hit_tokens`` onto cached tokens.

        Reasoning tokens nested under ``completion_tokens_details`` are
        already flattened by the base implementation.
        """
        normalized = super().normalize_usage(usage)
        raw = self._usage_to_dict(usage)
        if not raw:
            return normalized
        if raw.get("cached_tokens") is None:
            hit = raw.get("prompt_cache_hit_tokens")
            if isinstance(hit, (int, float)):
                normalized.cached_tokens = int(hit)
        return normalized
