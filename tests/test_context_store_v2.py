"""Round-trip and concurrency tests for the v2 context store.

The durable transcript keeps tool output in its own collection and only a
``ToolResultId`` in the assistant item, so these tests assert both halves:
the item row never embeds the output, and the result row can be resolved by
identity after a restart.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

from llmfetcher.context_handlers.linear.codec import (
    context_item_from_dict,
    context_item_to_dict,
    tool_result_from_dict,
    tool_result_to_dict,
)
from llmfetcher.context_handlers.storage import SQLiteContextStorage
from llmfetcher.llm_types import (
    AssistantContextItem,
    AssistantTurnInput,
    ContextItemId,
    ContextSummaryItem,
    JsonObject,
    TokenUsage,
    ToolCallInput,
    ToolCallRecord,
    ToolResultId,
    ToolResultInput,
    ToolResultRecord,
    UserContextItem,
)


def _result(index: int) -> ToolResultRecord:
    return ToolResultRecord(
        result_id=ToolResultId(f"result-{index}"),
        call_id=f"call-{index}",
        tool_name="ctf_search",
        output=f"complete output {index}",
        images=(),
        ok=True,
        duration_ms=index,
        created_at=float(index),
    )


def _assistant(index: int, result_id: ToolResultId | None) -> AssistantContextItem:
    return AssistantContextItem(
        item_id=ContextItemId(f"item-{index}"),
        timeline=index,
        content="",
        reasoning="reasoning",
        tool_calls=(
            ToolCallRecord(
                call_id=f"call-{index}",
                name="ctf_search",
                arguments={"query": str(index)},
                result_id=result_id,
            ),
        ),
        usage=TokenUsage(input_tokens=3, output_tokens=2, total_tokens=5),
        model_duration_ms=10,
        round_duration_ms=20,
        created_at=1.0,
    )


class CodecV2Tests(unittest.TestCase):
    def test_assistant_item_round_trips_a_reference_only(self) -> None:
        item = _assistant(1, ToolResultId("result-1"))

        payload = context_item_to_dict(item)
        decoded = context_item_from_dict(payload)

        self.assertEqual(decoded, item)
        self.assertNotIn("complete output", json.dumps(payload))

    def test_user_and_summary_round_trip(self) -> None:
        user = UserContextItem(
            item_id=ContextItemId("item-1"),
            timeline=1,
            content="hello",
            images=(),
        )
        summary = ContextSummaryItem(
            item_id=ContextItemId("item-9"),
            timeline=9,
            abstract="summary",
            source_item_ids=(ContextItemId("item-1"),),
            source_timeline=(1,),
            source_result_ids=(ToolResultId("result-1"),),
        )

        self.assertEqual(context_item_from_dict(context_item_to_dict(user)), user)
        self.assertEqual(context_item_from_dict(context_item_to_dict(summary)), summary)

    def test_missing_field_is_rejected_instead_of_defaulted(self) -> None:
        payload = context_item_to_dict(_assistant(1, None))
        del payload["content"]

        with self.assertRaises(ValueError):
            context_item_from_dict(payload)

    def test_unknown_kind_is_rejected(self) -> None:
        payload: JsonObject = {"kind": "future", "item_id": "item-1"}

        with self.assertRaises(ValueError):
            context_item_from_dict(payload)

    def test_tool_result_round_trips_status_and_duration(self) -> None:
        record = _result(3)

        decoded = tool_result_from_dict(tool_result_to_dict(record))

        self.assertEqual(decoded, record)


class TurnInputTests(unittest.TestCase):
    def test_turn_input_carries_tool_status_and_duration(self) -> None:
        turn = AssistantTurnInput(
            content="checking",
            reasoning="think",
            tool_calls=(ToolCallInput(call_id="call-1", name="ctf_search", arguments={"q": "x"}),),
            usage=TokenUsage(),
            model_duration_ms=1,
            round_duration_ms=2,
            created_at=3.0,
        )
        result = ToolResultInput(
            call_id="call-1",
            tool_name="ctf_search",
            output="out",
            images=(),
            ok=False,
            duration_ms=42,
            created_at=4.0,
        )

        self.assertEqual(turn.tool_calls[0].call_id, "call-1")
        self.assertEqual(result.ok, False)
        self.assertEqual(result.duration_ms, 42)

    def test_duplicate_call_ids_are_rejected(self) -> None:
        call = ToolCallInput(call_id="call-1", name="ctf_search", arguments={})

        with self.assertRaises(ValueError):
            AssistantTurnInput(
                content="",
                reasoning="",
                tool_calls=(call, call),
                usage=TokenUsage(),
                model_duration_ms=None,
                round_duration_ms=None,
                created_at=None,
            )


class StorageV2Tests(unittest.TestCase):
    def test_item_and_result_commit_together(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "context.sqlite3"
            storage = SQLiteContextStorage()
            result = _result(1)
            item = _assistant(1, result.result_id)

            storage.append_rows(
                database,
                [(item.timeline, json.dumps(context_item_to_dict(item)))],
                [],
                [(result.result_id.value, json.dumps(tool_result_to_dict(result)))],
            )

            rows = storage.read_rows(database)
            self.assertEqual(len(rows), 1)
            item_payload = cast(JsonObject, json.loads(rows[0][1]))
            decoded = context_item_from_dict(item_payload)
            self.assertEqual(decoded.tool_calls[0].result_id, result.result_id)
            self.assertNotIn(result.output, rows[0][1])

            stored = dict(storage.read_tool_results(database, [result.result_id.value]))
            self.assertEqual(
                tool_result_from_dict(cast(JsonObject, json.loads(stored[result.result_id.value]))),
                result,
            )

    def test_a_missing_reference_is_absent_not_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "context.sqlite3"
            storage = SQLiteContextStorage()
            storage.append_rows(database, [], [], [])

            self.assertEqual(storage.read_tool_results(database, ["result-missing"]), [])

    def test_concurrent_writers_keep_every_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "context.sqlite3"
            storage = SQLiteContextStorage()

            def write(index: int) -> None:
                result = _result(index)
                storage.append_rows(
                    database,
                    [],
                    [],
                    [(result.result_id.value, json.dumps(tool_result_to_dict(result)))],
                )

            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(write, range(64)))

            self.assertEqual(storage.count_tool_results(database), 64)


if __name__ == "__main__":
    unittest.main()
