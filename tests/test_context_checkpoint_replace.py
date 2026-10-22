"""The context pointer commit must survive a transient Windows rename denial.

Windows denies ``os.replace`` onto a destination that any handle still holds
open without delete sharing, including a plain ``read_text`` from another
thread, and a scanner can hold the freshly written temporary file. The commit
path therefore retries a bounded number of times, while in-process readers
share ``checkpoint_lock`` with the writer.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

from llmfetcher.context_handlers.base import checkpoint_lock
from llmfetcher.context_handlers.linear import (
    ContextHandlerLinear,
    read_persisted_context_page,
)


class ContextCheckpointReplaceTests(unittest.TestCase):
    def test_save_survives_a_reader_holding_the_pointer(self) -> None:
        """A concurrent read handle delays the rename instead of failing it."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            handler = ContextHandlerLinear(MagicMock())
            self.assertTrue(handler.save(path))

            opened = threading.Event()

            def hold_open() -> None:
                with path.open("r", encoding="utf-8") as handle:
                    handle.read()
                    opened.set()
                    # Long enough to deny the first rename, short enough for
                    # the retry budget to absorb it.
                    hold = threading.Event()
                    hold.wait(0.12)

            reader = threading.Thread(target=hold_open)
            reader.start()
            self.assertTrue(opened.wait(5))
            try:
                self.assertTrue(handler.save(path))
            finally:
                reader.join(5)

            self.assertEqual(3, json.loads(path.read_text(encoding="utf-8"))["schema_version"])
            self.assertIsNone(handler.last_save_error)

    def test_persistent_denial_is_reported_not_hidden(self) -> None:
        """A rename that never succeeds fails the save and keeps the cause."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            handler = ContextHandlerLinear(MagicMock())
            denied = PermissionError(13, "拒绝访问。")

            with patch("llmfetcher.context_handlers.base.os.replace", side_effect=denied), \
                    patch("llmfetcher.context_handlers.base._REPLACE_DELAY", 0.0):
                self.assertFalse(handler.save(path))

            self.assertIsInstance(handler.last_save_error, PermissionError)
            self.assertEqual([], list(Path(directory).glob("*.tmp")))
            self.assertEqual([], list(Path(directory).glob(".*.tmp")))

    def test_paging_reader_waits_for_the_commit_lock(self) -> None:
        """A reader cannot observe the pointer while a write holds its lock."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            handler = ContextHandlerLinear(MagicMock())
            self.assertTrue(handler.save(path))

            started = threading.Event()
            finished = threading.Event()

            def read_page() -> None:
                started.set()
                read_persisted_context_page(path)
                finished.set()

            reader = threading.Thread(target=read_page)
            with checkpoint_lock(path):
                reader.start()
                self.assertTrue(started.wait(5))
                self.assertFalse(finished.wait(0.1))
            reader.join(10)
            self.assertTrue(finished.is_set())


if __name__ == "__main__":
    unittest.main()
