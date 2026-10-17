from __future__ import annotations

import unittest

from llmfetcher.context_handlers import ContextBlock, ContextComposer, ContextPosition, ContextSnapshot
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.llm_types import LLMBackendConfig, LLMOutput, LLMToolCall


class _Compactor:
    @property
    def default_backend_config(self) -> LLMBackendConfig:
        return LLMBackendConfig(name="test", provider="test", model="test")


class _Provider:
    provider_id = "workspace"

    def build_blocks(self, snapshot: ContextSnapshot):
        return [ContextBlock(
            role="user", content="<workspace>stable</workspace>",
            source=self.provider_id, priority=10, persistent=True,
            position=ContextPosition.PERSISTENT,
        )]


class ContextComposerTests(unittest.TestCase):
    def test_orders_blocks_and_skips_disabled_or_empty(self) -> None:
        composer = ContextComposer()

        class Provider:
            provider_id = "test"

            def build_blocks(self, snapshot):
                return [
                    ContextBlock("user", "late", "test", priority=20),
                    ContextBlock("user", "", "test", priority=1),
                    ContextBlock("user", "disabled", "test", enabled=False),
                    ContextBlock("user", "early", "test", priority=1),
                ]

        composer.register(Provider())
        blocks = composer.blocks(ContextSnapshot(handler=None))
        self.assertEqual([block.content for block in blocks], ["early", "late"])

    def test_provider_injection_is_rendered_without_becoming_history(self) -> None:
        handler = ContextHandlerLinear(_Compactor())
        handler.register_context_provider(_Provider())
        handler.add_user_message("hello")

        messages = handler.build_messages(system_prompt="system")

        self.assertEqual(
            [(message.role, message.content) for message in messages],
            [
                ("system", "system"),
                ("user", "<workspace>stable</workspace>"),
                ("user", "hello"),
            ],
        )
        self.assertEqual([item.content for item in handler.messages], ["hello"])

    def test_handler_is_a_source_and_composer_controls_position(self) -> None:
        handler = ContextHandlerLinear(_Compactor())
        handler.add_user_message("hello")
        composer = ContextComposer((handler, _Provider()))
        messages = composer.compose(
            snapshot=ContextSnapshot(handler=handler), system_prompt="system"
        )
        self.assertEqual(
            [message.content for message in messages],
            ["system", "<workspace>stable</workspace>", "hello"],
        )
        self.assertEqual(
            [block.position for block in composer.blocks(ContextSnapshot(handler=handler))],
            [ContextPosition.PERSISTENT, ContextPosition.CURRENT_INPUT],
        )

    def test_tool_result_limit_keeps_newest_results_and_pairs_calls(self) -> None:
        handler = ContextHandlerLinear(_Compactor())
        handler.add_user_message("run tools")
        for index in range(3):
            handler.add_assistant_message(
                LLMOutput(
                    content="",
                    provider="test",
                    backend_name="test",
                    model="test",
                    tool_calls=[LLMToolCall(name=f"tool_{index}", call_id=f"call_{index}")],
                ),
                {f"call_{index}": f"complete-{index}"},
            )
        handler.tool_result_context_limit = 1
        messages = ContextComposer((handler,)).compose(
            snapshot=ContextSnapshot(handler=handler),
        )
        results = [message for message in messages if message.role == "tool"]
        self.assertEqual([message.tool_call_id for message in results], ["call_0", "call_1", "call_2"])
        self.assertIn("omitted", results[0].content or "")
        self.assertIn("omitted", results[1].content or "")
        self.assertEqual(results[2].content, "complete-2")
        first_tool_turn = next(item for item in handler.messages if item.tool_calls)
        self.assertEqual(first_tool_turn.tool_calls[0].result, "complete-0")


if __name__ == "__main__":
    unittest.main()
