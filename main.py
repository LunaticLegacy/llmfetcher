"""
News Monitoring Agent Swarm
===========================

A multi-agent pipeline that:
  1. Fetches news articles/topics via shell (curl) or direct input
  2. Analyzes content for relevance and key information
  3. Produces a final structured summary

Usage:
  python main.py "artificial intelligence breakthroughs 2025"
  python main.py   (prompts interactively)

Requires: OPENAI_API_KEY environment variable.
"""

import asyncio
import os
import sys
from typing import Any, Dict, List

# ── Add project root ──────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pack.llm_fetcher import LLMFetcher, LLMBackendConfig
from pack.tool import Tool
from pack.swarm.swarm import AgentSwarm
from pack.tools.shell_tools import create_shell_tools
from pack.swarm.execution_graph import GraphContext


# ======================================================================
# 1. Custom news analysis tools
# ======================================================================

def extract_source(url: str = "") -> str:
    """Extract domain or source name from a URL."""
    if not url:
        return "unknown"
    # strip protocol and path
    domain = url.replace("http://", "").replace("https://", "").split("/")[0]
    return domain if domain else "unknown"


def format_news_digest(articles: List[Dict[str, str]]) -> str:
    """Format a list of article dicts into a readable digest string.

    Each article dict should have keys: ``source``, ``title``, ``snippet``.
    """
    if not articles:
        return "No articles to report."

    lines = ["# News Digest", ""]
    for i, art in enumerate(articles, 1):
        lines.append(f"## {i}. {art.get('title', '(no title)')}")
        lines.append(f"   **Source:** {art.get('source', 'unknown')}")
        lines.append(f"   {art.get('snippet', '(no content)')}")
        lines.append("")
    return "\n".join(lines)


# ======================================================================
# 2. Backend configuration
# ======================================================================

