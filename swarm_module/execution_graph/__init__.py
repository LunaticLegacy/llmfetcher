"""Dependency-driven execution graph, split by concern.

This package replaces the former single-module ``execution_graph.py``. Every
name that module exported is re-exported here, so existing imports such as
``from llmfetcher.swarm_module.execution_graph import ExecutionGraph`` keep
working unchanged.

- :mod:`.errors` — ``GraphPersistenceError`` and the ``AgentFailure`` marker.
- :mod:`.types` — mapper/router and serializer/resolver contracts.
- :mod:`.serialization` — the durable snapshot version and the built-in
  tool-free Agent adapter.
- :mod:`.graph` — the stateful ``ExecutionGraph`` facade.
"""

from __future__ import annotations

from .errors import AgentFailure, GraphPersistenceError
from .graph import ExecutionGraph
from .serialization import (
    SNAPSHOT_VERSION,
    default_agent_resolver,
    default_agent_serializer,
)
from .types import (
    AgentResolver,
    AgentSerializer,
    CallbackResolver,
    CallbackSerializer,
    MapperFn,
    RouterFn,
)

__all__ = [
    "AgentFailure",
    "AgentResolver",
    "AgentSerializer",
    "CallbackResolver",
    "CallbackSerializer",
    "ExecutionGraph",
    "GraphPersistenceError",
    "MapperFn",
    "RouterFn",
    "SNAPSHOT_VERSION",
    "default_agent_resolver",
    "default_agent_serializer",
]
