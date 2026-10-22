"""Graph memory: graph-based long-term context for angelus (GraphRAG-style)."""

from .models import (
    CommunitySummary,
    EntityNode,
    GraphHit,
    GraphMemoryState,
    RelationEdge,
)
from .graph_store import GraphStore, normalize_entity_id
from .retriever import (
    GraphRetriever,
    GraphRetrievalResult,
    RetrievalConfig,
    render_graph_memory,
)
from .handler import GraphContextHandler
from .projection import (
    ContextGraphProjection,
    ProjectedCommunity,
    ProjectedEntity,
    ProjectedRelation,
)
from .tools import GraphToolProvider, create_graph_tools
from .semantic import SemanticGraphWorker

__all__ = [
    "CommunitySummary",
    "EntityNode",
    "GraphHit",
    "GraphMemoryState",
    "RelationEdge",
    "GraphStore",
    "normalize_entity_id",
    "GraphRetriever",
    "GraphRetrievalResult",
    "RetrievalConfig",
    "render_graph_memory",
    "GraphContextHandler",
    "ContextGraphProjection",
    "ProjectedCommunity",
    "ProjectedEntity",
    "ProjectedRelation",
    "GraphToolProvider",
    "create_graph_tools",
    "SemanticGraphWorker",
]
