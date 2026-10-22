"""Serializable projection of one Agent's long-term entity graph.

The graph belongs to :mod:`llmfetcher.graph_memory`; other modules only render
it.  This module is the single contract for that rendering: the live
``GraphStore`` and the committed ``graph_checkpoint`` companion file both decode
into the same frozen dataclasses, so a reader never has to know which handler
produced the graph or which JSON keys happen to be present.

``embedding`` is deliberately excluded: it is retrieval state, not display
state, and it can be large.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..llm_types import JsonArray, JsonObject
from .models import CommunitySummary, EntityNode, GraphMemoryState, RelationEdge


@dataclass(frozen=True)
class ProjectedEntity:
    """One graph node as a console renders it."""

    id: str
    name: str
    entity_type: str
    summary: str
    aliases: tuple[str, ...]
    first_seen: int
    last_seen: int
    freq: int

    @classmethod
    def from_node(cls, node: EntityNode) -> "ProjectedEntity":
        """Project one stored node, dropping its embedding vector."""
        return cls(
            id=node.id,
            name=node.name,
            entity_type=node.entity_type,
            summary=node.summary,
            aliases=tuple(node.aliases),
            first_seen=node.first_seen,
            last_seen=node.last_seen,
            freq=node.freq,
        )

    def to_json(self) -> JsonObject:
        """Return this node in the wire shape the console declares."""
        aliases: JsonArray = []
        aliases.extend(self.aliases)
        payload: JsonObject = {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "summary": self.summary,
            "aliases": aliases,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "freq": self.freq,
        }
        return payload


@dataclass(frozen=True)
class ProjectedRelation:
    """One graph edge as a console renders it."""

    source_id: str
    target_id: str
    relation: str
    weight: float
    first_seen: int
    last_seen: int
    valid: bool
    evidence: tuple[int, ...]

    @classmethod
    def from_edge(cls, edge: RelationEdge) -> "ProjectedRelation":
        """Project one stored relation."""
        return cls(
            source_id=edge.source_id,
            target_id=edge.target_id,
            relation=edge.relation,
            weight=edge.weight,
            first_seen=edge.first_seen,
            last_seen=edge.last_seen,
            valid=edge.valid,
            evidence=tuple(edge.evidence),
        )

    def to_json(self) -> JsonObject:
        """Return this edge in the wire shape the console declares."""
        evidence: JsonArray = []
        evidence.extend(self.evidence)
        payload: JsonObject = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "weight": self.weight,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "valid": self.valid,
            "evidence": evidence,
        }
        return payload


@dataclass(frozen=True)
class ProjectedCommunity:
    """One community summary as a console renders it."""

    level: int
    community_id: str
    summary: str
    member_entity_ids: tuple[str, ...]

    @classmethod
    def from_summary(cls, summary: CommunitySummary) -> "ProjectedCommunity":
        """Project one stored community summary."""
        return cls(
            level=summary.level,
            community_id=summary.community_id,
            summary=summary.summary,
            member_entity_ids=tuple(summary.member_entity_ids),
        )

    def to_json(self) -> JsonObject:
        """Return this summary in the wire shape the console declares."""
        members: JsonArray = []
        members.extend(self.member_entity_ids)
        payload: JsonObject = {
            "level": self.level,
            "community_id": self.community_id,
            "summary": self.summary,
            "member_entity_ids": members,
        }
        return payload


@dataclass(frozen=True)
class ContextGraphProjection:
    """The complete entity-graph view for one Agent context.

    Attributes:
        available: Whether any entity exists. A handler without a long-term
            graph answers ``False`` here instead of omitting the field.
        stale: Whether context editing invalidated the stored graph.
        truncated: Reserved for a bounded projection; the current projection is
            never truncated, so this is always ``False``.
        nodes: Projected entities in store order.
        edges: Projected relations in store order.
        communities: Every community summary across levels, finest first.
    """

    available: bool
    stale: bool
    truncated: bool
    nodes: tuple[ProjectedEntity, ...]
    edges: tuple[ProjectedRelation, ...]
    communities: tuple[ProjectedCommunity, ...]

    @property
    def node_count(self) -> int:
        """Return the number of projected entities."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Return the number of projected relations."""
        return len(self.edges)

    @property
    def community_count(self) -> int:
        """Return the number of projected community summaries."""
        return len(self.communities)

    @classmethod
    def empty(cls) -> "ContextGraphProjection":
        """Return the projection for a handler that has no entity graph."""
        return cls(
            available=False,
            stale=False,
            truncated=False,
            nodes=(),
            edges=(),
            communities=(),
        )

    @classmethod
    def from_state(
        cls,
        state: GraphMemoryState,
        *,
        stale: bool = False,
    ) -> "ContextGraphProjection":
        """Project one decoded graph state."""
        communities = tuple(
            ProjectedCommunity.from_summary(summary)
            for level in sorted(state.communities)
            for summary in state.communities[level]
        )
        nodes = tuple(ProjectedEntity.from_node(node) for node in state.nodes.values())
        edges = tuple(ProjectedRelation.from_edge(edge) for edge in state.edges)
        return cls(
            available=bool(nodes),
            stale=stale,
            truncated=False,
            nodes=nodes,
            edges=edges,
            communities=communities,
        )

    def to_json(self) -> JsonObject:
        """Return the projection in the console's declared wire shape."""
        nodes: JsonArray = []
        for node in self.nodes:
            nodes.append(node.to_json())
        edges: JsonArray = []
        for edge in self.edges:
            edges.append(edge.to_json())
        communities: JsonArray = []
        for community in self.communities:
            communities.append(community.to_json())
        payload: JsonObject = {
            "available": self.available,
            "stale": self.stale,
            "truncated": self.truncated,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "community_count": self.community_count,
            "nodes": nodes,
            "edges": edges,
            "communities": communities,
        }
        return payload


__all__ = [
    "ContextGraphProjection",
    "ProjectedCommunity",
    "ProjectedEntity",
    "ProjectedRelation",
]
