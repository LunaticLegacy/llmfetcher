"""Coverage for compaction that retains a verbatim tail.

``keep_recent`` moves the summarise/archive boundary: the newest entries stay
in the active transcript, only the entries before them are summarised, and the
abstract's provenance covers just what it replaced.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from llmfetcher.context_handlers import SQLiteContextStorage, create_context_handler
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.graph_memory import GraphContextHandler
from llmfetcher.llm_types import LLMBackendConfig, LLMOutput


class _ScriptedCompactor:
    """Yield one fixed ``<context_abstract>`` body for every summary request."""

    def __init__(self, raw: str = "<context_abstract>summary</context_abstract>") -> None:
        self._backend = LLMBackendConfig(name="test", provider="test", model="test-model")
        self.raw = raw

    @property
    def default_backend_config(self) -> LLMBackendConfig:
        """Describe the single backend this compactor reports as."""
        return self._backend

    def fetch_stream(self, **_: object):
        """Yield the scripted summary body as one streamed chunk."""
        yield self.raw


def _assistant(content: str) -> LLMOutput:
    """Build one assistant output with the fields the handler requires."""
    return LLMOutput(content=content, provider="test", backend_name="test", model="test-model")


class CompactionTailTests(unittest.TestCase):
    """The retained tail keeps its timelines and its turn in the request."""

    def test_handler_policy_applies_to_automatic_compaction(self) -> None:
        """A configured default governs the compaction the handler raises."""
        linear = ContextHandlerLinear(
            _ScriptedCompactor(),
            max_context_threshold=1,
            keep_recent=1,
        )
        linear.add_user_message("one")
        linear.add_user_message("two")

        linear.add_assistant_message(_assistant("three"))

        self.assertEqual([3], [message.timeline for message in linear.messages])
        self.assertEqual([1, 2], [message.timeline for message in linear.archive])

    def test_call_argument_overrides_the_handler_policy(self) -> None:
        """An explicit count wins over the configured default."""
        linear = ContextHandlerLinear(_ScriptedCompactor(), keep_recent=5)
        for index in range(4):
            linear.add_user_message(f"m{index}")

        self.assertTrue(linear.compact(keep_recent=1))

        self.assertEqual([4], [message.timeline for message in linear.messages])

    def test_registry_forwards_keep_recent_to_the_composed_handler(self) -> None:
        """The shared configuration reaches the handlers that expose it.

        ``sage`` is deliberately absent: its constructor is being rewritten and
        the registry only applies the policy there through a defensive lookup.
        """
        for name in ("graph", "linear"):
            with self.subTest(handler=name):
                handler = create_context_handler(name, fetcher=_ScriptedCompactor(), keep_recent=3)

                composed = getattr(handler, "linear", handler)

                self.assertEqual(3, composed.keep_recent)

    def test_keep_recent_leaves_a_verbatim_tail_outside_provenance(self) -> None:
        """Only the entries before the boundary are summarised and archived."""
        linear = ContextHandlerLinear(_ScriptedCompactor())
        for index in range(6):
            linear.add_user_message(f"m{index}")

        self.assertTrue(linear.compact(keep_recent=2))

        self.assertEqual([5, 6], [message.timeline for message in linear.messages])
        self.assertEqual([1, 2, 3, 4], [message.timeline for message in linear.archive])
        self.assertEqual([1, 2, 3, 4], linear.abstract.source_timeline)

    def test_retained_tail_suppresses_the_derived_resume_turn(self) -> None:
        """A retained tail is already the user-visible turn."""
        linear = ContextHandlerLinear(_ScriptedCompactor())
        linear.add_user_message("one")
        linear.add_user_message("two")

        self.assertTrue(linear.compact(keep_recent=1))

        contents = [message["content"] for message in linear.build_messages()]
        self.assertEqual(["two"], [message["content"] for message in linear.build_messages() if message["role"] == "user"])
        self.assertNotIn("Continue user's job from your checkpoint, now.", contents)

    def test_retained_rows_never_duplicate_a_timeline_in_the_checkpoint(self) -> None:
        """Retained rows must not also be archived, so pages stay unique."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            linear = ContextHandlerLinear(_ScriptedCompactor())
            for index in range(5):
                linear.add_user_message(f"m{index}")
            self.assertTrue(linear.compact(keep_recent=2))
            self.assertTrue(linear.save(path))

            database = path.with_suffix(path.suffix + ".sqlite3")
            timelines = [timeline for timeline, _ in SQLiteContextStorage().read_rows(database, include_archive=True)]

            self.assertEqual([1, 2, 3, 4, 5], timelines)
            self.assertEqual(sorted(set(timelines)), timelines)

    def test_default_still_archives_everything_and_resumes(self) -> None:
        """``keep_recent=0`` keeps the original behaviour."""
        linear = ContextHandlerLinear(_ScriptedCompactor())
        linear.add_user_message("one")
        linear.add_user_message("two")

        self.assertTrue(linear.compact())

        self.assertEqual([], linear.messages)
        self.assertEqual([1, 2], [message.timeline for message in linear.archive])
        contents = [message["content"] for message in linear.build_messages()]
        self.assertIn("Continue user's job from your checkpoint, now.", contents)

    def test_keep_recent_beyond_the_transcript_archives_everything(self) -> None:
        """An oversized retention count degrades to a full compaction."""
        linear = ContextHandlerLinear(_ScriptedCompactor())
        linear.add_user_message("one")

        self.assertTrue(linear.compact(keep_recent=99))

        self.assertEqual([], linear.messages)
        self.assertEqual([1], linear.abstract.source_timeline)
        contents = [message["content"] for message in linear.build_messages()]
        self.assertIn("Continue user's job from your checkpoint, now.", contents)

    def test_graph_handler_forwards_keep_recent(self) -> None:
        """The composing handler passes the retention boundary down."""
        handler = GraphContextHandler(compacting_fetcher=_ScriptedCompactor())
        for index in range(4):
            handler.add_user_message(f"m{index}")

        self.assertTrue(handler.compact(keep_recent=1))

        self.assertEqual([4], [message.timeline for message in handler.linear.messages])
        self.assertEqual([1, 2, 3], handler.linear.abstract.source_timeline)


if __name__ == "__main__": unittest.main()
