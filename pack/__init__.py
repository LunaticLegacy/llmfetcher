"""
LLM Fetcher - Multi-Agent Orchestration Framework

A powerful Python framework for building, orchestrating, and executing 
LLM-powered multi-agent systems with structured reasoning capabilities.
"""

__version__ = "0.3.0"
__author__ = "Luna"

# Core exports
from .llm_fetcher import LLMFetcher, LLMBackendConfig
from .agent import Agent
from .tool import Tool
from .thinking_graph import ThinkingGraph

# Swarm exports
from .swarm.swarm import AgentSwarm
from .swarm.execution_graph import GraphContext

# Tools
from .tools.shell_tools import create_shell_tools

__all__ = [
    "LLMFetcher",
    "LLMBackendConfig",
    "Agent",
    "Tool",
    "ThinkingGraph",
    "AgentSwarm",
    "GraphContext",
    "create_shell_tools",
]
