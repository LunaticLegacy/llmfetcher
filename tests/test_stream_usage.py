"""Offline regression tests for streamed token-usage accounting.

Streamed model responses must carry the same per-call usage as non-streamed
responses. These tests exercise:

* handler-level capture (OpenAI-compatible, DeepSeek cache fields, Anthropic
  split usage) into the per-call ``StreamUsageCapture``;
* the ``LLMFetcher.fetch_stream`` glue that normalizes the captured raw usage
  into a caller-supplied ``TokenUsage`` sink;
* the ``Agent`` streamed round publishing real numbers in ``agent:usage``
  ledger events so the session usage panel shows actual consumption.

No network call is ever made; all provider payloads are synthetic.
"""

from __future__ import annotations

import unittest

from llmfetcher.agent import Agent
from llmfetcher.fetcher_handlers import DeepSeekHandler
from llmfetcher.fetcher_handlers.anthropic import AnthropicHandler
from llmfetcher.fetcher_handlers.openai import OpenAIHandler
from llmfetcher.llm_fetcher import LLMFetcher, StreamUsageCapture
from llmfetcher.llm_types import LLMBackendConfig, LLMOutput, TokenUsage


def _deepseek_handler() -> DeepSeekHandler:
    return DeepSeekHandler(
        None,
        LLMBackendConfig(
            name="ds", provider="deepseek", model="deepseek-reasoner",
            api_key="test-key", api_url="https://api.deepseek.com",
        ),
    )


def _openai_handler() -> OpenAIHandler:
    return OpenAIHandler(
        None,
        LLMBackendConfig(
            name="oa", provider="openai", model="gpt-test",
            api_key="test-key", api_url="https://api.openai.com",
        ),
    )


def _anthropic_handler() -> AnthropicHandler:
    return AnthropicHandler(
        None,
        LLMBackendConfig(
            name="an", provider="anthropic", model="claude-test",
            api_key="test-key", api_url="https://api.anthropic.com",
        ),
    )


