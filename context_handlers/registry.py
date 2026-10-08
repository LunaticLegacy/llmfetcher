"""Selectable context handlers for hosts that let a user choose one.

Every registered implementation composes the same durable linear store, so the
shared configuration below is exactly what they need. ``retrieved`` and
``tlb`` are deliberately not registered: their constructors require
host-specific extras (a TLB fetcher, knowledge roots, a save path) and neither
is wired into a host yet.

Titles and descriptions are intentionally library-neutral English: this package
must not hard-code one host's UI language. A host maps :attr:`ContextHandlerSpec.id`
to its own localized label.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .base import ContextHandler
from .linear import ContextHandlerLinear
from .sage import SageContext
from .storage import ContextStorage


def _create_linear(
    *,
    fetcher,
    max_context_threshold: int,
    compaction_output_max_tokens: int,
    storage: ContextStorage | None = None,
) -> ContextHandler:
    """Build the flat durable transcript handler."""
    return ContextHandlerLinear(
        fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
    )


def _create_sage(
    *,
    fetcher,
    max_context_threshold: int,
    compaction_output_max_tokens: int,
    storage: ContextStorage | None = None,
) -> ContextHandler:
    """Build the tree-indexed transcript handler."""
    return SageContext(
        fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
    )


def _create_graph(
    *,
    fetcher,
    max_context_threshold: int,
    compaction_output_max_tokens: int,
    storage: ContextStorage | None = None,
) -> ContextHandler:
    """Build the transcript plus entity-relation graph handler."""
    # Imported lazily: graph_memory imports this package's linear handler.
    from ..graph_memory import GraphContextHandler

    return GraphContextHandler(
        compacting_fetcher=fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
    )


@dataclass(frozen=True)
class ContextHandlerSpec:
    """One host-selectable context implementation.

    Attributes:
        id: Stable value a host stores to select this handler.
        title: Short library-neutral name for a host's picker.
        description: One line describing what the handler keeps.
        factory: Builds the handler from the shared configuration.
    """

    id: str
    title: str
    description: str
    factory: Callable[..., ContextHandler]


# Registry of selectable handlers. Adding one here is all a host needs to offer
# it, provided its constructor accepts the shared configuration.
CONTEXT_HANDLERS: dict[str, ContextHandlerSpec] = {
    "graph": ContextHandlerSpec(
        id="graph",
        title="Graph memory",
        description="Linear transcript plus an entity-relation long-term graph.",
        factory=_create_graph,
    ),
    "linear": ContextHandlerSpec(
        id="linear",
        title="Linear",
        description="Flat transcript with LLM compaction.",
        factory=_create_linear,
    ),
    "sage": ContextHandlerSpec(
        id="sage",
        title="Sage",
        description="Linear transcript indexed as context trees.",
        factory=_create_sage,
    ),
}

# The handler a host should build when a user has not chosen one.
DEFAULT_CONTEXT_HANDLER = "graph"


def available_context_handlers() -> tuple[str, ...]:
    """Return every selectable handler id, sorted.

    Returns:
        Handler ids accepted by :func:`create_context_handler`.
    """
    return tuple(sorted(CONTEXT_HANDLERS))


def context_handler_specs() -> tuple[ContextHandlerSpec, ...]:
    """Return the catalog in the order a host should present it.

    Returns:
        Every spec, ordered by ``id``.
    """
    return tuple(CONTEXT_HANDLERS[name] for name in available_context_handlers())


def create_context_handler(
    name: str,
    *,
    fetcher,
    max_context_threshold: int = 262144,
    compaction_output_max_tokens: int = 8192,
    storage: ContextStorage | None = None,
) -> ContextHandler:
    """Build one registered context handler.

    Args:
        name: Handler id from :func:`available_context_handlers`.
        fetcher: Compaction fetcher shared by every implementation.
        max_context_threshold: Character threshold that triggers compaction.
        compaction_output_max_tokens: Compactor completion-token budget.
        storage: Optional durable row store.

    Returns:
        A configured handler.

    Raises:
        ValueError: If *name* is not registered.
    """
    spec = CONTEXT_HANDLERS.get(name)
    if spec is None:
        raise ValueError(
            "unknown context handler: "
            f"{name!r} (available: {', '.join(available_context_handlers())})"
        )
    return spec.factory(
        fetcher=fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
    )


__all__ = [
    "CONTEXT_HANDLERS",
    "ContextHandlerSpec",
    "DEFAULT_CONTEXT_HANDLER",
    "available_context_handlers",
    "context_handler_specs",
    "create_context_handler",
]
