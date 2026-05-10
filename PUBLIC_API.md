# Public API Reference

This document lists all symbols exported from the `pack` package that are available for external use.

## Quick Import

```python
from pack import *  # Not recommended - use explicit imports instead
```

**Recommended**: Import only what you need:

```python
from pack import Agent, LLMFetcher, Tool
```

---

## Complete Export List (44 items)

### Version Information

| Symbol | Type | Description |
|--------|------|-------------|
| `__version__` | `str` | Package version ("0.3.0") |
| `__author__` | `str` | Package author ("LunaticLegacy") |

---

### Core Classes (9 items)

#### LLM Backend

| Symbol | Type | Description |
|--------|------|-------------|
| `LLMFetcher` | Class | Main interface for calling LLM APIs |
| `LLMBackendConfig` | Class | Configuration for LLM backends |
| `LLMError` | Exception | Base exception for LLM errors |
| `LLMTimeoutError` | Exception | Timeout error during LLM calls |
| `LLMBackendError` | Exception | Backend-specific errors |

**Usage Example**:
```python
from pack import LLMFetcher, LLMBackendConfig

backend = LLMBackendConfig(
    name="deepseek",
    provider="anthropic",
    model="deepseek-chat",
    api_key="sk-...",
    api_url="https://api.deepseek.com/anthropic"
)

fetcher = LLMFetcher(backends=[backend])
```

#### Agent & Tools

| Symbol | Type | Description |
|--------|------|-------------|
| `Agent` | Class | Single agent with tool calling capability |
| `Tool` | Class | Custom tool definition |
| `ToolRegistry` | Class | Registry for managing multiple tools |

**Usage Example**:
```python
from pack import Agent, Tool

async def my_tool(param: str) -> str:
    return f"Result: {param}"

tool = Tool(
    name="my_tool",
    description="My custom tool",
    parameters={"type": "object", "properties": {...}},
    handler=my_tool
)

agent = Agent(llm_handler=fetcher, system_prompt="...", provider="anthropic")
```

---

### Thinking Graph (6 items)

| Symbol | Type | Description |
|--------|------|-------------|
| `ThinkingGraph` | Class | Graph-based reasoning system |
| `ThinkingNodeType` | Enum | Types of thinking nodes (QUESTION, EVIDENCE, etc.) |
| `ThinkingEdgeType` | Enum | Types of edges between nodes |
| `ThinkingGraphNode` | Class | Individual node in the graph |
| `ThinkingGraphEdge` | Class | Connection between nodes |
| `ThinkingGraphTransactionRecord` | Class | Record of graph operations |

**Usage Example**:
```python
from pack import ThinkingGraph, ThinkingNodeType

graph = ThinkingGraph()
await graph.add_node(
    node_type=ThinkingNodeType.EVIDENCE,
    info="Key finding",
    payload={"source": "url"}
)
```

---

### Context Management (4 items)

| Symbol | Type | Description |
|--------|------|-------------|
| `LLMContextHandler` | Class | Manages conversation context |
| `LLMContext` | Class | Single context entry |
| `LLMContextPair` | Class | Input-output pair |
| `LLMContextCompressed` | Class | Compressed context representation |

**Usage Example**:
```python
from pack import LLMContextHandler

handler = LLMContextHandler(max_tokens=4000)
await handler.add_pair("user message", "assistant response")
context = await handler.get_context()
```

---

### Swarm Orchestration (15 items)

#### Main Classes

| Symbol | Type | Description |
|--------|------|-------------|
| `AgentSwarm` | Class | Multi-agent orchestration engine |
| `SwarmSpec` | Class | Specification for swarm configuration |
| `GraphContext` | Class | Execution context for graphs |
| `ExecutionGraph` | Class | DAG-based execution workflow |

#### Edge & State

| Symbol | Type | Description |
|--------|------|-------------|
| `Edge` | Class | Connection between execution nodes |
| `ExecutionStopState` | Enum | States for execution termination |

#### Execution Nodes (7 types)

| Symbol | Type | Description |
|--------|------|-------------|
| `ExecutionNode` | ABC | Base class for all nodes |
| `AgentNode` | Class | Node that executes an agent |
| `ToolNode` | Class | Node that executes a tool |
| `RouterNode` | Class | Node that routes to different paths |
| `InputNode` | Class | Entry point for data |
| `OutputNode` | Class | Exit point for results |
| `JoinNode` | Class | Merges multiple execution paths |

