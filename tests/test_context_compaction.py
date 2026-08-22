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
    _TOOL_RESULT_MAX_CHARS,
    _TOOL_RESULT_TOTAL_MAX_CHARS,
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

    def test_compaction_exposes_unparseable_model_response_for_diagnostics(self) -> None:
        """Keep failure details transient while allowing applications to show them."""
        compactor = _RecordingCompactor()
        compactor.response = "I cannot compact this transcript."
        handler = ContextHandlerLinear(compactor, max_context_threshold=10**9)
        handler.add_user_message("continue the migration")

        self.assertFalse(handler.compact())
        self.assertIn("<context_abstract>", handler.last_compaction_error or "")
        self.assertEqual(handler.last_compaction_raw, compactor.response)

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
        # The latest user message is re-anchored for the next round.
        self.assertEqual(
            [message.content for message in handler.messages],
            ["one", "Continue user's job from your checkpoint, now."],
        )
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

    def test_request_bounds_oversized_tool_result_but_keeps_history(self) -> None:
        """A huge tool result is trimmed on the request, never in storage."""
        handler = ContextHandlerLinear(_RecordingCompactor(), max_context_threshold=10**9)
        handler.add_user_message("inspect")
        oversized = "A" * 100_000 + "TAIL-EVIDENCE"
        handler.add_assistant_message(
            LLMOutput(
                content="called",
                provider="test",
                backend_name="test",
                model="test",
                tool_calls=[LLMToolCall(name="shell", call_id="call-1")],
            ),
            tool_results={"call-1": oversized},
        )

        # Storage stays lossless: the full value is persisted for archive and
        # audit, mirroring the durable agent:tools_completed ledger.
        stored = handler.messages[-1].tool_calls[0].result
        self.assertEqual(stored, oversized)

        # The model request is bounded: one oversized result never inflates
        # every later prompt, and the tail evidence survives trimming.
        tool_messages = [
            m for m in handler.build_messages() if m.get("role") == "tool"
        ]
        self.assertEqual(len(tool_messages), 1)
        content = tool_messages[0]["content"]
        self.assertLessEqual(len(content), _TOOL_RESULT_MAX_CHARS)
        self.assertIn("omitted", content)
        self.assertIn("TAIL-EVIDENCE", content[-200:])

    def test_context_size_estimate_reflects_trimmed_request(self) -> None:
        """Oversized results must not inflate the compaction estimate."""
        handler = ContextHandlerLinear(_RecordingCompactor(), max_context_threshold=10**9)
        handler.add_user_message("inspect")
        handler.add_assistant_message(
            LLMOutput(
                content="called",
                provider="test",
                backend_name="test",
                model="test",
                tool_calls=[LLMToolCall(name="shell", call_id="call-1")],
            ),
            tool_results={"call-1": "Z" * 500_000},
        )

        estimate = handler._estimate_context_size()
        self.assertLess(estimate, 100_000)

    def test_compaction_reanchors_latest_user_message_for_next_round(self) -> None:
        """The first post-compaction round still has an explicit user input.

        Compaction archives every active message.  Without re-anchoring, the
        next request would be system-only (agent prompt + compacted abstract)
        and some providers return an empty completion for a request with no
        user turn, which the Agent rejects as ``EMPTY_RESPONSE``.
        """
        compactor = _RecordingCompactor()
        handler = ContextHandlerLinear(compactor, max_context_threshold=10**9)
        handler.add_user_message("original goal")
        handler.add_assistant_message(LLMOutput(
            content="working", provider="test", backend_name="test", model="test",
        ))

        self.assertTrue(handler.compact())
        self.assertEqual(handler.messages, [])
        assert handler.abstract is not None

        # The latest user message is re-anchored into the active buffer so the
        # next round has a concrete user input to answer.
        self.assertEqual(
            [m.role for m in handler.messages],
            ["user", "user"],
        )
        self.assertEqual(
            handler.messages[0].content,
            "original goal",
        )
        self.assertEqual(
            handler.messages[1].content,
            "Continue user's job from your checkpoint, now.",
        )

        # The rebuilt request carries both the abstract and the user turn.
        built = handler.build_messages()
        self.assertEqual([m["role"] for m in built], ["system", "user", "user"])
        self.assertIn("bounded summary", built[0]["content"])
        self.assertEqual(built[1]["content"], "original goal")
        self.assertEqual(
            built[2]["content"],
            "Continue user's job from your checkpoint, now.",
        )

    def test_compaction_reanchors_most_recent_user_message(self) -> None:
        """Only the newest user message is re-anchored, not older ones."""
        compactor = _RecordingCompactor()
        handler = ContextHandlerLinear(compactor, max_context_threshold=10**9)
        handler.add_user_message("first goal")
        handler.add_assistant_message(LLMOutput(
            content="one", provider="test", backend_name="test", model="test",
        ))
        handler.add_user_message("latest goal")

        self.assertTrue(handler.compact())

        self.assertEqual(
            handler.messages[0].content,
            "latest goal",
        )

    def test_compaction_without_user_message_still_adds_resume_prompt(self) -> None:
        """A user-less archive still yields a usable next-round request."""
        compactor = _RecordingCompactor()
        handler = ContextHandlerLinear(compactor, max_context_threshold=10**9)
        handler.add_assistant_message(LLMOutput(
            content="only assistant", provider="test", backend_name="test", model="test",
        ))

        self.assertTrue(handler.compact())

        self.assertEqual(
            [m.role for m in handler.messages],
            ["user"],
        )
        self.assertEqual(
            handler.messages[0].content,
            "Continue user's job from your checkpoint, now.",
        )




