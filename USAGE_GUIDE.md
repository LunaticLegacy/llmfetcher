# Using llmfetcher as an External Package

## Installation

### Option 1: Install from PyPI (when published)
```bash
pip install llmfetcher
```

### Option 2: Install from source
```bash
# Clone the repository
git clone https://github.com/LunaticLegacy/llmfetcher.git
cd llmfetcher

# Install in development mode
pip install -e .

# Or install directly
pip install .
```

### Option 3: Install from built wheel
```bash
# Build the package first
python -m build

# Install the wheel
pip install dist/llmfetcher-0.3.0-py3-none-any.whl
```

---

## Quick Start

### Basic Agent Setup

```python
import os
from pack import Agent, LLMFetcher, LLMBackendConfig

# Configure LLM backend
backend = LLMBackendConfig(
    name="deepseek",
    provider="anthropic",
    model="deepseek-chat",
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    api_url="https://api.deepseek.com/anthropic",
    timeout=120.0
)

# Create LLM fetcher
fetcher = LLMFetcher(backends=[backend])

# Create agent
agent = Agent(
    llm_handler=fetcher,
    system_prompt="You are a helpful assistant.",
    provider="anthropic"
)

# Use the agent
response = await agent.round_call("What is the capital of France?")
print(response)
```

### With Tool Calling

```python
from pack import Agent, LLMFetcher, LLMBackendConfig, Tool
from pack.tools import create_shell_tools

# Setup backend and fetcher (same as above)
backend = LLMBackendConfig(...)
fetcher = LLMFetcher(backends=[backend])

# Register tools
tools = create_shell_tools(
    allowed_commands=["ls", "cat", "grep"],
    max_timeout=60.0
)

# Create agent with tools
agent = Agent(
    llm_handler=fetcher,
    system_prompt="You can use shell commands to explore files.",
    provider="anthropic",
    tools=tools
)

# Agent will automatically use tools when needed
response = await agent.round_call("List all Python files in current directory")
```

### Multi-Agent Swarm

```python
from pack import AgentSwarm, LLMFetcher, LLMBackendConfig

# Setup fetcher
backend = LLMBackendConfig(...)
fetcher = LLMFetcher(backends=[backend])

# Create swarm
swarm = AgentSwarm(llm_fetcher=fetcher, name="my-swarm")

# Add agents
swarm.add_agent(
    "researcher",
    system_prompt="You research topics thoroughly.",
    share_thinking_tools=True
)

swarm.add_agent(
    "writer",
    system_prompt="You write clear summaries.",
    share_thinking_tools=True
)

# Connect agents in DAG
swarm.connect("input", "researcher")
swarm.connect("researcher", "writer")
swarm.connect("writer", "output")

# Execute
result = await swarm.execute("Research quantum computing")
print(result)
```

---

## Advanced Usage

### Custom Tools

```python
from pack import Tool

async def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Your implementation here
    return f"Weather in {city}: Sunny, 25°C"

weather_tool = Tool(
    name="get_weather",
    description="Get current weather information",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name"
            }
        },
        "required": ["city"]
    },
    handler=get_weather
)
```

### Multiple Backends

```python
from pack import LLMFetcher, LLMBackendConfig

backends = [
    LLMBackendConfig(
        name="openai",
        provider="openai",
        model="gpt-4o",
        api_key=os.environ.get("OPENAI_API_KEY")
    ),
    LLMBackendConfig(
        name="deepseek",
        provider="anthropic",
        model="deepseek-chat",
        api_key=os.environ.get("DEEPSEEK_API_KEY"),
        api_url="https://api.deepseek.com/anthropic"
    )
]

# Fetcher will try backends in order
fetcher = LLMFetcher(backends=backends)
```

### Thinking Graph Integration

```python
from pack import ThinkingGraph

graph = ThinkingGraph()

# Add nodes during agent execution
await graph.add_node(
    node_type="EVIDENCE",
    info="Key finding about topic",
    payload={"source": "url", "content": "..."}
)

# Query the graph
nodes = await graph.get_nodes_by_type("EVIDENCE")
full_graph = await graph.get_full_graph()
```

---

## API Reference

### Complete Export List

The `pack` package exports **44 public symbols** organized by category:

