from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .llm_fetcher import LLMFetcher
from .llm_context import LLMContext, LLMContextHandler, LLMContextPair
from .tool import Tool, ToolRegistry
from .tools.builtin_tools import create_builtin_tools

if TYPE_CHECKING:  # pragma: no cover - typing only
    from openai.types.chat import ChatCompletion, ChatCompletionMessage


# ---------------------------------------------------------------------------
# 类型别名定义
# ---------------------------------------------------------------------------

MessageDict = Dict[str, str]
Messages = List[MessageDict]

ToolArgs = Dict[str, object]
AssistantMessageDict = Dict[str, object]

ToolList = List[Tool]
OptionalToolList = Optional[ToolList]


class Agent:
    def __init__(
        self,
        llm_handler: LLMFetcher,
        system_prompt: str,
        tools: OptionalToolList = None,
        max_concurrent_tools: int = 1,
        fallback_order: Optional[List[str]] = None,
    ):
        """初始化Agent，绑定LLM处理器、系统提示词和可选工具列表。"""
        self._base_system_prompt: str = system_prompt
        self.memory_list: List[str] = []
        self.llm_handler = llm_handler
        self.llm_context_handler = LLMContextHandler(llm_handler=self.llm_handler)
        self.llm_context_hanlder = self.llm_context_handler
        self.tool_registry = ToolRegistry()
        self.max_concurrent_tools = max_concurrent_tools
        self.fallback_order = fallback_order

        # 注册内嵌工具（round_end 等），供 LLM 控制轮次生命周期
        self._register_builtin_tools()

        if tools:
            tool: Tool
            for tool in tools:
                self.tool_registry.register(tool)

    def _register_builtin_tools(self) -> None:
        """注册 Agent 内嵌的元工具，用于控制对话轮次的生命周期。"""
        for tool in create_builtin_tools():
            self.tool_registry.register(tool)

    @property
    def system_prompt(self) -> str:
        """Dynamic system prompt enriched with tool descriptions."""
        prompt: str = self._base_system_prompt
        hint: Optional[str] = self.tool_registry.get_prompt_hint()
        if hint:
            prompt = f"{prompt}\n{hint}"
        return prompt

    def update_system_prompt(self, new_prompt: str) -> None:
        """运行时动态修改 Agent 的系统提示词。"""
        self._base_system_prompt = new_prompt

    def add_tool(self, tool: "Tool") -> None:
        """运行时给 Agent 增加一个工具。"""
        self.tool_registry.register(tool)

    def remove_tool(self, tool_name: str) -> None:
        """运行时从 Agent 移除一个工具。"""
        self.tool_registry.unregister(tool_name)

    async def round_call(
        self,
        msg: str,
        stream: bool = False,
        verbose_info: bool = False,
        max_turns: int = 3,
    ) -> str:
        """
        进行一整个轮次的 Agent 执行轮。

        核心特性：
        - 多轮工具调用循环：LLM 可在一次 round_call 内连续调用多个工具，
          拿到结果后继续思考，直到决定结束。
        - 保留每轮 content：assistant 的原始回复与工具 JSON 都会保留。
        - round_end：LLM 可通过 JSON tool call 主动结束本轮。
        - 并行执行：当 max_concurrent_tools > 1 时，同一轮内的多个工具调用会并发执行。

        Args:
            msg: 本 agent 的本次输入。
            stream: 为 True 时，最终回复逐字打印到 stdout。
            verbose_info: 为 True 时，打印每轮调用、tool_calls、结果等调试信息。
            max_turns: 最大轮次上限。

        Returns:
            LLM 生成的完整回复文本。
        """
        # 建立本轮输入内容
        messages: Messages = await self._build_round_messages(msg)
        final_content: str = ""
        last_turn_content: str = ""

        turn: int
        for turn in range(1, max_turns + 1):
            if verbose_info:
                print(f"\n[Agent] ====== 执行第 {turn} 轮 ======")

            # ---- 调用 LLM ----
            response: ChatCompletion = await self.llm_handler.fetch(
                msg="",
                system_prompt=None,
                prev_messages=messages,
                tools=None,
                fallback_order=self.fallback_order,
            )
            # 解析消息内容
            message: ChatCompletionMessage = response.choices[0].message
            content: str = message.content or ""
            last_turn_content = content
            tool_calls: List[Dict[str, Any]] = self._parse_json_tool_calls(content)

            if verbose_info:
                print(f"[Agent] content={content[:120]!r}... | json_tool_calls={'有' if tool_calls else '无'}")

            # ---- 情况 A：无工具调用，说明 LLM 已给出最终回复 ----
            if not tool_calls:
                break

            # ---- 情况 B：有 JSON 工具调用，执行工具并继续下一轮 ----
            messages.append(self._format_assistant_message(content))

            has_round_end: bool = False
            if self.max_concurrent_tools > 1 and len(tool_calls) > 1:
                # 并发执行所有工具调用
                tasks = [self._execute_single_tool(tc, verbose_info) for tc in tool_calls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for tc, result_or_exc in zip(tool_calls, results):
                    if isinstance(result_or_exc, Exception):
                        result_str = f"Error: {result_or_exc}"
                    else:
                        result_str = result_or_exc
                    if tc["tool"] == "round_end":
                        has_round_end = True
                    messages.append({
                        "role": "user",
                        "content": self._format_tool_result_message(
                            tool_name=str(tc["tool"]),
                            result=result_str,
                        ),
                    })
            else:
                # 顺序执行（原逻辑）
                for tool_call in tool_calls:
                    result: str = await self._execute_single_tool(tool_call, verbose_info)
                    if tool_call["tool"] == "round_end":
                        has_round_end = True
                    messages.append({
                        "role": "user",
                        "content": self._format_tool_result_message(
                            tool_name=str(tool_call["tool"]),
                            result=result,
                        ),
                    })

            # ---- 情况 C：LLM 主动 round_end，保存本轮 content 并停止 ----
            if has_round_end:
                break
        else:
            # 达到 max_turns，取最后一轮 content（可能为空）
            last_turn_content = last_turn_content or ""

        # ---- 兜底：无论 final_content 是否有内容，都强制获取最终回复 ----
        if verbose_info:
            if not last_turn_content.strip():
                print("[Agent] final_content 为空，发起兜底总结调用...")
            else:
                print("[Agent] 发起最终总结调用...")
        
        # 在 messages 末尾追加一条引导，让 LLM 输出最终回复
        fallback_messages: Messages = messages.copy()
        fallback_messages.append({
            "role": "user",
            "content": "请基于以上内容给出你的最终回复。",
        })
        if stream:
            chunks: List[str] = []
            async for chunk in self.llm_handler.fetch_stream(
                msg="",
                system_prompt=None,
                prev_messages=fallback_messages,
                tools=None,
                fallback_order=self.fallback_order,
            ):
                chunks.append(chunk)
                print(chunk, end="", flush=True)
            final_content = "".join(chunks).strip()
        else:
            fallback_resp: ChatCompletion = await self.llm_handler.fetch(
                msg="",
                system_prompt=None,
                prev_messages=fallback_messages,
                tools=None,
                fallback_order=self.fallback_order,
            )
            final_content = fallback_resp.choices[0].message.content or last_turn_content
            if verbose_info and not final_content.strip():
                print("[Agent] fallback response 为空，保留上一轮内容。")

        # ---- 保存上下文 ----
        await self.llm_context_hanlder.add_context(
            LLMContextPair(
                LLMContext(role="user", content=msg),
                LLMContext(role="assistant", content=final_content or last_turn_content),
            )
        )

        return final_content or last_turn_content

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    def _strip_code_fence(self, text: str) -> str:
        """Remove a single surrounding fenced code block if present."""
        stripped = text.strip()
        if not stripped.startswith("```"):
            return stripped
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def _parse_json_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Parse our custom JSON tool-call protocol from assistant content."""
        text = self._strip_code_fence(content)
        if not text:
            return []

        payload: Any
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = self._extract_json_fragment(text)
            if payload is None:
                return []

        if isinstance(payload, dict):
            if "tool_calls" in payload and isinstance(payload["tool_calls"], list):
                return [tc for tc in payload["tool_calls"] if self._is_valid_tool_call(tc)]
            if self._is_valid_tool_call(payload):
                return [payload]
        if isinstance(payload, list):
            return [tc for tc in payload if self._is_valid_tool_call(tc)]
        return []

    def _is_valid_tool_call(self, payload: Any) -> bool:
        """Validate a single JSON tool-call object."""
        return (
            isinstance(payload, dict)
            and isinstance(payload.get("tool"), str)
            and isinstance(payload.get("arguments"), dict)
        )

    def _extract_json_fragment(self, text: str) -> Optional[Any]:
        """Extract the first JSON object or array embedded in free-form text."""
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char not in "{[":
                continue
            try:
                payload, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            return payload
        return None

    async def _build_round_messages(self, msg: str) -> Messages:
        """构建本轮的初始消息列表（system + 历史 + user msg）。"""
        prev: Messages = await self.llm_context_hanlder.get_now_context()
        messages: Messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(prev)
        messages.append({"role": "user", "content": msg})
        return messages

    def _format_assistant_message(self, content: str) -> AssistantMessageDict:
        """将 LLM 返回的 assistant 消息格式化为字典。"""
        return {
            "role": "assistant",
            "content": content,
        }

    def _format_tool_result_message(self, tool_name: str, result: Any) -> str:
        """Format a tool result message for the next model turn."""
        payload = {
            "type": "tool_result",
            "tool": tool_name,
            "result": result,
        }
        return json.dumps(payload, ensure_ascii=False)

    async def _execute_single_tool(self, tool_call: Dict[str, Any], verbose: bool) -> str:
        """Execute a single JSON tool-call object and return the result string."""
        tool_name: str = str(tool_call["tool"])
        args: ToolArgs = dict(tool_call.get("arguments") or {})

        if verbose:
            print(f"[Agent] 调用 {tool_name} | 参数: {json.dumps(args, ensure_ascii=False)}")

        if tool_name == "round_end":
            result: str = "Round ended."
        else:
            try:
                result = await self.tool_registry.execute(tool_name, args)
            except Exception as exc:
                result = f"Error: {exc}"

        if verbose:
            print(f"[Agent] 结果 {tool_name} -> {str(result)[:200]}")

        return str(result)