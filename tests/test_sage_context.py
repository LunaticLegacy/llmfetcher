"""Round-trip tests for Sage's branch-aware context handler."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from llmfetcher.context_handlers.sage import SageContext, create_sage_tools
from llmfetcher.llm_types import LLMOutput


class _Compactor:
    def __init__(self, body: str = "<sage_summary>goal: resume work</sage_summary>") -> None:
        self.body = body

    def fetch(self, **_: object) -> LLMOutput:
        return LLMOutput(content=self.body, provider="test", backend_name="test", model="test-model")


def _assistant(content: str) -> LLMOutput:
    return LLMOutput(content=content, provider="test", backend_name="test", model="test-model")


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

    def test_compaction_creates_sage_summary_and_keeps_raw_rows(self) -> None:
        sage = SageContext(_Compactor())
        sage.add_user_message("hello")
        sage.add_assistant_message(_assistant("hi"))
        self.assertTrue(sage.compact())
        self.assertEqual(sage.activate_context_id_list, [])
        self.assertEqual(sage.summaries, {-1: "goal: resume work"})
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


if __name__ == "__main__":
    unittest.main()
