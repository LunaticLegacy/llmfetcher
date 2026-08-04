"""Data models for graph-based long-term memory.

The graph is entity-centric (HippoRAG style index): nodes are named
entities (people, files, concepts, tools, decisions...), edges are
relations with temporal attributes and provenance (source timelines).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class EntityNode:
    """A single entity in the memory graph.

    Attributes:
        id: Normalized stable identifier (``type:name`` after NFKC +
            casefold). Merged entities keep the id of their first seen form.
        name: Display name (canonical form).
        entity_type: One of person / file / concept / tool / framework /
            project / decision / module / other.
        aliases: Alternative names seen in conversation (same-as merging).
        summary: Optional entity-level summary (produced by compaction).
        first_seen: First timeline (round) this entity appeared.
        last_seen: Most recent timeline this entity appeared.
        freq: Number of times the entity was observed.
        embedding: Optional dense vector for semantic matching.
    """

    id: str
    name: str
    entity_type: str = "concept"
    aliases: list[str] = field(default_factory=list)
    summary: str = ""
    first_seen: int = 0
    last_seen: int = 0
    freq: int = 1
    embedding: Optional[list[float]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntityNode":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            entity_type=data.get("entity_type", "concept"),
            aliases=list(data.get("aliases", [])),
            summary=data.get("summary", ""),
            first_seen=int(data.get("first_seen", 0)),
            last_seen=int(data.get("last_seen", 0)),
            freq=int(data.get("freq", 1)),
            embedding=data.get("embedding"),
        )


@dataclass
class RelationEdge:
    """A relation between two entities with temporal attributes.

    Attributes:
        source_id / target_id: Entity ids (graph itself is undirected;
            source/target preserve the extraction order).
        relation: Relation label, e.g. ``fixes``, ``depends_on``,
            ``implements``, ``rejects``.
        weight: Aggregated observation count / confidence.
        first_seen / last_seen: Timeline of first/last observation.
        valid: False when the fact has been superseded / rejected
            (Zep-style invalidation).
        evidence: Source timeline ids that support this relation.
    """

    source_id: str
    target_id: str
    relation: str = "related_to"
    weight: float = 1.0
    first_seen: int = 0
    last_seen: int = 0
    valid: bool = True
    evidence: list[int] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, str]:
        """Undirected canonical edge key (sorted pair)."""
        a, b = self.source_id, self.target_id
        return (a, b) if a <= b else (b, a)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RelationEdge":
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation=data.get("relation", "related_to"),
            weight=float(data.get("weight", 1.0)),
            first_seen=int(data.get("first_seen", 0)),
            last_seen=int(data.get("last_seen", 0)),
            valid=bool(data.get("valid", True)),
            evidence=[int(t) for t in data.get("evidence", [])],
        )


@dataclass
class CommunitySummary:
    """Summary of one community (cluster) of the memory graph.

    Produced during graph-aware compaction (map step). ``level`` 0 is the
    finest granularity; higher levels are reductions over finer ones.
    """

    level: int
    community_id: str
    summary: str
    member_entity_ids: list[str] = field(default_factory=list)
    source_timelines: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CommunitySummary":
        return cls(
            level=int(data.get("level", 0)),
            community_id=data.get("community_id", ""),
            summary=data.get("summary", ""),
            member_entity_ids=list(data.get("member_entity_ids", [])),
            source_timelines=[int(t) for t in data.get("source_timelines", [])],
        )


@dataclass
class GraphHit:
    """One retrieval hit: an entity plus its fused score."""

    entity: EntityNode
    score: float = 0.0
    matched_relation: Optional[str] = None
    neighbor_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity": self.entity.to_dict(),
            "score": self.score,
            "matched_relation": self.matched_relation,
            "neighbor_ids": list(self.neighbor_ids),
        }


@dataclass
class GraphMemoryState:
    """Serialization container for the whole memory graph."""

    version: int = 1
    nodes: dict[str, EntityNode] = field(default_factory=dict)
    edges: list[RelationEdge] = field(default_factory=list)
    communities: dict[int, list[CommunitySummary]] = field(default_factory=dict)
    next_id: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "communities": {
                str(level): [c.to_dict() for c in summaries]
                for level, summaries in self.communities.items()
            },
            "next_id": self.next_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphMemoryState":
        nodes = {
            k: EntityNode.from_dict(v)
            for k, v in data.get("nodes", {}).items()
        }
        edges = [RelationEdge.from_dict(e) for e in data.get("edges", [])]
        communities = {
            int(level): [CommunitySummary.from_dict(c) for c in summaries]
            for level, summaries in data.get("communities", {}).items()
        }
        return cls(
            version=int(data.get("version", 1)),
            nodes=nodes,
            edges=edges,
            communities=communities,
            next_id=int(data.get("next_id", 0)),
        )
