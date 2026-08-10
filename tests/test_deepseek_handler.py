"""Offline tests for the DeepSeek platform-specialised handler.

These tests exercise response/usage normalisation and stream parsing with
synthetic payloads; no network call is ever made.
"""

import unittest

from llmfetcher.fetcher_handlers import DeepSeekHandler
from llmfetcher.fetcher_handlers.base import LLMBackendHandler
from llmfetcher.fetcher_handlers.openai import OpenAIHandler
from llmfetcher.llm_fetcher import LLMFetcher
from llmfetcher.llm_types import LLMBackendConfig


def _make_handler() -> DeepSeekHandler:
    backend = LLMBackendConfig(
        name="ds",
        provider="deepseek",
        model="deepseek-reasoner",
        api_key="test-key",
        api_url="https://api.deepseek.com",
    )
    return DeepSeekHandler(None, backend)


class DeepSeekHandlerTests(unittest.TestCase):
    """Platform specialisation: reasoning field, cache accounting, dispatch."""

    def test_provider_registered(self) -> None:
        """DeepSeek is a registered provider name for the dispatcher."""
        self.assertIn("deepseek", DeepSeekHandler.provider_names)
        self.assertIn("deepseek", LLMFetcher.list_available_backend_providers())

    def test_dispatch_prefers_specialised_handler(self) -> None:
        """provider='deepseek' resolves to DeepSeekHandler, not OpenAIHandler."""
        backend = LLMBackendConfig(
            name="ds", provider="deepseek", model="m", api_key="k"
        )
        handler = LLMBackendHandler.create_for_backend(None, backend)
        self.assertIsInstance(handler, DeepSeekHandler)
        self.assertIsInstance(handler, OpenAIHandler)  # shares OpenAI machinery

    def test_normalize_completion_response_reasoning(self) -> None:
        """reasoning_content is captured from a non-streamed message."""
        handler = _make_handler()
        response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "final answer",
                    "reasoning_content": "chain of thought",
                },
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        out = handler.normalize_completion_response(response)
        self.assertEqual(out.content, "final answer")
        self.assertEqual(out.reasoning_content, "chain of thought")
        self.assertEqual(out.stop_reason, "stop")
        self.assertEqual(out.usage.total_tokens, 15)

    def test_normalize_completion_response_ignores_alien_aliases(self) -> None:
        """No fallback to reasoning/thinking aliases owned by other platforms."""
        handler = _make_handler()
        response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "answer",
                    "reasoning": "alien",
                    "thinking": "alien",
                },
                "finish_reason": "stop",
            }],
        }
        out = handler.normalize_completion_response(response)
        self.assertEqual(out.content, "answer")
        self.assertEqual(out.reasoning_content, "")

    def test_normalize_usage_cache_hit_tokens(self) -> None:
        """DeepSeek prompt_cache_hit_tokens maps onto cached_tokens."""
        handler = _make_handler()
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "prompt_cache_hit_tokens": 40,
            "prompt_cache_miss_tokens": 60,
        }
        normalized = handler.normalize_usage(usage)
        self.assertEqual(normalized.input_tokens, 100)
        self.assertEqual(normalized.output_tokens, 50)
        self.assertEqual(normalized.total_tokens, 150)
        self.assertEqual(normalized.cached_tokens, 40)

    def test_normalize_usage_reasoning_from_details(self) -> None:
        """Nested completion_tokens_details.reasoning_tokens is flattened."""
        handler = _make_handler()
        usage = {
            "prompt_tokens": 8,
            "completion_tokens": 300,
            "total_tokens": 308,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 8,
            "completion_tokens_details": {"reasoning_tokens": 200},
        }
        normalized = handler.normalize_usage(usage)
        self.assertEqual(normalized.cached_tokens, 0)
        self.assertEqual(normalized.reasoning_tokens, 200)

    def test_iter_stream_text_wraps_reasoning(self) -> None:
        """Streamed reasoning_content is wrapped in <think> when requested."""
        handler = _make_handler()
        chunks = [
            {"choices": [{"delta": {"reasoning_content": "step one "}}]},
            {"choices": [{"delta": {"reasoning_content": "step two"}}]},
            {"choices": [{"delta": {"content": "final"}}]},
        ]
        text = "".join(handler.iter_stream_text(chunks, output_reasoning=True))
        self.assertIn("<think>", text)
        self.assertIn("step one step two", text)
        self.assertIn("</think>", text)
        self.assertIn("final", text)

    def test_iter_stream_text_hides_reasoning_when_not_requested(self) -> None:
        """output_reasoning=False keeps the stream free of reasoning text."""
        handler = _make_handler()
        chunks = [
            {"choices": [{"delta": {"reasoning_content": "secret"}}]},
            {"choices": [{"delta": {"content": "answer"}}]},
        ]
        text = "".join(handler.iter_stream_text(chunks, output_reasoning=False))
        self.assertNotIn("secret", text)
        self.assertNotIn("<think>", text)
        self.assertEqual(text, "answer")

    def test_iter_stream_text_ignores_alien_reasoning_aliases(self) -> None:
        """Streaming never treats reasoning/thinking deltas as DeepSeek CoT."""
        handler = _make_handler()
        chunks = [
            {"choices": [{"delta": {"thinking": "alien thought", "reasoning": "alien reason"}}]},
            {"choices": [{"delta": {"content": "answer"}}]},
        ]
        text = "".join(handler.iter_stream_text(chunks, output_reasoning=True))
        self.assertNotIn("alien", text)
        self.assertEqual(text, "answer")

    def test_generic_openai_handler_keeps_alias_probing(self) -> None:
        """Regression guard: generic handler probes aliases; DeepSeek must not."""
        backend = LLMBackendConfig(
            name="oa", provider="openai", model="m", api_key="k"
        )
        generic = OpenAIHandler(None, backend)
        self.assertEqual(generic._message_reasoning({"thinking": "x"}), "")
        self.assertEqual(generic._message_reasoning({"reasoning_content": "r"}), "r")
        self.assertEqual(generic._delta_reasoning({"thinking": "t"}), "t")

        deepseek = _make_handler()
        self.assertEqual(deepseek._message_reasoning({"thinking": "x"}), "")
        self.assertEqual(deepseek._message_reasoning({"reasoning_content": "r"}), "r")
        self.assertIsNone(deepseek._delta_reasoning({"thinking": "t"}))


