"""Bounded reverse-timeline paging over a persisted context checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

from ..storage import ContextStorage, SQLiteContextStorage, is_sqlite_context_pointer
from ..base import checkpoint_lock
from ...llm_types import ContextItem
from .codec import context_item_from_dict

_CONTEXT_PAGE_SIZE = 200


def read_persisted_context_page(
    path: str | Path,
    *,
    before_timeline: int | None = None,
    limit: int = _CONTEXT_PAGE_SIZE,
    include_archive: bool = False,
    storage: ContextStorage | None = None,
) -> tuple[list[ContextItem], int | None, int]:
    """Read one reverse-timeline page without loading the full checkpoint.

    Args:
        path: Context pointer JSON naming the durable row store.
        before_timeline: Exclusive older-than timeline cursor, if supplied.
        limit: Maximum returned entries. Values are bounded to 200.
        include_archive: Include compacted transcript rows for a read-only
            history projection.  Keep this ``False`` when hydrating an Agent:
            archived rows must not be restored into its active model context.
        storage: Optional durable reader; defaults to the SQLite
            implementation.

    Returns:
        Chronological page items, the next older cursor or ``None``, and the
        persisted total message count.

    Raises:
        ValueError: If the pointer is malformed or not a row-store pointer.
        OSError: If the checkpoint cannot be read.
    """
    target = Path(path)
    # Readers take the same lock as ``save``: on Windows a read handle on the
    # pointer denies the atomic replace that commits a new generation.
    with checkpoint_lock(target):
        pointer = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(pointer, dict):
            raise ValueError("checkpoint must be an object")
        if not is_sqlite_context_pointer(pointer):
            raise ValueError("context paging requires a row-store checkpoint")
        bounded = max(1, min(limit, _CONTEXT_PAGE_SIZE))
        page = (storage or SQLiteContextStorage()).read_page(
            target,
            before_timeline=before_timeline,
            limit=bounded,
            include_archive=include_archive,
        )
        return [context_item_from_dict(row) for row in page.rows], page.next_before, page.total


def read_persisted_archive_page(
    path: str | Path,
    *,
    before_timeline: int | None = None,
    limit: int = 50,
    storage: ContextStorage | None = None,
) -> tuple[list[ContextItem], int | None, bool]:
    """Read one archive-only page without loading the active transcript.

    Args:
        path: Row-store context pointer.
        before_timeline: Exclusive older-than timeline cursor.
        limit: Maximum returned entries, bounded to 200.
        storage: Optional durable reader; defaults to the SQLite implementation.

    Returns:
        Chronological archived items, the next older cursor, and whether
        another older page exists.

    Raises:
        ValueError: If the checkpoint is malformed or not a row-store pointer.
        OSError: If the checkpoint or database cannot be read.
    """
    target = Path(path)
    with checkpoint_lock(target):
        pointer = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(pointer, dict):
            raise ValueError("checkpoint must be an object")
        if not is_sqlite_context_pointer(pointer):
            raise ValueError("archive paging requires a row-store checkpoint")
        bounded = max(1, min(limit, _CONTEXT_PAGE_SIZE))
        page = (storage or SQLiteContextStorage()).read_archive_page(
            target,
            before_timeline=before_timeline,
            limit=bounded,
        )
        return [context_item_from_dict(row) for row in page.rows], page.next_before, page.has_more


__all__ = ["read_persisted_context_page", "read_persisted_archive_page"]
