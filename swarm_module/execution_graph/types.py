"""Callback and serializer contracts used by the execution graph.

These aliases live apart from :mod:`.graph` so hosts and tools can annotate
against the graph's seams without importing the scheduler implementation.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from ...agent import Agent
from ...llm_types import JsonObject

MapperFn = Callable[[Mapping[str, Any]], str]
"""Node-level mapper: receives a ``{predecessor_name: raw_output}`` mapping
and returns the input string for the agent."""

RouterFn = Callable[[str], list[str]]
"""Post-completion router: receives the agent's output text and returns the
list of successor names that should be activated.  Successors not in the
returned list are skipped for this run."""

AgentSerializer = Callable[[str, Agent], JsonObject]
AgentResolver = Callable[[str, JsonObject], Agent]
CallbackSerializer = Callable[[str, str, Callable[..., Any]], str]
CallbackResolver = Callable[[str, str, str], Callable[..., Any]]

__all__ = [
    "AgentResolver",
    "AgentSerializer",
    "CallbackResolver",
    "CallbackSerializer",
    "MapperFn",
    "RouterFn",
]
