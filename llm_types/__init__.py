"""Provider-neutral LLM types shared by the kernel and its host application.

This package replaces the former single-module ``llm_types.py``.  Every name
that module exported is re-exported here, so ``from llmfetcher.llm_types import
X`` keeps working unchanged; the modules below exist only to keep the
declarations grouped by concern.

- :mod:`.json` — JSON value aliases.
- :mod:`.errors` — the LLM exception hierarchy.
- :mod:`.messages` — conversation entries, model output, token usage.
- :mod:`.context_records` — explicit context items and tool-result references.
- :mod:`.request` — outbound request description and backend configuration.
- :mod:`.tools` — tool declarations, schemas, and the handler contract.
"""

from __future__ import annotations

from .context_records import (
    AssistantContextItem,
    ContextItem,
    ContextItemId,
    ContextStore,
    ContextSummaryItem,
    ToolCallRecord,
    ToolResultId,
    ToolResultRecord,
    UserContextItem,
)
from .errors import (
    LLMBackendError,
    LLMError,
    LLMRequestCancelled,
    LLMTimeoutError,
)
from .json import JsonArray, JsonObject, JsonScalar, JsonValue
from .messages import (
    LLMContext,
    LLMContextCompacted,
    LLMOutput,
    LLMToolCall,
    MessageRole,
    RequestMessage,
    TokenUsage,
    ToolCallPayload,
    ToolInfo,
)
from .request import LLMBackendConfig, RemoteRequestSnapshot
from .tools import Tool, ToolBatch, ToolCallable, ToolParameter, ToolSchema

__all__ = [
    "JsonArray",
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "LLMBackendConfig",
    "LLMBackendError",
    "LLMContext",
    "LLMContextCompacted",
    "LLMError",
    "LLMOutput",
    "LLMRequestCancelled",
    "LLMTimeoutError",
    "LLMToolCall",
    "MessageRole",
    "RemoteRequestSnapshot",
    "RequestMessage",
    "TokenUsage",
    "Tool",
    "ToolBatch",
    "ToolCallable",
    "ToolCallPayload",
    "ToolInfo",
    "ToolParameter",
    "ToolSchema",
]
