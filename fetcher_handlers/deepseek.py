"""DeepSeek platform-specialised backend handler.

DeepSeek serves an OpenAI-compatible chat-completions endpoint, so
``DeepSeekHandler`` reuses the request construction, tool-call streaming
and tool-schema machinery of :class:`OpenAIHandler`. Three provider
surfaces are specialised here:

Reasoning field
    DeepSeek reasoner models (``deepseek-reasoner``) return their chain of
    thought in a dedicated ``reasoning_content`` field on the assistant
    message and on every streamed delta. Unlike the generic
    OpenAI-compatible handler, DeepSeek never falls back to the
    ``reasoning``/``thinking`` aliases used by other providers — those
    aliases can carry unrelated payloads and caused thinking leakage when
    DeepSeek traffic was routed through the generic handler.

<think> feedback loop
    The generic linear context handler wraps each assistant's reasoning in
    ``<think>...</think>`` and prepends it to the message content when it
    reconstructs conversation history. DeepSeek reasoner models already
    carry reasoning natively via ``reasoning_content``, so seeing those
    wrapped blocks in content makes them *mimic* the markers — raw
    ``<think>`` then leaks into their ``content`` (sometimes with broken
    XML fragments). This handler therefore:
      * strips ``<think>...</think>`` blocks from assistant content before
        every request (outbound), and
      * moves any ``<think>...</think>`` block the model still emits inside
        its content into ``reasoning_content`` (inbound), so the UI never
        shows the raw markers.

Cache accounting
    DeepSeek reports prompt-cache economics as
    ``prompt_cache_hit_tokens`` / ``prompt_cache_miss_tokens`` on the usage
    object instead of OpenAI's ``prompt_tokens_details.cached_tokens`` or
    Anthropic's ``cache_read_input_tokens``. ``normalize_usage`` maps the
    hit counter onto :class:`TokenUsage.cached_tokens`.
"""

from __future__ import annotations

import re
from typing import Any, List, Mapping, Optional, Sequence
from urllib.parse import urlparse

from ..llm_types import LLMOutput, TokenUsage, LLMBackendConfig
from .openai import OpenAIHandler

_THINK_BLOCK = re.compile(r"<think>(.*?)</think>", re.DOTALL)


class DeepSeekHandler(OpenAIHandler):
    """OpenAI-compatible chat-completions handler specialised for DeepSeek."""

    provider_names = frozenset({"deepseek"})
    selection_priority = 100

    @classmethod
    def supports_backend(cls, backend: LLMBackendConfig) -> bool:
        """Recognise DeepSeek behind an OpenAI-compatible configuration.

        ``provider="openai"`` describes the request wire format, not
        necessarily the model platform.  The explicit compatibility profile
        is preferred; the official DeepSeek hostname and DeepSeek model
        family are safe automatic signals for existing configurations.
        Other OpenAI-compatible endpoints retain the generic handler.
        """
        if backend.provider == "deepseek":
            return True
        if backend.provider != "openai":
            return False

        profile = (backend.compatibility_profile or "").strip().lower()
        if profile:
            return profile == "deepseek"

        model = (backend.model or "").strip().lower()
        if model.startswith("deepseek"):
            return True

        api_url = (backend.api_url or "").strip()
        hostname = (urlparse(api_url).hostname or "").lower()
        return hostname == "deepseek.com" or hostname.endswith(".deepseek.com")

    # -- reasoning extraction (native channel only) -----------------------

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

    # -- <think> feedback-loop control ------------------------------------

    @staticmethod
    def _strip_think_blocks(text: str) -> str:
        """Remove ``<think>...</think>`` blocks from assistant content.

        The generic context handler wraps previous reasoning in these
        markers when rebuilding history; DeepSeek must never see them in
        ``content`` because it carries reasoning natively and would mimic
        the markers in its own output.
        """
        return _THINK_BLOCK.sub("", text)

    @staticmethod
    def _split_think_blocks(text: str) -> tuple[str, str]:
        """Move ``<think>...</think>`` blocks out of model content.

        Returns:
            ``(content_without_blocks, concatenated_thinking)``. Only
            well-formed blocks are extracted; malformed leftovers stay in
            content so no legitimate output is dropped.
        """
        thinking: list[str] = []

        def _replace(match: "re.Match[str]") -> str:
            thinking.append(match.group(1).strip())
            return ""

        return _THINK_BLOCK.sub(_replace, text).strip(), "\n\n".join(thinking)

    def _sanitize_messages(
        self,
        messages: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Strip context-handler ``<think>`` wrappers from assistant turns."""
        out: list[dict[str, Any]] = []
        for msg in messages:
            if (
                isinstance(msg, dict)
                and msg.get("role") == "assistant"
                and isinstance(msg.get("content"), str)
                and "<think>" in msg["content"]
            ):
                msg = {**msg, "content": self._strip_think_blocks(msg["content"])}
            out.append(dict(msg) if isinstance(msg, dict) else msg)
        return out

    def create_completion(
        self,
        *,
        messages,
        temperature: float,
        max_tokens: int,
        stream: bool,
        tools: List["Any"] = None,
    ):
        """Send a request with assistant ``<think>`` wrappers removed."""
        return super().create_completion(
            messages=self._sanitize_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            tools=tools,
        )

    def normalize_completion_response(self, response) -> LLMOutput:
        """Extract any ``<think>`` the model echoed into ``reasoning_content``."""
        out = super().normalize_completion_response(response)
        clean_content, leaked_thinking = self._split_think_blocks(out.content)
        if not leaked_thinking:
            return out
        merged = "\n\n".join(
            part for part in (out.reasoning_content, leaked_thinking) if part
        )
        return LLMOutput(
            content=clean_content,
            provider=out.provider,
            backend_name=out.backend_name,
            model=out.model,
            role=out.role,
            reasoning_content=merged,
            tool_calls=out.tool_calls,
            stop_reason=out.stop_reason,
            usage=out.usage,
        )

    # -- cache accounting -------------------------------------------------

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
