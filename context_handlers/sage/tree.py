"""Sage context tree: an index of previous information over a transcript.

``SageContext`` keeps a session's history as *a set of context trees* rather
than one flat list.  This module owns only the node/tree structure and its
traversal helpers; which of those nodes a request renders stays a policy
decision of the handler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Sequence

from ...llm_types import LLMContext, LLMContextCompacted

# A tree indexes live messages and compacted abstracts alike, mirroring what
# ``ContextHandler.get_prev_messages`` exposes for one request.
SageMessage = LLMContext | LLMContextCompacted


@dataclass
class ContextNode:
    """One indexed entry, linked to the entry it continues.

    Attributes:
        node_id: Identity scoped to the owning tree's current index.
        message: The durable entry this node indexes.
        parent_id: Node this one followed when it was indexed, if any.
    """

    node_id: int
    message: SageMessage
    parent_id: int | None = None


@dataclass
class ContextTree:
    """A chain-shaped index over one context transcript.

    Entries are added with :meth:`append`, which links each node to the current
    tail; :meth:`rebuild` re-indexes a whole transcript, which is what the
    handler does after a compaction collapses the active history.  The
    structure is deliberately a chain today: branching only requires passing an
    explicit ``parent_id``.

    Attributes:
        nodes: Indexed nodes keyed by ``node_id``, in insertion order.
        root_id: Oldest node in the current index, or ``None`` when empty.
        tail_id: Newest node in the current index, or ``None`` when empty.
        next_id: Next node identity to hand out within this index generation.
    """

    nodes: Dict[int, ContextNode] = field(default_factory=dict)
    root_id: int | None = None
    tail_id: int | None = None
    next_id: int = 0

    def append(
        self,
        message: SageMessage,
        *,
        parent_id: int | None = None,
    ) -> ContextNode:
        """Index one message, linked to the current tail by default.

        Args:
            message: The entry to index.
            parent_id: Explicit parent, or ``None`` to continue from the tail.

        Returns:
            The newly created node.
        """
        # The default parent is whatever is currently newest, which is what
        # makes an append-only transcript a chain.
        node = ContextNode(
            node_id=self.next_id,
            message=message,
            parent_id=self.tail_id if parent_id is None else parent_id,
        )
        self.next_id += 1
        self.nodes[node.node_id] = node
        if self.root_id is None:
            self.root_id = node.node_id
        self.tail_id = node.node_id
        return node

    def rebuild(self, messages: Sequence[SageMessage]) -> None:
        """Replace the index with one chain over *messages*, in order.

        Args:
            messages: Active entries, oldest first.
        """
        # Ids are scoped to one index generation, so a rebuild restarts them
        # and no stale reference can alias a node of the previous index.
        self.clear()
        for message in messages:
            self.append(message)

    def clear(self) -> None:
        """Drop every indexed node so the tree can be reused."""
        self.nodes.clear()
        self.root_id = None
        self.tail_id = None
        self.next_id = 0

    def path_to(self, node_id: int) -> List[ContextNode]:
        """Return the root-first chain leading to *node_id*.

        Args:
            node_id: Identity of the node to trace.

        Returns:
            Nodes from the root down to *node_id*, or an empty list when the
            identity is unknown.
        """
        chain: List[ContextNode] = []
        current = self.nodes.get(node_id)
        while current is not None:
            chain.append(current)
            current = None if current.parent_id is None else self.nodes.get(current.parent_id)
        chain.reverse()
        return chain

    def ordered(self) -> List[ContextNode]:
        """Return every indexed node in insertion order."""
        return list(self.nodes.values())

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self) -> Iterator[ContextNode]:
        return iter(self.nodes.values())


__all__ = ["ContextNode", "ContextTree", "SageMessage"]
