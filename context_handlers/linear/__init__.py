"""Durable linear context as a package.

``ContextHandlerLinear`` (``handler.py``) is the public entry point; it owns
the transcript state and delegates each concern to a sibling module:

- ``codec.py`` — serialization between row payloads and context models
- ``compaction.py`` — compaction prompt, request planning and abstract parsing
- ``rendering.py`` — provider-neutral rendering of entries into request messages
- ``paging.py`` — bounded reverse-timeline reads over a persisted checkpoint

Importing ``llmfetcher.context_handlers.linear`` keeps the historical module
surface: ``ContextHandlerLinear``, ``CompactionFetcher``,
``CompactionRequestPreview`` and ``read_persisted_context_page``.
"""

from __future__ import annotations

from .assembly import (
    AssembledContext,
    ContextAssembler,
    ContextAssemblyError,
    ContextObservation,
)
from .codec import (
    context_item_from_dict,
    context_item_to_dict,
    tool_result_from_dict,
    tool_result_to_dict,
)
from .compaction import (
    CompactionFetcher,
    CompactionRequestPreview,
    build_request_preview,
    estimate_context_size,
    parse_compacted_abstract,
)
from .handler import ContextHandlerLinear
from .paging import read_persisted_archive_page, read_persisted_context_page
from .rendering import render_messages

__all__ = [
    "AssembledContext",
    "ContextAssembler",
    "ContextAssemblyError",
    "ContextObservation",
    "ContextHandlerLinear",
    "CompactionFetcher",
    "CompactionRequestPreview",
    "read_persisted_context_page",
    "read_persisted_archive_page",
    "build_request_preview",
    "estimate_context_size",
    "parse_compacted_abstract",
    "context_item_to_dict",
    "context_item_from_dict",
    "tool_result_to_dict",
    "tool_result_from_dict",
    "render_messages",
]