if __name__ == "__main__":
    unittest.main()


class DeepSeekThinkLeakTests(unittest.TestCase):
    """<think> feedback-loop control: outbound strip + inbound extraction."""

    def _handler_with_fake_client(self, recorded: dict) -> DeepSeekHandler:
        handler = _make_handler()

        class _FakeCompletions:
            def create(self, **kwargs):
                recorded["messages"] = kwargs.get("messages", [])
                recorded["kwargs"] = kwargs
                return object()  # caller only inspects sent messages here

        class _FakeChat:
            completions = _FakeCompletions()

        class _FakeClient:
            chat = _FakeChat()

        handler.client = _FakeClient()  # type: ignore[attr-defined]
        return handler

    def test_create_completion_strips_think_blocks_outbound(self) -> None:
        """Assistant <think> wrappers from the context handler never reach DeepSeek."""
        recorded: dict = {}
        handler = self._handler_with_fake_client(recorded)
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "assistant", "content": "<think>\nsecret chain\n</think>\n\nSummary here."},
            {"role": "user", "content": "go"},
        ]
        handler.create_completion(
            messages=messages,
            temperature=0.4,
            max_tokens=1024,
            stream=False,
        )
        sent = recorded["messages"]
        self.assertNotIn("<think>", sent[1]["content"])
        self.assertIn("Summary here.", sent[1]["content"])
        self.assertNotIn("secret chain", sent[1]["content"])
        # Other roles are untouched.
        self.assertEqual(sent[0]["content"], "sys")
        self.assertEqual(sent[2]["content"], "go")

    def test_create_completion_leaves_clean_messages_untouched(self) -> None:
        """Messages without think markers pass through byte-for-byte."""
        recorded: dict = {}
        handler = self._handler_with_fake_client(recorded)
        messages = [
            {"role": "assistant", "content": "Plain assistant reply."},
            {"role": "user", "content": "ok"},
        ]
        handler.create_completion(
            messages=messages, temperature=0.4, max_tokens=100, stream=False
        )
        self.assertEqual(recorded["messages"][0]["content"], "Plain assistant reply.")

    def test_normalize_completion_response_extracts_think_leak(self) -> None:
        """A <think> block the model echoed inside content moves to reasoning."""
        handler = _make_handler()
        response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "<think>\nleaked chain\n</think>\n\nFinal answer",
                    "reasoning_content": "native reasoning",
                },
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        out = handler.normalize_completion_response(response)
        self.assertEqual(out.content, "Final answer")
        self.assertNotIn("<think>", out.content)
        self.assertIn("leaked chain", out.reasoning_content)
        self.assertIn("native reasoning", out.reasoning_content)

    def test_normalize_completion_response_keeps_clean_content(self) -> None:
        """Content without think markers is returned unchanged."""
        handler = _make_handler()
        response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Clean answer",
                    "reasoning_content": "R",
                },
                "finish_reason": "stop",
            }],
        }
        out = handler.normalize_completion_response(response)
        self.assertEqual(out.content, "Clean answer")
        self.assertEqual(out.reasoning_content, "R")


if __name__ == "__main__":
    unittest.main()
