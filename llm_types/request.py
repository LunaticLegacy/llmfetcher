"""Outbound request descriptions shared with application hosts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, cast

from .json import JsonObject


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
    thinking_mode: str = "auto"
    reasoning_effort: str = "auto"

    def to_dict(self) -> JsonObject:
        """Return the JSON-safe event payload used by application hosts.

        Returns:
            A fresh top-level mapping containing only request fields that are
            safe to persist or render. Credentials and endpoint URLs are not
            part of this schema.
        """
        return cast("JsonObject", {
            "model": self.model,
            "messages": self.messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "thinking_mode": self.thinking_mode,
            "reasoning_effort": self.reasoning_effort,
            "stream": self.stream,
            "tools": self.tools,
        })


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
    extra: JsonObject = field(default_factory=dict)

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


__all__ = ["LLMBackendConfig", "RemoteRequestSnapshot"]
