"""Regression coverage for lifecycle-safe usage aggregation.

``Agent.usage`` intentionally describes only the most recent ``run``
lifecycle. The Session aggregate, however, must not shrink when a new
lifecycle starts: earlier usage has to survive. These tests pin that
``Agent.lifetime_usage`` never resets and that ``AgentSwarm`` reads it.
"""

from __future__ import annotations

import unittest

from llmfetcher.agent import Agent
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.llm_fetcher import LLMBackendConfig
from llmfetcher.llm_types import LLMOutput, TokenUsage
from llmfetcher.swarm_module.swarm import AgentSwarm


class _ScriptedFetcher:
    """Return a fixed provider usage for every model round."""

    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self._backend = LLMBackendConfig(
            name="test", provider="test", model="test-model"
        )
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    @property
    def default_backend_config(self) -> LLMBackendConfig:
        return self._backend

    def fetch(self, **_: object) -> LLMOutput:
        return LLMOutput(
            content="done",
            provider="test",
            backend_name="test",
            model="test-model",
            usage=TokenUsage(
                input_tokens=self.input_tokens,
                output_tokens=self.output_tokens,
                total_tokens=self.input_tokens + self.output_tokens,
            ),
        )


def _make_agent(fetcher: _ScriptedFetcher) -> Agent:
    handler = ContextHandlerLinear(
        compacting_llmfetcher_handler=fetcher,
        max_context_threshold=262144,
    )
    return Agent(
        fetcher,
        system_prompt="system",
        context_handler=handler,
        context_path=None,
    )


class _LegacyAgent:
    """Agent-shaped fake without ``lifetime_usage`` (older builds / hosts)."""

    def __init__(self, usage: TokenUsage) -> None:
        self.usage = usage


class UsageLifetimeTests(unittest.TestCase):
    """A new lifecycle must not erase the Session's earlier usage."""

    def test_lifetime_usage_accumulates_across_runs(self) -> None:
        """The per-run counter resets; the lifetime counter keeps growing."""
        fetcher = _ScriptedFetcher(input_tokens=100, output_tokens=50)
        agent = _make_agent(fetcher)

        agent.run("first")
        self.assertEqual(150, agent.usage.total_tokens)
        self.assertEqual(150, agent.lifetime_usage.total_tokens)

        fetcher.input_tokens, fetcher.output_tokens = 10, 5
        agent.run("second")

        # Per-run view describes only the newest lifecycle ...
        self.assertEqual(15, agent.usage.total_tokens)
        # ... while the lifetime view preserves the earlier lifecycle.
        self.assertEqual(165, agent.lifetime_usage.total_tokens)
        self.assertEqual(110, agent.lifetime_usage.input_tokens)
        self.assertEqual(55, agent.lifetime_usage.output_tokens)

    def test_swarm_total_usage_does_not_drop_on_new_lifecycle(self) -> None:
        """The Session aggregate is monotonic across consecutive runs."""
        fetcher = _ScriptedFetcher(input_tokens=100, output_tokens=50)
        swarm = AgentSwarm()
        agent = _make_agent(fetcher)
        swarm.add_agent("coordinator", agent)

        agent.run("first")
        first = swarm.total_usage()
        self.assertEqual(150, first["total"])

        fetcher.input_tokens, fetcher.output_tokens = 10, 5
        agent.run("second")
        second = swarm.total_usage()

        self.assertGreaterEqual(second["total"], first["total"])
        self.assertEqual(165, second["total"])
        self.assertEqual(165, swarm.agent_usage()["coordinator"]["total"])

    def test_swarm_falls_back_to_usage_without_lifetime_counter(self) -> None:
        """Legacy agents expose their per-run counter instead of dropping out."""
        swarm = AgentSwarm()
        legacy = _LegacyAgent(
            TokenUsage(input_tokens=7, output_tokens=3, total_tokens=10)
        )
        swarm.add_agent("legacy", legacy)  # type: ignore[arg-type]

        self.assertEqual(10, swarm.total_usage()["total"])
        self.assertEqual(10, swarm.agent_usage()["legacy"]["total"])


if __name__ == "__main__":
    unittest.main()
