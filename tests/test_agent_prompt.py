"""Regression tests for the model-facing Agent system prompt."""

from __future__ import annotations

import unittest

from llmfetcher.agent import Agent
from llmfetcher.llm_types import (
    LLMBackendConfig,
    LLMOutput,
    RemoteRequestSnapshot,
    Tool,
    ToolParameter,
    ToolSchema,
)


class _RecordingFetcher:
    """Minimal fetcher that exposes the Agent's preflight request boundary."""

    default_backend_config = LLMBackendConfig("test", "test", "test-model")

    def fetch(self, **kwargs):
        """Capture the native tool channel and emit its matching snapshot."""
        native_tools = [
            {"type": "function", "function": {"name": tool.name}}
            for tool in kwargs["tools"]
        ]
        kwargs["on_request"](RemoteRequestSnapshot(
            model="test-model",
            messages=[
                {"role": "system", "content": kwargs["system_prompt"]},
                {"role": "user", "content": "inspect"},
            ],
            temperature=kwargs["temperature"],
            max_tokens=kwargs["max_tokens"],
            stream=False,
            tools=native_tools,
        ))
        return LLMOutput(
            content="done", provider="test", backend_name="test", model="test-model",
        )


class AgentPromptTests(unittest.TestCase):
    """Verify that native tool schemas are not duplicated into system text."""

    def test_system_prompt_excludes_registered_tool_description(self) -> None:
        """Keep a tool's legacy text representation out of ``messages[0]``.

        ``Agent.run`` passes the same Tool object through the separate
        ``tools`` argument to ``LLMFetcher.fetch``. Including it in the system
        prompt would therefore make provider-native requests carry two copies
        of each schema.
        """
        agent = Agent(object(), system_prompt="Follow the user request.")
        agent.add_tool(Tool(
            name="inspect_workspace",
            description="Inspect a workspace without mutation.",
            schemas=ToolSchema(properties=[
                ToolParameter(name="path", type="string", description="Workspace path."),
            ]),
            handler=lambda **_kwargs: "ok",
        ))

        prompt = agent._build_prompt()

        self.assertEqual(prompt, "Follow the user request.")
        self.assertNotIn("Tool name: inspect_workspace", prompt)
        self.assertNotIn("Tool schemas:", prompt)

    def test_remote_request_keeps_tools_out_of_the_system_message(self) -> None:
        """Expose one schema in ``tools`` without duplicating it in ``messages``."""
        agent = Agent(_RecordingFetcher(), system_prompt="Use native tools.")
        agent.add_tool(Tool(
            name="inspect_workspace",
            description="Inspect a workspace without mutation.",
            schemas=ToolSchema(),
            handler=lambda **_kwargs: "ok",
        ))
        events = []
        agent.add_hook(events.append)

        agent.run("inspect")

        snapshot = next(event.data["request"] for event in events if event.event_type == "agent:remote_request")
        self.assertEqual(snapshot["messages"][0], {"role": "system", "content": "Use native tools."})
        self.assertEqual(snapshot["tools"], [{"type": "function", "function": {"name": "inspect_workspace"}}])
