"""Coverage for the host-selectable context handler catalog."""

from __future__ import annotations

import unittest

from llmfetcher.context_handlers import (
    DEFAULT_CONTEXT_HANDLER,
    SageContext,
    available_context_handlers,
    context_handler_specs,
    create_context_handler,
)
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.graph_memory import GraphContextHandler
from llmfetcher.llm_types import LLMBackendConfig


class _Fetcher:
    """Stand in for the compaction fetcher every handler is built with."""

    @property
    def default_backend_config(self) -> LLMBackendConfig:
        """Describe the one backend this fetcher reports."""
        return LLMBackendConfig(name="test", provider="test", model="test-model")


class ContextHandlerRegistryTests(unittest.TestCase):
    """The registry is the single list a host offers and builds from."""

    def test_catalog_is_sorted_and_fully_described(self) -> None:
        """Every selectable handler carries a title and a description."""
        ids = available_context_handlers()

        self.assertEqual(ids, tuple(sorted(ids)))
        self.assertEqual(ids, ("graph", "linear", "sage"))
        self.assertEqual([spec.id for spec in context_handler_specs()], list(ids))
        for spec in context_handler_specs():
            self.assertTrue(spec.title, spec.id)
            self.assertTrue(spec.description, spec.id)

    def test_default_handler_is_registered(self) -> None:
        """The fallback a host uses before a user chooses must exist."""
        self.assertIn(DEFAULT_CONTEXT_HANDLER, available_context_handlers())

    def test_each_entry_builds_its_handler(self) -> None:
        """A registry entry must be constructible from the shared config."""
        expected = {
            "graph": GraphContextHandler,
            "linear": ContextHandlerLinear,
            "sage": SageContext,
        }

        for name, handler_type in expected.items():
            with self.subTest(handler=name):
                handler = create_context_handler(name, fetcher=_Fetcher())
                self.assertIsInstance(handler, handler_type)

    def test_unknown_name_reports_the_available_ids(self) -> None:
        """A bad profile value must fail loudly and list the options."""
        with self.assertRaises(ValueError) as context:
            create_context_handler("nonexistent", fetcher=_Fetcher())

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("graph", str(context.exception))


if __name__ == "__main__": unittest.main()
