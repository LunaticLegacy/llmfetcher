from __future__ import annotations

import unittest

from llmfetcher.context_handlers import ContextBlock, ContextComposer, ContextPosition, ContextSnapshot
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.llm_types import LLMBackendConfig


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


if __name__ == "__main__":
    unittest.main()
