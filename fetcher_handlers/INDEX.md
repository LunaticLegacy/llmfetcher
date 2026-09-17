# llmfetcher/fetcher_handlers/ — Provider Adapters INDEX

Backend adapters selected by `LLMFetcher`. Each handler normalizes one provider
into the shared `LLMOutput` / `TokenUsage` contract.

| File | Responsibility |
|---|---|
| `base.py` | `LLMBackendHandler` abstract base plus JSON/tool type aliases and the `_UsageLike` protocol. |
| `openai.py` | OpenAI-compatible chat handler, including streamed deltas and tool-call assembly. |
| `deepseek.py` | `DeepSeekHandler`, a platform-specialised OpenAI-compatible variant. |
| `anthropic.py` | Anthropic Messages handler with native tool blocks. |
| `litellm.py` | LiteLLM multi-provider adapter. |
| `openvino.py` | OpenVINO GenAI local-model handler (`OpenVINOHandler`). |
| `onnxruntime.py` | ONNX Runtime GenAI handler for decoder-only local models (`OnnxRuntimeGenAIHandler`). |
| `_tool_schemas.py` | Tool-schema conversion helpers shared by adapters. |
| `__init__.py` | Defensive optional exports; unavailable SDKs import as `None`. |

## Boundaries

- Providers are optional: every import is guarded so a missing SDK never breaks
  the package, and `LLMFetcher` selects only configured backends.
