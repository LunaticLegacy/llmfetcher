"""Regression coverage for retry counts and backoff in ``LLMFetcher``."""

from __future__ import annotations

import threading
import unittest

from llmfetcher.llm_fetcher import LLMFetcher
from llmfetcher.llm_types import LLMBackendConfig, LLMOutput


class _TimeoutThenSuccessHandler:
    """Fail a configured number of calls before returning a model output."""

    def __init__(self, timeouts: int) -> None:
        self.timeouts = timeouts
        self.calls = 0

    def prepare_tools(self, _tools: object) -> None:
        """Return no provider tool schema for this retry-policy test."""
        return None

    def create_completion(self, **_: object) -> object:
        """Raise timeout errors until the configured successful attempt."""
        self.calls += 1
        if self.calls <= self.timeouts:
            raise TimeoutError("simulated timeout")
        return object()

    def normalize_completion_response(self, _raw: object) -> LLMOutput:
        """Return the stable success value after the final retry."""
        return LLMOutput(
            content="recovered",
            provider="test",
            backend_name="primary",
            model="test-model",
        )


def _fetcher_for(handler: _TimeoutThenSuccessHandler, retries: int) -> LLMFetcher:
    """Build a no-SDK fetcher with one controllable retrying backend."""
    backend = LLMBackendConfig(
        name="primary", provider="test", model="test-model", max_retries=retries,
    )
    fetcher = object.__new__(LLMFetcher)
    fetcher.backends = {backend.name: backend}
    fetcher.backend_order = [backend.name]
    fetcher.default_backend = backend.name
    fetcher.handlers = {backend.name: handler}
    fetcher._force_stopped = threading.Event()
    return fetcher


class RetryPolicyTests(unittest.TestCase):
    """Verify retry count means additional timeout attempts, not total calls."""

    def test_retry_count_adds_attempts_and_uses_exponential_backoff(self) -> None:
        """Three configured retries permit a fourth successful model call."""
        handler = _TimeoutThenSuccessHandler(timeouts=3)
        fetcher = _fetcher_for(handler, retries=3)
        delays: list[int] = []
        fetcher._sleep_before_retry = delays.append  # type: ignore[method-assign]

        result = fetcher.fetch("retry me")

        self.assertEqual(result.content, "recovered")
        self.assertEqual(handler.calls, 4)
        self.assertEqual(delays, [0, 1, 2])

    def test_no_delay_is_scheduled_after_the_last_timeout(self) -> None:
        """Exhaustion reports the last error without sleeping pointlessly."""
        handler = _TimeoutThenSuccessHandler(timeouts=2)
        fetcher = _fetcher_for(handler, retries=1)
        delays: list[int] = []
        fetcher._sleep_before_retry = delays.append  # type: ignore[method-assign]

        with self.assertRaisesRegex(Exception, "simulated timeout"):
            fetcher.fetch("exhaust me")

        self.assertEqual(handler.calls, 2)
        self.assertEqual(delays, [0])

    def test_default_backend_is_not_retried_again_as_its_own_fallback(self) -> None:
        """One backend receives exactly its configured initial-plus-retry budget."""
        handler = _TimeoutThenSuccessHandler(timeouts=2)
        fetcher = _fetcher_for(handler, retries=0)
        fetcher._sleep_before_retry = lambda _index: None  # type: ignore[method-assign]

        with self.assertRaisesRegex(Exception, "simulated timeout"):
            fetcher.fetch("do not duplicate primary")

        self.assertEqual(handler.calls, 1)


if __name__ == "__main__":
    unittest.main()
