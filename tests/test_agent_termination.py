"""Regression coverage for explicit Agent turn termination semantics."""

from __future__ import annotations

import unittest

from llmfetcher.agent import Agent, AgentRunLimitReached, AgentRunTermination
from llmfetcher.llm_fetcher import LLMBackendConfig
from llmfetcher.llm_types import LLMOutput, LLMToolCall, Tool, ToolSchema


class _SequenceFetcher:
    """Return predetermined model outputs while recording native tool delivery."""

    default_backend_config = LLMBackendConfig("test", "test", "test-model")

    def __init__(self, outputs: list[LLMOutput]) -> None:
        """Initialize one finite output sequence for an Agent run."""
        self.outputs = list(outputs)
        self.tool_names: list[list[str]] = []

    def fetch(self, **kwargs: object) -> LLMOutput:
        """Record the tools passed natively and return the next response."""
        tools = kwargs["tools"]
        self.tool_names.append([tool.name for tool in tools])  # type: ignore[union-attr]
        return self.outputs.pop(0)


class _StreamingFetcher:
    """Yield fixed provider chunks for Agent stream assembly coverage."""

    default_backend_config = LLMBackendConfig("test", "test", "test-model")

    def fetch_stream(self, **_kwargs: object):
        """Yield content and reasoning chunks in the normalized stream format."""
        yield "Hel"
        yield "lo"
        yield "\n<think>\n"
        yield "because"
        yield "\n</think>\n"


def _output(content: str = "", calls: list[LLMToolCall] | None = None) -> LLMOutput:
    """Create one compact test response with optional native tool calls."""
    return LLMOutput(
        content=content,
        provider="test",
        backend_name="test",
        model="test-model",
        tool_calls=calls or [],
    )


class AgentTerminationTests(unittest.TestCase):
    """Verify formal answers, control tools, empty responses, and budgets differ."""

    def test_formal_content_ends_without_a_tool_result(self) -> None:
        """A normal assistant response is a successful terminal outcome."""
        agent = Agent(_SequenceFetcher([_output("Answer")]), system_prompt="test")

        result = agent.run("question")

        self.assertEqual(result.content, "Answer")
        self.assertEqual(agent.last_outcome.termination, AgentRunTermination.FINAL_RESPONSE)  # type: ignore[union-attr]

    def test_streamed_chunks_become_deltas_and_one_final_output(self) -> None:
        """Streaming remains incremental for the UI but final for persistence."""
        agent = Agent(_StreamingFetcher(), system_prompt="test", default_stream=True)
        events = []
        agent.add_hook(events.append)

        result = agent.run("question")

        self.assertEqual((result.content, result.reasoning_content), ("Hello", "because"))
        self.assertEqual(
            [(event.data["channel"], event.data["delta"]) for event in events if event.event_type == "agent:stream_delta"],
            [("content", "Hel"), ("content", "lo"), ("reasoning", "because")],
        )

    def test_empty_tool_result_does_not_end_the_agent_turn(self) -> None:
        """Tool-call presence, not its returned text, controls continuation."""
        fetcher = _SequenceFetcher([
            _output(calls=[LLMToolCall("empty_tool", {}, "call-1")]),
            _output("Final answer"),
        ])
        agent = Agent(fetcher, system_prompt="test")
        agent.add_tool(Tool("empty_tool", "Returns no text.", ToolSchema(), lambda: ""))

        result = agent.run("question")

        self.assertEqual(result.content, "Final answer")
        self.assertEqual(len(fetcher.tool_names), 2)
        self.assertEqual(agent.last_outcome.termination, AgentRunTermination.FINAL_RESPONSE)  # type: ignore[union-attr]

    def test_stop_turn_ends_after_its_tool_batch(self) -> None:
        """The reserved tool creates a visible terminal control outcome."""
        agent = Agent(_SequenceFetcher([
            _output(calls=[LLMToolCall("stop_turn", {"reason": "awaiting user"}, "call-1")]),
        ]), system_prompt="test", enable_stop_turn=True)

        agent.run("question")

        self.assertEqual(agent.last_outcome.termination, AgentRunTermination.STOP_TURN)  # type: ignore[union-attr]
        self.assertEqual(agent.last_outcome.detail, "awaiting user")  # type: ignore[union-attr]

    def test_empty_model_response_is_not_silent_completion(self) -> None:
        """A blank response without tools raises an observable invalid outcome."""
        agent = Agent(_SequenceFetcher([_output()]), system_prompt="test")

        with self.assertRaisesRegex(RuntimeError, "no tool calls and no formal content"):
            agent.run("question")

        self.assertEqual(agent.last_outcome.termination, AgentRunTermination.EMPTY_RESPONSE)  # type: ignore[union-attr]

    def test_round_limit_rejects_an_unfinished_tool_loop(self) -> None:
        """Budget exhaustion cannot present a pending tool call as a final answer."""
        agent = Agent(_SequenceFetcher([
            _output(calls=[LLMToolCall("unfinished", {}, "call-1")]),
        ]), system_prompt="test")
        agent.add_tool(Tool("unfinished", "Leaves more work.", ToolSchema(), lambda: "ok"))

        with self.assertRaises(AgentRunLimitReached):
            agent.run("question", max_rounds=1)

        self.assertEqual(agent.last_outcome.termination, AgentRunTermination.ROUND_LIMIT)  # type: ignore[union-attr]

    def test_workflow_completion_remains_distinct_from_stop_turn(self) -> None:
        """Worker-report style handlers retain their explicit completion reason."""
        fetcher = _SequenceFetcher([
            _output(calls=[LLMToolCall("finish", {}, "call-1")]),
        ])
        agent = Agent(fetcher, system_prompt="test")
        agent.add_tool(Tool("finish", "Finish a workflow.", ToolSchema(), agent.request_completion))

        agent.run("question")

        self.assertEqual(agent.last_outcome.termination, AgentRunTermination.WORKFLOW_COMPLETION)  # type: ignore[union-attr]
