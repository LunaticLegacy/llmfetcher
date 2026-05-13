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
__author__ = "LunaticLegacy"

# ============================================================================
# Core Classes
# ============================================================================
from .pack import (
    LLMFetcher,
    LLMBackendConfig,
    LLMError,
    LLMTimeoutError,
    LLMBackendError,
    Agent,
    Tool, 
    ToolRegistry,
    ThinkingGraph,
    ThinkingNodeType,
    ThinkingEdgeType,
    ThinkingGraphNode,
    ThinkingGraphEdge,
    ThinkingGraphTransactionRecord,

# ============================================================================
# Context Management
# ============================================================================
    LLMContextHandler,
    LLMContext,
    LLMContextPair,
    LLMContextCompressed,
# ============================================================================
# Swarm Orchestration
# ============================================================================
    AgentSwarm, 
    SwarmSpec,
    GraphContext,
    Edge,
    ExecutionStopState,
    ExecutionNode,
    AgentNode,
    ToolNode,
    RouterNode,
    InputNode,
    OutputNode,
    JoinNode,
    ExecutionGraph,
    RuntimeSlot,
    RuntimeSlotManager,
    SlotStatus,

# ============================================================================
# Tool Factories
# ============================================================================
    create_shell_tools,
    create_builtin_tools,
    create_ctf_tools,

# ============================================================================
# Agent I/O (Optional - for advanced file operations)
# ============================================================================
    AgentFileIOManager,
    AgentWorkspacePolicy,
    AgentFileLocations,
    AgentFileSnapshot,

# ============================================================================
# Submodules (for advanced usage)
# ============================================================================
    tools as tool_modules,
    swarm as swarm_modules
)

# ============================================================================
# Public API Exports
# ============================================================================
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Core classes
    "LLMFetcher",
    "LLMBackendConfig",
    "LLMError",
    "LLMTimeoutError",
    "LLMBackendError",
    "Agent",
    "Tool",
    "ToolRegistry",
    
    # Thinking Graph
    "ThinkingGraph",
    "ThinkingNodeType",
    "ThinkingEdgeType",
    "ThinkingGraphNode",
    "ThinkingGraphEdge",
    "ThinkingGraphTransactionRecord",
    
    # Context Management
    "LLMContextHandler",
    "LLMContext",
    "LLMContextPair",
    "LLMContextCompressed",
    
    # Swarm orchestration
    "AgentSwarm",
    "SwarmSpec",
    "GraphContext",
    "Edge",
    "ExecutionStopState",
    "ExecutionNode",
    "AgentNode",
    "ToolNode",
    "RouterNode",
    "InputNode",
    "OutputNode",
    "JoinNode",
    "ExecutionGraph",
    
    # Runtime slots
    "RuntimeSlot",
    "RuntimeSlotManager",
    "SlotStatus",
    
    # Tool factories
    "create_shell_tools",
    "create_builtin_tools",
    "create_ctf_tools",
    
    # Agent I/O
    "AgentFileIOManager",
    "AgentWorkspacePolicy",
    "AgentFileLocations",
    "AgentFileSnapshot",
    
    # Submodules (for advanced usage)
    "tool_modules",
    "swarm_modules",
]
