"""Fail-closed Agent checkpoint loading and saving tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import pytest

from llmfetcher.agent import Agent, ContextLoadError, ContextSaveError
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.llm_types import LLMOutput


class _Fetcher:
    """Return one final answer while recording remote invocations."""

    default_backend_config = SimpleNamespace(
        name="test", provider="test", model="test-model",
    )

    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, **kwargs) -> LLMOutput:
        self.calls += 1
        return LLMOutput(
            content="done", provider="test", backend_name="test", model="test",
        )


class _FailingSaveHandler(ContextHandlerLinear):
    """Context handler whose durable commit always fails."""

    def save(self, path, **kwargs) -> bool:
        return False


def test_existing_corrupt_checkpoint_fails_before_remote_request() -> None:
    """A corrupt file is not treated as an absent, empty checkpoint."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "context.json"
        path.write_text("not-json", encoding="utf-8")
        fetcher = _Fetcher()
        agent = Agent(fetcher, system_prompt="test", context_path=path)

        with pytest.raises(ContextLoadError):
            agent.run("continue")

        assert fetcher.calls == 0


def test_checkpoint_save_failure_is_propagated() -> None:
    """A completed model boundary cannot report success without persistence."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "context.json"
        fetcher = _Fetcher()
        handler = _FailingSaveHandler(fetcher)
        agent = Agent(
            fetcher, system_prompt="test", context_path=path,
            context_handler=handler,
        )

        with pytest.raises(ContextSaveError):
            agent.run("continue")

        assert fetcher.calls == 1
