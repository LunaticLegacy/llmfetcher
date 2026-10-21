"""Typed snapshots of the live swarm graph.

``ExecutionGraph.view_snapshot`` used to return ``dict[str, Any]``, and the
same shape was re-described as ``dict[str, object]`` in the Angelus host and
again in its HTTP projection.  These records are that shape's single
definition: the kernel produces them, and the host reads attributes instead of
indexing string keys.

They are deliberately JSON-safe and credential-free: no Agent instance,
prompt, tool handler, or endpoint appears in a node, so a snapshot can be
journaled or rendered without a redaction pass.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..llm_types import JsonObject, JsonValue


@dataclass(frozen=True)
class GraphNodeView:
    """One node as a UI draws it.

    Attributes:
        id: Agent or routing-node name.
        kind: ``agent`` or ``routing``.
        dynamic: Whether a dispatched task currently owns this node.
        parent: Reporting Agent from the latest assignment, when known.
    """

    id: str
    kind: str
    dynamic: bool
    parent: str | None

    def to_json(self) -> JsonObject:
        """Return the wire form consumed by the graph projection."""
        return {
            "id": self.id,
            "kind": self.kind,
            "dynamic": self.dynamic,
            "parent": self.parent,
        }


@dataclass(frozen=True)
class GraphEdgeView:
    """One directed dependency edge between two nodes."""

    source: str
    target: str
    kind: str

    def to_json(self) -> JsonObject:
        """Return the wire form consumed by the graph projection."""
        return {"source": self.source, "target": self.target, "kind": self.kind}


@dataclass(frozen=True)
class GraphNodeState:
    """Current execution state of one node.

    Attributes:
        state: Machine-readable lifecycle state such as ``running``.
        message: Human-readable reason shown next to the node.
        updated_at: Wall-clock time of the last state change.
        task_id: TaskBus assignment currently bound to this node, if any.
    """

    state: str
    message: str
    updated_at: float
    task_id: str | None = None

    def to_json(self) -> JsonObject:
        """Return the wire form consumed by the graph projection."""
        payload: JsonObject = {
            "state": self.state,
            "message": self.message,
            "updated_at": self.updated_at,
        }
        if self.task_id is not None:
            payload["task_id"] = self.task_id
        return payload


@dataclass(frozen=True)
class SwarmViewSnapshot:
    """Point-in-time, JSON-safe view of one live execution graph.

    Attributes:
        nodes: Every node in the graph, ordered by name.
        edges: Every dependency edge, ordered by source then target.
        max_concurrency_agents: Scheduler limit in force for this run.
        assignments: Task identifier to assigned Agent name.
        task_states: Task identifier to lifecycle state.
        node_states: Agent name to its current execution state.
    """

    nodes: tuple[GraphNodeView, ...]
    edges: tuple[GraphEdgeView, ...]
    max_concurrency_agents: int
    assignments: dict[str, str]
    task_states: dict[str, str]
    node_states: dict[str, GraphNodeState]

    def to_json(self) -> JsonObject:
        """Return the JSON-safe mapping accepted by the host projection."""
        assignments: dict[str, JsonValue] = dict(self.assignments)
        task_states: dict[str, JsonValue] = dict(self.task_states)
        node_states: dict[str, JsonValue] = {
            name: record.to_json() for name, record in self.node_states.items()
        }
        return {
            "nodes": [node.to_json() for node in self.nodes],
            "edges": [edge.to_json() for edge in self.edges],
            "max_concurrency_agents": self.max_concurrency_agents,
            "assignments": assignments,
            "task_states": task_states,
            "node_states": node_states,
        }


@dataclass(frozen=True)
class GraphSpecNode:
    """One node of a durable graph snapshot.

    Attributes:
        name: Agent or routing-node name.
        kind: ``agent`` or ``routing``.
        spec: Agent specification produced by the caller's serializer, or
            ``None`` for a routing node. Its contents belong to the serializer,
            so the graph stores it as an opaque JSON object rather than
            re-deriving a schema it cannot validate.
    """

    name: str
    kind: str
    spec: JsonObject | None = None

    def to_json(self) -> JsonObject:
        """Return the persisted node object."""
        payload: JsonObject = {"name": self.name, "kind": self.kind}
        if self.spec is not None:
            payload["spec"] = self.spec
        return payload


@dataclass(frozen=True)
class GraphSpecEdge:
    """One persisted dependency edge."""

    source: str
    target: str

    def to_json(self) -> JsonObject:
        """Return the persisted edge object."""
        return {"source": self.source, "target": self.target}


@dataclass(frozen=True)
class GraphCallbackIds:
    """Stable identifiers for custom mapper and router callbacks."""

    mappers: dict[str, str]
    routers: dict[str, str]

    def to_json(self) -> JsonObject:
        """Return the persisted callback identifier object."""
        mappers: dict[str, JsonValue] = dict(self.mappers)
        routers: dict[str, JsonValue] = dict(self.routers)
        return {"mappers": mappers, "routers": routers}


@dataclass(frozen=True)
class GraphDeclarativeCallbacks:
    """Declarative mapper modes and router target sets."""

    mappers: dict[str, str]
    routers: dict[str, tuple[str, ...]]

    def to_json(self) -> JsonObject:
        """Return the persisted declarative callback object."""
        mappers: dict[str, JsonValue] = dict(self.mappers)
        routers: dict[str, JsonValue] = {
            name: list(targets) for name, targets in self.routers.items()
        }
        return {"mappers": mappers, "routers": routers}


@dataclass(frozen=True)
class ExecutionGraphSnapshot:
    """The complete durable representation of a quiescent execution graph.

    :meth:`ExecutionGraph.to_snapshot` produces this record and
    :meth:`ExecutionGraph.load` consumes the same field set through
    :meth:`from_json`, so a field the writer emits is a field the reader
    restores.
    """

    version: int
    max_concurrency_agents: int
    nodes: tuple[GraphSpecNode, ...]
    edges: tuple[GraphSpecEdge, ...]
    callbacks: GraphCallbackIds
    declarative_callbacks: GraphDeclarativeCallbacks
    router_scopes: dict[str, tuple[str, ...]]
    task_bus: JsonObject
    task_by_agent: dict[str, str]
    task_by_id: dict[str, str]

    def to_json(self) -> JsonObject:
        """Return the persisted graph document."""
        task_by_agent: dict[str, JsonValue] = dict(self.task_by_agent)
        task_by_id: dict[str, JsonValue] = dict(self.task_by_id)
        return {
            "version": self.version,
            "max_concurrency_agents": self.max_concurrency_agents,
            "nodes": [node.to_json() for node in self.nodes],
            "edges": [edge.to_json() for edge in self.edges],
            "callbacks": self.callbacks.to_json(),
            "declarative_callbacks": self.declarative_callbacks.to_json(),
            "router_scopes": {
                name: list(targets) for name, targets in self.router_scopes.items()
            },
            "task_bus": self.task_bus,
            "task_by_agent": task_by_agent,
            "task_by_id": task_by_id,
        }

    @classmethod
    def from_json(cls, value: JsonValue) -> "ExecutionGraphSnapshot":
        """Decode one persisted graph document.

        Raises:
            ValueError: If a field is missing, unknown, or mistyped.
        """
        raw = _mapping(value, "graph snapshot")
        _reject_unknown(
            raw,
            {
                "version", "max_concurrency_agents", "nodes", "edges",
                "callbacks", "declarative_callbacks", "router_scopes",
                "task_bus", "task_by_agent", "task_by_id",
            },
            "graph snapshot",
        )
        nodes = _sequence(raw.get("nodes"), "graph snapshot.nodes")
        edges = _sequence(raw.get("edges"), "graph snapshot.edges")
        callbacks = _mapping(raw.get("callbacks"), "graph snapshot.callbacks")
        declarative = _mapping(
            raw.get("declarative_callbacks"),
            "graph snapshot.declarative_callbacks",
        )
        return cls(
            version=_integer(raw.get("version"), "graph snapshot.version"),
            max_concurrency_agents=_integer(
                raw.get("max_concurrency_agents"),
                "graph snapshot.max_concurrency_agents",
            ),
            nodes=tuple(_spec_node(item, index) for index, item in enumerate(nodes)),
            edges=tuple(_spec_edge(item, index) for index, item in enumerate(edges)),
            callbacks=GraphCallbackIds(
                mappers=_string_map(
                    callbacks.get("mappers"), "graph snapshot.callbacks.mappers"
                ),
                routers=_string_map(
                    callbacks.get("routers"), "graph snapshot.callbacks.routers"
                ),
            ),
            declarative_callbacks=GraphDeclarativeCallbacks(
                mappers=_string_map(
                    declarative.get("mappers"),
                    "graph snapshot.declarative_callbacks.mappers",
                ),
                routers=_string_tuple_map(
                    declarative.get("routers"),
                    "graph snapshot.declarative_callbacks.routers",
                ),
            ),
            router_scopes=_string_tuple_map(
                raw.get("router_scopes"), "graph snapshot.router_scopes"
            ),
            task_bus=_mapping(raw.get("task_bus"), "graph snapshot.task_bus"),
            task_by_agent=_string_map(
                raw.get("task_by_agent"), "graph snapshot.task_by_agent"
            ),
            task_by_id=_string_map(
                raw.get("task_by_id"), "graph snapshot.task_by_id"
            ),
        )


def _mapping(value: JsonValue, where: str) -> JsonObject:
    """Return one JSON object, rejecting any other value."""
    if not isinstance(value, dict):
        raise ValueError(f"{where} must be a JSON object")
    return value


def _sequence(value: JsonValue, where: str) -> list[JsonValue]:
    """Return one JSON array, rejecting any other value."""
    if not isinstance(value, list):
        raise ValueError(f"{where} must be a JSON array")
    return value


def _text(value: JsonValue, where: str) -> str:
    """Return one JSON string, rejecting any other value."""
    if not isinstance(value, str):
        raise ValueError(f"{where} must be a string")
    return value


def _integer(value: JsonValue, where: str) -> int:
    """Return one JSON integer, rejecting booleans and floats."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{where} must be an integer")
    return value


