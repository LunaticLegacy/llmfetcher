"""Concurrency regression coverage for the context SQLite sidecar.

``SQLiteContextStorage`` opens one connection per write with WAL enabled. A
second writer must wait for the first transaction to commit instead of failing
with "database is locked"; the wait budget comes from the connection's busy
timeout.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from llmfetcher.context_handlers.storage import SQLiteContextStorage


class ContextSQLiteConcurrencyTests(unittest.TestCase):
    def test_concurrent_appends_keep_every_row(self) -> None:
        """Six parallel writers commit six distinct timelines."""
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "context.json.sqlite3"
            storage = SQLiteContextStorage()
            storage.append_rows(database, [(0, "{}")], [])
            writers = 6
            barrier = threading.Barrier(writers)

            def append(index: int) -> None:
                barrier.wait(10)
                storage.append_rows(database, [(index + 1, f'{{"i": {index}}}')], [])

            with ThreadPoolExecutor(max_workers=writers) as pool:
                list(pool.map(append, range(writers)))

            self.assertEqual(writers + 1, storage.count(database, "messages"))

    def test_writer_waits_for_an_open_write_transaction(self) -> None:
        """A writer blocked by another transaction commits once it releases."""
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "context.json.sqlite3"
            storage = SQLiteContextStorage()
            storage.append_rows(database, [(0, "{}")], [])
            release = threading.Event()
            locked = threading.Event()

            def hold() -> None:
                connection = sqlite3.connect(database, isolation_level=None)
                try:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute(
                        "INSERT OR REPLACE INTO messages(timeline, payload) "
                        "VALUES (?, ?)",
                        (100, "{}"),
                    )
                    locked.set()
                    release.wait(5)
                    connection.execute("COMMIT")
                finally:
                    connection.close()

            holder = threading.Thread(target=hold)
            holder.start()
            self.assertTrue(locked.wait(5))
            result: list[str] = []

            def write() -> None:
                try:
                    storage.append_rows(database, [(1, "{}")], [])
                    result.append("ok")
                except sqlite3.OperationalError as exc:
                    result.append(f"{type(exc).__name__}: {exc}")

            writer = threading.Thread(target=write)
            writer.start()
            release.set()
            holder.join(10)
            writer.join(10)

            self.assertEqual(["ok"], result)
            # Holder row 100 + initial row 0 + writer row 1.
            self.assertEqual(3, storage.count(database, "messages"))


if __name__ == "__main__":
    unittest.main()
