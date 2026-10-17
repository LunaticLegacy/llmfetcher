"""Selectable context handlers for hosts that let a user choose one.

Every registered implementation accepts the shared configuration below.
``retrieved`` and
``tlb`` are deliberately not registered: their constructors require
host-specific extras (a TLB fetcher, knowledge roots, a save path) and neither
is wired into a host yet.

Titles and descriptions are intentionally library-neutral English: this package
must not hard-code one host's UI language. A host maps :attr:`ContextHandlerSpec.id`
to its own localized label.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .base import ContextHandler
from .linear import CompactionFetcher, ContextHandlerLinear
from .sage import SageContext
from .storage import ContextStorage


def _create_linear(
    *,
    fetcher: CompactionFetcher,
    max_context_threshold: int,
    compaction_output_max_tokens: int,
    storage: ContextStorage | None = None,
    keep_recent: int = 0,
    settings: Mapping[str, Any] | None = None,
) -> ContextHandler:
    """Build the flat durable transcript handler."""
    return ContextHandlerLinear(
        fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
        keep_recent=keep_recent,
    )


def _create_sage(
    *,
    fetcher: CompactionFetcher,
    max_context_threshold: int,
    compaction_output_max_tokens: int,
    storage: ContextStorage | None = None,
    keep_recent: int = 0,
    settings: Mapping[str, Any] | None = None,
) -> ContextHandler:
    """Build the branch-aware Sage handler."""
    handler = SageContext(
        fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
        keep_recent=keep_recent,
    )
    return handler


def _create_graph(
    *,
    fetcher: CompactionFetcher,
    max_context_threshold: int,
    compaction_output_max_tokens: int,
    storage: ContextStorage | None = None,
    keep_recent: int = 0,
    settings: Mapping[str, Any] | None = None,
) -> ContextHandler:
    """Build the transcript plus entity-relation graph handler."""
    # Imported lazily: graph_memory imports this package's linear handler.
    from ..graph_memory import GraphContextHandler

    values = dict(settings or {})
    return GraphContextHandler(
        compacting_fetcher=fetcher,
        extraction_fetcher=fetcher if values.get("auto_extract", True) else None,
        query_fetcher=fetcher,
        graph_update_every=int(values.get("graph_update_every", 2)),
        retrieval_trigger=str(values.get("retrieval_trigger", "every_message")),
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
        keep_recent=keep_recent,
    )


@dataclass(frozen=True)
class ContextSettingSpec:
    """One UI and validation descriptor for a handler-specific setting."""

    key: str
    title: str
    description: str
    type: str
    default: Any
    enum: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None


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
    exposed_tools: tuple[str, ...] = ()
    settings: tuple[ContextSettingSpec, ...] = ()


# Registry of selectable handlers. Adding one here is all a host needs to offer
# it, provided its constructor accepts the shared configuration.
CONTEXT_HANDLERS: dict[str, ContextHandlerSpec] = {
    "graph": ContextHandlerSpec(
        id="graph",
        title="Graph memory",
        description="Linear transcript plus an entity-relation long-term graph.",
        factory=_create_graph,
        exposed_tools=(
            "graph_search", "graph_get_neighbors", "graph_upsert_entity",
            "graph_upsert_relation", "graph_invalidate_relation",
            "graph_delete_relation", "graph_delete_entity",
        ),
        settings=(
            ContextSettingSpec(
                key="graph_update_every", title="Graph update frequency",
                description="Flush pending conversation messages into the graph after this many messages.",
                type="integer", default=2, minimum=1, maximum=20,
            ),
            ContextSettingSpec(
                key="retrieval_trigger", title="Graph retrieval trigger",
                description="Choose when graph memory is refreshed for a new request.",
                type="enum", default="every_message",
                enum=("every_message", "first_message", "auto", "manual"),
            ),
            ContextSettingSpec(
                key="auto_extract", title="Automatic graph extraction",
                description="Use an internal LLM call to extract entities and relations.",
                type="boolean", default=True,
            ),
        ),
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
        description="Branch-aware worktree context with Sage-specific compaction.",
        factory=_create_sage,
        exposed_tools=(
            "sage_get_worktree", "sage_fork_branch", "sage_checkout_branch",
            "sage_pause_branch", "sage_resume_branch", "sage_finish_branch",
        ),
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


def context_handler_revision() -> str:
    """Return a stable revision for host Agent cache fingerprints."""
    return "|".join(f"{name}:{CONTEXT_HANDLERS[name].title}" for name in available_context_handlers())


def context_handler_specs() -> tuple[ContextHandlerSpec, ...]:
    """Return the catalog in the order a host should present it.

    Returns:
        Every spec, ordered by ``id``.
    """
    return tuple(CONTEXT_HANDLERS[name] for name in available_context_handlers())


def create_context_handler(
    name: str,
    *,
    fetcher: CompactionFetcher,
    max_context_threshold: int = 262144,
    compaction_output_max_tokens: int = 8192,
    storage: ContextStorage | None = None,
    keep_recent: int = 0,
    settings: Mapping[str, Any] | None = None,
) -> ContextHandler:
    """Build one registered context handler.

    Args:
        name: Handler id from :func:`available_context_handlers`.
        fetcher: Compaction fetcher shared by every implementation.
        max_context_threshold: Character threshold that triggers compaction.
        compaction_output_max_tokens: Compactor completion-token budget.
        storage: Optional durable row store.
        keep_recent: Number of newest active entries compaction keeps verbatim
            instead of summarising (``0`` summarises the whole transcript).

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
    values = normalize_context_settings(spec, settings)
    return spec.factory(
        fetcher=fetcher,
        max_context_threshold=max_context_threshold,
        compaction_output_max_tokens=compaction_output_max_tokens,
        storage=storage,
        keep_recent=keep_recent,
        settings=values,
    )


def normalize_context_settings(
    spec: ContextHandlerSpec,
    values: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Apply defaults and validate handler-specific settings."""
    submitted = dict(values or {})
    allowed = {item.key: item for item in spec.settings}
    unknown = set(submitted) - set(allowed)
    if unknown:
        raise ValueError(f"unknown {spec.id} context settings: {', '.join(sorted(unknown))}")
    result = {item.key: item.default for item in spec.settings}
    for key, value in submitted.items():
        descriptor = allowed[key]
        if descriptor.type == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"{spec.id}.{key} must be a boolean")
        elif descriptor.type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"{spec.id}.{key} must be an integer")
        elif descriptor.type == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"{spec.id}.{key} must be a number")
        elif descriptor.type in {"enum", "string"}:
            if not isinstance(value, str):
                raise ValueError(f"{spec.id}.{key} must be a string")
        if descriptor.enum and value not in descriptor.enum:
            raise ValueError(f"{spec.id}.{key} must be one of: {', '.join(descriptor.enum)}")
        if descriptor.minimum is not None and value < descriptor.minimum:
            raise ValueError(f"{spec.id}.{key} is below the minimum")
        if descriptor.maximum is not None and value > descriptor.maximum:
            raise ValueError(f"{spec.id}.{key} is above the maximum")
        result[key] = value
    return result


__all__ = [
    "CONTEXT_HANDLERS",
    "ContextSettingSpec",
    "ContextHandlerSpec",
    "DEFAULT_CONTEXT_HANDLER",
    "available_context_handlers",
    "context_handler_specs",
    "context_handler_revision",
    "create_context_handler",
    "normalize_context_settings",
]
