"""多后端 LLM 请求路由与流式输出管理模块。

本模块封装对 OpenAI、LiteLLM 等后端服务的统一调用接口，
支持 fallback 自动切换、流式增量提取（含 reasoning 内容）、
超时重试以及限流器集成。

主要导出内容：
    - :class:`LLMContext`: 单条对话消息。
    - :class:`LLMBackendConfig`: 单个后端配置。
    - :class:`LLMError`: 基础异常。
    - :class:`LLMTimeoutError`: 超时异常。
    - :class:`LLMBackendError`: 所有后端均失败异常。
    - :class:`LLMFetcher`: 请求路由管理器。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported only for static analysis
    from openai import OpenAI
    from openai.types.chat import ChatCompletion


@dataclass
class LLMContext:
    """One chat message carried into a backend request."""

    role: str
    content: str


@dataclass
class LLMBackendConfig:
    """Configuration for one routable LLM backend."""

    name: str
    provider: str
    model: str
    api_key: str
    api_url: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


class LLMError(RuntimeError):
    """Base error for LLM backends."""


class LLMTimeoutError(LLMError, TimeoutError):
    """Raised when the selected LLM backend times out."""


class LLMBackendError(LLMError):
    """Raised when every configured backend fails."""


class LLMFetcher:
    """Route chat requests across one or more configured LLM backends."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        *,
        provider: str = "openai",
        timeout: float = 60.0,
        backends: Optional[Sequence[LLMBackendConfig]] = None,
        default_backend: Optional[str] = None,
        limiter: Optional[Any] = None,
    ) -> None:
        """初始化 LLM 管理器。

        支持两种构造方式：

        1. 兼容旧接口，直接传入 `api_url`、`api_key`、`model`
        2. 传入多个 `LLMBackendConfig`，构造带路由与回退能力的多后端管理器

        Args:
            api_url: 旧接口模式下的模型服务地址。
            api_key: 旧接口模式下的 API 密钥。
            model: 旧接口模式下的模型名称。
            provider: 旧接口模式下使用的提供方类型。
            timeout: 旧接口模式下的默认超时时间，单位为秒。
            backends: 多后端模式下的后端配置列表。
            default_backend: 多后端模式下的默认后端名称。
            limiter: 可选的并发限流器，用于控制 LLM 请求速率。

        Raises:
            ValueError: 当没有提供有效的构造参数，或默认后端名称不存在时抛出。
        """
        self.backends: Dict[str, LLMBackendConfig] = {}
        self.backend_order: List[str] = []
        self.openai_clients: Dict[str, Any] = {}
        self.anthropic_clients: Dict[str, Any] = {}  # ← 新增：Anthropic 客户端字典

        if backends:
            for backend in backends:
                self._register_backend(backend)
        elif api_key and model:
            self._register_backend(
                LLMBackendConfig(
                    name="default",
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    api_url=api_url,
                    timeout=timeout,
                )
            )
        else:
            raise ValueError("Either pass backends or the legacy api_url/api_key/model arguments.")

        if default_backend is not None:
            if default_backend not in self.backends:
                raise ValueError(f"Unknown default backend: {default_backend}")
            self.default_backend = default_backend
        else:
            self.default_backend = self.backend_order[0]

        self.limiter = limiter

    def _register_backend(self, backend: LLMBackendConfig) -> None:
        """注册单个后端，并在需要时预创建客户端。

        Args:
            backend: 要注册的后端配置。

        Raises:
            ValueError: 当后端名称重复时抛出。
        """
        if backend.name in self.backends:
            raise ValueError(f"Duplicate backend name: {backend.name}")
        self.backends[backend.name] = backend
        self.backend_order.append(backend.name)
        
        if backend.provider == "openai":
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover - depends on optional package
                raise ValueError("openai provider requires the 'openai' package to be installed.") from exc
            self.openai_clients[backend.name] = OpenAI(
                api_key=backend.api_key,
                base_url=backend.api_url,
                max_retries=backend.max_retries,
            )
        
        elif backend.provider == "anthropic":
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - depends on optional package
                raise ValueError("anthropic provider requires the 'anthropic' package to be installed.") from exc
            
            # Create Anthropic client with optional base_url (for DeepSeek compatibility)
            client_kwargs = {
                "api_key": backend.api_key,
                "timeout": backend.timeout,
            }
            
            # If api_url is specified, use it as base_url (for DeepSeek, etc.)
            if backend.api_url:
                client_kwargs["base_url"] = backend.api_url
            
            self.anthropic_clients[backend.name] = anthropic.Anthropic(**client_kwargs)

    def _resolve_backends(
        self,
        backend_name: Optional[str],
        fallback_order: Optional[Sequence[str]],
    ) -> List[LLMBackendConfig]:
        """解析一次请求应使用的后端顺序。

        Args:
            backend_name: 显式指定的单个后端名称。
            fallback_order: 额外指定的回退后端顺序。

        Returns:
            按请求顺序排列的后端配置列表。

        Raises:
            ValueError: 当显式指定的后端名称不存在时抛出。
        """
        if backend_name:
            if backend_name not in self.backends:
                raise ValueError(f"Unknown backend: {backend_name}")
            names = [backend_name]
        else:
            names = [self.default_backend]
            if fallback_order:
                names.extend(fallback_order)
            names.extend(name for name in self.backend_order if name not in names)
        return [self.backends[name] for name in names]

    def _build_messages(
        self,
        msg: str,
        prev_messages: Optional[List[Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """构造发送给后端的消息列表。

        Args:
            msg: 当前轮用户输入。
            prev_messages: 需要拼接的历史上下文。
            system_prompt: 当前请求使用的系统提示词。

        Returns:
            符合聊天接口格式的消息列表。
        """
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if prev_messages:
            for item in prev_messages:
                if isinstance(item, dict):
                    role = str(item.get("role", ""))
                    content = str(item.get("content", ""))
                else:
                    role = str(getattr(item, "role", ""))
                    content = str(getattr(item, "content", ""))
                if not role:
                    continue
                messages.append({"role": role, "content": content})
        
        # Only append user message if msg is non-empty OR there are no previous messages
        # This prevents adding empty user messages which can confuse the LLM
        if msg or not prev_messages:
            messages.append({"role": "user", "content": msg})
        
        return messages

    def _convert_to_anthropic_messages(
        self,
        messages: List[Dict[str, str]]
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Convert OpenAI-style messages to Anthropic format.
        
        Anthropic has some key differences:
        - No "system" role (use system parameter instead)
        - Tool results use different format
        - Content can be mixed (text + tool_use/tool_result)
        
        Args:
            messages: OpenAI-format message list
            
        Returns:
            Tuple of (Anthropic-format message list, system prompt string)
        """
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                # Anthropic doesn't have system role in messages
                # Store it separately (will be passed as system parameter)
                system_message = content
                continue
            
            elif role == "tool":
                # Convert tool result to Anthropic format
                tool_call_id = msg.get("tool_call_id", "")
                anthropic_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call_id,
                            "content": content
                        }
                    ]
                })
            
            else:
                # user or assistant messages
                anthropic_messages.append({
                    "role": role,
                    "content": content
                })
        
        return anthropic_messages, system_message

    def _convert_to_anthropic_tools(
        self,
        tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert OpenAI-style tool schemas to Anthropic format.
        
        OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "...",
                "description": "...",
                "parameters": {...}
            }
        }
        
        Anthropic format:
        {
            "name": "...",
            "description": "...",
            "input_schema": {...}
        }
        
        Args:
            tools: OpenAI-format tool schemas
            
        Returns:
            Anthropic-format tool schemas
        """
        anthropic_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {})
                })
            else:
                # Already in Anthropic format or unknown format
                anthropic_tools.append(tool)
        
        return anthropic_tools

    def _create_completion(
        self,
        backend: LLMBackendConfig,
        *,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """向具体后端发起补全请求。

        Args:
            backend: 当前要调用的后端配置。
            messages: 已整理好的消息列表。
            temperature: 采样温度。
            max_tokens: 最大输出 token 数。
            stream: 是否启用流式返回。
            tools: 可选的工具 schema 列表（OpenAI 或 Anthropic 格式）。

        Returns:
            后端 SDK 返回的原始响应对象或流式迭代器。

        Raises:
            ValueError: 当提供方类型不受支持时抛出。
        """
        if backend.provider == "openai":
            client = self.openai_clients[backend.name]
            kwargs: Dict[str, Any] = {
                "model": backend.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
                "timeout": backend.timeout,
            }
            if tools:
                # OpenAI 要求 tools 与 tool_choice 成对出现，仅在传入 tools 时补充 tool_choice
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            kwargs.update(backend.extra)
            return client.chat.completions.create(**kwargs)

        elif backend.provider == "anthropic":
            client = self.anthropic_clients[backend.name]
            
            # Anthropic 使用不同的消息格式和参数
            # 需要将 OpenAI 格式的消息转换为 Anthropic 格式
            anthropic_messages, system_prompt = self._convert_to_anthropic_messages(messages)
            
            kwargs: Dict[str, Any] = {
                "model": backend.model,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
            }
            
            # Anthropic 支持 system prompt 作为单独参数
            if system_prompt:
                kwargs["system"] = system_prompt
            
            # Anthropic 的工具格式不同
            if tools:
                # 转换工具 schema 为 Anthropic 格式
                anthropic_tools = self._convert_to_anthropic_tools(tools)
                kwargs["tools"] = anthropic_tools
            
            kwargs.update(backend.extra)
            
            return client.messages.create(**kwargs)

        if backend.provider == "litellm":
            try:
                from litellm import completion as litellm_completion
            except ImportError as exc:  # pragma: no cover - depends on optional package
                raise ValueError(
                    "litellm provider requires the 'litellm' package to be installed."
                ) from exc
            kwargs: Dict[str, Any] = {
                "model": backend.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
                "timeout": backend.timeout,
                "api_key": backend.api_key,
            }
            if backend.api_url:
                kwargs["api_base"] = backend.api_url
            kwargs.update(backend.extra)
            return litellm_completion(**kwargs)

        raise ValueError(f"Unsupported provider: {backend.provider}")

    def _normalize_exception(self, backend: LLMBackendConfig, exc: Exception) -> LLMError:
        """将提供方异常映射为本地统一异常。

        Args:
            backend: 发生错误的后端配置。
            exc: 原始异常对象。

        Returns:
            统一后的本地异常实例。
        """
        message = f"Backend '{backend.name}' ({backend.provider}) failed: {exc}"
        if isinstance(exc, TimeoutError) or isinstance(exc, asyncio.TimeoutError):
            return LLMTimeoutError(message)
        if "timeout" in str(exc).lower():
            return LLMTimeoutError(message)
        return LLMError(message)

    def _timeout_retry_count(self, backend: LLMBackendConfig) -> int:
        """计算某个后端在超时场景下允许的重试次数。

        将配置中的 ``max_retries`` 转换为至少一次尝试的整数。

        Args:
            backend: 目标后端配置。

        Returns:
            int: 该后端在超时失败时允许的重试次数（至少为 1）。
        """
        return max(1, int(backend.max_retries))

    def _extract_content(self, delta: Any) -> Optional[str]:
        """从流式增量中提取正文内容。

        Args:
            delta: SDK 对象或字典形式的增量数据。

        Returns:
            提取出的正文内容；若不存在则返回 `None`。
        """
        if delta is None:
            return None
        if isinstance(delta, dict):
            return delta.get("content")
        return getattr(delta, "content", None)

    def _extract_reasoning(self, delta: Any) -> Optional[str]:
        """从流式增量中提取推理内容。

        Args:
            delta: SDK 对象或字典形式的增量数据。

        Returns:
            提取出的推理内容；若不存在则返回 `None`。
        """
        if delta is None:
            return None
        if isinstance(delta, dict):
            return delta.get("reasoning_content") or delta.get("reasoning")
        return getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)

    def _iter_stream_text(
        self,
        response: Iterable[Any],
        *,
        output_reasoning: bool,
    ) -> Iterable[str]:
        """将流式响应标准化为文本片段。

        Args:
            response: 后端返回的流式响应迭代器。
            output_reasoning: 是否输出推理内容标记与文本。

        Yields:
            标准化后的文本片段。
        """
        # 维护 thinking 状态机，用于在 reasoning 内容与正文之间插入分界标记
        in_thinking = False
        for chunk in response:
            choices = getattr(chunk, "choices", None)
            if not choices and isinstance(chunk, dict):
                choices = chunk.get("choices")
            if not choices:
                continue

            delta = getattr(choices[0], "delta", None)
            if delta is None and isinstance(choices[0], dict):
                delta = choices[0].get("delta")

            reasoning = self._extract_reasoning(delta)
            if reasoning and output_reasoning:
                if not in_thinking:
                    yield "\n<<<THINKING>>>\n"
                    in_thinking = True
                yield reasoning

            content = self._extract_content(delta)
            if content:
                if in_thinking:
                    yield "\n<<<THINK_END>>>\n"
                    in_thinking = False
                yield content

        if in_thinking:
            yield "\n<<<THINK_END>>>\n"

    async def fetch(
        self,
        msg: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        prev_messages: Optional[List[LLMContext]] = None,
        backend_name: Optional[str] = None,
        fallback_order: Optional[Sequence[str]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """执行一次非流式请求，并按顺序尝试后端回退。

        Args:
            msg: 当前轮用户输入。
            system_prompt: 当前请求使用的系统提示词。
            temperature: 采样温度。
            max_tokens: 最大输出 token 数。
            prev_messages: 历史上下文。
            backend_name: 显式指定的后端名称。
            fallback_order: 额外指定的回退后端顺序。
            tools: 可选的 OpenAI tools schema 列表。

        Returns:
            后端 SDK 返回的原始补全响应对象。

        Raises:
            LLMBackendError: 当所有候选后端均调用失败时抛出。
        """
        messages = self._build_messages(msg, prev_messages=prev_messages, system_prompt=system_prompt)
        backend_errors: List[str] = []

        if self.limiter:
            await self.limiter.acquire_llm()
        try:
            for backend in self._resolve_backends(backend_name, fallback_order):
                retries_left = self._timeout_retry_count(backend)
                while True:
                    try:
                        return await asyncio.to_thread(
                            self._create_completion,
                            backend,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=False,
                            tools=tools,
                        )
                    except Exception as exc:
                        normalized = self._normalize_exception(backend, exc)
                        if isinstance(normalized, LLMTimeoutError) and retries_left > 0:
                            retries_left -= 1
                            # 采用指数退避思想，但将单次等待上限限制在 1.5 秒，避免高频重试拖慢整体响应
                            await asyncio.sleep(min(1.5, 0.25 * (self._timeout_retry_count(backend) - retries_left)))
                            continue
                        backend_errors.append(str(normalized))
                        break

            raise LLMBackendError("; ".join(backend_errors))
        finally:
            if self.limiter:
                self.limiter.release_llm()

    async def fetch_stream(
        self,
        msg: str,
        prev_messages: Optional[List[LLMContext]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        output_reasoning: bool = False,
        backend_name: Optional[str] = None,
        fallback_order: Optional[Sequence[str]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[str, None]:
        """执行一次流式请求，并按顺序尝试后端回退。

        Args:
            msg: 当前轮用户输入。
            prev_messages: 历史上下文。
            system_prompt: 当前请求使用的系统提示词。
            temperature: 采样温度。
            max_tokens: 最大输出 token 数。
            output_reasoning: 是否输出推理内容。
            backend_name: 显式指定的后端名称。
            fallback_order: 额外指定的回退后端顺序。
            tools: 可选的 OpenAI tools schema 列表。

        Yields:
            标准化后的流式文本片段。

        Raises:
            LLMBackendError: 当所有候选后端均调用失败时抛出。
            LLMError: 当流已经部分输出后，当前后端又发生异常时抛出。
        """
        messages = self._build_messages(msg, prev_messages=prev_messages, system_prompt=system_prompt)
        backend_errors: List[str] = []

        if self.limiter:
            await self.limiter.acquire_llm()
        try:
            for backend in self._resolve_backends(backend_name, fallback_order):
                retries_left = self._timeout_retry_count(backend)
                while True:
                    yielded_any = False
                    try:
                        response = self._create_completion(
                            backend,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=True,
                            tools=tools,
                        )
                        for text in self._iter_stream_text(response, output_reasoning=output_reasoning):
                            yielded_any = True
                            yield text
                        return
                    except Exception as exc:
                        normalized_error = self._normalize_exception(backend, exc)
                        if isinstance(normalized_error, LLMTimeoutError) and not yielded_any and retries_left > 0:
                            retries_left -= 1
                            # 采用指数退避思想，但将单次等待上限限制在 1.5 秒，避免高频重试拖慢整体响应
                            await asyncio.sleep(min(1.5, 0.25 * (self._timeout_retry_count(backend) - retries_left)))
                            continue
                        if yielded_any:
                            raise normalized_error
                        backend_errors.append(str(normalized_error))
                        break

            raise LLMBackendError("; ".join(backend_errors))
        finally:
            if self.limiter:
                self.limiter.release_llm()


async def chat_test() -> None:
    """执行本地后端接线的手工冒烟测试。"""
    llm = LLMFetcher(
        backends=[
            LLMBackendConfig(
                name="deepseek-primary",
                provider="openai",
                api_url="https://api.deepseek.com",
                api_key="sk-replace-me",
                model="deepseek-reasoner",
                timeout=60.0,
            )
        ]
    )

    async for chunk in llm.fetch_stream(
        msg="给我一段用于调试流式输出的样例文本。",
        system_prompt="你是一个简洁的调试助手。",
        temperature=0.7,
        max_tokens=512,
        output_reasoning=True,
    ):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(chat_test())
    except KeyboardInterrupt:
        print("== exit ==")
