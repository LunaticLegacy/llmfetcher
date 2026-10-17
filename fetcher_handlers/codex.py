"""OpenAI Responses API handler for Codex models."""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, Optional, Sequence

from ..llm_types import LLMOutput, LLMToolCall
from ._tool_schemas import to_openai_tool_schemas
from .base import LLMBackendHandler, ToolDefinition, ToolSchemaDict


class CodexHandler(LLMBackendHandler):
    """Dispatch Codex through the OpenAI Responses API."""

    provider_names = frozenset({"codex"})
    selection_priority = 20

    def __init__(self, fetcher, backend):
        super().__init__(fetcher, backend)
        import openai
        self.client = openai.OpenAI(api_key=backend.api_key, base_url=backend.api_url)

    @staticmethod
    def _field(value: object, name: str, default: Any = None) -> Any:
        if isinstance(value, Mapping):
            return value.get(name, default)
        return getattr(value, name, default)

    @staticmethod
    def _parse_arguments(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}

    @classmethod
    def _input_items(cls, messages: Sequence[Mapping[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        instructions: list[str] = []
        items: list[dict[str, Any]] = []
        for message in messages:
            role = str(message.get("role", "user"))
            content = message.get("content")
            if role == "system":
                if content:
                    instructions.append(str(content))
                continue
            if role == "tool":
                items.append({"type": "function_call_output", "call_id": str(message.get("tool_call_id", "")), "output": str(content or "")})
                continue
            tool_calls = message.get("tool_calls") or []
            if role == "assistant" and tool_calls:
                if content:
                    items.append({"role": "assistant", "content": str(content)})
                for call in tool_calls:
                    items.append({
                        "type": "function_call",
                        "call_id": str(call.get("id", call.get("call_id", ""))),
                        "name": str(call.get("name", "")),
                        "arguments": json.dumps(call.get("arguments", {}), ensure_ascii=False),
                    })
                continue
            items.append({"role": role, "content": str(content or "")})
        return "\n\n".join(instructions), items

    def prepare_tools(self, tools: Optional[Sequence[ToolDefinition]]) -> Optional[list[ToolSchemaDict]]:
        schemas = to_openai_tool_schemas(tools)
        if not schemas:
            return schemas
        converted: list[ToolSchemaDict] = []
        for schema in schemas:
            function = schema.get("function") if isinstance(schema, dict) else None
            if not isinstance(function, dict):
                converted.append(schema)
                continue
            converted.append({
                "type": "function",
                "name": function.get("name", "tool"),
                "description": function.get("description", ""),
                "parameters": function.get("parameters", {"type": "object", "properties": {}}),
            })
        return converted

    def create_completion(self, *, messages, temperature: float, max_tokens: int, stream: bool,
                          tools=None, thinking_mode: str = "auto", reasoning_effort: str = "auto"):
        instructions, input_items = self._input_items(messages)
        kwargs: dict[str, Any] = {
            "model": self.backend.model,
            "input": input_items,
            "max_output_tokens": max_tokens,
            "stream": stream,
            "timeout": self.backend.timeout,
        }
        if instructions:
            kwargs["instructions"] = instructions
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if reasoning_effort != "auto":
            kwargs["reasoning"] = {"effort": reasoning_effort}
        if self.backend.extra.get("supports_temperature"):
            kwargs["temperature"] = temperature
        extra = dict(self.backend.extra)
        extra.pop("supports_temperature", None)
        kwargs.update(extra)
        return self.client.responses.create(**kwargs)

    def normalize_completion_response(self, response) -> LLMOutput:
        text = self._field(response, "output_text", "") or ""
        calls: list[LLMToolCall] = []
        for item in list(self._field(response, "output", []) or []):
            if self._field(item, "type") != "function_call":
                continue
            calls.append(LLMToolCall(
                name=str(self._field(item, "name", "")),
                arguments=self._parse_arguments(self._field(item, "arguments", {})),
                call_id=self._field(item, "call_id", None),
                source="codex_responses",
            ))
        return LLMOutput(
            content=str(text), provider=self.backend.provider, backend_name=self.backend.name,
            model=self.backend.model, role="assistant", tool_calls=calls,
            stop_reason=self._field(response, "status", None),
            usage=self.normalize_usage(self._field(response, "usage", None)),
        )

    def iter_stream_text(self, response, *, output_reasoning: bool, usage_capture=None) -> Iterable[str]:
        calls: dict[str, dict[str, Any]] = {}
        for event in response:
            event_type = str(self._field(event, "type", ""))
            if event_type == "response.output_text.delta":
                delta = self._field(event, "delta", "")
                if delta:
                    yield str(delta)
            elif event_type == "response.output_item.added":
                item = self._field(event, "item", None)
                if self._field(item, "type") == "function_call":
                    key = str(self._field(item, "call_id", self._field(item, "id", "")))
                    calls[key] = {"name": str(self._field(item, "name", "")), "args": []}
            elif event_type == "response.function_call_arguments.delta":
                key = str(self._field(event, "item_id", self._field(event, "call_id", "")))
                calls.setdefault(key, {"name": "", "args": []})["args"].append(str(self._field(event, "delta", "")))
            elif event_type == "response.completed" and usage_capture is not None:
                response_obj = self._field(event, "response", None)
                usage_capture.merge(self._usage_to_dict(self._field(response_obj, "usage", None)))
        for call in calls.values():
            if call["name"]:
                payload = {"name": call["name"], "arguments": self._parse_arguments("".join(call["args"]))}
                yield "\n<tool_call>\n" + json.dumps(payload, ensure_ascii=False) + "\n</tool_call>\n"