def _string_map(value: JsonValue, where: str) -> dict[str, str]:
    """Return a JSON object whose every value is a string."""
    raw = _mapping(value, where)
    return {key: _text(item, f"{where}.{key}") for key, item in raw.items()}


def _string_tuple_map(value: JsonValue, where: str) -> dict[str, tuple[str, ...]]:
    """Return a JSON object mapping string keys to arrays of strings."""
    raw = _mapping(value, where)
    return {
        key: tuple(
            _text(item, f"{where}.{key}[{index}]")
            for index, item in enumerate(_sequence(item_value, f"{where}.{key}"))
        )
        for key, item_value in raw.items()
    }


def _reject_unknown(
    value: JsonObject, allowed: set[str], where: str
) -> None:
    """Reject fields the writer never emits for this schema version."""
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"{where} has unknown fields: {', '.join(unknown)}")


def _spec_node(value: JsonValue, index: int) -> GraphSpecNode:
    """Decode one persisted node entry."""
    where = f"graph snapshot.nodes[{index}]"
    raw = _mapping(value, where)
    _reject_unknown(raw, {"name", "kind", "spec"}, where)
    kind = _text(raw.get("kind"), f"{where}.kind")
    if kind not in {"agent", "routing"}:
        raise ValueError(f"{where}.kind is not supported: {kind}")
    spec_value = raw.get("spec")
    spec = None if spec_value is None else _mapping(spec_value, f"{where}.spec")
    if kind == "agent" and spec is None:
        raise ValueError(f"{where}.spec is required for an agent node")
    return GraphSpecNode(
        name=_text(raw.get("name"), f"{where}.name"),
        kind=kind,
        spec=spec,
    )


def _spec_edge(value: JsonValue, index: int) -> GraphSpecEdge:
    """Decode one persisted edge entry."""
    where = f"graph snapshot.edges[{index}]"
    raw = _mapping(value, where)
    _reject_unknown(raw, {"source", "target"}, where)
    return GraphSpecEdge(
        source=_text(raw.get("source"), f"{where}.source"),
        target=_text(raw.get("target"), f"{where}.target"),
    )


__all__ = [
    "ExecutionGraphSnapshot",
    "GraphCallbackIds",
    "GraphDeclarativeCallbacks",
    "GraphEdgeView",
    "GraphNodeState",
    "GraphNodeView",
    "GraphSpecEdge",
    "GraphSpecNode",
    "SwarmViewSnapshot",
]
