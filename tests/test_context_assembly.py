"""Assembly tests for the interleaved and deferred tool-result layouts."""

from __future__ import annotations

import json
import unittest

from llmfetcher.context_handlers.linear.assembly import (
    ContextAssembler,
    ContextAssemblyError,
)
from llmfetcher.context_handlers.placement import (
    RESUME_PROMPT,
    ToolResultPlacement,
)
from llmfetcher.llm_types import (
    AssistantContextItem,
    ContextItemId,
    TokenUsage,
    ToolCallRecord,
    ToolResultId,
    ToolResultRecord,
    UserContextItem,
)


def _result(index: int, call_id: str) -> ToolResultRecord:
    return ToolResultRecord(
        result_id=ToolResultId(f"r{index}"),
        call_id=call_id,
        tool_name=f"tool{index}",
        output=f"output-{index}",
        images=(),
        ok=True,
        duration_ms=index,
        created_at=float(index),
    )


def _call(call_id: str, result_id: ToolResultId | None) -> ToolCallRecord:
    return ToolCallRecord(
        call_id=call_id,
        name="ctf_search",
        arguments={"q": call_id},
        result_id=result_id,
    )


def _assistant(index: int, calls: list[ToolCallRecord], reasoning: str = "") -> AssistantContextItem:
    return AssistantContextItem(
        item_id=ContextItemId(f"i{index}"),
        timeline=index,
        content=f"content-{index}",
        reasoning=reasoning,
        tool_calls=tuple(calls),
        usage=TokenUsage(),
        model_duration_ms=None,
        round_duration_ms=None,
        created_at=None,
    )


def _user(index: int, content: str) -> UserContextItem:
    return UserContextItem(
        item_id=ContextItemId(f"i{index}"),
        timeline=index,
        content=content,
        images=(),
    )


class _Store:
    def __init__(self, *records: ToolResultRecord) -> None:
        self._records = {record.result_id.value: record for record in records}

    def resolve_tool_result(self, result_id: ToolResultId) -> ToolResultRecord:
        return self._records[result_id.value]


class ContextAssemblyTests(unittest.TestCase):
    def _items(self) -> tuple[tuple[UserContextItem | AssistantContextItem, ...], ToolResultRecord, ToolResultRecord]:
        first = _result(1, "c1")
        second = _result(3, "c3")
        items = (
            _user(1, "first"),
            _assistant(2, [_call("c1", first.result_id), _call("c2", None)]),
            _assistant(3, [_call("c3", second.result_id)]),
            _user(4, "second"),
        )
        return items, first, second

    def test_interleaved_puts_each_result_after_its_assistant(self) -> None:
        items, first, second = self._items()

        assembled = ContextAssembler(_Store(first, second)).assemble(items)

        self.assertEqual(
            [message.role for message in assembled.messages],
            ["user", "assistant", "tool", "assistant", "tool", "user"],
        )
        self.assertEqual(assembled.messages[2].tool_call_id, "c1")
        self.assertEqual(assembled.messages[2].content, "output-1")
        self.assertEqual(assembled.messages[4].tool_call_id, "c3")
        self.assertEqual(
            [call.id for call in assembled.messages[1].tool_calls],
            ["c1", "c2"],
        )

    def test_interleaved_folds_reasoning_into_content(self) -> None:
        item = _assistant(1, [], reasoning="deliberate")

        assembled = ContextAssembler(_Store()).assemble((item,))

        self.assertIn("<think>\ndeliberate\n</think>", assembled.messages[0].content or "")

    def test_deferred_merges_every_result_into_one_system_block(self) -> None:
        items, first, second = self._items()

        assembled = ContextAssembler(_Store(first, second)).assemble(
            items,
            placement=ToolResultPlacement.DEFERRED,
        )

        self.assertEqual(
            [message.role for message in assembled.messages],
            ["user", "assistant", "assistant", "system", "user"],
        )
        payload = json.loads(assembled.messages[3].content or "")
        entries = payload["tool_results"]
        self.assertEqual([entry["call_id"] for entry in entries], ["c1", "c3"])
        self.assertEqual([entry["result_id"] for entry in entries], ["r1", "r3"])
        self.assertEqual(entries[0]["output"], "output-1")
        self.assertEqual(entries[1]["duration_ms"], 3)
        self.assertEqual(assembled.messages[4].content, "second")

    def test_deferred_rejects_repeated_call_ids(self) -> None:
        first = _result(1, "dup")
        second = _result(2, "dup")
        items = (
            _assistant(1, [_call("dup", first.result_id)]),
            _assistant(2, [_call("dup", second.result_id)]),
        )

        with self.assertRaises(ContextAssemblyError):
            ContextAssembler(_Store(first, second)).assemble(
                items,
                placement=ToolResultPlacement.DEFERRED,
            )

    def test_missing_result_fails_instead_of_emptying(self) -> None:
        items = (_assistant(1, [_call("missing", ToolResultId("r-missing"))]),)

        with self.assertRaises(KeyError):
            ContextAssembler(_Store()).assemble(items)

    def test_observations_mark_the_result_source_per_mode(self) -> None:
        items, first, second = self._items()
        assembler = ContextAssembler(_Store(first, second))

        interleaved = assembler.assemble(items)
        interleaved_results = [
            row for row in interleaved.observations if row.kind == "tool_result"
        ]
        self.assertEqual(
            [row.source for row in interleaved_results],
            ["linear.tool_result", "linear.tool_result"],
        )
        self.assertEqual(
            [row.result_id for row in interleaved_results],
            [first.result_id, second.result_id],
        )

        deferred = assembler.assemble(
            items,
            placement=ToolResultPlacement.DEFERRED,
        )
        deferred_results = [
            row for row in deferred.observations if row.kind == "tool_result"
        ]
        self.assertEqual(
            [row.source for row in deferred_results],
            ["linear.system.tool_results", "linear.system.tool_results"],
        )
        self.assertEqual(
            len([row for row in deferred.observations if row.kind == "tool_results"]),
            1,
        )

    def test_pending_resume_stays_last(self) -> None:
        assembled = ContextAssembler(_Store()).assemble(
            (_user(1, "hi"),),
            pending_resume=True,
        )

        self.assertEqual(assembled.messages[-1].role, "user")
        self.assertEqual(assembled.messages[-1].content, RESUME_PROMPT)


if __name__ == "__main__":
    unittest.main()
