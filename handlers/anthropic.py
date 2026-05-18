from __future__ import annotations

from typing import Iterable, Mapping, Optional

from ..llm_types import LLMOutput
from .base import JSONValue, ToolSchema, LLMBackendConfig, LLMToolCall, LLMBackendHandler


class AnthropicHandler(LLMBackendHandler):
    provider_names = frozenset({"anthropic"})

    def __init__(self, fetcher, backend: LLMBackendConfig) -> None:
        super().__init__(fetcher, backend)
        import anthropic

        client_kwargs = {
            "api_key": backend.api_key,
            "timeout": backend.timeout,
        }
        if backend.api_url:
            client_kwargs["base_url"] = backend.api_url
        self.client = anthropic.Anthropic(**client_kwargs)

    def convert_messages(self, messages: list[dict[str, str]]) -> tuple[list[dict[str, JSONValue]], Optional[str]]:
        anthropic_messages: list[dict[str, JSONValue]] = []
        system_message: Optional[str] = None

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "system":
                system_message = content
                continue
            if role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                anthropic_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call_id,
                                "content": content,
                            }
                        ],
                    }
                )
            else:
                anthropic_messages.append({"role": role, "content": content})

        return anthropic_messages, system_message

    def convert_tools(self, tools: list[ToolSchema]) -> list[ToolSchema]:
        anthropic_tools: list[ToolSchema] = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                anthropic_tools.append(
                    {
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {}),
                    }
                )
            else:
                anthropic_tools.append(tool)
        return anthropic_tools

    def create_completion(
        self,
        *,
        messages,
        temperature: float,
        max_tokens: int,
        stream: bool,
        tools=None,
    ):
        anthropic_messages, system_prompt = self.convert_messages(messages)
        kwargs = {
            "model": self.backend.model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = self.convert_tools(tools)
        kwargs.update(self.backend.extra)
        return self.client.messages.create(**kwargs)

    def normalize_completion_response(self, response) -> LLMOutput:
        blocks = self._read_field(response, "content", None) or []
        content, reasoning, tool_calls = self._normalize_anthropic_blocks(blocks)
        return LLMOutput(
            content=content,
            provider=self.backend.provider,
            backend_name=self.backend.name,
            model=self.backend.model,
            role=self._read_field(response, "role", "assistant") or "assistant",
            reasoning_content=reasoning,
            tool_calls=tool_calls,
            stop_reason=self._read_field(response, "stop_reason", None),
            usage=self._usage_to_dict(self._read_field(response, "usage", None)),
        )

    def iter_stream_text(self, response, *, output_reasoning: bool) -> Iterable[str]:
        in_thinking = False
        for chunk in response:
            if isinstance(chunk, dict):
                event_type = chunk.get("type")
                delta = chunk.get("delta")
            else:
                event_type = getattr(chunk, "type", None)
                delta = getattr(chunk, "delta", None)

            if event_type == "content_block_start":
                block = chunk.get("content_block") if isinstance(chunk, dict) else getattr(chunk, "content_block", None)
                block_type = self._read_field(block, "type", None)
                if block_type == "text":
                    content = self._read_field(block, "text", None)
                    if in_thinking and content:
                        yield "\n</think>\n"
                        in_thinking = False
                    if content:
                        yield str(content)
                elif block_type in {"thinking", "reasoning"} and output_reasoning:
                    reasoning = self._extract_reasoning(block)
                    if reasoning:
                        if not in_thinking:
                            yield "\n<think>\n"
                            in_thinking = True
                        yield reasoning
                continue

            if event_type == "content_block_delta":
                delta_type = self._read_field(delta, "type", None)
                if delta_type == "text_delta":
                    text = self._read_field(delta, "text", None)
                    if in_thinking and text:
                        yield "\n</think>\n"
                        in_thinking = False
                    if text:
                        yield str(text)
                elif delta_type in {"thinking_delta", "reasoning_delta"} and output_reasoning:
                    reasoning = self._extract_reasoning(delta)
                    if reasoning:
                        if not in_thinking:
                            yield "\n<think>\n"
                            in_thinking = True
                        yield reasoning
                continue

            if event_type == "text_delta":
                content = self._extract_content(delta or chunk)
                if in_thinking and content:
                    yield "\n</think>\n"
                    in_thinking = False
                if content:
                    yield content
                continue

            if event_type in {"thinking_delta", "reasoning_delta"} and output_reasoning:
                reasoning = self._extract_reasoning(delta or chunk)
                if reasoning:
                    if not in_thinking:
                        yield "\n<think>\n"
                        in_thinking = True
                    yield reasoning

        if in_thinking:
            yield "\n</think>\n"
