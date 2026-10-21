"""Provider-neutral LLM exception hierarchy."""

from __future__ import annotations


class LLMError(Exception):
    """Base exception for all LLM-related errors."""


class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""


class LLMBackendError(LLMError):
    """Raised when all candidate backends fail."""


class LLMRequestCancelled(LLMError):
    """Raised when a terminal force-stop cancels an in-flight LLM request."""


__all__ = [
    "LLMBackendError",
    "LLMError",
    "LLMRequestCancelled",
    "LLMTimeoutError",
]