def get_backend() -> LLMBackendConfig:
    """Read LLM backend config from environment."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return LLMBackendConfig(
            name="openai",
            provider="openai",
            model="gpt-4o-mini",      # fast & cheap; change to gpt-4o for heavier reasoning
            api_key=api_key,
            timeout=120.0,
        )

    # Optional: support a JSON-encoded env var with multiple backends
    fallback = os.environ.get("LLM_BACKEND_CONFIG")
    if fallback:
        import json
        cfg = json.loads(fallback)
        return LLMBackendConfig(**cfg)

    raise RuntimeError(
        "No LLM backend configured. Set OPENAI_API_KEY or LLM_BACKEND_CONFIG."
    )


# ======================================================================
# 3. Swarm topology builder
# ======================================================================

def build_news_monitor_swarm(fetcher: LLMFetcher) -> AgentSwarm:
    """Construct the news-monitoring DAG.

    Topology::

        input ──► fetcher ──► analyzer ──► summarizer ──► output
                     │                        │
                     └────────────────────────┘
                           (thinking graph
                            shared across all)
    """
    swarm = AgentSwarm(
        llm_fetcher=fetcher,
        name="news-monitor",
    )

    # ── Register global tools ──────────────────────────────────────────
    # All agents get the shell tool for web fetching
    shell_tools = create_shell_tools()
    swarm.add_tools(shell_tools)  # "shell" tool added globally

    # ── Build DAG nodes ────────────────────────────────────────────────
    swarm.add_input("input")

    # Agent 1: News Fetcher – uses shell + thinking graph to retrieve articles
    swarm.add_agent(
        "fetcher",
        system_prompt=(
            "你是新闻采集专家。你的任务是根据用户提供的主题，使用 shell 工具获取相关新闻。\n\n"
            "操作步骤：\n"
            "1. 使用 shell 工具执行 curl 命令获取新闻源。例如：\n"
            '   curl -s "https://newsapi.org/v2/everything?q=AI&apiKey=YOUR_KEY" 2>/dev/null | head -500\n'
            "   或使用简易的 lnews 命令行工具（如果可用）。\n"
            "2. 如果无法直接获取，可以请求用户提供具体文章链接。\n"
            "3. 将提取到的原始内容整理成结构化的文章列表（标题、来源、摘要片段）。\n\n"
            "请始终在思考图谱中记录你找到的关键文章节点。"
        ),
        share_thinking_tools=True,      # can record findings in ThinkingGraph
        share_graph_tools=False,
        max_concurrent_tools=2,
    )

    # Agent 2: News Analyzer – evaluates relevance, extracts entities
    swarm.add_agent(
        "analyzer",
        system_prompt=(
            "你是新闻分析专家。你的任务：\n"
            "1. 分析采集到的新闻内容与用户查询主题的相关性（高/中/低）。\n"
            "2. 提取关键实体（人名、组织、技术术语）。\n"
            "3. 识别每篇文章的核心观点和情感倾向。\n"
            "4. 标记可能存在的偏见或信息冲突。\n\n"
            "输出格式：为每篇文章生成一个结构化分析记录，包含：\n"
            "- 标题\n- 相关性评分\n- 关键实体列表\n- 核心观点\n- 情感倾向\n- 冲突/偏见标记\n\n"
            "使用思考图谱记录你的分析节点，以便总结阶段参考。"
        ),
        share_thinking_tools=True,
        share_graph_tools=False,
        max_concurrent_tools=1,
    )

    # Agent 3: Summarizer – produces final digest
    swarm.add_agent(
        "summarizer",
        system_prompt=(
            "你是新闻摘要专家。你的任务：\n"
            "1. 综合采集和分析阶段的所有输出。\n"
            "2. 从思考图谱中提取关键洞察。\n"
            "3. 生成一份最终新闻摘要，包含：\n"
            "   - 主题总览（1-2句话）\n"
            "   - 主要文章摘要（每篇 2-3 句话）\n"
            "   - 关键趋势和洞察\n"
            "   - 信息来源标注\n\n"
            "输出使用 Markdown 格式，清晰易读。"
        ),
        share_thinking_tools=True,      # reads ThinkingGraph nodes from previous agents
        share_graph_tools=False,
        max_concurrent_tools=1,
    )

    # Output node – collects final summary
    swarm.add_output("output", collector=lambda inputs: inputs[0] if inputs else "")

    # ── Wire the DAG ───────────────────────────────────────────────────
    swarm.connect("input", "fetcher")
    swarm.connect("fetcher", "analyzer")
    swarm.connect("analyzer", "summarizer")
    swarm.connect("summarizer", "output")

    # Optional: set timeouts for individual nodes (in seconds)
    swarm.set_timeout("fetcher", 180.0)    # allow extra time for web fetches
    swarm.set_timeout("analyzer", 120.0)
    swarm.set_timeout("summarizer", 90.0)

    return swarm


# ======================================================================
# 4. Interactive / CLI entry point
# ======================================================================

async def run_once(swarm: AgentSwarm, query: str) -> GraphContext:
    """Execute a single news-monitoring run."""
    print(f"\n{'='*60}")
    print(f"🔍  News Monitor: {query}")
    print(f"{'='*60}\n")

    ctx = await swarm.run(initial_input=query, entry_node_id="input")

    print(f"\n{'='*60}")
    print("📰  Final Output")
    print(f"{'='*60}\n")
    print(ctx.get_output("output"))
    print()

    # Optionally show ThinkingGraph state
    tg = await swarm.thinking_graph.get_full_graph()
    nodes = tg.get("nodes", [])
    edges = tg.get("edges", [])
    if nodes:
        print(f"[ThinkingGraph: {len(nodes)} nodes, {len(edges)} edges]")
    return ctx


async def main(query: str | None = None) -> None:
    # ── Bootstrap ──────────────────────────────────────────────────────
    backend = get_backend()
    fetcher = LLMFetcher(backends=[backend])

    swarm = build_news_monitor_swarm(fetcher)

    # ── Interactive loop ───────────────────────────────────────────────
    if query:
        await run_once(swarm, query)
    else:
        print("📡  News Monitor Swarm  📡")
        print("Type your news query, or 'quit' to exit.\n")
        while True:
            try:
                q = input("Query> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not q:
                continue
            if q.lower() in ("quit", "exit", "q"):
                break
            await run_once(swarm, q)


if __name__ == "__main__":
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(query=query))