- Handlers translate provider payloads; retry/fallback, timeout classification
  and cancellation policy stay in `../llm_fetcher.py`.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [_tool_schemas.py](_tool_schemas.py#L8) | `tool_to_openai_schema` | `tool: Tool` | `ToolSchemaDict` | Serialize an executable tool into OpenAI-style function schema. |
| [_tool_schemas.py](_tool_schemas.py#L20) | `to_openai_tool_schemas` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Normalize runtime tools or legacy schemas into OpenAI-compatible payloads. |
| [_tool_schemas.py](_tool_schemas.py#L36) | `to_anthropic_tool_schemas` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Normalize runtime tools or legacy schemas into Anthropic tool payloads. |
| [anthropic.py](anthropic.py#L28) | `AnthropicHandler.convert_messages` | `messages: list[dict[str, str]]` | `tuple[list[dict[str, JSONValue]], Optional[str]]` | Implement `AnthropicHandler.convert_messages`. |
| [anthropic.py](anthropic.py#L69) | `AnthropicHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Prepare tools for Anthropic's `input_schema` tool format. |
| [anthropic.py](anthropic.py#L76) | `AnthropicHandler._normalize_anthropic_blocks` | `blocks: Iterable[object \| Mapping[str, JSONValue]]` | `tuple[str, str, list[LLMToolCall]]` | Implement `AnthropicHandler._normalize_anthropic_blocks`. |
| [anthropic.py](anthropic.py#L108) | `AnthropicHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: Any` | `Any` | Implement `AnthropicHandler.create_completion`. |
| [anthropic.py](anthropic.py#L132) | `AnthropicHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `AnthropicHandler.normalize_completion_response`. |
| [anthropic.py](anthropic.py#L147) | `AnthropicHandler.iter_stream_text` | `response: Any, output_reasoning: bool, usage_capture: Any` | `Iterable[str]` | Implement `AnthropicHandler.iter_stream_text`. |
| [base.py](base.py#L30) | `_UsageLike.model_dump` | `None` | `JSONObject` | Implement `_UsageLike.model_dump`. |
| [base.py](base.py#L58) | `LLMBackendHandler.supports_backend` | `backend: LLMBackendConfig` | `bool` | Args: cls: The class to check. Should be a subclass of `LLMBackendHandler`. backend: The backend configuration to check. |
| [base.py](base.py#L70) | `LLMBackendHandler.from_backend` | `fetcher: 'LLMFetcher', backend: LLMBackendConfig` | `'LLMBackendHandler'` | Create an instance from a backend config. |
| [base.py](base.py#L86) | `LLMBackendHandler._iter_descendants` | `None` | `Iterable[type['LLMBackendHandler']]` | Implement `LLMBackendHandler._iter_descendants`. |
| [base.py](base.py#L92) | `LLMBackendHandler.create_for_backend` | `fetcher: 'LLMFetcher', backend: LLMBackendConfig` | `'LLMBackendHandler'` | Implement `LLMBackendHandler.create_for_backend`. |
| [base.py](base.py#L111) | `LLMBackendHandler.create_completion` | `messages: list[dict[str, str]], temperature: float, max_tokens: int, stream: bool, tools: Optional[list[ToolSchemaDict]]` | `Any` | Implement `LLMBackendHandler.create_completion`. |
| [base.py](base.py#L123) | `LLMBackendHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `LLMBackendHandler.normalize_completion_response`. |
| [base.py](base.py#L127) | `LLMBackendHandler.iter_stream_text` | `response: Any, output_reasoning: bool, usage_capture: Any` | `Iterable[str]` | Yield normalized text chunks, optionally capturing raw usage. |
| [base.py](base.py#L150) | `LLMBackendHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Convert registry tools or prebuilt schemas into this provider's shape. |
| [base.py](base.py#L167) | `LLMBackendHandler.build_chat_history` | `messages: list[dict[str, str]], tools: Optional[list[ToolSchemaDict]]` | `Any` | Implement `LLMBackendHandler.build_chat_history`. |
| [base.py](base.py#L174) | `LLMBackendHandler.generation_config` | `temperature: float, max_tokens: int` | `JSONObject` | Generate a JSON object for the LLM backend to use as a generation configuration. Optional for inhereting classes. |
| [base.py](base.py#L181) | `LLMBackendHandler.abort_active_request` | `None` | `bool` | Close this handler's client to interrupt an in-flight request. |
| [base.py](base.py#L201) | `LLMBackendHandler.result_text` | `result: Any` | `str` | Implement `LLMBackendHandler.result_text`. |
| [base.py](base.py#L204) | `LLMBackendHandler._read_field` | `value: object \| Mapping[str, JSONValue] \| None, name: str, default: object \| JSONValue \| None` | `object \| JSONValue \| None` | Read a field from a value. |
| [base.py](base.py#L222) | `LLMBackendHandler._coerce_content_to_text` | `content: str \| Sequence[JSONValue] \| object \| None` | `str` | Implement `LLMBackendHandler._coerce_content_to_text`. |
| [base.py](base.py#L245) | `LLMBackendHandler._usage_to_dict` | `usage: _UsageLike \| Mapping[str, JSONValue] \| None` | `JSONObject` | Deprecated: use _normalize_usage() instead. Kept for subclasses that may override this method. |
| [base.py](base.py#L271) | `LLMBackendHandler.normalize_usage` | `usage: _UsageLike \| Mapping[str, JSONValue] \| None` | `TokenUsage` | Normalize a provider-specific usage response into a platform-irrelevant TokenUsage. |
| [base.py](base.py#L309) | `LLMBackendHandler._parse_arguments` | `arguments: str \| Mapping[str, JSONValue] \| None` | `JSONObject` | Implement `LLMBackendHandler._parse_arguments`. |
| [base.py](base.py#L320) | `LLMBackendHandler._extract_content` | `delta: object \| Mapping[str, JSONValue] \| None` | `Optional[str]` | Implement `LLMBackendHandler._extract_content`. |
| [base.py](base.py#L332) | `LLMBackendHandler._extract_reasoning` | `delta: object \| Mapping[str, JSONValue] \| None` | `Optional[str]` | Implement `LLMBackendHandler._extract_reasoning`. |
| [deepseek.py](deepseek.py#L58) | `DeepSeekHandler.supports_backend` | `backend: LLMBackendConfig` | `bool` | Recognise DeepSeek behind an OpenAI-compatible configuration. |
| [deepseek.py](deepseek.py#L86) | `DeepSeekHandler._message_reasoning` | `message: object \| Mapping[str, object] \| None` | `str` | DeepSeek exposes reasoning exclusively via ``reasoning_content``. |
| [deepseek.py](deepseek.py#L98) | `DeepSeekHandler._delta_reasoning` | `delta: object \| Mapping[str, object] \| None` | `Optional[str]` | Read ``reasoning_content`` from one streamed delta (and only that). |
| [deepseek.py](deepseek.py#L114) | `DeepSeekHandler._strip_think_blocks` | `text: str` | `str` | Remove ``<think>...</think>`` blocks from assistant content. |
| [deepseek.py](deepseek.py#L125) | `DeepSeekHandler._split_think_blocks` | `text: str` | `tuple[str, str]` | Move ``<think>...</think>`` blocks out of model content. |
| [deepseek.py](deepseek.py#L141) | `DeepSeekHandler._sanitize_messages` | `messages: Sequence[Mapping[str, Any]]` | `list[dict[str, Any]]` | Strip context-handler ``<think>`` wrappers from assistant turns. |
| [deepseek.py](deepseek.py#L158) | `DeepSeekHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: List['Any']` | `Any` | Send a request with assistant ``<think>`` wrappers removed. |
| [deepseek.py](deepseek.py#L176) | `DeepSeekHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Extract any ``<think>`` the model echoed into ``reasoning_content``. |
| [deepseek.py](deepseek.py#L199) | `DeepSeekHandler.normalize_usage` | `usage: object \| Mapping[str, object] \| None` | `TokenUsage` | Map DeepSeek's ``prompt_cache_hit_tokens`` onto cached tokens. |
| [litellm.py](litellm.py#L13) | `LiteLLMHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: Any` | `Any` | Implement `LiteLLMHandler.create_completion`. |
| [onnxruntime.py](onnxruntime.py#L21) | `_ensure_cuda_runtime` | `None` | `bool` | Pre-load CUDA 12 compat .so files from nvidia pip packages. |
| [onnxruntime.py](onnxruntime.py#L65) | `_parse_xml_tool_calls` | `text: str` | `list[_ParsedToolCall]` | Extract ``<tool_call>`` blocks containing JSON from *text*. |
| [onnxruntime.py](onnxruntime.py#L88) | `_strip_xml_tool_calls` | `text: str` | `str` | Remove ``<tool_call>`` XML blocks from *text*. |
| [onnxruntime.py](onnxruntime.py#L121) | `_resolve_model_options` | `device: str` | `dict[str, Any]` | Map a human-readable device name to onnxruntime-genai model options. |
| [onnxruntime.py](onnxruntime.py#L154) | `_resolve_search_options` | `temperature: float, max_tokens: int, extra: Optional[dict[str, Any]]` | `dict[str, Any]` | Build the search-options dict passed to ``GeneratorParams.set_search_options``. |
| [onnxruntime.py](onnxruntime.py#L175) | `_coerce_chat_template_context` | `value: Any` | `dict[str, Any]` | Return backend ``extra_context`` as template keyword arguments. |
| [onnxruntime.py](onnxruntime.py#L184) | `_infer_enable_thinking` | `messages: Sequence[dict[str, str]]` | `Optional[bool]` | Infer Qwen thinking mode from the last explicit prompt directive. |
| [onnxruntime.py](onnxruntime.py#L194) | `_apply_thinking_prefix` | `prompt: str, context: dict[str, Any]` | `str` | Inject Qwen3's no-thinking prefix after ORT renders the chat template. |
| [onnxruntime.py](onnxruntime.py#L260) | `OnnxRuntimeGenAIHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Implement `OnnxRuntimeGenAIHandler.prepare_tools`. |
| [onnxruntime.py](onnxruntime.py#L268) | `OnnxRuntimeGenAIHandler.build_chat_history` | `messages: list[dict[str, str]], tools: Optional[list[ToolSchemaDict]]` | `list[dict[str, str]]` | Return messages as-is; the tokenizer's built-in chat template handles the formatting during ``tokenizer.encode_chat()``. |
| [onnxruntime.py](onnxruntime.py#L280) | `OnnxRuntimeGenAIHandler.generation_config` | `temperature: float, max_tokens: int` | `JSONObject` | Implement `OnnxRuntimeGenAIHandler.generation_config`. |
| [onnxruntime.py](onnxruntime.py#L296) | `OnnxRuntimeGenAIHandler.chat_template_context` | `messages: Sequence[dict[str, str]]` | `dict[str, Any]` | Implement `OnnxRuntimeGenAIHandler.chat_template_context`. |
| [onnxruntime.py](onnxruntime.py#L309) | `OnnxRuntimeGenAIHandler.create_completion` | `messages: list[dict[str, str]], temperature: float, max_tokens: int, stream: bool, tools: Optional[list[ToolSchemaDict]]` | `Any` | Implement `OnnxRuntimeGenAIHandler.create_completion`. |
| [onnxruntime.py](onnxruntime.py#L339) | `OnnxRuntimeGenAIHandler._create_completion_blocking` | `input_ids: Any, params: Any` | `_ONNXCompletionResponse` | Generate the full output sequence without streaming. |
| [onnxruntime.py](onnxruntime.py#L366) | `OnnxRuntimeGenAIHandler._create_stream` | `input_ids: Any, params: Any` | `Iterable[str]` | Yield text chunks as they are generated, via a background thread. |
| [onnxruntime.py](onnxruntime.py#L401) | `OnnxRuntimeGenAIHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `OnnxRuntimeGenAIHandler.normalize_completion_response`. |
| [onnxruntime.py](onnxruntime.py#L429) | `OnnxRuntimeGenAIHandler.iter_stream_text` | `response: Any, output_reasoning: bool` | `Iterable[str]` | Implement `OnnxRuntimeGenAIHandler.iter_stream_text`. |
| [openai.py](openai.py#L24) | `OpenAIHandler._normalize_messages` | `messages: list[dict[str, Any]]` | `list[dict[str, Any]]` | Convert backend-neutral ``tool_calls`` to OpenAI format. |
| [openai.py](openai.py#L54) | `OpenAIHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Prepare tools for OpenAI-compatible chat-completion APIs. |
| [openai.py](openai.py#L61) | `OpenAIHandler._normalize_openai_tool_calls` | `message: object \| Mapping[str, Any] \| None` | `list[LLMToolCall]` | Implement `OpenAIHandler._normalize_openai_tool_calls`. |
| [openai.py](openai.py#L79) | `OpenAIHandler._message_reasoning` | `message: object \| Mapping[str, Any] \| None` | `str` | Extract reasoning text from a non-streamed assistant message. |
| [openai.py](openai.py#L96) | `OpenAIHandler._delta_reasoning` | `delta: object \| Mapping[str, Any] \| None` | `Optional[str]` | Extract reasoning text from a single streamed delta. |
| [openai.py](openai.py#L120) | `OpenAIHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `OpenAIHandler.normalize_completion_response`. |
| [openai.py](openai.py#L139) | `OpenAIHandler.iter_stream_text` | `response: Any, output_reasoning: bool, usage_capture: Any` | `Iterable[str]` | Implement `OpenAIHandler.iter_stream_text`. |
| [openai.py](openai.py#L248) | `OpenAIHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: List['Tool']` | `Any` | Implement `OpenAIHandler.create_completion`. |
| [openvino.py](openvino.py#L14) | `_OpenVINOChatHistory.append` | `item: dict[str, JSONValue]` | `None` | Implement `_OpenVINOChatHistory.append`. |
| [openvino.py](openvino.py#L16) | `_OpenVINOChatHistory.set_tools` | `tools: Sequence[ToolSchemaDict]` | `None` | Implement `_OpenVINOChatHistory.set_tools`. |
| [openvino.py](openvino.py#L18) | `_OpenVINOChatHistory.set_extra_context` | `extra_context: JSONValue` | `None` | Implement `_OpenVINOChatHistory.set_extra_context`. |
| [openvino.py](openvino.py#L65) | `OpenVINOHandler.prepare_tools` | `tools: Optional[Sequence[ToolDefinition]]` | `Optional[list[ToolSchemaDict]]` | Prepare tools for OpenVINO chat history/template consumption. 当前的实现采用的仍然是 openai 的 tool schema，这个……可以改。 |
| [openvino.py](openvino.py#L74) | `OpenVINOHandler.build_chat_history` | `messages: list[dict[str, str]], tools: Optional[list[ToolSchemaDict]]` | `OpenVINOHistory` | Implement `OpenVINOHandler.build_chat_history`. |
| [openvino.py](openvino.py#L102) | `OpenVINOHandler.generation_config` | `temperature: float, max_tokens: int` | `JSONObject` | Implement `OpenVINOHandler.generation_config`. |
| [openvino.py](openvino.py#L109) | `OpenVINOHandler.result_text` | `result: OpenVINOGenerateResult` | `str` | Implement `OpenVINOHandler.result_text`. |
| [openvino.py](openvino.py#L120) | `OpenVINOHandler.create_completion` | `messages: Any, temperature: float, max_tokens: int, stream: bool, tools: Any` | `Any` | Implement `OpenVINOHandler.create_completion`. |
| [openvino.py](openvino.py#L139) | `OpenVINOHandler.call_generate` | `prompt_or_history: OpenVINOGenerateInputs, config: JSONObject` | `OpenVINOGenerateResult` | Implement `OpenVINOHandler.call_generate`. |
| [openvino.py](openvino.py#L142) | `OpenVINOHandler.create_stream` | `prompt_or_history: OpenVINOGenerateInputs, config: JSONObject` | `Iterable[str]` | Implement `OpenVINOHandler.create_stream`. |
| [openvino.py](openvino.py#L177) | `OpenVINOHandler.normalize_completion_response` | `response: Any` | `LLMOutput` | Implement `OpenVINOHandler.normalize_completion_response`. |
| [openvino.py](openvino.py#L188) | `OpenVINOHandler.iter_stream_text` | `response: Any, output_reasoning: bool` | `Iterable[str]` | Implement `OpenVINOHandler.iter_stream_text`. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [anthropic.py](anthropic.py#L13) | `AnthropicHandler` | `fetcher: Any, backend: LLMBackendConfig` | `LLMBackendHandler` | Provide `AnthropicHandler` behavior. |
| [base.py](base.py#L20) | `_UsageLike` | `prompt_tokens: int \| None, completion_tokens: int \| None, total_tokens: int \| None, input_tokens: int \| None, output_tokens: int \| None` | `Protocol` | A protocol for a usage object. |
| [base.py](base.py#L33) | `LLMBackendHandler` | `fetcher: 'LLMFetcher', backend: LLMBackendConfig` | `ABC` | Base class for backend-specific request/response handlers. |
| [deepseek.py](deepseek.py#L51) | `DeepSeekHandler` | `None` | `OpenAIHandler` | OpenAI-compatible chat-completions handler specialised for DeepSeek. |
| [litellm.py](litellm.py#L7) | `LiteLLMHandler` | `fetcher: Any, backend: LLMBackendConfig` | `OpenAIHandler` | Provide `LiteLLMHandler` behavior. |
| [onnxruntime.py](onnxruntime.py#L59) | `_ParsedToolCall` | `tool_name: str, arguments: dict[str, Any]` | `object` | Result of parsing a single ``<tool_call>`` block. |
| [onnxruntime.py](onnxruntime.py#L103) | `_StreamSentinel` | `None` | `object` | Provide `_StreamSentinel` behavior. |
| [onnxruntime.py](onnxruntime.py#L108) | `_ONNXCompletionResponse` | `content: str, raw: str, usage: JSONObject, stop_reason: Optional[str], tool_calls: list[ToolCallDict]` | `object` | Lightweight container returned by non-streaming create_completion. |
| [onnxruntime.py](onnxruntime.py#L208) | `OnnxRuntimeGenAIHandler` | `fetcher: Any, backend: LLMBackendConfig` | `LLMBackendHandler` | Backend handler for decoder-only LLMs via onnxruntime-genai. |
| [openai.py](openai.py#L12) | `OpenAIHandler` | `fetcher: Any, backend: Any` | `LLMBackendHandler` | Provide `OpenAIHandler` behavior. |
| [openvino.py](openvino.py#L13) | `_OpenVINOChatHistory` | `None` | `Protocol` | Provide `_OpenVINOChatHistory` behavior. |
| [openvino.py](openvino.py#L21) | `_OpenVINOTextsResult` | `texts: Sequence[str]` | `Protocol` | Provide `_OpenVINOTextsResult` behavior. |
| [openvino.py](openvino.py#L25) | `_OpenVINOTextResult` | `text: str` | `Protocol` | Provide `_OpenVINOTextResult` behavior. |
| [openvino.py](openvino.py#L29) | `_StreamSentinel` | `None` | `object` | Provide `_StreamSentinel` behavior. |
| [openvino.py](openvino.py#L40) | `_OpenVINOCompletionResponse` | `content: str, raw: str, usage: JSONObject, stop_reason: Optional[str]` | `object` | Provide `_OpenVINOCompletionResponse` behavior. |
| [openvino.py](openvino.py#L47) | `OpenVINOHandler` | `fetcher: Any, backend: LLMBackendConfig` | `LLMBackendHandler` | Provide `OpenVINOHandler` behavior. |

<!-- END GENERATED SYMBOL MAP -->
