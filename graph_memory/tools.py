"""Agent-facing tools for reading and editing one GraphContext graph."""

from __future__ import annotations

import json
from typing import Any

from ..llm_types import Tool, ToolParameter, ToolSchema


class GraphToolProvider:
    """Bind graph operations to one ``GraphContextHandler`` instance."""

    def __init__(self, context: Any) -> None:
        self.context = context

    def tools(self) -> list[Tool]:
        return [
            Tool(
                "graph_search",
                "Search the current Agent's long-term entity-relation graph.",
                ToolSchema(properties=[
                    ToolParameter("query", description="Entity names or a question to search for."),
                ]),
                self.search,
            ),
            Tool(
                "graph_get_neighbors",
                "Inspect entities connected to one graph node.",
                ToolSchema(properties=[
                    ToolParameter("entity", description="Entity ID, name, or alias."),
                    ToolParameter("hop", type="integer", description="Maximum hop distance (1-3).", required=False, default=1),
                ]),
                self.get_neighbors,
            ),
            Tool(
                "graph_upsert_entity",
                "Create or enrich one entity in the current Agent's graph.",
                ToolSchema(properties=[
                    ToolParameter("name", description="Canonical display name."),
                    ToolParameter("entity_type", description="Entity type such as file, project, class, or concept.", required=False, default="concept"),
                    ToolParameter("aliases", type="array", description="Alternative names for the same entity.", required=False, default=[]),
                    ToolParameter("summary", description="Short factual summary.", required=False, default=""),
                ]),
                self.upsert_entity,
            ),
            Tool(
                "graph_upsert_relation",
                "Create or strengthen a typed relation between two existing entities.",
                ToolSchema(properties=[
                    ToolParameter("source", description="Source entity ID, name, or alias."),
                    ToolParameter("target", description="Target entity ID, name, or alias."),
                    ToolParameter("relation", description="Short relation label such as uses, depends_on, or fixes."),
                    ToolParameter("evidence", type="array", description="Optional source timeline numbers.", required=False, default=[]),
                ]),
                self.upsert_relation,
            ),
            Tool(
                "graph_invalidate_relation",
                "Mark all relations between two entities as no longer valid.",
                ToolSchema(properties=[
                    ToolParameter("source", description="Source entity ID, name, or alias."),
                    ToolParameter("target", description="Target entity ID, name, or alias."),
                ]),
                self.invalidate_relation,
            ),
        ]

    def _timeline(self) -> int:
        return int(getattr(getattr(self.context, "linear", None), "_round", 0) or 0) + 1

    def _entity(self, value: str):
        store = self.context.store
        text = str(value).strip()
        if not text:
            raise ValueError("entity must not be empty")
        node = store.get_entity(text) or store.find_entity_by_name(text)
        if node is None:
            raise ValueError(f"unknown graph entity: {text}")
        return node

    @staticmethod
    def _dump(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    def search(self, query: str, **_: Any) -> str:
        if not str(query).strip():
            raise ValueError("query must not be empty")
        return self._dump(self.context.retrieve(str(query)).to_dict())

    def get_neighbors(self, entity: str, hop: int = 1, **_: Any) -> str:
        node = self._entity(entity)
        distance = max(1, min(int(hop), 3))
        neighbors = self.context.store.neighbors(node.id, distance)
        return self._dump({
            "entity": node.to_dict(),
            "neighbors": [
                {"distance": distance, "entity": self.context.store.get_entity(entity_id).to_dict()}
                for entity_id, distance in neighbors.items()
                if self.context.store.get_entity(entity_id) is not None
            ],
            "relations": [edge.to_dict() for edge in self.context.store.edges_for(node.id)],
        })

    def upsert_entity(
        self,
        name: str,
        entity_type: str = "concept",
        aliases: list[str] | None = None,
        summary: str = "",
        **_: Any,
    ) -> str:
        node = self.context.store.upsert_entity(
            name=str(name).strip(),
            entity_type=str(entity_type).strip() or "concept",
            aliases=[str(alias).strip() for alias in (aliases or []) if str(alias).strip()],
            summary=str(summary).strip(),
            timeline=self._timeline(),
        )
        return self._dump({"entity": node.to_dict(), "created_or_updated": True})

    def upsert_relation(
        self,
        source: str,
        target: str,
        relation: str,
        evidence: list[int] | None = None,
        **_: Any,
    ) -> str:
        source_node = self._entity(source)
        target_node = self._entity(target)
        edge = self.context.store.upsert_relation(
            source_id=source_node.id,
            target_id=target_node.id,
            relation=str(relation).strip() or "related_to",
            timeline=self._timeline(),
            evidence=[int(item) for item in (evidence or [])],
        )
        if edge is None:
            raise ValueError("relation endpoints must exist in the graph")
        return self._dump({"relation": edge.to_dict(), "created_or_updated": True})

    def invalidate_relation(self, source: str, target: str, **_: Any) -> str:
        source_node = self._entity(source)
        target_node = self._entity(target)
        return self._dump({
            "source": source_node.id,
            "target": target_node.id,
            "invalidated": self.context.store.invalidate_relation(source_node.id, target_node.id),
        })


def create_graph_tools(context: Any) -> list[Tool]:
    """Return graph tools bound to one ``GraphContextHandler``."""
    return GraphToolProvider(context).tools()


__all__ = ["GraphToolProvider", "create_graph_tools"]
