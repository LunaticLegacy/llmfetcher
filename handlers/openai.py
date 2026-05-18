from __future__ import annotations

from .base import LLMBackendConfig
from .openai_compat import OpenAICompatibleHandler


class OpenAIHandler(OpenAICompatibleHandler):
    provider_names = frozenset({"openai"})

    def __init__(self, fetcher, backend: LLMBackendConfig) -> None:
        super().__init__(fetcher, backend)
        from openai import OpenAI

        self.client = OpenAI(
            api_key=backend.api_key,
            base_url=backend.api_url,
            max_retries=backend.max_retries,
        )

    def create_completion(
        self,
        *,
        messages,
        temperature: float,
        max_tokens: int,
        stream: bool,
        tools=None,
    ):
        kwargs = {
            "model": self.backend.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
            "timeout": self.backend.timeout,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        kwargs.update(self.backend.extra)
        return self.client.chat.completions.create(**kwargs)

