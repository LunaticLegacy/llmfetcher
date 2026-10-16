"""A full image context compacts before the provider request is built."""

import unittest
from types import SimpleNamespace

from llmfetcher.agent import Agent
from llmfetcher.multimodal import UserMessage


class FakeContext:
    def __init__(self, count):
        self.messages = [
            {"role": "user", "images": [{"attachment_id": str(index), "media_type": "image/png"}]}
            for index in range(count)
        ]
        self.carried = None

    def build_messages(self):
        return self.messages

    def add_user_message(self, message):
        self.carried = message
        self.messages.append({"role": "user", "images": message.images})


class ImageBudgetCompactionTests(unittest.TestCase):
    def test_compacts_at_limit_and_replays_latest_image(self):
        context = FakeContext(20)
        calls = []

        def compact_context(*, control=None):
            calls.append(control)
            context.messages.clear()
            return True

        agent = SimpleNamespace(context_handler=context, compact_context=compact_context,
                                _save_context=lambda: calls.append("saved"))
        self.assertTrue(Agent._compact_for_image_budget(agent))
        self.assertIsInstance(context.carried, UserMessage)
        self.assertEqual(context.carried.images[0]["attachment_id"], "19")
        self.assertEqual(len(context.build_messages()[0]["images"]), 1)
        self.assertEqual(calls, [None, "saved"])

    def test_no_compaction_below_limit(self):
        context = FakeContext(19)
        agent = SimpleNamespace(context_handler=context)
        self.assertFalse(Agent._compact_for_image_budget(agent))

    def test_failed_compaction_preserves_images(self):
        context = FakeContext(20)
        context.last_compaction_error = "summary unavailable"
        agent = SimpleNamespace(context_handler=context, compact_context=lambda **_kwargs: False)
        with self.assertRaisesRegex(RuntimeError, "summary unavailable"):
            Agent._compact_for_image_budget(agent)
        self.assertEqual(len(context.messages), 20)


if __name__ == "__main__":
    unittest.main()
