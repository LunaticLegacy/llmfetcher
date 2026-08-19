"""Offline regression tests for bounded linear-context compaction."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

from llmfetcher.context_handlers.linear import (
    _COMPACTION_INPUT_CHAR_LIMIT,
    _COMPACTION_OUTPUT_MAX_TOKENS,
    _COMPACTING_SYSTEM_PROMPT,
    ContextHandlerLinear,
)
from llmfetcher.llm_types import LLMOutput, LLMToolCall


class _RecordingCompactor:
    """Fake fetcher that records a compaction request without an LLM call."""

    def __init__(self) -> None:
        """Initialize storage for the latest compaction keyword arguments."""
        self.request: dict[str, Any] = {}
        self.response = (
            "<context_abstract>bounded summary</context_abstract>\n"
            "<source_timelines>[1, 2]</source_timelines>"
        )

    def fetch(
        self,
        msg: str,
        system_prompt: str | None = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        context_handler: Any = None,
        backend_name: str | None = None,
        tools: Any = None,
    ) -> LLMOutput:
        """Record the request and return a valid compacted-context payload.

        Args:
            msg: Text supplied to the compactor.
            system_prompt: System instruction for compaction.
            temperature: Sampling temperature requested by the handler.
            max_tokens: Response budget requested by the handler.
            context_handler: Must be ``None`` for standalone compaction.
            backend_name: Optional backend selector.
            tools: Optional tool definitions, unused during compaction.

        Returns:
            Synthetic response in the expected XML-like output format.
        """
        self.request = {
            "msg": msg,
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "context_handler": context_handler,
            "backend_name": backend_name,
            "tools": tools,
        }
        return LLMOutput(
            content=self.response,
            provider="test",
            backend_name="test",
            model="test",
        )


class ContextCompactionTests(unittest.TestCase):
    """Verify oversized tool output cannot inflate a compaction request."""

    def test_compaction_uses_bounded_stateless_request(self) -> None:
        """Compact a large tool result without using full history as context."""
        compactor = _RecordingCompactor()
        handler = ContextHandlerLinear(compactor, max_context_threshold=1)
        handler.add_user_message("inspect one large command result")
        output = LLMOutput(
            content="tool result follows",
            provider="test",
            backend_name="test",
            model="test",
            tool_calls=[LLMToolCall(name="shell", call_id="call-1")],
        )

        handler.add_assistant_message(
            output,
            tool_results={"call-1": "x" * (_COMPACTION_INPUT_CHAR_LIMIT * 3)},
        )

        self.assertIsNone(compactor.request["context_handler"])
        self.assertEqual(compactor.request["temperature"], 0.0)
        self.assertEqual(compactor.request["max_tokens"], _COMPACTION_OUTPUT_MAX_TOKENS)
        self.assertLessEqual(
            len(compactor.request["msg"]),
            _COMPACTION_INPUT_CHAR_LIMIT + 200,
        )
        self.assertIsNotNone(handler.abstract)
        assert handler.abstract is not None
        self.assertEqual(handler.abstract.abstract_msg, "bounded summary")

    def test_compaction_prompt_bounds_working_summary_and_treats_history_as_data(self) -> None:
        """Keep compaction instructions bounded and resistant to transcript prompts."""
        self.assertIn("untrusted reference data", _COMPACTING_SYSTEM_PROMPT)
        self.assertIn("at most 6,000 characters", _COMPACTING_SYSTEM_PROMPT)
        self.assertIn("drop low-priority detail", _COMPACTING_SYSTEM_PROMPT)
        self.assertIn("closing tag", _COMPACTING_SYSTEM_PROMPT)

    def test_compaction_accepts_truncated_tagged_summary(self) -> None:
        """Retain a usable summary when a provider omits only the closing tag."""
        compactor = _RecordingCompactor()
        compactor.response = "<context_abstract>goal: finish the migration"
        handler = ContextHandlerLinear(compactor, max_context_threshold=10**9)
        handler.add_user_message("finish the migration")

        self.assertTrue(handler.compact())
        assert handler.abstract is not None
        self.assertEqual(handler.abstract.abstract_msg, "goal: finish the migration")

    def test_tool_result_is_complete_in_history_storage(self) -> None:
        """Retain the complete tool result for lossless persistence/export."""
        compactor = _RecordingCompactor()
        handler = ContextHandlerLinear(compactor, max_context_threshold=10**9)
        output = LLMOutput(
            content="tool result follows",
            provider="test",
            backend_name="test",
            model="test",
            tool_calls=[LLMToolCall(name="shell", call_id="call-1")],
        )

        raw_result = "x" * (_COMPACTION_INPUT_CHAR_LIMIT + 1)
        handler.add_assistant_message(
            output,
            tool_results={"call-1": raw_result},
        )

        stored_result = handler.messages[-1].tool_calls[0].result
        self.assertIsNotNone(stored_result)
        assert stored_result is not None
        self.assertEqual(stored_result, raw_result)

    def test_load_restores_round_for_new_and_legacy_contexts(self) -> None:
        """Continue timeline numbering after loading either context format."""
        compactor = _RecordingCompactor()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            original = ContextHandlerLinear(compactor, max_context_threshold=10**9)
            original.add_user_message("first")
            original.add_user_message("second")
            self.assertTrue(original.save(path))

            restored = ContextHandlerLinear(compactor, max_context_threshold=10**9)
            self.assertTrue(restored.load(path))
            restored.add_user_message("third")
            self.assertEqual([message.timeline for message in restored.messages], [1, 2, 3])

            # Removing fields added by newer formats simulates an old file.
            payload = path.read_text(encoding="utf-8")
            payload = payload.replace('  "round": 2,\n', "")
            payload = payload.replace('  "archive": [],\n', "")
            path.write_text(payload, encoding="utf-8")
            legacy = ContextHandlerLinear(compactor, max_context_threshold=10**9)
            self.assertTrue(legacy.load(path))
            legacy.add_user_message("legacy third")
            self.assertEqual([message.timeline for message in legacy.messages], [1, 2, 3])

    def test_load_restores_round_from_compacted_timeline(self) -> None:
        """Recover the counter when compaction leaves no retained messages."""
        compactor = _RecordingCompactor()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            original = ContextHandlerLinear(compactor, max_context_threshold=1)
            original.add_user_message("first")
            original.add_assistant_message(LLMOutput(
                content="second",
                provider="test",
                backend_name="test",
                model="test",
            ))
            self.assertTrue(original.save(path))

            restored = ContextHandlerLinear(compactor, max_context_threshold=10**9)
            self.assertTrue(restored.load(path))
            restored.add_user_message("third")
            self.assertEqual(restored.messages[-1].timeline, 3)

    def test_compaction_archives_raw_messages_and_owns_provenance(self) -> None:
        """Never trust model timeline tags or discard raw compacted turns."""
        compactor = _RecordingCompactor()
        compactor.response = (
            "<context_abstract>first summary</context_abstract>\n"
            "<source_timelines>[999]</source_timelines>"
        )
        handler = ContextHandlerLinear(compactor, max_context_threshold=10**9)
        handler.add_user_message("one")
        handler.add_assistant_message(LLMOutput(
            content="two", provider="test", backend_name="test", model="test",
        ))

        self.assertTrue(handler.compact())
        self.assertEqual([message.timeline for message in handler.archive], [1, 2])
        self.assertEqual(handler.messages, [])
        assert handler.abstract is not None
        self.assertEqual(handler.abstract.source_timeline, [1, 2])

        compactor.response = "<context_abstract>second summary</context_abstract>"
        handler.add_user_message("three")
        self.assertTrue(handler.compact())
        self.assertEqual([message.timeline for message in handler.archive], [1, 2, 3])
        assert handler.abstract is not None
        self.assertEqual(handler.abstract.source_timeline, [1, 2, 3])

    def test_save_load_preserves_raw_compaction_archive(self) -> None:
        """Archived raw entries survive restart while staying out of prompts."""
        compactor = _RecordingCompactor()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            original = ContextHandlerLinear(compactor, max_context_threshold=10**9)
            original.add_user_message("retrieve this raw evidence")
            self.assertTrue(original.compact())
            self.assertTrue(original.save(path))

            restored = ContextHandlerLinear(compactor, max_context_threshold=10**9)
            self.assertTrue(restored.load(path))
            self.assertEqual(
                [message.content for message in restored.archive],
                ["retrieve this raw evidence"],
            )
            self.assertNotIn(
                "retrieve this raw evidence",
                str(restored.build_messages()),
            )

    def test_clear_context_restarts_timeline(self) -> None:
        """Assign timeline one to the first message after an explicit clear."""
        handler = ContextHandlerLinear(_RecordingCompactor(), max_context_threshold=10**9)
        handler.add_user_message("old")

        self.assertTrue(handler.clear_context())
        handler.add_user_message("new")

        self.assertEqual(handler.messages[-1].timeline, 1)

    def test_save_failure_keeps_previous_file_and_removes_temporary_file(self) -> None:
        """A failed replacement must not corrupt the last committed context."""
        handler = ContextHandlerLinear(_RecordingCompactor(), max_context_threshold=10**9)
        handler.add_user_message("new context")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            path.write_text("old context", encoding="utf-8")
            with patch(
                "llmfetcher.context_handlers.linear.os.replace",
                side_effect=OSError("replace failed"),
            ):
                self.assertFalse(handler.save(path))

            self.assertEqual(path.read_text(encoding="utf-8"), "old context")
            self.assertEqual(list(Path(directory).glob(".context.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
