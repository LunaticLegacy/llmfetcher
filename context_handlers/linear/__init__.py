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

from .codec import (
    compacted_from_dict,
    compacted_to_dict,
    context_from_dict,
    context_to_dict,
)
from .compaction import (
    CompactionFetcher,
    CompactionRequestPreview,
    build_request_preview,
    estimate_context_size,
    parse_compacted_abstract,
)
from .handler import ContextHandlerLinear
from .paging import read_persisted_context_page
from .rendering import append_context_entry, render_messages

__all__ = [
    "ContextHandlerLinear",
    "CompactionFetcher",
    "CompactionRequestPreview",
    "read_persisted_context_page",
    "build_request_preview",
    "estimate_context_size",
    "parse_compacted_abstract",
    "context_to_dict",
    "context_from_dict",
    "compacted_to_dict",
    "compacted_from_dict",
    "append_context_entry",
    "render_messages",
]
