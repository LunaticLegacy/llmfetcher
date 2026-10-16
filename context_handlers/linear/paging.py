"""Bounded reverse-timeline paging over a persisted context checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

from ..storage import ContextStorage, SQLiteContextStorage, is_sqlite_context_pointer
from ...llm_types import LLMContext
from .codec import context_from_dict

_CONTEXT_PAGE_SIZE = 200


def read_persisted_context_page(
    path: str | Path,
    *,
    before_timeline: int | None = None,
    limit: int = _CONTEXT_PAGE_SIZE,
    include_archive: bool = False,
    storage: ContextStorage | None = None,
) -> tuple[list[LLMContext], int | None, int]:
    """Read one reverse-timeline page without loading the full checkpoint.

    Args:
        path: Context pointer JSON or legacy full-JSON checkpoint path.
        before_timeline: Exclusive older-than timeline cursor, if supplied.
        limit: Maximum returned entries. Values are bounded to 200.
        include_archive: Include compacted transcript rows for a read-only
            history projection.  Keep this ``False`` when hydrating an Agent:
            archived rows must not be restored into its active model context.
        storage: Optional durable reader; defaults to the SQLite
            implementation. Injecting it keeps the SQL boundary owned by one
            component instead of being re-created at every call site.

    Returns:
        Chronological page entries, the next older cursor or ``None``, and
        the persisted total message count.

    Raises:
        ValueError: If the pointer is malformed or an entry is invalid.
        OSError: If the checkpoint cannot be read.
    """
    target = Path(path)
    pointer = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(pointer, dict):
        raise ValueError("checkpoint must be an object")
    bounded = max(1, min(limit, _CONTEXT_PAGE_SIZE))
    if is_sqlite_context_pointer(pointer):
        page = (storage or SQLiteContextStorage()).read_page(
            target,
            before_timeline=before_timeline,
            limit=bounded,
            include_archive=include_archive,
        )
        return [context_from_dict(row) for row in page.rows], page.next_before, page.total
    # Legacy compatibility is deliberately bounded for callers. Migration is
    # the required route for large checkpoints because a JSON array is not
    # randomly addressable.
    entries_raw = pointer.get("messages", [])
    if not isinstance(entries_raw, list):
        raise ValueError("legacy checkpoint messages must be a list")
    filtered = [item for item in entries_raw if isinstance(item, dict) and (before_timeline is None or item.get("timeline", 0) < before_timeline)]
    selected = filtered[-bounded:]
    next_cursor = selected[0].get("timeline") if len(filtered) > len(selected) and selected else None
    return [context_from_dict(item) for item in selected], next_cursor, len(entries_raw)


__all__ = ["read_persisted_context_page"]
