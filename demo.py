"""
Minimal demo of the LLM Swarm library.
Creates a single-agent swarm, runs a query, and prints the result.
"""

import os
from pack.llm_fetcher import LLMFetcher
from pack.swarm.swarm import AgentSwarm

def main():
    # 1. Configure LLM backend (try environment, fallback to local)
    api_key = os.getenv("OPENAI_API_KEY", "sk-dummy")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    api_url = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")

    fetcher = LLMFetcher(
        api_url=api_url,
        api_key=api_key,
        model=model,
        provider="openai",
        timeout=30
    )

    # 2. Build swarm
    swarm = AgentSwarm(fetcher, name="DemoSwarm")

    # 3. Add nodes
    swarm.add_input("input")
    swarm.add_agent("agent", system_prompt="You are a helpful assistant.")
    swarm.add_output("output")

    swarm.connect("input", "agent")
    swarm.connect("agent", "output")

    # 4. Run
    result = swarm.run("What is the capital of France?")
    print("Swarm output:", result)

if __name__ == "__main__":
    main()