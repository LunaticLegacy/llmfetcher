"""Tests for Agent-facing GraphContext tools."""

from __future__ import annotations

import json
import unittest

from llmfetcher.graph_memory import GraphContextHandler, create_graph_tools
from llmfetcher.llm_types import LLMBackendConfig, LLMOutput


class _Compactor:
    @property
    def default_backend_config(self) -> LLMBackendConfig:
        return LLMBackendConfig(name="test", provider="test", model="test-model")


class GraphToolTests(unittest.TestCase):
    def test_context_build_order_is_previous_graph_last_round_current_user(self) -> None:
        context = GraphContextHandler(compacting_fetcher=_Compactor(), retrieval_trigger="manual")
        context.add_user_message("previous user")
        context.add_assistant_message(LLMOutput(
            content="previous assistant", provider="test",
            backend_name="test", model="test-model",
        ))
        context.add_user_message("current user")
        context._graph_memory = "<graph_memory>retrieved</graph_memory>"

        messages = context.build_messages(system_prompt="system")

        self.assertEqual(
            [(message.role, message.content) for message in messages],
            [
                ("system", "system"),
                ("user", "previous user"),
                ("user", "<graph_memory>retrieved</graph_memory>"),
                ("assistant", "previous assistant"),
                ("user", "current user"),
            ],
        )

    def test_graph_tools_edit_and_read_the_bound_store(self) -> None:
        context = GraphContextHandler(compacting_fetcher=_Compactor(), retrieval_trigger="manual")
        tools = {tool.name: tool for tool in create_graph_tools(context)}

        first = json.loads(tools["graph_upsert_entity"].handler(name="GraphContext", entity_type="class"))
        second = json.loads(tools["graph_upsert_entity"].handler(name="GraphStore", entity_type="class"))
        relation = json.loads(tools["graph_upsert_relation"].handler(
            source=first["entity"]["id"],
            target=second["entity"]["id"],
            relation="uses",
        ))

        neighbors = json.loads(tools["graph_get_neighbors"].handler(entity="GraphContext"))
        self.assertEqual(relation["relation"]["relation"], "uses")
        self.assertEqual([item["entity"]["name"] for item in neighbors["neighbors"]], ["GraphStore"])

        invalidated = json.loads(tools["graph_invalidate_relation"].handler(
            source="GraphContext", target="GraphStore",
        ))
        self.assertEqual(invalidated["invalidated"], 1)

    def test_graph_search_returns_retrieval_projection(self) -> None:
        context = GraphContextHandler(compacting_fetcher=_Compactor(), retrieval_trigger="manual")
        tools = {tool.name: tool for tool in create_graph_tools(context)}
        tools["graph_upsert_entity"].handler(name="GraphStore", entity_type="class")

        result = json.loads(tools["graph_search"].handler(query="GraphStore"))

        self.assertEqual(result["query"], "GraphStore")
        self.assertEqual(result["hits"][0]["entity"]["name"], "GraphStore")


if __name__ == "__main__":
    unittest.main()
