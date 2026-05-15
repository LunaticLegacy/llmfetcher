# LLM Fetcher Semantics

## Architecture

- `pack/llm_fetcher.py` owns backend routing, fallback, retries, rate limiting, and conversion from SDK-specific responses into backend-neutral output objects.
- `pack/agent.py` consumes `LLMOutput` instead of reading OpenAI or Anthropic SDK response layouts directly in the main agent loop.
- `pack/llm_context.py` stores conversation context and uses `LLMOutput.content` when it asks the fetcher to summarize or create memory.
- `pack/tools/builtin_tools.py` provides Agent-bound management tools for reading, listing, compressing context, and managing persistent memories.

## Types

- `LLMBackendConfig`: input configuration for one backend. It carries provider name, model, key, optional API URL, timeout, retry count, and provider-specific `extra` kwargs.
- `LLMToolCall`: backend-neutral tool call. Inputs are `name`, `arguments`, optional `call_id`, and optional `source`. Output helper `to_execution_format()` returns `{"tool": name, "arguments": arguments}` for `ToolRegistry`.
- `LLMOutput`: backend-neutral non-stream response. It exposes `content`, `reasoning_content`, `tool_calls`, `usage`, provider/backend/model metadata, role, and stop reason. `text` and `str(output)` both return `content`.
- `LLMContextPair`: compatibility container for older imports. New agent persistence stores user and assistant messages as separate `LLMContext` entries.
- `LLMContextCompressed`: compatibility alias for `LLMContextCompacted`.

## Functions

- `LLMFetcher.fetch(...) -> LLMOutput`: builds messages, resolves fallback order, applies optional limiter, calls the selected backend in a worker thread, normalizes the SDK response into `LLMOutput`, and retries timeout failures before moving to fallback backends.
- `LLMFetcher.fetch_stream(...) -> AsyncGenerator[str, None]`: builds messages, resolves fallback order, calls the selected backend with `stream=True`, and yields only normalized text fragments. When `output_reasoning=True`, reasoning fragments are wrapped with `<THINK>` and `</THINK>` markers.
- `LLMFetcher._normalize_completion_response(...)`: converts OpenAI/LiteLLM `choices[0].message` or Anthropic `content` blocks into `LLMOutput`.
- `LLMFetcher._normalize_openai_tool_calls(...)`: converts native OpenAI-compatible function calls into `LLMToolCall` entries and parses JSON argument strings into dictionaries.
- `LLMFetcher._normalize_anthropic_blocks(...)`: extracts text, reasoning, and `tool_use` blocks from Anthropic-compatible message content.
- `LLMFetcher._iter_stream_text(...)`: reads OpenAI/LiteLLM chat deltas and Anthropic content-block events, yielding only text or optional reasoning text markers.
- `Agent.chat_once(...)`: performs exactly one `LLMFetcher.fetch()` call, optionally includes serialized history and tool schemas, optionally stores the assistant response, and never executes returned tool calls.
- `Agent.run_agent_round(...)`: sends the user message on each tool-loop turn with the dynamic system prompt and serialized history, asks `LLMFetcher.fetch()` for `LLMOutput`, executes any native provider tool calls, stores assistant/tool context, and stops when a turn has no tool calls. It raises `MaxTurnsExceededError` if the loop reaches `max_turns`.
- `Agent._register_builtin_tools(...)`: registers built-in tools returned by `create_builtin_tools(agent=self)` so handlers can call the Agent context and memory APIs.
- `Agent._tagify_context(...)`: builds tag input from assistant text plus tool call/result records. Empty contexts get no tags; non-empty contexts are sent to the LLM with a strict comma-separated snake_case tag prompt, then parsed with a regex and capped at five tags.
- `Agent._agent_message_from_output(...)`: builds diagnostics from `LLMOutput` without depending on SDK response objects.
- `Agent._extract_response_text(...)`: returns `LLMOutput.content` for normalized responses and keeps legacy extraction as fallback for older callers.
- `LLMContextHandler.add_context(...)`: stores a context entry, indexes it by object id, and indexes tags when present.
- `LLMContextHandler.context_len() -> int`: returns the character length of active context only, counting uncompacted role/content/tool data/tags and compacted abstract/source_ids/tags without recursively counting compressed source objects.
- `LLMContextHandler.get_content_as_single_str(...)`: serializes compacted and uncompacted context into text, including stored tool-call records and tool results for later Agent turns.
- `LLMContextHandler.compress_context(...)`: sends serialized context to `LLMFetcher.fetch()` and reads the abstracted result from `response.content`.
- `LLMContextHandler.generate_memory(...)`: asks the fetcher for a memory summary and returns `response.content` when present.
- `create_builtin_tools(agent=None) -> List[Tool]`: creates built-in tools. The context and memory tools require an Agent binding; unbound calls raise a runtime error.
- `context_list`: returns context ids, entry type, role/source ids, tags, and one-line previews. Inputs include optional `limit`, `include_compacted`, and `include_uncompacted`.
- `context_read`: serializes selected context ids, or all context when `ids` is omitted, using the Agent's conversation summary API.
- `context_compress`: compresses selected uncompacted context ids, or all uncompacted context when `ids` is omitted.
- `memory_create`: generates and stores a persistent memory summary from selected context ids.
- `memory_list`: returns indexed persistent memories stored on the Agent.
- `memory_clear`: clears all persistent memories stored on the Agent.

## Compatibility Impact

- Public `fetch()` no longer returns raw provider SDK objects. Callers should read `response.content`, `response.reasoning_content`, `response.tool_calls`, and `response.usage`.
- Public `fetch_stream()` remains a text stream. The abstraction now covers Anthropic-style streaming events in addition to OpenAI-compatible chat deltas.
- Legacy tool-call normalization can still accept `LLMOutput` via its `tool_calls` attribute.