#### Core Classes (9)
- `LLMFetcher`, `LLMBackendConfig`, `LLMError`, `LLMTimeoutError`, `LLMBackendError`
- `Agent`, `Tool`, `ToolRegistry`

#### Thinking Graph (6)
- `ThinkingGraph`, `ThinkingNodeType`, `ThinkingEdgeType`
- `ThinkingGraphNode`, `ThinkingGraphEdge`, `ThinkingGraphTransactionRecord`

#### Context Management (4)
- `LLMContextHandler`, `LLMContext`, `LLMContextPair`, `LLMContextCompressed`

#### Swarm Orchestration (15)
- `AgentSwarm`, `SwarmSpec`, `GraphContext`, `ExecutionGraph`
- `Edge`, `ExecutionStopState`
- Execution Nodes: `ExecutionNode`, `AgentNode`, `ToolNode`, `RouterNode`, `InputNode`, `OutputNode`, `JoinNode`

#### Runtime Slots (3)
- `RuntimeSlot`, `RuntimeSlotManager`, `SlotStatus`

#### Tool Factories (2)
- `create_shell_tools`, `create_builtin_tools`

#### Agent I/O (4)
- `AgentFileIOManager`, `AgentWorkspacePolicy`, `AgentFileLocations`, `AgentFileSnapshot`

#### Submodules (2)
- `tool_modules`, `swarm_modules`

For detailed documentation on each symbol, see [PUBLIC_API.md](PUBLIC_API.md).

---

## Environment Variables

Set these before running your code:

```bash
# For DeepSeek
export DEEPSEEK_API_KEY="sk-..."

# For OpenAI
export OPENAI_API_KEY="sk-..."

# For Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Common Patterns

### Pattern 1: Research Assistant

```python
from pack import Agent, LLMFetcher, LLMBackendConfig
from pack.tools import create_shell_tools

backend = LLMBackendConfig(...)
fetcher = LLMFetcher(backends=[backend])

agent = Agent(
    llm_handler=fetcher,
    system_prompt="""
    You are a research assistant. Use available tools to gather information.
    Always cite your sources.
    """,
    provider="anthropic",
    tools=create_shell_tools()
)

result = await agent.round_call("Research the latest AI developments")
```

### Pattern 2: Code Review Bot

```python
async def analyze_code(file_path: str) -> str:
    """Analyze code quality."""
    with open(file_path) as f:
        code = f.read()
    # Your analysis logic
    return "Analysis result..."

code_review_tool = Tool(
    name="analyze_code",
    description="Review code quality",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {"type": "string"}
        },
        "required": ["file_path"]
    },
    handler=analyze_code
)

agent = Agent(
    llm_handler=fetcher,
    system_prompt="You review code and suggest improvements.",
    provider="anthropic",
    tools=[code_review_tool]
)
```

### Pattern 3: Data Pipeline

```python
from pack import AgentSwarm

swarm = AgentSwarm(llm_fetcher=fetcher, name="data-pipeline")

# Extract
swarm.add_agent("extractor", system_prompt="Extract data from sources...")

# Transform
swarm.add_agent("transformer", system_prompt="Clean and transform data...")

# Load
swarm.add_agent("loader", system_prompt="Load data to destination...")

# Wire up
swarm.connect("input", "extractor")
swarm.connect("extractor", "transformer")
swarm.connect("transformer", "loader")
swarm.connect("loader", "output")

result = await swarm.execute("Process sales data")
```

---

## Troubleshooting

### Import Error

If you see `ModuleNotFoundError: No module named 'pack'`:

```bash
# Make sure you installed the package
pip show llmfetcher

# Reinstall if needed
pip install -e .
```

### API Key Not Set

```python
import os

# Check if key is set
print(os.environ.get("DEEPSEEK_API_KEY"))

# If None, set it or pass directly to config
backend = LLMBackendConfig(
    ...,
    api_key="your-key-here"  # Not recommended for production
)
```

### Tool Not Found

Ensure tools are registered with the agent:

```python
agent = Agent(
    ...,
    tools=[my_tool]  # Don't forget this!
)
```

---

## Next Steps

1. Read the [README.md](README.md) for detailed documentation
2. Check out examples in the repository
3. Join discussions on GitHub
4. Contribute by submitting issues or PRs

Happy building! 🚀
