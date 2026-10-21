"""Default Agent serialization used by the durable execution-graph snapshot.

The graph stores a JSON object per Agent and asks the caller for an adapter
when the Agent carries tools or a custom context handler. These two functions
are the built-in adapter for the standard tool-free linear-context Agent.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

from ...agent import Agent
from ...context_handlers import ContextHandlerLinear
from ...llm_fetcher import LLMFetcher
from ...llm_types import JsonObject, LLMBackendConfig

from .errors import GraphPersistenceError

SNAPSHOT_VERSION = 1
"""Schema version written into every durable graph snapshot."""


def default_agent_serializer(agent_name: str, agent: Agent) -> JsonObject:
    """Serialize a standard tool-free Agent into JSON-compatible config.

    Args:
        agent_name: Graph-local name used in validation errors.
        agent: Agent whose LLM, context-path, and execution settings are saved.

    Returns:
        Versioned Agent specification that :func:`default_agent_resolver` restores.

    Raises:
        GraphPersistenceError: If tools or a custom context handler need an
            application-supplied serializer.
    """
    if not isinstance(agent.context_handler, ContextHandlerLinear):
        raise GraphPersistenceError(
            f"Agent {agent_name!r} uses custom context; provide agent_serializer"
        )
    if agent.tool_handler.get_all_tools():
        raise GraphPersistenceError(
            f"Agent {agent_name!r} has tools; provide agent_serializer"
        )
    try:
        result = {
            "kind": "llmfetcher.agent.v1",
            "backends": [
                asdict(item) for item in agent.llm_fetcher.backend_configs.values()
            ],
            "default_backend": agent.llm_fetcher.default_backend,
            "system_prompt": agent.system_prompt,
            "max_concurrency": agent.max_concurrency,
            "max_context_threshold": agent.max_context_threshold,
            "context_path": str(agent.context_path) if agent.context_path else None,
            "default_max_rounds": agent.default_max_rounds,
            "default_max_tokens": agent.default_max_tokens,
        }
    except (AttributeError, TypeError, ValueError) as exc:
        raise GraphPersistenceError(
            f"Cannot serialize Agent {agent_name!r}: {exc}"
        ) from exc
    return cast("JsonObject", result)


def default_agent_resolver(agent_name: str, spec: JsonObject) -> Agent:
    """Recreate a standard tool-free Agent from a persisted specification.

    Args:
        agent_name: Graph-local name used in validation errors.
        spec: JSON-decoded standard Agent configuration.

    Returns:
        Reconstructed Agent without application tools.

    Raises:
        GraphPersistenceError: If ``spec`` is unsupported or malformed.
    """
    if spec.get("kind") != "llmfetcher.agent.v1":
        raise GraphPersistenceError(
            f"Agent {agent_name!r} requires a custom agent_resolver"
        )
    raw_backends = spec.get("backends")
    if not isinstance(raw_backends, list):
        raise GraphPersistenceError(
            f"Invalid Agent spec for {agent_name!r}: backends must be an array"
        )
    try:
        backends = [
            LLMBackendConfig(**cast("dict[str, Any]", item))
            for item in raw_backends
            if isinstance(item, dict)
        ]
        return Agent(
            llm_fetcher=LLMFetcher(
                backends,
                default_backend=cast("str | None", spec.get("default_backend")),
            ),
            system_prompt=str(spec["system_prompt"]),
            max_concurrency=int(cast("int", spec["max_concurrency"])),
            max_context_threshold=int(cast("int", spec["max_context_threshold"])),
            context_path=cast("str | None", spec.get("context_path")),
            default_max_rounds=int(cast("int", spec["default_max_rounds"])),
            default_max_tokens=int(cast("int", spec["default_max_tokens"])),
            context_providers=(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise GraphPersistenceError(
            f"Invalid Agent spec for {agent_name!r}: {exc}"
        ) from exc


__all__ = [
    "SNAPSHOT_VERSION",
    "default_agent_resolver",
    "default_agent_serializer",
]
