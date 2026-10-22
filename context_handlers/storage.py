"""Persistence ports and the SQLite implementation for context handlers.

The context handlers own the shape of their messages.  This module owns only
the durable row store and its bounded paging operations, keeping SQLite
details out of composed handlers and host applications.

Every schema fact lives here: the two row tables, their primary keys, the
archive invariant and the version-3 pointer marker. Callers exchange
serialized payloads and never construct SQL.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

from .base import checkpoint_lock


@dataclass(frozen=True)
class PersistedContextPage:
    """One bounded page returned from durable context storage.

    Attributes:
        rows: Deserialized payloads in chronological order.
        next_before: Exclusive older-than cursor, or ``None`` when exhausted.
        total: Total rows visible to the query that produced this page.
    """

    rows: list[dict[str, Any]]
    next_before: int | None
    total: int


@dataclass(frozen=True)
class PersistedArchivePage:
    """One bounded archive-only page returned from durable storage.

    Attributes:
        rows: Deserialized archived payloads in chronological order.
        next_before: Exclusive older-than cursor, or ``None`` when exhausted.
        has_more: Whether at least one older archived row exists.
    """

    rows: list[dict[str, Any]]
    next_before: int | None
    has_more: bool


def is_sqlite_context_pointer(pointer: Any) -> bool:
    """Return whether a parsed checkpoint is a schema-3 SQLite pointer.

    This is the single place that recognizes the durable row-store format so
    readers do not each re-implement the version/storage test.

    Args:
        pointer: A parsed checkpoint object, or any value read from disk.

    Returns:
        ``True`` only for a mapping declaring schema version 3 and the
        ``sqlite`` storage marker.
    """
    return (
        isinstance(pointer, dict)
        and pointer.get("schema_version") == 3
        and pointer.get("storage") == "sqlite"
    )


class ContextStorage(Protocol):
    """Storage contract used by durable context handlers.

    Implementations persist serialized active and archived transcript rows and
    expose bounded reads. Timelines are unique integers per table.
    """

    def append_rows(
        self,
        database: Path,
        messages: Sequence[tuple[int, str]],
        archive: Sequence[tuple[int, str]],
        tool_results: Sequence[tuple[str, str]] = (),
    ) -> None:
        """Append or replace serialized rows atomically.

        Archiving a timeline removes that timeline from active ``messages``
        within the same transaction; this is the storage invariant that keeps
        compacted rows out of the active transcript. Tool results share the
        transaction so a reference written in ``messages`` can never commit
        without the result it points at.

        Args:
            database: Durable sidecar database path.
            messages: ``(timeline, payload)`` pairs to upsert as active rows.
            archive: ``(timeline, payload)`` pairs to upsert as archived rows
                and drop from the active table.
            tool_results: ``(result_id, payload)`` pairs to upsert in the
                independent result collection.
        """

    def replace_active(
        self,
        database: Path,
        rows: Sequence[tuple[int, str]],
    ) -> None:
        """Replace every active row, leaving archived rows untouched.

        Args:
            database: Durable sidecar database path.
            rows: Complete ``(timeline, payload)`` set for the active table.
        """

    def read_page(
        self,
        checkpoint: Path,
        *,
        before_timeline: int | None = None,
        limit: int = 200,
        include_archive: bool = False,
    ) -> PersistedContextPage:
        """Read a bounded page using the checkpoint's database pointer.

        Args:
            checkpoint: Pointer JSON that names the sidecar database.
            before_timeline: Exclusive older-than timeline cursor.
            limit: Maximum returned rows; implementations bound this value.
            include_archive: Merge archived rows into the pageable source.

        Returns:
            One chronological page plus its older cursor and total.
        """
        ...

    def read_archive_page(
        self,
        checkpoint: Path,
        *,
        before_timeline: int | None = None,
        limit: int = 50,
    ) -> PersistedArchivePage:
        """Read one archive-only page using the checkpoint's database pointer.

        Args:
            checkpoint: Pointer JSON that names the sidecar database.
            before_timeline: Exclusive older-than timeline cursor.
            limit: Maximum returned rows; implementations bound this value.

        Returns:
            One chronological archive page plus its older cursor and whether
            another older page exists.
        """
        ...

    def read_rows(
        self,
        database: Path,
        *,
        include_archive: bool = False,
    ) -> list[tuple[int, str]]:
        """Read raw ``(timeline, payload)`` pairs in ascending timeline order.

        Args:
            database: Durable sidecar database path.
            include_archive: Merge archived rows into the result.

        Returns:
            Every stored row, oldest first, with payloads left unparsed.
        """
        ...

    def count(self, database: Path, table: str) -> int:
        """Count rows in one storage-owned table.

        Args:
            database: Durable sidecar database path.
            table: Storage-owned table name.

        Returns:
            Current row count.
        """
        ...

    def max_timeline(self, database: Path, table: str) -> int:
        """Return the greatest timeline in one storage-owned table.

        Args:
            database: Durable sidecar database path.
            table: Storage-owned table name.

        Returns:
            Largest timeline, or zero for an empty table.
        """
        ...

    def read_tool_results(
        self,
        database: Path,
        result_ids: Sequence[str],
    ) -> list[tuple[str, str]]:
        """Read raw ``(result_id, payload)`` pairs for the requested results.

        Args:
            database: Durable sidecar database path.
            result_ids: Result identities a restored transcript references.

        Returns:
            Every stored pair, leaving payload parsing to the caller. A
            requested identity with no row is simply absent from the result,
            so the caller can fail on a dangling reference.
        """
        ...

    def count_tool_results(self, database: Path) -> int:
        """Count the independently stored tool results.

        Args:
            database: Durable sidecar database path.

        Returns:
            Current row count.
        """
        ...


class SQLiteContextStorage:
    """SQLite implementation of :class:`ContextStorage`.

    SQL schema details are intentionally confined to this class.  Callers
    exchange serialized payloads and never need to know table names or query
    construction.
    """

    # Only these two table names may be interpolated into a count/max query.
    _TABLES = frozenset({"messages", "archive"})

    @staticmethod
    def _check_table(table: str) -> str:
        """Validate a table name against the storage-owned allowlist.

        Args:
            table: Caller-supplied table name.

        Returns:
            The same name when it is storage-owned.

        Raises:
            ValueError: If the name is not one of the storage-owned tables.
        """
        # Reject anything outside the allowlist so no caller can interpolate an
        # arbitrary identifier into a query.
        if table not in SQLiteContextStorage._TABLES:
            raise ValueError("unsupported context storage table")
        return table

    @staticmethod
    def _connect(database: Path, *, readonly: bool = False) -> sqlite3.Connection:
        """Open a SQLite connection, read-only when requested.

        Args:
            database: Durable sidecar database path.
            readonly: Open through a ``mode=ro`` URI instead of read-write.

        Returns:
            An open connection; the caller owns closing it.
        """
        # Read-only callers must never create a database as a side effect.
        if readonly:
            return sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=30)
        # Writable callers may need the parent directory to exist first.
        database.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(database, timeout=30)

    @staticmethod
    def _ensure_schema(connection: sqlite3.Connection) -> None:
        """Create the row tables and their timeline indexes when absent.

        Args:
            connection: Open read-write connection to initialize.
        """
        # One table per storage concern, keyed by unique timeline.
        connection.execute(
            "CREATE TABLE IF NOT EXISTS messages "
            "(timeline INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS archive "
            "(timeline INTEGER PRIMARY KEY, payload TEXT NOT NULL)"
        )
        # Tool results live in their own collection so an assistant item can
        # hold a reference instead of a copy of the output.
        connection.execute(
            "CREATE TABLE IF NOT EXISTS tool_results "
            "(result_id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        # Descending timeline indexes serve the newest-first page queries.
        connection.execute(
            "CREATE INDEX IF NOT EXISTS messages_timeline_desc "
            "ON messages(timeline DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS archive_timeline_desc "
            "ON archive(timeline DESC)"
        )

    @staticmethod
    def _database_path(checkpoint: Path) -> Path:
        """Resolve and validate the sidecar database named by a checkpoint.

        Args:
            checkpoint: Pointer JSON written by a schema-3 context handler.

        Returns:
            The sibling SQLite database path.

        Raises:
            ValueError: If the pointer is malformed or names an unsafe path.
            OSError: If the pointer cannot be read.
        """
        pointer = json.loads(checkpoint.read_text(encoding="utf-8"))
        if not isinstance(pointer, dict):
            raise ValueError("checkpoint must be an object")
        if not is_sqlite_context_pointer(pointer):
            raise ValueError("checkpoint is not a SQLite context pointer")
        database_name = pointer.get("database")
        if not isinstance(database_name, str) or Path(database_name).name != database_name:
            raise ValueError("checkpoint database reference is invalid")
        return checkpoint.with_name(database_name)

    def append_rows(
        self,
        database: Path,
        messages: Sequence[tuple[int, str]],
        archive: Sequence[tuple[int, str]],
        tool_results: Sequence[tuple[str, str]] = (),
    ) -> None:
        """Append or replace serialized rows in one transaction.

        Args:
            database: Durable sidecar database path.
            messages: ``(timeline, payload)`` pairs to upsert as active rows.
            archive: ``(timeline, payload)`` pairs to upsert as archived rows
                and remove from the active table.
            tool_results: ``(result_id, payload)`` pairs to upsert as
                independently addressable results.
        """
        # Writers of one database serialize in-process; SQLite's own write
        # lock plus the busy timeout cover any connection this process does
        # not coordinate directly.
        with checkpoint_lock(database):
            connection = self._connect(database)
            try:
                # WAL keeps concurrent readers (projections) from blocking a save.
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA busy_timeout=5000")
                self._ensure_schema(connection)
                # Autocommit mode lets the explicit BEGIN below own the whole
                # batch, including the tool results, as one unit.
                connection.isolation_level = None
                connection.execute("BEGIN IMMEDIATE")
                try:
                    # Upsert each newly created active row.
                    for timeline, payload in messages:
                        connection.execute(
                            "INSERT OR REPLACE INTO messages(timeline, payload) VALUES (?, ?)",
                            (timeline, payload),
                        )
                    # Upsert archived rows, then enforce the archive invariant: an
                    # archived timeline must no longer be visible as active context.
                    for timeline, payload in archive:
                        connection.execute(
                            "INSERT OR REPLACE INTO archive(timeline, payload) VALUES (?, ?)",
                            (timeline, payload),
                        )
                        connection.execute("DELETE FROM messages WHERE timeline = ?", (timeline,))
                    # Resolve-by-reference is only safe when the result commits
                    # in the same transaction as the item pointing at it.
                    for result_id, payload in tool_results:
                        connection.execute(
                            "INSERT OR REPLACE INTO tool_results(result_id, payload) VALUES (?, ?)",
                            (result_id, payload),
                        )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
            finally:
                connection.close()

    def read_tool_results(
        self,
        database: Path,
        result_ids: Sequence[str],
    ) -> list[tuple[str, str]]:
        """Read the stored payloads for the requested result identities.

        Args:
            database: Durable sidecar database path.
            result_ids: Result identities a restored transcript references.

        Returns:
            Every stored ``(result_id, payload)`` pair. A requested identity
            with no row is absent, so the caller can reject the dangling
            reference instead of substituting an empty result.
        """
        if not result_ids:
            return []
        connection = self._connect(database, readonly=True)
        try:
            placeholders = ",".join("?" for _ in result_ids)
            rows = connection.execute(
                f"SELECT result_id, payload FROM tool_results "
                f"WHERE result_id IN ({placeholders})",
                tuple(result_ids),
            ).fetchall()
        finally:
            connection.close()
        return [(str(result_id), str(payload)) for result_id, payload in rows]

    def count_tool_results(self, database: Path) -> int:
        """Count the independently stored tool results.

        Args:
            database: Durable sidecar database path.

        Returns:
            Current row count.
        """
        connection = self._connect(database, readonly=True)
        try:
            row = connection.execute("SELECT COUNT(*) FROM tool_results").fetchone()
        finally:
            connection.close()
        return int(row[0] if row else 0)

    def replace_active(
        self,
        database: Path,
        rows: Sequence[tuple[int, str]],
    ) -> None:
        """Replace every active message row in one transaction.

        Archived rows are deliberately left untouched so a rewritten active
        transcript keeps the compacted history that read-only projections
        still page through.

        Args:
            database: Durable sidecar database path.
            rows: Complete ``(timeline, payload)`` set for the active table.
        """
        with checkpoint_lock(database):
            connection = self._connect(database)
            try:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA busy_timeout=5000")
                self._ensure_schema(connection)
                connection.isolation_level = None
                connection.execute("BEGIN IMMEDIATE")
                try:
                    # Clear the active window; the archive table is not touched.
                    connection.execute("DELETE FROM messages")
                    # Write the replacement rows in a single batched statement.
                    connection.executemany(
                        "INSERT OR REPLACE INTO messages(timeline, payload) VALUES (?, ?)",
                        list(rows),
                    )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
            finally:
                connection.close()

    def read_rows(
        self,
        database: Path,
        *,
        include_archive: bool = False,
    ) -> list[tuple[int, str]]:
        """Read every stored row in ascending timeline order.

        Returns raw ``(timeline, payload)`` pairs so a caller can validate or
        skip individual payloads; parsing them into context entries stays with
        the caller.

        Args:
            database: Durable sidecar database path.
            include_archive: Merge archived rows into the result.

        Returns:
            Every stored row, oldest first.
        """
        # Active rows only, or the shared timeline of active and archived rows.
        source = (
            "SELECT timeline, payload FROM messages "
            "UNION ALL SELECT timeline, payload FROM archive"
            if include_archive else "SELECT timeline, payload FROM messages"
        )
        connection = self._connect(database, readonly=True)
        try:
            rows = connection.execute(
                f"SELECT timeline, payload FROM ({source}) ORDER BY timeline ASC"
            ).fetchall()
        finally:
            connection.close()
        # Normalize the driver's row tuples to plain int/str pairs.
        return [(int(timeline), str(payload)) for timeline, payload in rows]

    def read_page(
        self,
        checkpoint: Path,
        *,
        before_timeline: int | None = None,
        limit: int = 200,
        include_archive: bool = False,
    ) -> PersistedContextPage:
        """Read one bounded, newest-first page from the pointer's database.

        Args:
            checkpoint: Pointer JSON that names the sidecar database.
            before_timeline: Exclusive older-than timeline cursor.
            limit: Maximum returned rows, clamped to 200.
            include_archive: Merge archived rows into the pageable source.

        Returns:
            A chronological page with its older cursor and total.

        Raises:
            ValueError: If the pointer is not a valid schema-3 SQLite pointer.
            OSError: If the pointer cannot be read.
        """
        # Parse and validate the pointer before touching any database.
        database = self._database_path(checkpoint)
        # Bound the page size regardless of what the caller asked for.
        bounded = max(1, min(int(limit), 200))
        # Active rows only, or the shared timeline of active and archived rows.
        source = (
            "SELECT timeline, payload FROM messages "
            "UNION ALL SELECT timeline, payload FROM archive"
            if include_archive else "SELECT timeline, payload FROM messages"
        )
        # Add the exclusive cursor predicate only when a cursor was supplied.
        where = ""
        values: tuple[object, ...] = ()
        if before_timeline is not None:
            where = " WHERE timeline < ?"
            values = (before_timeline,)
        # Resolve the sidecar path next to the pointer and read read-only.
        connection = self._connect(database, readonly=True)
        try:
            # Total visible rows is independent of the cursor.
            total_row = connection.execute(f"SELECT COUNT(*) FROM ({source})").fetchone()
            # Newest-first page for this cursor.
            rows = connection.execute(
                f"SELECT timeline, payload FROM ({source}){where} "
                "ORDER BY timeline DESC LIMIT ?",
                (*values, bounded),
            ).fetchall()
            # Expose a next cursor only when older rows actually remain.
            older = bool(rows) and connection.execute(
                f"SELECT EXISTS(SELECT 1 FROM ({source}) WHERE timeline < ?)",
                (rows[-1][0],),
            ).fetchone()[0] == 1
        finally:
            connection.close()
        # Reverse the newest-first rows into chronological order for callers.
        return PersistedContextPage(
            rows=[json.loads(row[1]) for row in reversed(rows)],
            next_before=rows[-1][0] if rows and older else None,
            total=int(total_row[0] if total_row else 0),
        )

    def read_archive_page(
        self,
        checkpoint: Path,
        *,
        before_timeline: int | None = None,
        limit: int = 50,
    ) -> PersistedArchivePage:
        """Read one bounded, archive-only page from the pointer's database.

        This deliberately queries only ``archive`` instead of reusing
        :meth:`read_page` with ``include_archive=True``: active and archived
        rows have different semantics, and an archive browser must not pay for
        a ``UNION ALL`` or a total count on every page.

        Args:
            checkpoint: Pointer JSON that names the sidecar database.
            before_timeline: Exclusive older-than timeline cursor.
            limit: Maximum returned rows, clamped to 200.

        Returns:
            A chronological archive page, the next older cursor, and whether
            another older page exists.

        Raises:
            ValueError: If the pointer is malformed or the limit is invalid.
            OSError: If the pointer or database cannot be read.
        """
        database = self._database_path(checkpoint)
        bounded = max(1, min(int(limit), 200))
        where = ""
        values: tuple[object, ...] = ()
        if before_timeline is not None:
            where = " WHERE timeline < ?"
            values = (before_timeline,)
        connection = self._connect(database, readonly=True)
        try:
            # Fetch one extra row so ``has_more`` never requires COUNT(*).
            rows = connection.execute(
                f"SELECT timeline, payload FROM archive{where} "
                "ORDER BY timeline DESC LIMIT ?",
                (*values, bounded + 1),
            ).fetchall()
        finally:
            connection.close()
        has_more = len(rows) > bounded
        page_rows = rows[:bounded]
        return PersistedArchivePage(
            rows=[json.loads(row[1]) for row in reversed(page_rows)],
            next_before=page_rows[-1][0] if has_more and page_rows else None,
            has_more=has_more,
        )

    def count(self, database: Path, table: str) -> int:
        """Count rows in one storage-owned table.

        Args:
            database: Durable sidecar database path.
            table: Storage-owned table name.

        Returns:
            Current row count.
        """
        # Validate before interpolating the identifier into the query.
        table = self._check_table(table)
        connection = self._connect(database, readonly=True)
        try:
            return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        finally:
            connection.close()

    def max_timeline(self, database: Path, table: str) -> int:
        """Return the greatest timeline in one storage-owned table.

        Args:
            database: Durable sidecar database path.
            table: Storage-owned table name.

        Returns:
            Largest timeline, or zero for an empty table.
        """
        # Validate before interpolating the identifier into the query.
        table = self._check_table(table)
        connection = self._connect(database, readonly=True)
        try:
            row = connection.execute(
                f"SELECT COALESCE(MAX(timeline), 0) FROM {table}"
            ).fetchone()
        finally:
            connection.close()
        return int(row[0])


__all__ = [
    "ContextStorage",
    "PersistedArchivePage",
    "PersistedContextPage",
    "SQLiteContextStorage",
    "is_sqlite_context_pointer",
]
