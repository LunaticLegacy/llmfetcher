from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

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
Messages = List[MessageDict]    # Alias for List[Dict[str, str]]

ToolArgs = Dict[str, object]
AssistantMessageDict = Dict[str, object]

ToolList = List[Tool]
OptionalToolList = Optional[ToolList]


class AgentExecutionError(RuntimeError):
    """执行出错时报错"""
    pass


class EmptyModelResponseError(AgentExecutionError):
    """错误：空响应"""
    pass


class NoToolCallError(AgentExecutionError):
    """错误：没有 tool call"""
    pass


class MaxTurnsExceededError(AgentExecutionError):
    """错误：最大轮次"""
    pass


@dataclass
class AgentMessage:
    """定义一个 Agent 的对话轮使用的内容"""
    provider: str   # 模型提供商？？还是什么？
    role: str = "assistant" # 规则
    content: str = ""       # 输出内容
    reasoning_content: str = "" # 
    tool_blocks: List[Any] = field(default_factory=list)    # 使用的工具
    stop_reason: Optional[str] = None   # 停止原因


class Agent:
    def __init__(
        self,
        llm_handler: LLMFetcher,
        system_prompt: str,
        tools: OptionalToolList = None,
        max_concurrent_tools: int = 1,
        fallback_order: Optional[List[str]] = None,
        provider: str = "custom_json",
        round_compress_threshold: Optional[int] = None,
        round_compress_keep_tail: int = 6,
    ):
        """
        初始化Agent，绑定LLM处理器、系统提示词和可选工具列表。
        TODO: 再这么下去这傻逼东西迟早会成为一个超级类，可能不能再这么下去了。

        Args:
            llm_handler: LLM fetcher instance
            system_prompt: Base system prompt
            tools: Initial tools to register
            max_concurrent_tools: Max parallel tool executions
                                  TODO: 设置为-1，以无限制并行工具。
            fallback_order: Backend fallback order
            provider: LLM provider for tool calling. 
                     Options: "openai", "anthropic", "custom_json"
            round_compress_threshold: Auto-compress temporary in-round messages when
                                      their count reaches this value. None or not set will disables it.

            round_compress_keep_tail: Number of latest in-round messages to keep verbatim.
        """
        self._base_system_prompt: str = system_prompt   # 系统提示词。
        self.memory_list: List[str] = []    # 记忆，该内容不会被上下文管理器干扰。
        self.llm_handler = llm_handler  # 用于处理 llm api 通信相关的东西。
        self.llm_context_handler = LLMContextHandler(llm_handler=self.llm_handler)  # 上下文管理器。
        self.tool_registry = ToolRegistry() # 注册工具。
        self.max_concurrent_tools = max_concurrent_tools    # 本 agent 最大可并发多少工具。
        self.fallback_order = fallback_order
        self.provider = provider  # ← 保存 provider 设置
        self.round_compress_threshold = round_compress_threshold
        self.round_compress_keep_tail = round_compress_keep_tail
        self._round_summary_prefix = "Round context abstract as: "  # 这个可能要直接删掉。

        # 注册内嵌工具（round_end 等），供 LLM 控制轮次生命周期
        self._register_builtin_tools()  # 现在这里只有一个 turn end……我可能需要将结束回合的东西单独从工具里摘出来。

        # 如果有工具，则对本内容注册工具。
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
        """
        Dynamic system prompt enriched with tool descriptions.
        该函数会拼装系统提示词，和工具提示词。
        """
        prompt: str = self._base_system_prompt
        hint: Optional[str] = self.tool_registry.get_prompt_hint()  # 获取所有工具提示。
        if hint:
            prompt = f"{prompt}\n{hint}"    # 拼接提示，随后返回数据。
        return prompt

    def update_system_prompt(self, new_prompt: str) -> None:
        """运行时动态修改 Agent 的系统提示词。"""
        self._base_system_prompt = new_prompt

    def add_tool(self, tool: "Tool") -> None:
        """运行时给 Agent 增加一个工具。"""
        self.tool_registry.register(tool)

    def remove_tool(self, tool_name: str) -> None:
        """在运行期间，从本 Agent 的工具注册表内，移除一个命名工具。"""
        self.tool_registry.unregister(tool_name)

    # ------------------------------------------------------------------
    # 上下文管理接口
    # ------------------------------------------------------------------

    async def add_context(self, msg: LLMContext) -> None:
        """
        增加上下文内容。
        """
        await self.llm_context_handler.add_context(msg)

    async def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        获取完整的对话历史。
        异步，等待当前上下文内容。
        
        Returns:
            List of message dicts with 'role' and 'content' keys.
        """
        return await self.llm_context_handler.get_now_context()

    async def get_conversation_summary(self) -> str:
        """
        获取格式化的对话摘要。
        
        Returns:
            Human-readable conversation summary string.
        """
        return await self.llm_context_handler.get_now_context_as_single_str()

    async def compress_history(self, selective_ids: Optional[List[int]] = None) -> bool:
        """
        压缩对话历史以节省 token。
        
        Args:
            selective_ids: Optional list of context IDs to compress. 
                          If None, compresses all history.
            
        Returns:
            True if compression succeeded, False if no history to compress.
        """
        return await self.llm_context_handler.compress_context(selective_ids)

    async def create_memory(self, context_ids: List[int]) -> Optional[str]:
        """
        从特定对话中提取关键信息作为永久记忆。
        本函数会调用上下文管理器实例，创建新的记忆。
        
        Args:
            context_ids: List of context IDs to summarize into memory.
            
        Returns:
            Memory summary string, or None if extraction failed.
        """
        memory = await self.llm_context_handler.generate_memory(context_ids)
        if memory:
            self.memory_list.append(memory)
        return memory

    def get_memories(self) -> List[str]:
        """
        获取所有已存储的记忆。

        Returns:
            List of memory summary strings.
        """
        return self.memory_list.copy()

    def clear_memories(self) -> None:
        """
        清除所有记忆。
        """
        self.memory_list.clear()

    def get_context_count(self) -> int:
        """
        获取存储的上下文条目数量。
        
        Returns:
            Number of conversation rounds stored.
        """
        return len(self.llm_context_handler.context_dict)

    async def get_context_by_ids(self, ids: List[int]) -> List:
        """
        Retrieve specific context entries by their IDs.
        根据ID检索特定的上下文条目。
        
        Args:
            ids: List of context IDs to retrieve.
            
        Returns:
            List of LLMInfo objects (LLMContextPair or LLMContextCompressed).
        """
        return await self.llm_context_handler.get_context_by_id(ids)

    async def run_agent_round(
        self,
        msg: str,
        stream: bool = False,
        verbose_info: bool = False,
        max_turns: int = 3,
    ) -> str:
        """
        进行一整个轮次的 Agent 执行轮。

        核心特性：
        - 多轮工具调用循环：LLM 可在一次 agent 轮内连续调用多个工具，
          拿到结果后继续思考，直到决定结束。
        - 保留每轮 content：assistant 的原始回复与工具 JSON 都会保留。
        - round_end：LLM 可通过 JSON tool call 主动结束本轮。
        - 并行执行：当 max_concurrent_tools > 1 时，同一轮内的多个工具调用会并发执行。
        - 支持多种 LLM provider（OpenAI, Anthropic, custom JSON）

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
        
        # 获取 provider-specific tool schemas
        tool_schemas = self.tool_registry.get_schemas_for_provider(self.provider)

        turn: int
        for turn in range(1, max_turns + 1):

            # 
            messages = await self._maybe_compress_round_messages(
                messages,
                verbose_info=verbose_info,
            )

            if verbose_info:
                print(f"\n[Agent] ====== Executing Turn: {turn} ======")
                print(f"[Agent] Provider: {self.provider}")
                print(f"[Agent] Tool schemas count: {len(tool_schemas)}")

            # ---- 调用 LLM - 这里采用异步执行 ----
            response: ChatCompletion = await self.llm_handler.fetch(
                msg="",
                system_prompt=None,
                prev_messages=messages,
                tools=tool_schemas if tool_schemas else None,  # 传递工具信息
                fallback_order=self.fallback_order,
            )
            
            # 解析工具调用（根据 provider 使用不同的解析方式）
            from .tool_call_adapter import normalize_tool_calls, ToolCallSource
            
            if self.provider == "openai":
                # OpenAI: response.choices[0].message.content / .tool_calls
                agent_message = self._extract_openai_message(response)
                content = self._extract_openai_content(response)
                normalized_calls = normalize_tool_calls(
                    response,
                    source=ToolCallSource.OPENAI_NATIVE,
                )

            elif self.provider == "anthropic":
                # Anthropic: response.content = [text/tool_use/... blocks]
                agent_message = self._extract_anthropic_message(response)
                content = self._extract_anthropic_content(response)
                normalized_calls = normalize_tool_calls(
                    response,
                    source=ToolCallSource.ANTHROPIC,
                )

            else:
                # Fallback to custom JSON parsing
                message: ChatCompletionMessage = response.choices[0].message
                content: str = message.content or ""
                agent_message = AgentMessage(
                    provider=self.provider,
                    role=getattr(message, "role", "assistant") or "assistant",
                    content=content,
                    raw_message=message,
                    raw_response=response,
                )
                normalized_calls = normalize_tool_calls(
                    response,
                    source=ToolCallSource.CUSTOM_JSON,
                    fallback_parser=self._parse_json_tool_calls
                )
            
            # Convert to legacy format for backward compatibility
            tool_calls: List[Dict[str, Any]] = [
                tc.to_execution_format() for tc in normalized_calls
            ]

            # 然后显示原始文本
            if verbose_info:
                print("-=-=-=-=-=-=- Model Output Diagnosis -=-=-=-=-=-=-")
                print(f"provider={agent_message.provider}")
                print(f"role={agent_message.role}")
                print(f"stop_reason={agent_message.stop_reason}")
                print(f"content={agent_message.content!r}")
                print(f"reasoning_content={agent_message.reasoning_content!r}")
                print(f"tool_blocks={len(agent_message.tool_blocks)}")
                print(f"parsed_tool_calls={len(tool_calls)}")
                print(f"token_usage={self._format_token_usage(response)}")
                print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
            
            # Extract content for display (handle both OpenAI and Anthropic formats)
            # 在这里会读取到可能来自两种格式的东西
            content = ""
            if hasattr(response, 'choices'):
                # OpenAI format
                message = response.choices[0].message
                content = message.content or ""
            elif hasattr(response, 'content'):
                # Anthropic format - extract text content
                if response.content:
                    # Get text from content blocks
                    text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
                    content = " ".join(text_blocks) if text_blocks else ""
            
            last_turn_content = content

            if verbose_info:
                print(f"[Agent] Provider: {self.provider}")
                print(f"[Agent] Tool calls count: {len(tool_calls)}")
                if tool_calls:
                    for tc in tool_calls:
                        print(f"  - {tc['tool']}: {tc['arguments']}")
                elif not content.strip():
                    print("[Agent] Warning: No tool calls and no content received!")

            # ---- 情况 A：无工具调用 ----
            if not tool_calls:
                if not content.strip():
                    # 空白输出时直接报错。
                    if verbose_info:
                        print("[Agent] ERROR: No tool calls and no content received.")
                    raise EmptyModelResponseError(
                        "LLM returned no tool calls and no content. "
                        "Treating as provider/parser failure."
                    )

                # 有文本但没有工具调用：不能当 final，除非你显式允许纯文本模式
                messages.append(self._format_assistant_message(content))
                messages.append({
                    "role": "system",
                    "content": (
                        "No tool call was made. For this task, tool usage is mandatory. "
                        "Call a tool now. If you cannot proceed, call round_end with an explicit failure reason."
                    ),
                })

                if verbose_info:
                    print("[Agent] Context with tool call detected. Demanding for next round.")

                # 保存上下文，然后继续。

                self.save_cone
                continue
            
            # ---- 情况 B：有工具调用，执行工具并继续下一轮 ----
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
            # 达到 max_turns，直接报错。
            raise MaxTurnsExceededError(
                f"Agent reached max_turns={max_turns} without round_end or valid final result."
            )

        # ---- 保存上下文 ----
        assistant_saved_content = final_content or last_turn_content

        if not assistant_saved_content.strip():
            raise EmptyModelResponseError(
                "round_call ended with empty assistant content. Refusing to save empty context."
            )

        await self.llm_context_handler.add_context(
            LLMContextPair(
                LLMContext(role="user", content=msg),
                LLMContext(role="assistant", content=assistant_saved_content),
            )
        )

        # ---- 自动压缩检查，你还是别再这里压更好，必须在每一个 round 轮内进行压缩。 ----

        return assistant_saved_content

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    async def _maybe_compress_round_messages(
        self,
        messages: Messages,
        verbose_info: bool = False,
    ) -> Messages:
        """
        Compress temporary messages inside one agent round when configured.
        不是哥们，就用这个函数来压缩上下文？？
        TODO: 我可能需要删掉这个函数，将上下文管理器放在里面。

        Args:
            messages: 等待压缩的信息。
            verbose_info: 是否正式输出内容。
        """

        # 如果没有上下文压缩阈值，或未达到阈值，则直接返回原始信息。
        if self.round_compress_threshold is None:
            return messages
        if len(messages) < self.round_compress_threshold:
            return messages

        # 这个……
        keep_tail = max(1, self.round_compress_keep_tail)
        system_messages: Messages = []
        body_messages: Messages = []

        # 对于每一组原始信息，将其区分为系统信息和（语义不详）
        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            if role == "system" and not content.startswith(self._round_summary_prefix):
                system_messages.append(message)
            else:
                body_messages.append(message)

        if len(body_messages) <= keep_tail:
            return messages

        messages_to_compress = body_messages[:-keep_tail]
        tail_messages = body_messages[-keep_tail:]
        text = self._format_messages_for_summary(messages_to_compress)
        if not text.strip():
            return messages

        prompt = (
            "请压缩以下 Agent 本轮内部上下文。"
            "保留用户目标、已经执行的工具调用、关键工具结果、失败信息、"
            "约束条件，以及下一步必须继续依据的状态。"
            "不要编造不存在的工具结果。\n\n"
            f"{text}"
        )

        response = await self.llm_handler.fetch(
            msg=prompt,
            fallback_order=self.fallback_order,
        )
        summary = self._extract_response_text(response).strip()
        if not summary:
            return messages

        compressed_message: MessageDict = {
            "role": "system",
            "content": f"{self._round_summary_prefix}\n{summary}",
        }

        if verbose_info:
            print(
                "[Agent] 已压缩本轮临时上下文: "
                f"{len(messages_to_compress)} 条 -> 1 条摘要，保留最近 {len(tail_messages)} 条"
            )

        return system_messages + [compressed_message] + tail_messages

    def _format_messages_for_summary(self, messages: Messages) -> str:
        """Render chat messages as compact text for compression prompts."""
        lines: List[str] = []
        for message in messages:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            lines.append(f"[{role}]: {content}")
        return "\n".join(lines)

    def _extract_response_text(self, response: Any) -> str:
        """Extract plain text from supported LLM response shapes."""
        if hasattr(response, "choices") and response.choices:
            message = getattr(response.choices[0], "message", None)
            if message is not None:
                return self._coerce_content_to_text(getattr(message, "content", None))

        blocks = getattr(response, "content", None)
        if blocks:
            parts: List[str] = []
            for block in blocks:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        parts.append(str(block.get("text", "")))
                    elif "text" in block:
                        parts.append(str(block["text"]))
                else:
                    text = getattr(block, "text", None)
                    if text:
                        parts.append(str(text))
            return "".join(parts)

        return ""

    def _format_token_usage(self, response: Any) -> str:
        """Return a compact token usage string for verbose diagnostics."""
        usage = self._get_usage_payload(response)
        if usage is None:
            return "unavailable"

        input_tokens = self._get_usage_value(
            usage,
            "prompt_tokens",
            "input_tokens",
        )
        output_tokens = self._get_usage_value(
            usage,
            "completion_tokens",
            "output_tokens",
        )
        total_tokens = self._get_usage_value(usage, "total_tokens")

        parts: List[str] = []
        if input_tokens is not None:
            parts.append(f"input={input_tokens}")
        if output_tokens is not None:
            parts.append(f"output={output_tokens}")
        if total_tokens is not None:
            parts.append(f"total={total_tokens}")
        elif input_tokens is not None and output_tokens is not None:
            parts.append(f"total={input_tokens + output_tokens}")

        return ", ".join(parts) if parts else "unavailable"

    def _get_usage_payload(self, response: Any) -> Optional[Any]:
        """Extract usage payload from SDK object or dict responses."""
        if isinstance(response, dict):
            return response.get("usage")
        return getattr(response, "usage", None)

    def _get_usage_value(self, usage: Any, *names: str) -> Optional[int]:
        """Read the first matching integer token field from a usage payload."""
        for name in names:
            if isinstance(usage, dict):
                value = usage.get(name)
            else:
                value = getattr(usage, name, None)

            if value is None:
                continue

            try:
                return int(value)
            except (TypeError, ValueError):
                continue

        return None

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
            # Try multiple extraction strategies
            payload = self._extract_json_fragment(text)
            if payload is None:
                # Last resort: try to find JSON with relaxed parsing
                payload = self._relaxed_json_extract(text)
                if payload is None:
                    print(f"[Agent] Warning: Failed to parse JSON from content: {text[:200]}")
                    return []

        if isinstance(payload, dict):
            if "tool_calls" in payload and isinstance(payload["tool_calls"], list):
                return [tc for tc in payload["tool_calls"] if self._is_valid_tool_call(tc)]
            if self._is_valid_tool_call(payload):
                return [payload]
        if isinstance(payload, list):
            return [tc for tc in payload if self._is_valid_tool_call(tc)]
        return []

    def _relaxed_json_extract(self, text: str) -> Optional[Any]:
        """Attempt to extract JSON using multiple fallback strategies."""
        import re
        
        # Strategy 1: Find JSON-like patterns with regex
        json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                payload = json.loads(match)
                if self._is_valid_tool_call(payload):
                    return payload
            except json.JSONDecodeError:
                continue
        
        # Strategy 2: Look for array of tool calls
        array_pattern = r'\[[^\[\]]*\{"tool"[^\[\]]*\}\]'
        matches = re.findall(array_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                payload = json.loads(match)
                if isinstance(payload, list):
                    valid_calls = [tc for tc in payload if self._is_valid_tool_call(tc)]
                    if valid_calls:
                        return payload
            except json.JSONDecodeError:
                continue
        
        return None

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

    def _get_openai_message(self, response: Any) -> Any:
        """Extract OpenAI ChatCompletion message."""
        if not hasattr(response, "choices") or not response.choices:
            raise EmptyModelResponseError("OpenAI response has no choices.")

        choice = response.choices[0]
        message = getattr(choice, "message", None)
        if message is None:
            raise EmptyModelResponseError("OpenAI response choice has no message.")

        return message

    def _extract_openai_message(self, response: Any) -> AgentMessage:
        if not hasattr(response, "choices") or not response.choices:
            raise EmptyModelResponseError("OpenAI response has no choices.")

        choice = response.choices[0]
        message = getattr(choice, "message", None)
        if message is None:
            raise EmptyModelResponseError("OpenAI response choice has no message.")

        raw_content = getattr(message, "content", None)
        content = self._coerce_content_to_text(raw_content)

        reasoning_content = getattr(message, "reasoning_content", None) or ""

        tool_calls = getattr(message, "tool_calls", None) or []

        return AgentMessage(
            provider="openai",
            role=getattr(message, "role", "assistant") or "assistant",
            content=content,
            reasoning_content=reasoning_content,
            raw_message=message,
            raw_response=response,
            tool_blocks=list(tool_calls),
            stop_reason=getattr(choice, "finish_reason", None),
        )
    
    def _extract_anthropic_message(self, response: Any) -> AgentMessage:
        blocks = getattr(response, "content", None) or []

        text_parts = []
        tool_blocks = []

        for block in blocks:
            block_type = getattr(block, "type", None)

            # SDK object style
            if block_type == "text":
                text = getattr(block, "text", "")
                if text:
                    text_parts.append(str(text))

            elif block_type == "tool_use":
                tool_blocks.append(block)

            # dict style fallback
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    text_parts.append(str(block.get("text", "")))
                elif block.get("type") == "tool_use":
                    tool_blocks.append(block)

        return AgentMessage(
            provider="anthropic",
            role="assistant",
            content="".join(text_parts),
            raw_message=response,      # Anthropic 没有 choices[0].message，就把 response 当 raw_message
            raw_response=response,
            tool_blocks=tool_blocks,
            stop_reason=getattr(response, "stop_reason", None),
        )
            
    def _extract_openai_content(self, response: Any) -> str:
        """Extract assistant text from OpenAI ChatCompletion response."""
        message = self._get_openai_message(response)
        content = getattr(message, "content", None)

        if content is None:
            return ""

        # Most Chat Completions responses use str.
        if isinstance(content, str):
            return content

        # Some compatible providers may return content parts.
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        parts.append(str(part.get("text", "")))
                    elif "text" in part:
                        parts.append(str(part["text"]))
                else:
                    text = getattr(part, "text", None)
                    if text:
                        parts.append(str(text))
            return "".join(parts)

        return str(content)
    def _extract_anthropic_content(self, response: Any) -> str:
        """Extract assistant text from Anthropic Messages response."""
        blocks = getattr(response, "content", None)
        if not blocks:
            return ""

        parts = []
        for block in blocks:
            # SDK object style: block.type, block.text
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text = getattr(block, "text", "")
                if text:
                    parts.append(str(text))

            # Dict style, if your fetcher returns dicts
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))

        return "".join(parts)
    
    def _coerce_content_to_text(self, content: str | list | Any) -> str:
        """Convert provider-specific message content into plain text."""
        if content is None:
            return ""

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: List[str] = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        parts.append(str(part.get("text", "")))
                    elif "text" in part:
                        parts.append(str(part["text"]))
                else:
                    text = getattr(part, "text", None)
                    if text:
                        parts.append(str(text))
            return "".join(parts)

        return str(content)

    async def _build_round_messages(self, msg: str) -> Messages:
        """
        构建本轮的初始消息列表（system + 历史 + user msg）。
        每当执行一次 run_agent_round 函数时，该函数会被调用一次。
        """
        prev: Messages = await self.llm_context_handler.get_now_context()   # 获取当前上下文
        messages: Messages = []
        if self.system_prompt:  # 加入系统提示，注意这里有个 property 装饰其
            messages.append({"role": "system", "content": self.system_prompt})

        messages.extend(prev)   # 加入上一轮信息
        if msg:  # ← 只在msg非空时添加
            messages.append({"role": "user", "content": msg})   # 加入用户输入
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
        """
        执行一个工具。
        工具执行结果需要直接返回。
        傻逼LLM又在这给我整烂活，气煞我也🤬

        Args:
            tool_call: 一个 tool call 方法。
            verbose: 显示 tool call 信息。
        """
        tool_name: str = str(tool_call["tool"])
        args: ToolArgs = dict(tool_call.get("arguments") or {})

        if verbose:
            print(f"[Agent] Calling tool {tool_name} with param: {json.dumps(args, ensure_ascii=False)}")

        if tool_name == "round_end":
            result: str = "Round ended."
        else:
            try:
                result = await self.tool_registry.execute(tool_name, args)
            except Exception as exc:
                result = f"Error: {exc}"

        if verbose:
            print(f"[Agent] Result of tool {tool_name} as: \n{str(result)}")

        return str(result)
