"""Contract tests for the explicit context records.

The durable model keeps tool results outside the assistant item: an
assistant turn holds a :class:`ToolResultId` reference, and only the
:class:`ContextStore` can turn that reference into a complete result.
"""

from __future__ import annotations

import dataclasses
import unittest

from llmfetcher.llm_types import (
    AssistantContextItem,
    ContextItem,
    ContextItemId,
    ContextSummaryItem,
    TokenUsage,
    ToolCallRecord,
    ToolResultId,
    ToolResultRecord,
    UserContextItem,
)


class _Store:
    """Minimal ContextStore used to prove references resolve by identity."""

    def __init__(self, record: ToolResultRecord) -> None:
        self._record = record

    def resolve_tool_result(self, result_id: ToolResultId) -> ToolResultRecord:
        if result_id != self._record.result_id:
            raise KeyError(result_id.value)
        return self._record


class ContextRecordTests(unittest.TestCase):
    def test_generated_ids_are_distinct_and(self) -> None:
        first = ContextItemId.new()
        second = ContextItemId.new()

        self.assertIsInstance(first, ContextItemId)
        self.assertTrue(first.value)
        self.assertNotEqual(first.value, second.value)

    def test_an_empty_id_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ContextItemId("  ")
        with self.assertRaises(ValueError):
            ToolResultId("")

    def test_tool_call_holds_a_reference_instead_of_result_text(self) -> None:
        fields = {field.name for field in dataclasses.fields(ToolCallRecord)}

        self.assertNotIn("result", fields)
        self.assertNotIn("output", fields)
        call = ToolCallRecord(
            call_id="call_1",
            name="ctf_search",
            arguments={"query": "ret2libc"},
            result_id=ToolResultId("result-1"),
        )
        self.assertEqual(call.result_id, ToolResultId("result-1"))

    def test_assistant_item_never_embeds_the_tool_output(self) -> None:
        record = AssistantContextItem(
            item_id=ContextItemId("item-2"),
            timeline=2,
            content="",
            reasoning="inspect the binary",
            tool_calls=(
                ToolCallRecord(
                    call_id="call_1",
                    name="ctf_search",
                    arguments={"query": "ret2libc"},
                    result_id=ToolResultId("result-1"),
                ),
            ),
            usage=TokenUsage(input_tokens=3),
            model_duration_ms=10,
            round_duration_ms=20,
            created_at=1.0,
        )

        self.assertFalse(hasattr(record, "result"))
        self.assertEqual(record.tool_calls[0].result_id, ToolResultId("result-1"))

    def test_summary_records_the_ranges_it_collapsed(self) -> None:
        summary = ContextSummaryItem(
            item_id=ContextItemId("item-9"),
            timeline=9,
            abstract="The agent established the ret2libc offset.",
            source_item_ids=(ContextItemId("item-1"), ContextItemId("item-2")),
            source_timeline=(1, 2),
            source_result_ids=(ToolResultId("result-1"),),
        )

        self.assertEqual(summary.source_timeline, (1, 2))
        self.assertEqual(summary.source_result_ids, (ToolResultId("result-1"),))

    def test_items_are_frozen(self) -> None:
        item = UserContextItem(
            item_id=ContextItemId("item-1"),
            timeline=1,
            content="hello",
            images=(),
        )

        with self.assertRaises(dataclasses.FrozenInstanceError):
            item.content = "changed"  # type: ignore[misc]

    def test_store_resolves_a_reference_to_the_complete_result(self) -> None:
        result = ToolResultRecord(
            result_id=ToolResultId("result-1"),
            call_id="call_1",
            tool_name="ctf_search",
            output="complete output",
            images=(),
            ok=True,
            duration_ms=12,
            created_at=2.0,
        )
        item: ContextItem = AssistantContextItem(
            item_id=ContextItemId("item-2"),
            timeline=2,
            content="",
            reasoning="",
            tool_calls=(
                ToolCallRecord(
                    call_id="call_1",
                    name="ctf_search",
                    arguments={},
                    result_id=result.result_id,
                ),
            ),
            usage=TokenUsage(),
            model_duration_ms=None,
            round_duration_ms=None,
            created_at=None,
        )

        resolved = _Store(result).resolve_tool_result(item.tool_calls[0].result_id)

        self.assertEqual(resolved.output, "complete output")
        self.assertIs(resolved, result)


if __name__ == "__main__":
    unittest.main()
