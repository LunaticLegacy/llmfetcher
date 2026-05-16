"""
News Monitoring Agent Swarm
===========================

A multi-agent pipeline that:
  1. Fetches news articles/topics via web scraping tools
  2. Analyzes content for relevance and key information
  3. Produces a final structured summary

Usage:
  python main.py "artificial intelligence breakthroughs 2025"
  python main.py   (prompts interactively)

Requires: DEEPSEEK_API_KEY environment variable.
"""

import asyncio
import os
import sys
from typing import Any, Dict, List

# ── Add package parent for direct script execution ────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llmfetcher.llm_fetcher import LLMFetcher, LLMBackendConfig
from llmfetcher.tool import Tool
from llmfetcher.swarm.swarm import AgentSwarm
from llmfetcher.tools.shell_tools import create_shell_tools
from llmfetcher.swarm.execution_graph import GraphContext


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
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        return LLMBackendConfig(
            name="deepseek",
            provider="anthropic",  # DeepSeek uses Anthropic-compatible format
            model="deepseek-chat",
            api_key=api_key,
            api_url="https://api.deepseek.com/anthropic",
            timeout=120.0,
        )

    # Optional: support a JSON-encoded env var with multiple backends
    fallback = os.environ.get("LLM_BACKEND_CONFIG")
    if fallback:
        import json
        cfg = json.loads(fallback)
        return LLMBackendConfig(**cfg)

    raise RuntimeError(
        "No LLM backend configured. Set DEEPSEEK_API_KEY or LLM_BACKEND_CONFIG."
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
    # All agents get the shell tool for web fetching (with security restrictions)
    shell_tools = create_shell_tools(
        allowed_commands=["ls", "cat", "grep", "find", "pwd", "curl", "wget"],
        max_timeout=60.0,
        sandbox_cwd=os.getcwd(),  # Restrict to current directory
    )
    swarm.add_tools(shell_tools)  # "shell" tool added globally

    # ── Build DAG nodes ────────────────────────────────────────────────
    swarm.add_input("input")

    # Agent 1: News Fetcher – uses web scraping tools to retrieve articles
    swarm.add_agent(
        "fetcher",
        system_prompt=(
            "你是新闻采集专家。你的任务是获取关于用户查询主题的最新新闻。\n\n"
            "**重要：你必须严格按照以下步骤执行，不得跳过：**\n\n"
            "步骤 1（必须首先执行）：使用 web_fetch 或 web_scrape 工具搜索并获取新闻内容\n"
            "   - 调用 web_fetch 工具获取单个网页\n"
            "   - 或调用 web_scrape 工具批量获取多个URL\n"
            "   - 搜索关键词应基于用户的查询主题\n"
            "   - 例如：用户问'百度文心一言最新模型'，你应该搜索相关新闻网站\n\n"
            "步骤 2：将获取到的新闻内容整理成结构化格式\n"
            "   - 提取：标题、来源URL、摘要/关键内容\n"
            "   - 至少获取 3-5 条相关新闻\n\n"
            "步骤 3：使用 thinking_graph_add_node 记录每条新闻\n"
            "   - node_type: 'EVIDENCE' 或 'ARTIFACT'\n"
            "   - info: 包含标题和摘要\n"
            "   - payload: 包含完整URL和详细内容\n\n"
            "步骤 4：调用 round_end 工具结束本轮\n"
            "   - 只有完成以上所有步骤后才能调用 round_end\n\n"
            "**禁止行为：**\n"
            "   - ❌ 不要在未获取任何新闻前就调用 round_end\n"
            "   - ❌ 不要只查询 thinking_graph 而不获取新数据\n"
            "   - ❌ 不要请求用户提供链接（你应该主动搜索）\n\n"
            "**成功标准：**\n"
            "   - ✅ ThinkingGraph 中至少有 3 个 EVIDENCE/ARTIFACT 节点\n"
            "   - ✅ 每个节点都包含实际的新闻内容\n"
            "   - ✅ 最后调用 round_end 结束"
        ),
        share_thinking_tools=True,      # can record findings in ThinkingGraph
        share_graph_tools=False,
        max_concurrent_tools=3,         # 允许并行获取多条新闻
    )

    # Agent 2: News Analyzer – evaluates relevance, extracts entities
    swarm.add_agent(
        "analyzer",
        system_prompt=(
            "你是新闻分析专家。你的任务是从 ThinkingGraph 中读取 Fetcher 采集的新闻并进行深度分析。\n\n"
            "**执行步骤：**\n\n"
            "步骤 1：使用 thinking_graph_get_full_graph 获取所有新闻节点\n"
            "   - 查找 node_type 为 'EVIDENCE' 或 'ARTIFACT' 的节点\n"
            "   - 如果 graph 为空或没有新闻节点，说明 Fetcher 未完成工作\n\n"
            "步骤 2：对每条新闻进行分析\n"
            "   1. 相关性评分（高/中/低）- 与用户查询主题的匹配度\n"
            "   2. 提取关键实体（人名、组织、技术术语、产品名）\n"
            "   3. 识别核心观点和主要信息\n"
            "   4. 判断情感倾向（正面/负面/中性）\n"
            "   5. 标记可能的偏见、冲突或不一致之处\n\n"
            "步骤 3：将分析结果写入 ThinkingGraph\n"
            "   - 为每条新闻创建 'CLAIM' 或 'SUMMARY' 节点\n"
            "   - 使用 SUPPORTS/DERIVES_FROM 边连接到原始 EVIDENCE 节点\n"
            "   - payload 中包含完整的分析结果\n\n"
            "步骤 4：调用 round_end 结束\n\n"
            "**注意：**\n"
            "   - 如果 ThinkingGraph 中没有新闻数据，不要进行分析，直接报告问题\n"
            "   - 保持客观，标注信息来源的不确定性"
        ),
        share_thinking_tools=True,
        share_graph_tools=False,
        max_concurrent_tools=2,
    )

    # Agent 3: Summarizer – produces final digest
    swarm.add_agent(
        "summarizer",
        system_prompt=(
            "你是新闻摘要专家。你的任务是综合 Fetcher 和 Analyzer 的工作成果，生成最终报告。\n\n"
            "**执行步骤：**\n\n"
            "步骤 1：使用 thinking_graph_get_full_graph 获取完整思考图谱\n"
            "   - 查看所有节点类型：EVIDENCE（原始新闻）、CLAIM/SUMMARY（分析结果）\n"
            "   - 理解节点之间的关系（通过 edges）\n\n"
            "步骤 2：从图谱中提取关键信息\n"
            "   - 最重要的发现和趋势\n"
            "   - 各方观点和立场\n"
            "   - 存在的争议或不确定性\n\n"
            "步骤 3：生成结构化的最终摘要（Markdown 格式）\n"
            "   ```\n"
            "   # [主题] 新闻摘要\n"
            "   \n"
            "   ## 📌 总览\n"
            "   [1-2句话概括核心内容]\n"
            "   \n"
            "   ## 📰 主要新闻\n"
            "   ### 1. [标题]\n"
            "   - **来源**: [来源名称/URL]\n"
            "   - **要点**: [2-3句话摘要]\n"
            "   - **分析**: [相关性、关键观点等]\n"
            "   \n"
            "   ## 🔍 关键洞察\n"
            "   - [洞察点1]\n"
            "   - [洞察点2]\n"
            "   \n"
            "   ## ⚠️ 注意事项\n"
            "   - [偏见/冲突/不确定性说明]\n"
            "   \n"
            "   ## 📚 信息来源\n"
            "   - [列出所有参考的新闻来源]\n"
            "   ```\n\n"
            "步骤 4：输出最终摘要并调用 round_end\n\n"
            "**质量要求：**\n"
            "   - 内容准确，基于 ThinkingGraph 中的实际数据\n"
            "   - 结构清晰，易于阅读\n"
            "   - 标注信息来源，保持透明度"
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

    # Show available tools for debugging
    print("📋 Available Tools:")
    for tool_name in swarm.tool_schemas():
        print(f"   - {tool_name}")
    print()

    ctx = await swarm.run(initial_input=query, entry_node_id="input")

    print(f"\n{'='*60}")
    print("📰  Final Output")
    print(f"{'='*60}\n")
    print(ctx.get_output("output"))
    print()

    # Show ThinkingGraph state for debugging
    tg = await swarm.thinking_graph.get_full_graph()
    nodes = tg.get("nodes", [])
    edges = tg.get("edges", [])
    if nodes:
        print(f"\n[ThinkingGraph Summary]")
        print(f"   Total Nodes: {len(nodes)}")
        print(f"   Total Edges: {len(edges)}")
        
        # Show node types distribution
        from collections import Counter
        node_types = Counter(node.get("node_type", "unknown") for node in nodes)
        print(f"   Node Types: {dict(node_types)}")
        
        # Show first few nodes as sample
        print(f"\n   Sample Nodes (first 3):")
        for i, node in enumerate(nodes[:3]):
            print(f"     [{i+1}] Type: {node.get('node_type')}")
            print(f"         Info: {node.get('info', '')[:100]}...")
    else:
        print("\n⚠️  Warning: ThinkingGraph is empty! This indicates the fetcher didn't collect any data.")
    
    return ctx


async def main(query: str | None = None) -> None:
    # ── Bootstrap ──────────────────────────────────────────────────────
    fetcher = LLMFetcher(
            api_url="https://api.deepseek.com",
            api_key=os.environ.get("DEEPSEEK_API_KEY"),
            model="deepseek-v4-flash",
            timeout=120.0
        )

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
