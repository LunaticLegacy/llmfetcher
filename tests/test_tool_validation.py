"""Regression coverage for malformed model tool calls and save diagnostics."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from llmfetcher.agent import Agent, ContextSaveError
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.llm_types import LLMToolCall, Tool, ToolParameter, ToolSchema
from llmfetcher.tool_executor import ToolExecutor
from llmfetcher.tool_handler import ToolCallValidationError, ToolHandler


class ToolCallValidationTests(unittest.TestCase):
    """Ensure malformed model calls become recoverable tool feedback."""

    def setUp(self) -> None:
        self.handler = ToolHandler()
        self.handler.add_tool(Tool(
            "weather",
            "Read weather at one location.",
            ToolSchema(properties=[ToolParameter("location", "string")]),
            lambda location: f"weather for {location}",
        ))

    def _execute(self, call: LLMToolCall) -> object:
        handlers, arguments = self.handler.get_handlers_and_arguments([call])
        return ToolExecutor().execute_batch(handlers, arguments)[0]

    def test_missing_required_field_returns_model_visible_error(self) -> None:
        result = self._execute(LLMToolCall("weather", {}))

        self.assertIsInstance(result, ToolCallValidationError)
        self.assertIn("missing required field(s): location", str(result))

    def test_wrong_type_and_unknown_name_return_model_visible_errors(self) -> None:
        wrong_type = self._execute(LLMToolCall("weather", {"location": ["Xi'an"]}))
        unknown = self._execute(LLMToolCall("not_registered", {}))

        self.assertIsInstance(wrong_type, ToolCallValidationError)
        self.assertIn("location must be string", str(wrong_type))
        self.assertIsInstance(unknown, ToolCallValidationError)
        self.assertEqual("Unknown tool: not_registered", str(unknown))

    def test_compact_schema_rejects_unexpected_field(self) -> None:
        result = self._execute(LLMToolCall("weather", {"location": "Xi'an", "units": "metric"}))

        self.assertIsInstance(result, ToolCallValidationError)
        self.assertIn("unexpected field: units", str(result))


class ContextSaveDiagnosticTests(unittest.TestCase):
    """Retain the actual context-save failure through the Agent boundary."""

    def test_agent_chains_handler_save_failure(self) -> None:
        context = ContextHandlerLinear(object())
        context.add_user_message("persist this")
        with TemporaryDirectory() as directory:
            agent = object.__new__(Agent)
            agent.context_path = Path(directory) / "context.json"
            agent.context_handler = context
            cause = OSError("database is locked")
            with patch.object(context, "_save_sqlite_rows", side_effect=cause):
                with self.assertRaises(ContextSaveError) as caught:
                    agent._save_context()

        self.assertIs(caught.exception.__cause__, cause)
        self.assertIn("OSError: database is locked", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
