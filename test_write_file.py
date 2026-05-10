import os
import asyncio

from pack import LLMFetcher, create_obscura_tools, create_shell_tools, Tool, Agent

from typing import List

def get_fetcher() -> LLMFetcher:
    """Read LLM backend config from environment."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        return LLMFetcher(
            api_url="https://api.deepseek.com",
            api_key=api_key,
            model="deepseek-v4-flash",
            timeout=120.0
        )

    raise RuntimeError(
        "No LLM backend configured."
    )

async def main():
    fetcher: LLMFetcher = get_fetcher()
    
    obscura_tool: List[Tool] = create_obscura_tools()
    file_io_tool: List[Tool] = create_shell_tools()
    total_tools: List[Tool] = obscura_tool + file_io_tool
    # print(total_tools)
    
    agent1: Agent = Agent(
        fetcher,
        "You are a programmer. Use tools to write file to $(pwd)/workspace",
        total_tools,
        provider="openai"
    )

    call_msg: str = await agent1.round_call("Write a Python demo.", verbose_info=False, stream=True, max_turns=10)
    
    print("=" * 20 + " Finished demo" + "=" * 20)

    return

if __name__ == "__main__":
    asyncio.run(main())
