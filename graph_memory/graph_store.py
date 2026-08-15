"""GraphStore: entity-relation memory graph with temporal attributes.

Pure-python adjacency for PPR (no numpy required) + NetworkX for community
detection (Louvain). Nodes are entities; edges are relations with
first/last_seen, weight, validity and evidence (source timelines).

Design notes (see docs/graph_context_design.md):
- P1: entity-relation graph is the *index*; raw conversation is the content.
- P3: temporal awareness (first/last_seen) powers recency weighting.
- P4: Personalized PageRank implements graph-diffusion retrieval.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Optional

from .models import CommunitySummary, EntityNode, GraphMemoryState, RelationEdge

# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


def normalize_entity_id(name: str, entity_type: str = "concept") -> str:
    """Produce a deterministic stable id for an entity name.

    Applies NFKC normalization, collapses whitespace and case-folds, then
    prefixes with a type slug so ``file:x.py`` never collides with
    ``concept:x.py``.
    """
    key = re.sub(
        r"\s+", " ",
        unicodedata.normalize("NFKC", str(name).strip()),
    ).casefold()
    prefix = re.sub(r"[^a-z0-9]", "_", str(entity_type).casefold()) or "concept"
    return f"{prefix}:{key}"


# ---------------------------------------------------------------------------
# PPR (power iteration, no numpy dependency)
# ---------------------------------------------------------------------------


def personalized_pagerank(
    adjacency: dict[str, list[str]],
    seed_ids: Iterable[str],
    alpha: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> dict[str, float]:
    """Personalized PageRank over an undirected adjacency map.

    r = (1 - alpha) * p + alpha * M^T r, where p is the personalization
    (teleport) distribution concentrated on ``seed_ids``.

    Returns a dict of node -> score. Nodes not reachable from seeds may
    receive zero mass; a small teleport baseline is added for numeric
    stability (smoothing over the personalization only, per standard PPR).
    """
    if not adjacency or not seed_ids:
        return {}
    nodes = list(adjacency.keys())
    seed = {s: 1.0 for s in seed_ids if s in adjacency}
    if not seed:
        return {}
    total = sum(seed.values())
    pers = {s: v / total for s, v in seed.items()}

    rank: dict[str, float] = {n: 0.0 for n in nodes}
    for n, v in pers.items():
        rank[n] = v

    for _ in range(max_iter):
        new_rank = {n: (1.0 - alpha) * pers.get(n, 0.0) for n in nodes}
        for u in nodes:
            ru = rank.get(u, 0.0)
            if ru == 0.0:
                continue
            nbrs = adjacency[u]
            if not nbrs:
                continue
            share = alpha * ru / len(nbrs)
            for v in nbrs:
                new_rank[v] = new_rank.get(v, 0.0) + share
        diff = sum(abs(new_rank[n] - rank.get(n, 0.0)) for n in nodes)
        rank = new_rank
        if diff < tol:
            break
    return rank


# ---------------------------------------------------------------------------
# GraphStore
# ---------------------------------------------------------------------------


class GraphStore:
    """In-memory entity-relation graph with temporal + provenance metadata."""

    def __init__(self) -> None:
        self.nodes: dict[str, EntityNode] = {}
        # Undirected edge map: key = (RelationEdge.key, relation) so the
        # same entity pair may carry multiple distinct relation labels.
        self._edges: dict[tuple[tuple[str, str], str], RelationEdge] = {}
        self.communities: dict[int, list[CommunitySummary]] = {}
        self.next_id: int = 0
        self._lock = threading.RLock()

    # -- entities ----------------------------------------------------------

    def upsert_entity(
        self,
        name: str,
        entity_type: str = "concept",
        aliases: Optional[list[str]] = None,
        timeline: Optional[int] = None,
        summary: Optional[str] = None,
        embedding: Optional[list[float]] = None,
    ) -> EntityNode:
        """Insert or merge an entity.

        Same-as merging: an existing node whose name or alias normalizes to
        the same id is merged (freq++, first/last_seen updated, aliases and
        summary enriched).

        Returns the canonical EntityNode.
        """
        aliases = [a for a in (aliases or []) if a and a.strip()]
        entity_id = normalize_entity_id(name, entity_type)
        timeline = timeline if timeline is not None else self.next_id

        with self._lock:
            existing = self.nodes.get(entity_id)
            if existing is None:
                existing = self._find_same_as(entity_id, name, aliases)

            if existing is None:
                node = EntityNode(
                    id=entity_id,
                    name=name.strip(),
                    entity_type=entity_type,
                    aliases=aliases,
                    summary=summary or "",
                    first_seen=timeline,
                    last_seen=timeline,
                    freq=1,
                    embedding=embedding,
                )
                self.nodes[node.id] = node
                self.next_id += 1
                return node

            # merge into existing
            existing.freq += 1
            existing.first_seen = min(existing.first_seen, timeline)
            existing.last_seen = max(existing.last_seen, timeline)
            for a in aliases:
                if a not in existing.aliases:
                    existing.aliases.append(a)
            if summary and not existing.summary:
                existing.summary = summary
            if embedding is not None and existing.embedding is None:
                existing.embedding = embedding
            return existing

    def _find_same_as(
        self,
        entity_id: str,
        name: str,
        aliases: list[str],
    ) -> Optional[EntityNode]:
        """Find an existing node that should be merged with the new entity."""
        names = [name] + aliases
        norm_names = {normalize_entity_id(n) for n in names if n}
        for node in self.nodes.values():
            node_names = {normalize_entity_id(node.name)} | {
                normalize_entity_id(a) for a in node.aliases
            }
            if norm_names & node_names:
                return node
        return None

    def get_entity(self, entity_id: str) -> Optional[EntityNode]:
        return self.nodes.get(entity_id)

    def find_entity_by_name(
        self, name: str, entity_type: str = "concept"
    ) -> Optional[EntityNode]:
        """Find an entity by (possibly partial) name or alias match."""
        target = normalize_entity_id(name, entity_type)
        for node in self.nodes.values():
            if node.id == target:
                return node
        t_norm = normalize_entity_id(name)
        for node in self.nodes.values():
            if normalize_entity_id(node.name) == t_norm:
                return node
            for a in node.aliases:
                if normalize_entity_id(a) == t_norm:
                    return node
        # substring match on names (cheap fallback)
        low = name.casefold().strip()
        for node in self.nodes.values():
            if low in node.name.casefold() or any(
                low in a.casefold() for a in node.aliases
            ):
                return node
        return None

    # -- relations ---------------------------------------------------------

    def upsert_relation(
        self,
        source_id: str,
        target_id: str,
        relation: str = "related_to",
        timeline: Optional[int] = None,
        weight: float = 1.0,
        valid: bool = True,
        evidence: Optional[list[int]] = None,
    ) -> Optional[RelationEdge]:
        """Insert or merge an undirected relation edge.

        Same pair with the same relation label aggregates weight and
        updates temporal attributes. Different relation labels between the
        same pair are kept as separate edges (multigraph semantics on the
        relation dimension).

        Returns None when either endpoint does not exist.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        timeline = timeline if timeline is not None else self.next_id
        evidence = [int(t) for t in (evidence or [])]

        with self._lock:
            # exact pair + relation match
            for e in self._iter_edges_between(source_id, target_id):
                if e.relation == relation:
                    e.weight += weight
                    e.first_seen = min(e.first_seen, timeline)
                    e.last_seen = max(e.last_seen, timeline)
                    e.valid = e.valid and valid
                    for t in evidence:
                        if t not in e.evidence:
                            e.evidence.append(t)
                    return e

            edge = RelationEdge(
                source_id=source_id,
                target_id=target_id,
                relation=relation,
                weight=weight,
                first_seen=timeline,
                last_seen=timeline,
                valid=valid,
                evidence=evidence,
            )
            self._edges[(edge.key, relation)] = edge
            return edge

    def _iter_edges_between(self, a: str, b: str) -> Iterable[RelationEdge]:
        for e in self._edges.values():
            if e.source_id in (a, b) and e.target_id in (a, b):
                yield e

    def edges(self) -> list[RelationEdge]:
        return list(self._edges.values())

    def edges_for(self, entity_id: str) -> list[RelationEdge]:
        return [
            e
            for e in self._edges.values()
            if e.source_id == entity_id or e.target_id == entity_id
        ]

    def neighbors(self, entity_id: str, max_hop: int = 1) -> dict[str, int]:
        """Return neighbor entity ids at exact hop distance <= max_hop."""
        result: dict[str, int] = {}
        frontier = {entity_id}
        for hop in range(1, max_hop + 1):
            nxt: set[str] = set()
            for node in frontier:
                for e in self._edges.values():
                    other = None
                    if e.source_id == node:
                        other = e.target_id
                    elif e.target_id == node:
                        other = e.source_id
                    if other is not None and other not in result and other != entity_id:
                        result[other] = hop
                        nxt.add(other)
            frontier = nxt
            if not frontier:
                break
        return result

    def invalidate_relation(self, source_id: str, target_id: str) -> int:
        """Mark all relations between two entities invalid (fact superseded)."""
        count = 0
        with self._lock:
            for e in self._iter_edges_between(source_id, target_id):
                e.valid = False
                count += 1
        return count

    # -- graph algorithms --------------------------------------------------

    def _adjacency(self, valid_only: bool = True) -> dict[str, list[str]]:
        adj: dict[str, list[str]] = {nid: [] for nid in self.nodes}
        for e in self._edges.values():
            if valid_only and not e.valid:
                continue
            adj.setdefault(e.source_id, []).append(e.target_id)
            adj.setdefault(e.target_id, []).append(e.source_id)
        return adj

    def pagerank(
        self,
        seed_ids: Iterable[str],
        alpha: float = 0.85,
        max_iter: int = 100,
        tol: float = 1e-6,
    ) -> dict[str, float]:
        """Personalized PageRank from seed entities (graph diffusion)."""
        return personalized_pagerank(
            self._adjacency(), list(seed_ids), alpha, max_iter, tol
        )

    def detect_communities(self, seed: int = 42) -> list[list[str]]:
        """Community detection via NetworkX Louvain.

        Returns a list of communities, each a list of entity ids.
        Empty when the graph has no edges.
        """
        if not self._edges:
            return []
        try:
            import networkx as nx
        except ImportError:  # pragma: no cover - graceful fallback
            return self._communities_connected_components()

        G = nx.Graph()
        for nid in self.nodes:
            G.add_node(nid)
        for e in self._edges.values():
            if e.valid:
                G.add_edge(e.source_id, e.target_id, weight=e.weight)
        try:
            comms = nx.community.louvain_communities(
                G, weight="weight", seed=seed
            )
            return [sorted(c) for c in comms]
        except Exception:  # pragma: no cover - defensive fallback
            return self._communities_connected_components()

    def _communities_connected_components(self) -> list[list[str]]:
        seen: set[str] = set()
        result: list[list[str]] = []
        for node in self.nodes:
            if node in seen:
                continue
            component = {node}
            frontier = {node}
            seen.add(node)
            while frontier:
                nxt: set[str] = set()
                for u in frontier:
                    for e in self._edges.values():
                        other = None
                        if e.source_id == u:
                            other = e.target_id
                        elif e.target_id == u:
                            other = e.source_id
                        if other is not None and other not in component:
                            component.add(other)
                            nxt.add(other)
                seen |= component
                frontier = nxt
            result.append(sorted(component))
        return result

    # -- temporal helpers --------------------------------------------------

    @staticmethod
    def time_decay(age: int, lam: float = 0.02) -> float:
        """Recency weight for an entity/relation of given timeline age.

        ``age`` = current_timeline - last_seen. Larger lambda = stronger
        decay. Age 0 -> 1.0.
        """
        age = max(0, age)
        return float(__import__("math").exp(-lam * age))

    # -- subgraph export ---------------------------------------------------

    def subgraph(
        self, entity_ids: Iterable[str], hop: int = 1
    ) -> tuple[dict[str, EntityNode], list[RelationEdge]]:
        """Export nodes + edges within ``hop`` hops of the given seeds."""
        ids = set(entity_ids)
        result_nodes: dict[str, EntityNode] = {
            i: self.nodes[i] for i in ids if i in self.nodes
        }
        result_edges: list[RelationEdge] = []
        frontier = set(ids)
        for _ in range(hop):
            nxt: set[str] = set()
            for e in self._edges.values():
                if not e.valid:
                    continue
                if e.source_id in frontier or e.target_id in frontier:
                    if e.source_id in result_nodes and e.target_id in result_nodes:
                        result_edges.append(e)
                    for nid in (e.source_id, e.target_id):
                        if nid in self.nodes and nid not in result_nodes:
                            result_nodes[nid] = self.nodes[nid]
                            nxt.add(nid)
            frontier = nxt
        # dedupe edges
        seen: set[tuple[str, str]] = set()
        unique_edges: list[RelationEdge] = []
        for e in result_edges:
            if e.key not in seen:
                seen.add(e.key)
                unique_edges.append(e)
        return result_nodes, unique_edges

    # -- serialization -----------------------------------------------------

    def to_state(self) -> GraphMemoryState:
        return GraphMemoryState(
            nodes=dict(self.nodes),
            edges=self.edges(),
            communities={
                level: list(summaries)
                for level, summaries in self.communities.items()
            },
            next_id=self.next_id,
        )

    def clear(self) -> None:
        """Reset the graph to an empty state (keeps the lock alive).

        Used when a context is loaded without its companion graph file, so
        stale long-term data never leaks into a fresh session.
        """
        with self._lock:
            self.nodes.clear()
            self._edges.clear()
            self.communities.clear()
            self.next_id = 0

    def from_state(self, state: GraphMemoryState) -> None:
        self.nodes = dict(state.nodes)
        self._edges = {}
        for e in state.edges:
            self._edges[(e.key, e.relation)] = e
        self.communities = {
            level: list(summaries)
            for level, summaries in state.communities.items()
        }
        self.next_id = state.next_id

    def to_dict(self) -> dict[str, Any]:
        return self.to_state().to_dict()

    def from_dict(self, data: dict[str, Any]) -> None:
        self.from_state(GraphMemoryState.from_dict(data))

    def save(self, path: str | Path) -> bool:
        """Serialize the graph to JSON. Returns True on success."""
        if not path:
            return False
        try:
            target = Path(path)
            serialized = json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
            temp_path: Optional[Path] = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=target.parent,
                    prefix=f".{target.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                    temp_file.write(serialized)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                os.replace(temp_path, target)
            except OSError:
                if temp_path is not None:
                    try:
                        temp_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                raise
            return True
        except (OSError, TypeError, ValueError):
            return False

    def load(self, path: str | Path) -> bool:
        """Deserialize the graph from JSON. Returns True on success."""
        if not path:
            return False
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        try:
            self.from_dict(raw)
            return True
        except (TypeError, KeyError, ValueError):
            return False

    def __len__(self) -> int:
        return len(self.nodes)
