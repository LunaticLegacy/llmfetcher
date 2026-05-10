"""
LLM Fetcher - Multi-Agent Orchestration Framework

A powerful Python framework for building, orchestrating, and executing 
LLM-powered multi-agent systems with structured reasoning capabilities.

Example usage:
    from pack import Agent, LLMFetcher, Tool
    
    fetcher = LLMFetcher(backends=[...])
    agent = Agent(llm_handler=fetcher, system_prompt="...", provider="anthropic")
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

# Tool factories
from .tools.shell_tools import create_shell_tools
from .tools.builtin_tools import create_builtin_tools

# Optional: Import all tools module for advanced usage
from . import tools as tool_modules
from . import swarm as swarm_modules

__all__ = [
    # Core classes
    "LLMFetcher",
    "LLMBackendConfig",
    "Agent",
    "Tool",
    "ThinkingGraph",
    
    # Swarm orchestration
    "AgentSwarm",
    "GraphContext",
    
    # Tool factories
    "create_shell_tools",
    "create_builtin_tools",
    
    # Submodules (for advanced usage)
    "tool_modules",
    "swarm_modules",
]