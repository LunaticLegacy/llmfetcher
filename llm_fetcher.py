"""平台无关的 LLM 调度器。

本模块只负责后端注册、fallback 顺序、重试、限流与统一输出调度。
具体 provider 的请求构造、响应归一化和流式解析都委托给 `handlers/` 里的后端类。

"""

from __future__ import annotations

import asyncio
from typing import (
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Sequence,
)

from .prompt import DEBUG_STREAM_SYSTEM_PROMPT
from .llm_types import (
    LLMBackendConfig,
    LLMContext, LLMToolCall, LLMOutput,
    LLMError,
    LLMTimeoutError, LLMBackendError
)

from .handlers import (
    ToolSchema,
    LLMBackendHandler,
)

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
        limiter: Optional[_LLMLimiter] = None,
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
        self.handlers: Dict[str, LLMBackendHandler] = {}

        if backends:
            for backend in backends:
                self._register_backend(backend)
        elif model and (api_key or provider == "openvino"):
            self._register_backend(
                LLMBackendConfig(
                    name="default",
                    provider=provider,
                    model=model,
                    api_key=api_key or "",
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
        self.handlers[backend.name] = LLMBackendHandler.create_for_backend(self, backend)

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

    def _handler_for_backend(self, backend: LLMBackendConfig) -> LLMBackendHandler:
        return self.handlers[backend.name]

    def _build_messages(
        self,
        msg: str,
        prev_messages: Optional[List[LLMContext]] = None,
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

        # 系统提示词内容
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 历史上下文内容
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

    async def fetch(
        self,
        msg: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        prev_messages: Optional[List[LLMContext]] = None,
        backend_name: Optional[str] = None,
        fallback_order: Optional[Sequence[str]] = None,
        tools: Optional[List[ToolSchema]] = None,
    ) -> LLMOutput:
        """执行一次非流式请求，并按顺序尝试后端回退。

        Args:
            msg: 当前轮用户输入。
            system_prompt: 当前请求使用的系统提示词。
            temperature: 采样温度。
            max_tokens: 最大输出 token 数。
            prev_messages: 历史上下文。（在未来，这个东西有可能会是被精选后的上下文了）
            backend_name: 显式指定的后端名称。
            fallback_order: 额外指定的回退后端顺序。
            tools: 可选的 OpenAI tools schema 列表。

        Returns:
            抽象后的 LLM 输出，只暴露正文、推理内容、工具调用、用量等统一字段。

        Raises:
            LLMBackendError: 当所有候选后端均调用失败时抛出。
        """
        messages = self._build_messages(msg, prev_messages=prev_messages, system_prompt=system_prompt)
        backend_errors: List[str] = []

        if self.limiter:
            await self.limiter.acquire_llm()
        try:
            # 解析后端，返回一个后端表
            for backend in self._resolve_backends(backend_name, fallback_order):
                # backend: LLMBackendConfig
                retries_left = self._timeout_retry_count(backend)
                while True:
                    try:
                        handler = self._handler_for_backend(backend)
                        raw_response = handler.create_completion(
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=False,
                            tools=tools,
                        )
                        return handler.normalize_completion_response(raw_response)
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
        tools: Optional[List[ToolSchema]] = None,
    ) -> AsyncGenerator[str, None]:
        """执行一次流式请求，并按顺序尝试后端回退。
        TODO: 让这个函数可正式返回一个函数包体。

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
                        handler = self._handler_for_backend(backend)
                        response = handler.create_completion(
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=True,
                            tools=tools,
                        )
                        stream_iterator: Iterator[str] = handler.iter_stream_text(
                            response,
                            output_reasoning=output_reasoning,
                        )
                        for text in stream_iterator:
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
        system_prompt=DEBUG_STREAM_SYSTEM_PROMPT,
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
