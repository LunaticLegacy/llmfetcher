"""OpenAI wire-name normalization regression tests."""

from __future__ import annotations

import unittest

from llmfetcher.fetcher_handlers.openai import OpenAIHandler
from llmfetcher.llm_types import Tool, ToolSchema


class OpenAIToolNameTests(unittest.TestCase):
    def test_invalid_names_are_normalized_and_reversible(self) -> None:
        handler = object.__new__(OpenAIHandler)
        tools = [Tool("plugin.gzctf.gzctf_login", "login", ToolSchema(), lambda: None)]

        schemas, internal_to_wire, wire_to_internal = handler.prepare_tools_with_mapping(tools)

        wire_name = schemas[0]["function"]["name"]
        self.assertNotEqual(wire_name, tools[0].name)
        self.assertRegex(wire_name, r"^[a-zA-Z0-9_-]+$")
        self.assertEqual(wire_name, internal_to_wire[tools[0].name])
        self.assertEqual(tools[0].name, wire_to_internal[wire_name])

    def test_valid_names_are_preserved(self) -> None:
        handler = object.__new__(OpenAIHandler)
        tools = [Tool("read_task-plan_1", "read", ToolSchema(), lambda: None)]

        schemas, internal_to_wire, wire_to_internal = handler.prepare_tools_with_mapping(tools)

        self.assertEqual("read_task-plan_1", schemas[0]["function"]["name"])
        self.assertEqual({"read_task-plan_1": "read_task-plan_1"}, internal_to_wire)
        self.assertEqual({"read_task-plan_1": "read_task-plan_1"}, wire_to_internal)

    def test_wire_name_collision_is_rejected(self) -> None:
        handler = object.__new__(OpenAIHandler)
        tools = [
            Tool("a__x2e__b", "one", ToolSchema(), lambda: None),
            Tool("a.b", "two", ToolSchema(), lambda: None),
        ]

        with self.assertRaisesRegex(ValueError, "collision"):
            handler.prepare_tools_with_mapping(tools)


if __name__ == "__main__":
    unittest.main()
