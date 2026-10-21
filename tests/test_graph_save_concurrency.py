"""Concurrency regression coverage for ``ExecutionGraph.save``.

Each save writes a uniquely named temporary file and atomically replaces the
destination, so concurrent saves must never leave a torn document or a stray
temp file behind.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import threading
import unittest

from llmfetcher.agent import Agent
from llmfetcher.llm_fetcher import LLMFetcher
from llmfetcher.llm_types import LLMBackendConfig
from llmfetcher.swarm_module.execution_graph import ExecutionGraph


def _agent() -> Agent:
    """Build a tool-free Agent the default serializer accepts."""
    return Agent(
        llm_fetcher=LLMFetcher(
            [
                LLMBackendConfig(
                    name="backend",
                    provider="openai",
                    model="model",
                    api_key="test-key",
                )
            ],
            default_backend="backend",
        ),
        system_prompt="You are a worker.",
        context_providers=(),
    )


class ExecutionGraphSaveConcurrencyTests(unittest.TestCase):
    def test_concurrent_saves_leave_one_valid_document(self) -> None:
        """Six parallel saves leave one parseable document and no temp files."""
        graph = ExecutionGraph(max_concurrency_agents=4)
        self.assertTrue(graph.add_agent("coordinator", _agent()))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            writers = 6
            barrier = threading.Barrier(writers)

            def save(_index: int) -> None:
                barrier.wait(10)
                graph.save(path)

            with ThreadPoolExecutor(max_workers=writers) as pool:
                list(pool.map(save, range(writers)))

            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(1, document["version"])
            self.assertEqual(
                ["coordinator"], [node["name"] for node in document["nodes"]]
            )
            leftovers = sorted(
                item.name
                for item in Path(directory).iterdir()
                if item.name != "graph.json"
            )
            self.assertEqual([], leftovers)


if __name__ == "__main__":
    unittest.main()
