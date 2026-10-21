"""Round-trip the durable execution-graph snapshot."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from llmfetcher.agent import Agent
from llmfetcher.llm_fetcher import LLMFetcher
from llmfetcher.llm_types import LLMBackendConfig
from llmfetcher.swarm_module.execution_graph import ExecutionGraph
from llmfetcher.swarm_module.snapshots import ExecutionGraphSnapshot


def _agent() -> Agent:
    """Build a tool-free Agent the default serializer accepts."""
    return Agent(
        llm_fetcher=LLMFetcher(
            [LLMBackendConfig(name="backend", provider="openai", model="model", api_key="test-key")],
            default_backend="backend",
        ),
        system_prompt="You are a worker.",
        context_providers=(),
    )


class ExecutionGraphSnapshotTests(unittest.TestCase):
    def test_snapshot_json_round_trip(self) -> None:
        """One writer field set decodes back into an equal record."""
        graph = ExecutionGraph(max_concurrency_agents=4)
        self.assertTrue(graph.add_agent("coordinator", _agent()))
        snapshot = graph.to_snapshot()

        encoded = json.loads(json.dumps(snapshot.to_json()))

        self.assertEqual(ExecutionGraphSnapshot.from_json(encoded), snapshot)

    def test_saved_graph_reloads_with_the_same_view(self) -> None:
        """``save`` and ``load`` agree on topology and node state."""
        graph = ExecutionGraph(max_concurrency_agents=4)
        self.assertTrue(graph.add_agent("coordinator", _agent()))
        self.assertTrue(graph.add_agent("worker", _agent()))
        graph.add_connection("coordinator", "worker")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            graph.save(path)

            restored = ExecutionGraph.load(path)

        self.assertEqual(restored.view_snapshot(), graph.view_snapshot())

    def test_snapshot_rejects_an_unknown_field(self) -> None:
        """A field the writer never emits is a decode error."""
        graph = ExecutionGraph()
        self.assertTrue(graph.add_agent("coordinator", _agent()))
        document = graph.to_snapshot().to_json()
        document["extra"] = 1

        with self.assertRaises(ValueError):
            ExecutionGraphSnapshot.from_json(document)


if __name__ == "__main__":
    unittest.main()
