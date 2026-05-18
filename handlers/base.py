from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import ClassVar, Iterable, Mapping, Optional, Protocol, Sequence, TYPE_CHECKING, TypeAlias

from ..llm_types import LLMBackendConfig, LLMOutput, LLMToolCall

if TYPE_CHECKING:  # pragma: no cover - imported only for type checking
    from .openvino import OpenVINOGenerateResult, OpenVINOHistory
    from ..llm_fetcher import LLMFetcher


JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
JSONObject: TypeAlias = dict[str, JSONValue]
ToolSchema: TypeAlias = dict[str, JSONValue]


class _UsageLike(Protocol):
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    input_tokens: int | None
    output_tokens: int | None

    def model_dump(self) -> JSONObject: ...


class LLMBackendHandler(ABC):
    """Base class for backend-specific request/response handlers."""

    provider_names: ClassVar[frozenset[str]] = frozenset()

    def __init__(self, fetcher: "LLMFetcher", backend: LLMBackendConfig) -> None:
        self.fetcher = fetcher
        self.backend = backend

    @classmethod
    def supports_backend(cls, backend: LLMBackendConfig) -> bool:
        return backend.provider in cls.provider_names

    @classmethod
    def from_backend(cls, fetcher: "LLMFetcher", backend: LLMBackendConfig) -> "LLMBackendHandler":
        return cls(fetcher, backend)

    @classmethod
    def _iter_descendants(cls) -> Iterable[type["LLMBackendHandler"]]:
        for subclass in cls.__subclasses__():
            yield subclass
            yield from subclass._iter_descendants()

    @classmethod
    def create_for_backend(
        cls,
        fetcher: "LLMFetcher",
        backend: LLMBackendConfig,
    ) -> "LLMBackendHandler":
        for handler_cls in cls._iter_descendants():
            if handler_cls.supports_backend(backend):
                return handler_cls.from_backend(fetcher, backend)
        raise ValueError(f"Unsupported provider: {backend.provider}")

    @abstractmethod
    def create_completion(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        tools: Optional[list[ToolSchema]] = None,
    ):
        raise NotImplementedError

    @abstractmethod
    def normalize_completion_response(self, response) -> LLMOutput:
        raise NotImplementedError

    @abstractmethod
    def iter_stream_text(self, response, *, output_reasoning: bool) -> Iterable[str]:
        raise NotImplementedError

    def convert_messages(self, messages: list[dict[str, str]]) -> tuple[list[dict[str, JSONValue]], Optional[str]]:
        return messages, None

    def convert_tools(self, tools: list[ToolSchema]) -> list[ToolSchema]:
        return tools

    def build_chat_history(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[ToolSchema]] = None,
    ):
        return messages

    def generation_config(self, *, temperature: float, max_tokens: int) -> JSONObject:
        return {}

    def call_generate(self, prompt_or_history, config: JSONObject):
        raise NotImplementedError

    def result_text(self, result) -> str:
        return str(result)

    def create_stream(self, prompt_or_history, config: JSONObject) -> Iterable[str]:
        raise NotImplementedError

    def _read_field(
        self,
        value: object | Mapping[str, JSONValue] | None,
        name: str,
        default: object | JSONValue | None = None,
    ) -> object | JSONValue | None:
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)

    def _coerce_content_to_text(
        self,
        content: str | Sequence[JSONValue] | object | None,
    ) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        parts.append(str(part.get("text", "")))
                    elif "text" in part:
                        parts.append(str(part["text"]))
                else:
                    text = getattr(part, "text", None)
                    if text:
                        parts.append(str(text))
            return "".join(parts)
        return str(content)

    def _usage_to_dict(self, usage: _UsageLike | Mapping[str, JSONValue] | None) -> JSONObject:
        if usage is None:
            return {}
        if isinstance(usage, dict):
            return dict(usage)
        if hasattr(usage, "model_dump"):
            dumped = usage.model_dump()
            return dict(dumped) if isinstance(dumped, dict) else {}

        result: JSONObject = {}
        for name in (
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "input_tokens",
            "output_tokens",
        ):
            value = getattr(usage, name, None)
            if value is not None:
                result[name] = value
        return result

    def _parse_arguments(self, arguments: str | Mapping[str, JSONValue] | None) -> JSONObject:
        if isinstance(arguments, dict):
            return dict(arguments)
        if isinstance(arguments, str) and arguments.strip():
            try:
                parsed = json.loads(arguments)
            except json.JSONDecodeError:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _extract_content(
        self,
        delta: object | Mapping[str, JSONValue] | None,
    ) -> Optional[str]:
        if delta is None:
            return None
        if isinstance(delta, dict):
            content = delta.get("content") or delta.get("text")
            return str(content) if content is not None else None
        content = getattr(delta, "content", None) or getattr(delta, "text", None)
        return str(content) if content is not None else None

    def _extract_reasoning(
        self,
        delta: object | Mapping[str, JSONValue] | None,
    ) -> Optional[str]:
        if delta is None:
            return None
        if isinstance(delta, dict):
            reasoning = delta.get("reasoning_content") or delta.get("reasoning") or delta.get("thinking")
            return str(reasoning) if reasoning is not None else None
        reasoning = (
            getattr(delta, "reasoning_content", None)
            or getattr(delta, "reasoning", None)
            or getattr(delta, "thinking", None)
        )
        return str(reasoning) if reasoning is not None else None

    def _normalize_openai_tool_calls(self, message: object | Mapping[str, JSONValue] | None) -> list[LLMToolCall]:
        raw_calls = self._read_field(message, "tool_calls", None) or []
        calls: list[LLMToolCall] = []
        for raw_call in raw_calls:
            function = self._read_field(raw_call, "function", {}) or {}
            name = self._read_field(function, "name", "")
            if not name:
                continue
            calls.append(
                LLMToolCall(
                    name=str(name),
                    arguments=self._parse_arguments(self._read_field(function, "arguments", {})),
                    call_id=self._read_field(raw_call, "id", None),
                    source="openai_native",
                )
            )
        return calls

    def _normalize_anthropic_blocks(
        self,
        blocks: Iterable[object | Mapping[str, JSONValue]],
    ) -> tuple[str, str, list[LLMToolCall]]:
        text_parts: list[str] = []
        reasoning_parts: list[str] = []
        tool_calls: list[LLMToolCall] = []

        for block in blocks:
            block_type = self._read_field(block, "type", None)
            if block_type == "text":
                text_parts.append(str(self._read_field(block, "text", "")))
            elif block_type in {"thinking", "reasoning"}:
                reasoning = self._read_field(block, "thinking", None)
                if reasoning is None:
                    reasoning = self._read_field(block, "text", "")
                reasoning_parts.append(str(reasoning))
            elif block_type == "tool_use":
                name = self._read_field(block, "name", "")
                if not name:
                    continue
                tool_calls.append(
                    LLMToolCall(
                        name=str(name),
                        arguments=self._parse_arguments(self._read_field(block, "input", {})),
                        call_id=self._read_field(block, "id", None),
                        source="anthropic",
                    )
                )

        return "".join(text_parts), "".join(reasoning_parts), tool_calls
