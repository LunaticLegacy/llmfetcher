"""
Demo: Agent and AgentSwarm usage.
Demonstrates:
- Direct Agent instantiation with fallback and concurrent tools.
- AgentSwarm with multi-agent execution graph, routing, and thinking graph.
"""

import asyncio
from pack.llm_fetcher import LLMFetcher
from pack.agent import Agent
from pack.tool import Tool
from pack.swarm.swarm import AgentSwarm

# ---------------------------------------------------------------------------
# Helper to check if the LLM endpoint is reachable (optional)
# ---------------------------------------------------------------------------
async def check_endpoint(fetcher: LLMFetcher) -> bool:
    try:
        async with await fetcher._client.get(fetcher.api_url + "/models", timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Main Demo
# ---------------------------------------------------------------------------
async def main():
    llm_fetcher = LLMFetcher(
        api_url="http://localhost:1234/v1",   # example local endpoint (LM Studio / localai)
        api_key="not-needed",
        model="local-model",
        provider="openai"
    )

    # Optional: warn if endpoint not reachable
    if not await check_endpoint(llm_fetcher):
        print("WARNING: LLM endpoint not reachable at", llm_fetcher.api_url)
        print("The demo will likely fail on LLM calls. Continue if you have a local server.\n")

    # -----------------------------
    # Part A: Standalone Agent
    # -----------------------------
    print("=== Standalone Agent Demo ===")

    # Define a simple tool
    async def greet(name: str) -> str:
        return f"Hello, {name}!"

    greet_tool = Tool(
        name="greet",
        description="Greet a person by name",
        parameters={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"]
        },
        handler=greet
    )

    # Create an agent with concurrent tools and fallback order
    agent = Agent(
        llm_handler=llm_fetcher,
        system_prompt="You are a polite assistant. When asked to greet, use the greet tool.",
        tools=[greet_tool],
        max_concurrent_tools=2,          # allow two concurrent tool executions
        fallback_order=["default"]       # fallback to the same backend
    )

    response = await agent.round_call("Greet Alice and Bob separately.")
    print(f"Agent response: {response}")

    # -----------------------------
    # Part B: AgentSwarm with Graph
    # -----------------------------
    print("\n=== AgentSwarm Demo ===")

    swarm = AgentSwarm(llm_fetcher=llm_fetcher, name="DemoSwarm")

    # Create a router agent – small prompt for decision making
    router_agent = swarm.add_agent(
        node_id="router_agent",
        system_prompt=(
            "You are a router that decides which agent should handle the user's request. "
            "If the request involves creativity or storytelling, route to 'agent_2'. "
            "Otherwise route to 'agent_1'. Output only the node name: agent_1 or agent_2."
        ),
        max_concurrent_tools=1,
        fallback_order=["default"]
    )

    # Create two worker agents
    agent_1 = swarm.add_agent(
        node_id="agent_1",
        system_prompt="You are a research assistant. Answer factually.",
        share_thinking_tools=True,   # enable thinking graph tools
        max_concurrent_tools=1,
        fallback_order=["default"]
    )
    agent_2 = swarm.add_agent(
        node_id="agent_2",
        system_prompt="You are a creative writer. Provide imaginative responses.",
        max_concurrent_tools=1,
        fallback_order=["default"]
    )

    # Define routes mapping – router agent will output one of these keys
    routes = {
        "agent_1": "agent_1",
        "agent_2": "agent_2"
    }

    # Add a router node using the router agent
    swarm.add_router(
        node_id="router",
        routes=routes,
        agent=router_agent,            # LLM-based routing
        default_route="agent_1"
    )

    # Wire the execution graph
    swarm.add_input_node("input")
    swarm.connect("input", "router")
    swarm.connect("router", "agent_1")
    swarm.connect("router", "agent_2")
    swarm.add_output_node(
        node_id="output",
        collector=lambda outputs: "\n".join(str(o) for o in outputs)
    )
    swarm.connect("agent_1", "output")
    swarm.connect("agent_2", "output")

    # Run the swarm with a sample query that should trigger creativity
    context = await swarm.run(initial_input="Tell me a creative story about a robot.")
    print(f"Swarm final output: {context.node_outputs.get('output')}")

    # Also test with a research-style query
    print("\n--- Second query (research) ---")
    context2 = await swarm.run(initial_input="Explain the concept of recursion in programming.")
    print(f"Swarm final output: {context2.node_outputs.get('output')}")

if __name__ == "__main__":
    asyncio.run(main())