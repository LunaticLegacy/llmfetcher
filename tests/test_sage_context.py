"""Round-trip coverage for the Sage context trees.

Option-A behaviour: the trees index the composed linear transcript, so reads
and persistence must stay equivalent to ``ContextHandlerLinear`` while the
index tracks appends, compaction and reload.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from llmfetcher.context_handlers.sage import SageContext
from llmfetcher.llm_types import (
    LLMBackendConfig,
    LLMContextCompacted,
    LLMOutput,
    TokenUsage,
)


class _ScriptedCompactor:
    """Yield one scripted compaction body per summary request."""

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


class SageContextTests(unittest.TestCase):
    """Create/read/update/delete over the tree index and its checkpoint."""

    def test_append_indexes_a_chain_in_history_order(self) -> None:
        """Appending turns extends one ordered chain."""
        sage = SageContext(_ScriptedCompactor())

        sage.add_user_message("hello")
        sage.add_assistant_message(_assistant("hi"))

        self.assertEqual(len(sage.tree), 2)
        nodes = sage.tree.ordered()
        self.assertEqual([node.message.content for node in nodes], ["hello", "hi"])
        self.assertIsNone(nodes[0].parent_id)
        self.assertEqual(nodes[1].parent_id, nodes[0].node_id)
        self.assertEqual(sage.tree.root_id, nodes[0].node_id)
        self.assertEqual(sage.tree.tail_id, nodes[1].node_id)
        self.assertEqual([m["content"] for m in sage.build_messages()], ["hello", "hi"])

    def test_path_to_returns_the_root_first_chain(self) -> None:
        """Traversal walks parents from the root down."""
        sage = SageContext(_ScriptedCompactor())
        sage.add_user_message("hello")
        sage.add_assistant_message(_assistant("hi"))
        nodes = sage.tree.ordered()

        chain = sage.tree.path_to(nodes[1].node_id)

        self.assertEqual([node.node_id for node in chain], [nodes[0].node_id, nodes[1].node_id])
        self.assertEqual(sage.tree.path_to(404), [])

    def test_compaction_reindexes_the_tree_onto_the_abstract(self) -> None:
        """A successful compaction collapses the index to the abstract."""
        sage = SageContext(_ScriptedCompactor())
        sage.add_user_message("hello")

        self.assertTrue(sage.compact())

        self.assertEqual(len(sage.linear.messages), 0)
        self.assertEqual(len(sage.linear.archive), 1)
        self.assertEqual(len(sage.tree), 1)
        node = sage.tree.ordered()[0]
        self.assertIsInstance(node.message, LLMContextCompacted)
        self.assertIsNone(node.parent_id)
        self.assertEqual(sage.build_messages()[0]["role"], "system")

    def test_failed_compaction_leaves_the_index_unchanged(self) -> None:
        """An unusable summary must not disturb the active index."""
        sage = SageContext(_ScriptedCompactor(raw="no element here"))
        sage.add_user_message("hello")

        self.assertFalse(sage.compact())

        self.assertEqual(len(sage.tree), 1)
        self.assertEqual(len(sage.linear.messages), 1)

    def test_save_and_load_restore_history_and_index(self) -> None:
        """A reload rebuilds the same chain from the durable checkpoint."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sage.json"
            sage = SageContext(_ScriptedCompactor())
            sage.add_user_message("hello")
            sage.add_assistant_message(_assistant("hi"))
            self.assertTrue(sage.save(path))

            restored = SageContext(_ScriptedCompactor())
            self.assertTrue(restored.load(path))

            self.assertEqual([m.content for m in restored.linear.messages], ["hello", "hi"])
            nodes = restored.tree.ordered()
            self.assertEqual([node.message.content for node in nodes], ["hello", "hi"])
            self.assertEqual(restored.tree.root_id, nodes[0].node_id)
            self.assertEqual(restored.tree.tail_id, nodes[1].node_id)

    def test_replace_active_context_reindexes_the_replacement_rows(self) -> None:
        """Editing the active window rebuilds the index from the new rows."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sage.json"
            sage = SageContext(_ScriptedCompactor())
            sage.add_user_message("hello")
            sage.add_assistant_message(_assistant("hi"))
            self.assertTrue(sage.save(path))
            database = path.with_suffix(path.suffix + ".sqlite3")

            high_water = sage.replace_active_context(
                [{"role": "user", "content": "edited"}],
                database=database,
            )

            self.assertGreater(high_water, 2)
            self.assertEqual([m.content for m in sage.linear.messages], ["edited"])
            nodes = sage.tree.ordered()
            self.assertEqual([node.message.content for node in nodes], ["edited"])
            self.assertIsNone(nodes[0].parent_id)
            self.assertEqual(sage.tree.tail_id, nodes[0].node_id)
            self.assertEqual(sage.build_messages()[0]["content"], "edited")

    def test_clear_context_empties_history_and_index(self) -> None:
        """Clearing resets the transcript, the timeline and the tree."""
        sage = SageContext(_ScriptedCompactor())
        sage.add_user_message("hello")

        self.assertTrue(sage.clear_context())

        self.assertEqual(sage.linear.messages, [])
        self.assertEqual(len(sage.tree), 0)
        self.assertIsNone(sage.tree.root_id)
        self.assertIsNone(sage.tree.tail_id)
        self.assertEqual(sage.build_messages(), [])

    def test_save_failure_surfaces_the_composed_cause(self) -> None:
        """``Agent`` reads ``last_save_error`` here, so it must be mirrored."""
        sage = SageContext(_ScriptedCompactor())

        self.assertFalse(sage.save(""))

        self.assertIsInstance(sage.last_save_error, ValueError)

    def test_usage_is_forwarded_to_the_composed_handler(self) -> None:
        """Internal-call usage and drain records belong to the composed handler."""
        sage = SageContext(_ScriptedCompactor())

        sage.record_usage(TokenUsage(input_tokens=3, output_tokens=4, total_tokens=7))

        self.assertEqual(sage.extra_usage.total_tokens, 7)
        self.assertEqual(sage.drain_usage_records(), [])


if __name__ == "__main__": unittest.main()
