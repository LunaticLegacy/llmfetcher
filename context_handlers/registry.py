"""Selectable context-handler factories.

Hosts persist a stable handler ID and construct the concrete handler at Agent
creation time.  Optional handlers are registered lazily so the base registry
does not import experimental implementations such as the in-progress Sage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .base import ContextHandler
from .linear import CompactionFetcher, ContextHandlerLinear


@dataclass(frozen=True)
class ContextHandlerSpec:
    id: str
    title: str
    description: str
    factory: Callable[..., ContextHandler]


def _create_linear(*, fetcher: CompactionFetcher, max_context_threshold: int,
                   compaction_output_max_tokens: int, storage: Any = None,
                   keep_recent: int = 0) -> ContextHandler:
    return ContextHandlerLinear(
        fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        keep_recent=keep_recent,
    )


def _create_graph(*, fetcher: CompactionFetcher, max_context_threshold: int,
                  compaction_output_max_tokens: int, storage: Any = None,
                  keep_recent: int = 0) -> ContextHandler:
    from ..graph_memory import GraphContextHandler

    return GraphContextHandler(
        compacting_fetcher=fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        keep_recent=keep_recent,
    )


CONTEXT_HANDLERS: dict[str, ContextHandlerSpec] = {
    "graph": ContextHandlerSpec("graph", "Graph memory", "Transcript plus entity-relation memory.", _create_graph),
    "linear": ContextHandlerSpec("linear", "Linear", "Transcript with LLM compaction.", _create_linear),
}
DEFAULT_CONTEXT_HANDLER = "graph"


def available_context_handlers() -> tuple[str, ...]:
    return tuple(sorted(CONTEXT_HANDLERS))


def context_handler_specs() -> tuple[ContextHandlerSpec, ...]:
    return tuple(CONTEXT_HANDLERS[name] for name in available_context_handlers())


def context_handler_revision() -> tuple[str, ...]:
    """Return a stable identity for the currently registered strategies."""
    return tuple(sorted(CONTEXT_HANDLERS))


def create_context_handler(name: str, *, fetcher: CompactionFetcher,
                           max_context_threshold: int = 262144,
                           compaction_output_max_tokens: int = 8192,
                           storage: Any = None,
                           keep_recent: int = 0) -> ContextHandler:
    spec = CONTEXT_HANDLERS.get(name)
    if spec is None:
        raise ValueError(f"unknown context handler: {name!r} (available: {', '.join(available_context_handlers())})")
    return spec.factory(
        fetcher=fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
        keep_recent=keep_recent,
    )


__all__ = [
    "CONTEXT_HANDLERS", "ContextHandlerSpec", "DEFAULT_CONTEXT_HANDLER",
    "available_context_handlers", "context_handler_revision",
    "context_handler_specs", "create_context_handler",
]