class StreamUsageCaptureTests(unittest.TestCase):
    """Handler-level capture of usage carried on streamed chunks."""

    def test_openai_final_usage_chunk_is_captured(self) -> None:
        """A final usage-only chunk (empty choices) must not be discarded."""
        handler = _openai_handler()
        chunks = [
            {"choices": [{"delta": {"content": "hello"}}]},
            {"choices": [{"delta": {"content": " world"}}]},
            {
                "choices": [],
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 30,
                    "total_tokens": 150,
                    "prompt_tokens_details": {"cached_tokens": 40},
                },
            },
        ]
        capture = StreamUsageCapture()
        text = "".join(handler.iter_stream_text(
            chunks, output_reasoning=False, usage_capture=capture,
        ))
        self.assertEqual(text, "hello world")
        self.assertIsNotNone(capture.raw)
        usage = handler.normalize_usage(capture.raw)
        self.assertEqual(usage.input_tokens, 120)
        self.assertEqual(usage.output_tokens, 30)
        self.assertEqual(usage.total_tokens, 150)
        self.assertEqual(usage.cached_tokens, 40)

    def test_openai_usage_on_content_chunk_is_captured(self) -> None:
        """Some compatible endpoints attach usage to a normal choice chunk."""
        handler = _openai_handler()
        chunks = [
            {
                "choices": [{"delta": {"content": "answer"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
            },
        ]
        capture = StreamUsageCapture()
        "".join(handler.iter_stream_text(
            chunks, output_reasoning=False, usage_capture=capture,
        ))
        usage = handler.normalize_usage(capture.raw)
        self.assertEqual(usage.total_tokens, 7)

    def test_deepseek_stream_captures_cache_hit_tokens(self) -> None:
        """DeepSeek prompt-cache economics survive the streaming path."""
        handler = _deepseek_handler()
        chunks = [
            {"choices": [{"delta": {"reasoning_content": "think"}}]},
            {"choices": [{"delta": {"content": "answer"}}]},
            {
                "choices": [],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                    "prompt_cache_hit_tokens": 40,
                    "prompt_cache_miss_tokens": 60,
                },
            },
        ]
        capture = StreamUsageCapture()
        text = "".join(handler.iter_stream_text(
            chunks, output_reasoning=True, usage_capture=capture,
        ))
        self.assertIn("<think>", text)
        usage = handler.normalize_usage(capture.raw)
        self.assertEqual(usage.input_tokens, 100)
        self.assertEqual(usage.output_tokens, 50)
        self.assertEqual(usage.cached_tokens, 40)

    def test_anthropic_stream_merges_start_and_delta_usage(self) -> None:
        """Anthropic splits usage; both halves must be merged."""
        handler = _anthropic_handler()
        chunks = [
            {
                "type": "message_start",
                "message": {"usage": {"input_tokens": 200, "output_tokens": 0}},
            },
            {"type": "content_block_start", "content_block": {"type": "text", "text": "hi"}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " there"}},
            {"type": "message_delta", "usage": {"output_tokens": 42}},
        ]
        capture = StreamUsageCapture()
        text = "".join(handler.iter_stream_text(
            chunks, output_reasoning=False, usage_capture=capture,
        ))
        self.assertEqual(text, "hi there")
        usage = handler.normalize_usage(capture.raw)
        self.assertEqual(usage.input_tokens, 200)
        self.assertEqual(usage.output_tokens, 42)
        self.assertEqual(usage.total_tokens, 242)


class LLMFetcherStreamUsageTests(unittest.TestCase):
    """The fetch_stream glue normalizes captured usage into a sink."""

    def test_fetch_stream_fills_usage_sink(self) -> None:
        backend = LLMBackendConfig(
            name="oa", provider="openai", model="gpt-test",
            api_key="test-key", api_url="https://api.openai.com",
        )
        fetcher = LLMFetcher(backends=[backend])

        def fake_create(**kwargs: object):
            # Wire-level stream_options behavior is covered separately by
            # OpenAIHandlerWireTests; swapping in fake_create bypasses the
            # real create_completion, so do not assert stream_options here.
            self.assertTrue(kwargs.get("stream"))
            return [
                {"choices": [{"delta": {"content": "hello"}}]},
                {
                    "choices": [],
                    "usage": {"prompt_tokens": 90, "completion_tokens": 10, "total_tokens": 100},
                },
            ]

        handler = fetcher.handlers["oa"]
        handler.create_completion = fake_create

        sink = TokenUsage()
        chunks = list(fetcher.fetch_stream(
            msg="hi", system_prompt="be brief", usage_sink=sink,
        ))
        self.assertEqual("".join(chunks), "hello")
        self.assertEqual(sink.input_tokens, 90)
        self.assertEqual(sink.output_tokens, 10)
        self.assertEqual(sink.total_tokens, 100)

    def test_fetch_stream_no_usage_leaves_sink_untouched(self) -> None:
        backend = LLMBackendConfig(
            name="oa", provider="openai", model="gpt-test",
            api_key="test-key", api_url="https://api.openai.com",
        )
        fetcher = LLMFetcher(backends=[backend])

        def fake_create(**kwargs: object):
            return [{"choices": [{"delta": {"content": "plain"}}]}]

        fetcher.handlers["oa"].create_completion = fake_create

        sink = TokenUsage()
        list(fetcher.fetch_stream(msg="hi", usage_sink=sink))
        self.assertEqual(sink.total_tokens, 0)


class _UsageStreamingFetcher:
    """Yield normalized chunks and fill the usage sink like real fetchers."""

    default_backend_config = LLMBackendConfig("test", "test", "test-model")

    def fetch_stream(self, usage_sink: TokenUsage | None = None, **_kwargs: object):
        if usage_sink is not None:
            usage_sink.input_tokens = 300
            usage_sink.output_tokens = 60
            usage_sink.total_tokens = 360
            usage_sink.cached_tokens = 100
            usage_sink.reasoning_tokens = 25
        yield "Hel"
        yield "lo"
        yield "\n<think>\n"
        yield "because"
        yield "\n</think>\n"


class AgentStreamUsageTests(unittest.TestCase):
    """A streamed Agent round must publish real token usage."""

    def test_streamed_run_records_usage_in_ledger_event(self) -> None:
        agent = Agent(_UsageStreamingFetcher(), system_prompt="test", default_stream=True)
        events = []
        agent.add_hook(events.append)

        result = agent.run("question")

        self.assertEqual((result.content, result.reasoning_content), ("Hello", "because"))
        # The returned LLMOutput now carries the provider streamed usage.
        self.assertEqual(result.usage.total_tokens, 360)
        self.assertEqual(result.usage.input_tokens, 300)
        self.assertEqual(result.usage.output_tokens, 60)
        self.assertEqual(result.usage.cached_tokens, 100)
        self.assertEqual(result.usage.reasoning_tokens, 25)
        # Agent-accumulated usage includes the streamed round.
        self.assertEqual(agent.usage.total_tokens, 360)
        # The canonical ledger event consumers aggregate must carry real data.
        usage_events = [
            event.data for event in events
            if event.event_type == "agent:usage"
        ]
        self.assertEqual(len(usage_events), 1)
        usage = usage_events[0]["usage"]
        self.assertEqual(usage["total"], 360)
        self.assertEqual(usage["input"], 300)
        self.assertEqual(usage["output"], 60)
        self.assertEqual(usage["cached"], 100)
        self.assertEqual(usage["reasoning"], 25)

    def test_streamed_run_round_usage_field_is_populated(self) -> None:
        """agent:round.round_usage reflects the real per-call usage."""
        agent = Agent(_UsageStreamingFetcher(), system_prompt="test", default_stream=True)
        events = []
        agent.add_hook(events.append)

        agent.run("question")

        round_events = [
            event.data for event in events if event.event_type == "agent:round"
        ]
        self.assertTrue(round_events)
        round_usage = round_events[-1]["round_usage"]
        self.assertEqual(round_usage["total"], 360)


class EndToEndStreamedAgentRunTests(unittest.TestCase):
    """Real handler + real fetcher through Agent.run, with a stubbed wire.

    This is the same call chain the deployed runtime exercises when it
    forces streaming: OpenAIHandler.iter_stream_text captures the usage
    chunk, fetch_stream normalizes it into the sink, and the Agent
    publishes real numbers in the ledger event.
    """

    def _stub_openai_fetcher(self) -> LLMFetcher:
        backend = LLMBackendConfig(
            name="oa", provider="openai", model="gpt-test",
            api_key="test-key", api_url="https://api.openai.com",
        )
        fetcher = LLMFetcher(backends=[backend])

        class _Completions:
            @staticmethod
            def create(**kwargs):
                # OpenAI-compatible stream: two content deltas then the
                # final usage-only chunk (choices empty).
                return [
                    {"choices": [{"delta": {"role": "assistant", "content": ""}}]},
                    {"choices": [{"delta": {"content": "Hello"}}]},
                    {"choices": [{"delta": {"content": " world"}}]},
                    {"choices": [], "usage": {
                        "prompt_tokens": 120,
                        "completion_tokens": 15,
                        "total_tokens": 135,
                    }},
                ]

        class _Chat:
            completions = _Completions()

        fetcher.handlers["oa"].client = type("client", (), {"chat": _Chat()})()
        return fetcher

    def test_real_pipeline_publishes_ledger_usage_event(self) -> None:
        fetcher = self._stub_openai_fetcher()
        agent = Agent(fetcher, system_prompt="test", default_stream=True)
        events: list = []
        agent.add_hook(events.append)

        result = agent.run("hi")

        self.assertEqual(result.content, "Hello world")
        self.assertEqual(result.usage.input_tokens, 120)
        self.assertEqual(result.usage.output_tokens, 15)
        self.assertEqual(result.usage.total_tokens, 135)
        self.assertEqual(agent.usage.total_tokens, 135)

        usage_events = [
            event.data for event in events if event.event_type == "agent:usage"
        ]
        self.assertEqual(len(usage_events), 1)
        usage = usage_events[0]["usage"]
        self.assertEqual(usage["total"], 135)
        self.assertEqual(usage["input"], 120)
        self.assertEqual(usage["output"], 15)

        round_events = [
            event.data for event in events if event.event_type == "agent:round"
        ]
        self.assertTrue(round_events)
        self.assertEqual(round_events[-1]["round_usage"]["total"], 135)


class OpenAIHandlerWireTests(unittest.TestCase):
    """create_completion requests include_usage only for streamed calls."""

    def test_streaming_requests_include_usage(self) -> None:
        captured: list[dict] = []

        class _FakeClient:
            def __init__(self) -> None:
                self.chat = type("chat", (), {})()
                self.chat.completions = type("c", (), {
                    "create": lambda self, **kw: captured.append(kw) or [],
                })()

        handler = _openai_handler()
        handler.client = _FakeClient()
        handler.create_completion(
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.4,
            max_tokens=16,
            stream=True,
        )
        self.assertEqual(captured[0]["stream_options"], {"include_usage": True})

    def test_non_streaming_omits_include_usage(self) -> None:
        captured: list[dict] = []

        class _FakeClient:
            def __init__(self) -> None:
                self.chat = type("chat", (), {})()
                self.chat.completions = type("c", (), {
                    "create": lambda self, **kw: captured.append(kw) or [],
                })()

        handler = _openai_handler()
        handler.client = _FakeClient()
        handler.create_completion(
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.4,
            max_tokens=16,
            stream=False,
        )
        self.assertNotIn("stream_options", captured[0])


if __name__ == "__main__":
    unittest.main()
