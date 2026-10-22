from __future__ import annotations

import unittest

from llmfetcher.context_handlers import ContextBlock, ContextComposer, ContextPosition, ContextSnapshot
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.llm_types import (
    AssistantContextItem,
    AssistantTurnInput,
    LLMBackendConfig,
    TokenUsage,
    ToolCallInput,
    ToolResultInput,
)


class _Compactor:
    @property
    def default_backend_config(self) -> LLMBackendConfig:
        return LLMBackendConfig(name="test", provider="test", model="test")


class _Provider:
    def __init__(
        self,
        provider_id: str = "workspace",
        position: ContextPosition = ContextPosition.PERSISTENT,
        priority: int = 0,
        content: str = "<workspace>stable</workspace>",
    ) -> None:
        self.provider_id = provider_id
        self.position = position
        self.priority = priority
        self.content = content

    @property
    def source_id(self) -> str:
        return self.provider_id

    def build_blocks(self, snapshot: ContextSnapshot):
        return [ContextBlock(
            role="user", content=self.content,
            source=self.provider_id, priority=self.priority, persistent=True,
            position=self.position,
        )]


class ContextComposerTests(unittest.TestCase):
    def test_orders_blocks_and_skips_disabled_or_empty(self) -> None:
        composer = ContextComposer(())

        class Provider:
            provider_id = "test"
            source_id = "test"

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
        handler.add_user_message("hello")

        messages = ContextComposer((handler, _Provider())).compose(
            snapshot=ContextSnapshot(handler=handler),
            system_prompt="system",
        )

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
                AssistantTurnInput(
                    content="",
                    reasoning="",
                    tool_calls=(ToolCallInput(
                        call_id=f"call_{index}",
                        name=f"tool_{index}",
                        arguments={},
                    ),),
                    usage=TokenUsage(),
                    model_duration_ms=None,
                    round_duration_ms=None,
                    created_at=None,
                ),
                (ToolResultInput(
                    call_id=f"call_{index}",
                    tool_name=f"tool_{index}",
                    output=f"complete-{index}",
                    images=(),
                    ok=True,
                    duration_ms=1,
                    created_at=None,
                ),),
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
        first_tool_turn = next(
            item for item in handler.messages
            if isinstance(item, AssistantContextItem) and item.tool_calls
        )
        result_id = first_tool_turn.tool_calls[0].result_id
        assert result_id is not None
        self.assertEqual(handler.resolve_tool_result(result_id).output, "complete-0")

    def test_priority_precedes_position(self) -> None:
        handler = ContextHandlerLinear(_Compactor())
        composer = ContextComposer((
            handler,
            _Provider("late", ContextPosition.CUSTOM, priority=20, content="late"),
            _Provider("early", ContextPosition.CUSTOM, priority=10, content="early"),
            _Provider("worktree", ContextPosition.WORKTREE, priority=0, content="worktree"),
        ))
        messages = composer.compose(snapshot=ContextSnapshot(handler=handler))
        self.assertEqual(
            [message.content for message in messages],
            ["worktree", "early", "late"],
        )

    def test_source_priority_overrides_position_and_missing_sources_are_ignored(self) -> None:
        handler = ContextHandlerLinear(_Compactor())
        composer = ContextComposer(
            (
                handler,
                _Provider("workspace", ContextPosition.PERSISTENT, content="workspace"),
                _Provider("notes", ContextPosition.CUSTOM, content="notes"),
            ),
            priority_overrides={"notes": -5, "uninstalled.plugin": 1},
        )
        messages = composer.compose(
            snapshot=ContextSnapshot(handler=handler),
            system_prompt="system",
        )
        self.assertEqual(
            [message.content for message in messages],
            ["system", "notes", "workspace"],
        )


if __name__ == "__main__":
    unittest.main()
