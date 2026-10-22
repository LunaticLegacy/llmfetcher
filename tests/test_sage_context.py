"""Round-trip tests for Sage's branch-aware context handler."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from llmfetcher.context_handlers.sage import SageContext, create_sage_tools
from llmfetcher.llm_types import (
    AssistantContextItem,
    AssistantTurnInput,
    LLMOutput,
    TokenUsage,
    ToolCallInput,
    ToolResultInput,
)


class _Compactor:
    def __init__(self, body: str = "<sage_summary>goal: resume work</sage_summary>") -> None:
        self.body = body

    def fetch(self, **_: object) -> LLMOutput:
        return LLMOutput(content=self.body, provider="test", backend_name="test", model="test-model")


def _assistant(content: str) -> AssistantTurnInput:
    return AssistantTurnInput(
        content=content,
        reasoning="",
        tool_calls=(),
        usage=TokenUsage(),
        model_duration_ms=None,
        round_duration_ms=None,
        created_at=None,
    )


class SageContextTests(unittest.TestCase):
    def test_append_tracks_active_context_and_worktree(self) -> None:
        sage = SageContext(_Compactor())
        sage.add_user_message("hello")
        sage.add_assistant_message(_assistant("hi"))
        self.assertEqual(sage.activate_context_id_list, [0, 1])
        root = sage.current_worktree_stack[-1]
        self.assertEqual(root.holding_context_ids, [0, 1])
        self.assertEqual([item.content for item in sage.raw_contexts_info], ["hello", "hi"])
        messages = sage.build_messages()
        self.assertEqual(messages[0].content, "hello")
        self.assertIn("<worktree_state>", messages[1].content)
        self.assertEqual(messages[-1].content, "hi")

    def test_request_preview_labels_persisted_and_synthetic_messages(self) -> None:
        sage = SageContext(_Compactor())
        sage.add_user_message("hello")
        sage.add_assistant_message(_assistant("hi"))
        sage.add_user_message("")

        messages = sage.build_messages(system_prompt="system")
        metadata = sage.describe_request_messages(messages)

        self.assertEqual(len(metadata), len(messages))
        self.assertEqual(
            [item["source"] for item in metadata],
            ["system_prompt", "sage_context", "sage_worktree", "sage_context", "hypothetical_input"],
        )
        self.assertEqual(
            [item["persisted"] for item in metadata],
            [False, True, False, True, False],
        )

    def test_compaction_creates_sage_summary_and_keeps_raw_rows(self) -> None:
        sage = SageContext(_Compactor())
        sage.add_user_message("hello")
        sage.add_assistant_message(_assistant("hi"))
        self.assertTrue(sage.compact())
        self.assertEqual(sage.activate_context_id_list, [])
        self.assertEqual(
            {key: summary.abstract for key, summary in sage.summaries.items()},
            {-1: "goal: resume work"},
        )
        summary = sage.summaries[-1]
        self.assertEqual(summary.kind, "summary")
        self.assertEqual(summary.source_timeline, (0, 1))
        self.assertEqual(len(sage.raw_contexts_info), 2)
        self.assertIn("goal: resume work", sage.build_messages()[0].content)

    def test_failed_compaction_preserves_active_projection(self) -> None:
        sage = SageContext(_Compactor("not a Sage summary"))
        sage.add_user_message("hello")
        sage.add_assistant_message(_assistant("hi"))
        active_before = list(sage.activate_context_id_list)
        self.assertFalse(sage.compact())
        self.assertEqual(sage.activate_context_id_list, active_before)
        self.assertEqual(sage.summaries, {})

    def test_branch_tool_queue_and_apply(self) -> None:
        sage = SageContext(_Compactor())
        tools = {tool.name: tool for tool in create_sage_tools(sage)}
        result = tools["sage_fork_branch"].handler(description="try another approach", checkout=True)
        self.assertIn('"queued": true', result)
        applied = sage.apply_pending_branch_commands()
        self.assertEqual(len(applied), 1)
        self.assertEqual(len(sage.current_worktree_stack), 2)
        self.assertEqual(sage.current_worktree_stack[-1].description, "try another approach")

    def test_save_and_load_restore_worktree_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sage.json"
            sage = SageContext(_Compactor())
            sage.add_user_message("hello")
            sage.add_assistant_message(_assistant("hi"))
            sage.compact()
            tools = {tool.name: tool for tool in create_sage_tools(sage)}
            tools["sage_fork_branch"].handler(description="child", checkout=True)
            sage.apply_pending_branch_commands()
            self.assertTrue(sage.save(path))
            restored = SageContext(_Compactor())
            self.assertTrue(restored.load(path))
            self.assertEqual(restored.timeline, sage.timeline)
            self.assertEqual(restored.summaries, sage.summaries)
            self.assertEqual(set(restored.worktree_dict), set(sage.worktree_dict))
            self.assertEqual([b.id for b in restored.current_worktree_stack], [b.id for b in sage.current_worktree_stack])
            self.assertIn("goal: resume work", restored.build_messages()[0].content)

    def test_tool_results_are_stored_by_reference_and_restored(self) -> None:
        sage = SageContext(_Compactor())
        sage.add_user_message("hello")
        sage.add_assistant_message(
            AssistantTurnInput(
                content="used a tool",
                reasoning="",
                tool_calls=(
                    ToolCallInput(call_id="c1", name="shell", arguments={"cmd": "ls"}),
                ),
                usage=TokenUsage(),
                model_duration_ms=None,
                round_duration_ms=None,
                created_at=None,
            ),
            (
                ToolResultInput(
                    call_id="c1",
                    tool_name="shell",
                    output="a.txt",
                    images=(),
                    ok=True,
                    duration_ms=3,
                    created_at=None,
                ),
            ),
        )

        assistant = sage.raw_contexts_info[-1]
        self.assertIsInstance(assistant, AssistantContextItem)
        assert isinstance(assistant, AssistantContextItem)
        result_id = assistant.tool_calls[0].result_id
        assert result_id is not None
        self.assertEqual(sage.resolve_tool_result(result_id).output, "a.txt")
        self.assertEqual(sage.build_messages()[-1].content, "a.txt")
        with self.assertRaises(KeyError):
            sage.resolve_tool_result(type(result_id)("missing"))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sage.json"
            self.assertTrue(sage.save(path))
            restored = SageContext(_Compactor())
            self.assertTrue(restored.load(path))
            restored_assistant = restored.raw_contexts_info[-1]
            assert isinstance(restored_assistant, AssistantContextItem)
            restored_id = restored_assistant.tool_calls[0].result_id
            assert restored_id is not None
            self.assertEqual(restored.resolve_tool_result(restored_id).output, "a.txt")
            self.assertEqual(restored.build_messages(), sage.build_messages())

            database = path.with_suffix(path.suffix + ".sqlite3")
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("DELETE FROM tool_results")
                connection.commit()
            self.assertFalse(SageContext(_Compactor()).load(path))


if __name__ == "__main__":
    unittest.main()
