"""Regression tests for durable internal LLM usage accounting."""

from __future__ import annotations

import unittest

from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.agent import Agent
from llmfetcher.graph_memory.builder import GraphBuilder
from llmfetcher.graph_memory.graph_store import GraphStore
from llmfetcher.graph_memory.retriever import GraphRetriever
from llmfetcher.llm_types import LLMBackendConfig, LLMContext, LLMOutput, TokenUsage


class _Fetcher:
    def __init__(self, content: str, usage: TokenUsage) -> None:
        self.content = content
        self.usage = usage

    def fetch(self, **_kwargs):
        return LLMOutput(
            content=self.content, provider="test", backend_name="test",
            model="test", usage=self.usage,
        )


class _AgentFetcher(_Fetcher):
    default_backend_config = LLMBackendConfig("test", "test", "test")

    def fetch(self, **kwargs):
        if "context compactor" in (kwargs.get("system_prompt") or ""):
            return LLMOutput(
                content="<context_abstract>kept</context_abstract>",
                provider="test", backend_name="test", model="test",
                usage=TokenUsage(8, 3, 11, 2, 1),
            )
        return LLMOutput(
            content="done", provider="test", backend_name="test", model="test",
            usage=TokenUsage(5, 4, 9, 1, 2),
        )


class UsageLedgerTests(unittest.TestCase):
    def test_compaction_record_is_drained_once(self):
        handler = ContextHandlerLinear(
            _Fetcher("<context_abstract>kept</context_abstract>", TokenUsage(
                input_tokens=8, output_tokens=3, total_tokens=11,
                cached_tokens=2, reasoning_tokens=1,
            )),
        )
        handler.add_user_message("history")
        self.assertTrue(handler.compact())
        records = handler.drain_usage_records()
        self.assertEqual([(r.kind, r.usage.total_tokens) for r in records], [("compaction", 11)])
        self.assertEqual(handler.drain_usage_records(), [])

    def test_graph_calls_have_distinct_kinds_and_preserve_dimensions(self):
        usage = TokenUsage(4, 2, 6, 1, 2)
        builder = GraphBuilder(GraphStore(), fetcher=_Fetcher(
            '{"entities": [{"name": "Thing", "type": "concept"}], "relations": []}', usage,
        ))
        builder.ingest([LLMContext("user", 1, "Thing")])
        extraction = builder.drain_usage_records()
        self.assertEqual(extraction[0].kind, "graph_extraction")
        self.assertEqual(extraction[0].usage.cached_tokens, 1)
        self.assertEqual(extraction[0].usage.reasoning_tokens, 2)

        store = GraphStore()
        store.upsert_entity("Thing", "concept", timeline=1)
        retriever = GraphRetriever(store, query_fetcher=_Fetcher(
            '{"entities": [{"name": "Thing"}]}', usage,
        ))
        retriever.retrieve("Thing")
        query = retriever.drain_usage_records()
        self.assertEqual(query[0].kind, "graph_query")
        self.assertEqual(query[0].usage.total_tokens, 6)
        self.assertEqual(retriever.drain_usage_records(), [])

    def test_agent_emits_primary_and_internal_usage_once(self):
        fetcher = _AgentFetcher("", TokenUsage())
        handler = ContextHandlerLinear(fetcher, max_context_threshold=1)
        agent = Agent(fetcher, system_prompt="test", context_handler=handler)
        events = []
        agent.add_hook(events.append)
        agent.run("input")

        usage_events = [event for event in events if event.event_type == "agent:usage"]
        internal_events = [event for event in events if event.event_type == "agent:internal_usage"]
        self.assertEqual(len(usage_events), 1)
        self.assertEqual(usage_events[0].data["usage"], {
            "input": 5, "output": 4, "total": 9, "cached": 1, "reasoning": 2,
        })
        self.assertEqual(len(internal_events), 1)
        self.assertEqual(internal_events[0].data["kind"], "compaction")
        complete = next(event for event in events if event.event_type == "agent:complete")
        self.assertEqual(complete.data["usage"], {
            "input": 13, "output": 7, "total": 20, "cached": 3, "reasoning": 3,
        })


if __name__ == "__main__":
    unittest.main()
