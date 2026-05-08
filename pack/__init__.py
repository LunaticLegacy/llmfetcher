"""`llm_fetcher` 子系统的公共接口聚合。

这个包是 Angelus 里负责 LLM 路由、Agent 执行、思考图与 swarm 编排的
基础运行时。为了便于独立发布与复用，这里尽量把常用的公共类型都
统一导出，外部可以直接从 `modules.llm_fetcher` 或顶层兼容包
`llm_fetcher` 导入。
"""

from .agent import Agent
from .agent_io import (
    AgentFileIOManager,
    AgentFileLocations,
    AgentFileSnapshot,
    AgentWorkspacePolicy,
)
from .llm_fetcher import (
    LLMBackendConfig,
    LLMBackendError,
    LLMContext,
    LLMError,
    LLMFetcher,
    LLMTimeoutError,
)
from .swarm.execution_graph import (
    AgentNode,
    Edge,
    ExecutionGraph,
    ExecutionNode,
    GraphContext,
    InputNode,
    JoinNode,
    OutputNode,
    RouterNode,
    ToolNode,
)
from .swarm.runtime_slot import RuntimeSlot, RuntimeSlotManager, SlotStatus
from .swarm.swarm import AgentSwarm, SwarmSpec
from .thinking_graph import (
    ALLOWED_EDGE_SCHEMA,
    ThinkingEdgeType,
    ThinkingGraph,
    ThinkingGraphEdge,
    ThinkingGraphNode,
    ThinkingGraphObject,
    ThinkingGraphTransactionRecord,
    ThinkingNodeType,
)
from .tool import Tool, ToolRegistry
from .tools.builtin_tools import create_builtin_tools
from .tools.execution_graph_tools import create_execution_graph_tools
from .tools.obscura_tools import create_obscura_tools
from .tools.runtime_slot_tools import create_runtime_slot_tools
from .tools.shell_tools import create_shell_tools
from .tools.thinking_graph_tools import create_thinking_graph_tools

__all__ = [
    "Agent",
    "AgentSwarm",
    "SwarmSpec",
    "Tool",
    "ToolRegistry",
    "LLMFetcher",
    "LLMContext",
    "LLMBackendConfig",
    "LLMError",
    "LLMTimeoutError",
    "LLMBackendError",
    "AgentFileIOManager",
    "AgentFileSnapshot",
    "AgentFileLocations",
    "AgentWorkspacePolicy",
    "ThinkingGraph",
    "ThinkingGraphObject",
    "ThinkingGraphNode",
    "ThinkingGraphEdge",
    "ThinkingGraphTransactionRecord",
    "ThinkingNodeType",
    "ThinkingEdgeType",
    "ALLOWED_EDGE_SCHEMA",
    "ExecutionGraph",
    "ExecutionNode",
    "GraphContext",
    "AgentNode",
    "ToolNode",
    "InputNode",
    "OutputNode",
    "RouterNode",
    "JoinNode",
    "Edge",
    "RuntimeSlot",
    "RuntimeSlotManager",
    "SlotStatus",
    "create_builtin_tools",
    "create_execution_graph_tools",
    "create_obscura_tools",
    "create_runtime_slot_tools",
    "create_shell_tools",
    "create_thinking_graph_tools",
]