**Usage Example**:
```python
from pack import AgentSwarm, AgentNode, ToolNode

swarm = AgentSwarm(llm_fetcher=fetcher, name="my-swarm")

# Add agents
swarm.add_agent("researcher", system_prompt="Research topics...")
swarm.add_agent("writer", system_prompt="Write summaries...")

# Connect in DAG
swarm.connect("input", "researcher")
swarm.connect("researcher", "writer")
swarm.connect("writer", "output")

# Execute
result = await swarm.execute("Research quantum computing")
```

---

### Runtime Slots (3 items)

| Symbol | Type | Description |
|--------|------|-------------|
| `RuntimeSlot` | Class | Represents a runtime execution slot |
| `RuntimeSlotManager` | Class | Manages multiple runtime slots |
| `SlotStatus` | Enum | Status of a runtime slot (IDLE, RUNNING, etc.) |

**Usage Example**:
```python
from pack import RuntimeSlotManager, SlotStatus

manager = RuntimeSlotManager(max_slots=5)
slot = await manager.allocate_slot()
print(slot.status)  # SlotStatus.RUNNING
```

---

### Tool Factories (2 items)

| Symbol | Type | Description |
|--------|------|-------------|
| `create_shell_tools` | Function | Creates shell execution tools with security controls |
| `create_builtin_tools` | Function | Creates built-in utility tools |

**Usage Example**:
```python
from pack import create_shell_tools

tools = create_shell_tools(
    allowed_commands=["ls", "cat", "grep"],
    max_timeout=60.0,
    sandbox_cwd="/safe/directory"
)
```

---

### Agent I/O (4 items)

| Symbol | Type | Description |
|--------|------|-------------|
| `AgentFileIOManager` | Class | Manages file I/O for agents |
| `AgentWorkspacePolicy` | Class | Policy for workspace access control |
| `AgentFileLocations` | Class | Manages file location mappings |
| `AgentFileSnapshot` | Class | Snapshot of file state |

**Usage Example**:
```python
from pack import AgentFileIOManager, AgentWorkspacePolicy

policy = AgentWorkspacePolicy(allow_read=True, allow_write=False)
io_manager = AgentFileIOManager(policy=policy, root_dir="/workspace")
```

---

### Submodules (2 items)

For advanced usage, you can access entire submodules:

| Symbol | Type | Description |
|--------|------|-------------|
| `tool_modules` | Module | All tool implementations |
| `swarm_modules` | Module | All swarm-related modules |

**Usage Example**:
```python
from pack import tool_modules

# Access specific tool module
shell_tools = tool_modules.shell_tools
```

---

## Import Patterns

### Pattern 1: Minimal Import (Recommended)

Import only what you need:

```python
from pack import Agent, LLMFetcher, LLMBackendConfig, Tool
```

### Pattern 2: Grouped Import

Import related components together:

```python
from pack import (
    # Core
    Agent, LLMFetcher, LLMBackendConfig,
    
    # Tools
    Tool, create_shell_tools,
    
    # Thinking
    ThinkingGraph, ThinkingNodeType,
)
```

### Pattern 3: Full Import (Not Recommended)

Import everything (can cause namespace pollution):

```python
from pack import *
```

---

## What's NOT Exported

The following are **internal implementation details** and should not be used directly:

- Private classes/functions (prefixed with `_`)
- Internal modules not listed in `__all__`
- Implementation-specific utilities

If you need something that's not exported, please open an issue on GitHub.

---

## Version Compatibility

All exports follow semantic versioning:

- **Major version** (X.0.0): May include breaking changes
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

Check current version:
```python
import pack
print(pack.__version__)  # "0.3.0"
```

---

## Migration Guide

If you were importing from internal modules before:

### Before (❌ Not recommended)
```python
from pack.llm_fetcher import LLMFetcher
from pack.agent import Agent
from pack.swarm.swarm import AgentSwarm
```

### After (✅ Recommended)
```python
from pack import LLMFetcher, Agent, AgentSwarm
```

**Benefits**:
- Cleaner imports
- Stable public API
- Easier to maintain
- Better IDE support

---

## Need More?

If you need access to additional symbols:

1. **Check if it's already exported** - Look at this list
2. **Open an issue** - Request the symbol be added to public API
3. **Use submodule access** - Import the entire module if needed

```python
# Advanced: Access internal modules (use with caution)
from pack.llm_fetcher import SomeInternalClass
```

⚠️ **Warning**: Internal APIs may change without notice between versions.

---

**Total Public Exports**: 44 items  
**Last Updated**: 2026-05-10  
**Version**: 0.3.0