class CompactionLifecycleEventTests(unittest.TestCase):
    """Verify compaction lifecycle events reach an optional observer."""

    def _handler(self, compactor, **kwargs) -> ContextHandlerLinear:
        events: list[tuple[str, str, dict]] = []
        handler = ContextHandlerLinear(
            compactor,
            max_context_threshold=kwargs.pop("threshold", 10**9),
            **kwargs,
        )
        handler.set_compaction_event_hook(
            lambda event_type, message, data: events.append(
                (event_type, message, data)
            )
        )
        handler._events = events  # type: ignore[attr-defined]
        return handler

    def test_success_emits_started_then_success(self) -> None:
        """A successful compaction reports started -> success in order."""
        compactor = _RecordingCompactor()
        handler = self._handler(compactor)
        handler.add_user_message("one")
        handler.add_assistant_message(LLMOutput(
            content="two", provider="test", backend_name="test", model="test",
        ))
        self.assertTrue(handler.compact())

        events = handler._events  # type: ignore[attr-defined]
        self.assertEqual(
            [event_type for event_type, _, _ in events],
            ["context:compact_started", "context:compact_success"],
        )
        started = events[0][2]
        success = events[1][2]
        self.assertEqual(started["round"], 2)
        self.assertGreater(started["context_size"], 0)
        self.assertGreater(started["compaction_input_characters"], 0)
        self.assertEqual(started["compress_threshold"], 10**9)
        self.assertGreaterEqual(started["ratio"], 0)
        self.assertEqual(
            started["ratio"],
            round(100.0 * started["context_size"] / 10**9, 1),
        )
        self.assertGreaterEqual(success["duration_ms"], 0)
        self.assertEqual(success["archived_messages"], 2)
        self.assertGreater(success["abstract_characters"], 0)
        self.assertEqual(success["source_timeline"], [1, 2])

    def test_skipped_emits_only_skipped(self) -> None:
        """Compacting an empty context reports skipped without a model call."""
        compactor = _RecordingCompactor()
        handler = self._handler(compactor)

        self.assertFalse(handler.compact())

        events = handler._events  # type: ignore[attr-defined]
        self.assertEqual(
            [event_type for event_type, _, _ in events],
            ["context:compact_skipped"],
        )
        self.assertIn("No active messages", events[0][2]["reason"])

    def test_empty_response_emits_failed_with_error(self) -> None:
        """An empty model response reports failed with the error message."""
        compactor = _RecordingCompactor()
        compactor.response = "   \n  "
        handler = self._handler(compactor)
        handler.add_user_message("one")

        self.assertFalse(handler.compact())

        events = handler._events  # type: ignore[attr-defined]
        self.assertEqual(
            [event_type for event_type, _, _ in events],
            ["context:compact_started", "context:compact_failed"],
        )
        failed = events[1][2]
        self.assertIn("empty content", failed["error"])
        self.assertGreaterEqual(failed["duration_ms"], 0)

    def test_unparseable_response_reports_failed_with_raw_retained(self) -> None:
        """An unparseable response reports failed while keeping raw content."""
        compactor = _RecordingCompactor()
        compactor.response = "I cannot compact this transcript."
        handler = self._handler(compactor)
        handler.add_user_message("one")

        self.assertFalse(handler.compact())

        events = handler._events  # type: ignore[attr-defined]
        self.assertEqual(
            [event_type for event_type, _, _ in events],
            ["context:compact_started", "context:compact_failed"],
        )
        self.assertTrue(events[1][2]["raw_retained"])
        self.assertIn("<context_abstract>", events[1][2]["error"])

    def test_model_exception_emits_failed_and_reraises(self) -> None:
        """A raising fetcher reports failed and still propagates the error."""
        class _BoomCompactor(_RecordingCompactor):
            def fetch(self, *args, **kwargs) -> LLMOutput:
                raise RuntimeError("backend exploded")

        handler = self._handler(_BoomCompactor())
        handler.add_user_message("one")

        with self.assertRaises(RuntimeError):
            handler.compact()

        events = handler._events  # type: ignore[attr-defined]
        self.assertEqual(
            [event_type for event_type, _, _ in events],
            ["context:compact_started", "context:compact_failed"],
        )
        self.assertIn("backend exploded", events[1][2]["error"])

    def test_raising_hook_never_breaks_compaction(self) -> None:
        """A broken observer is isolated and compaction semantics stay intact."""
        compactor = _RecordingCompactor()
        handler = ContextHandlerLinear(compactor, max_context_threshold=10**9)
        handler.add_user_message("one")

        def bad_hook(event_type: str, message: str, data: dict) -> None:
            raise RuntimeError("observer exploded")

        handler.set_compaction_event_hook(bad_hook)
        self.assertTrue(handler.compact())
        self.assertIsNotNone(handler.abstract)


if __name__ == "__main__":
    unittest.main()
