# llmfetcher/ — LLMFetcher Submodule INDEX

Git submodule. LLM abstraction layer: backend providers, context management, tool execution, event system.

> ⚠️ This is a submodule. Its INDEX.md lives inside the submodule repo.
> For LLMFetcher's own code structure, see `llmfetcher/` directory contents directly.

## What Angelus uses from LLMFetcher

| Component | Path | Purpose |
|-----------|------|---------|
| `LLMFetcher` | `llm_fetcher.py` | Main fetch/stream interface to LLM backends with fallback |
| `LLMBackendConfig` | `llm_types.py` | Backend configuration (provider, model, API key) |
| `LLMOutput` | `llm_types.py` | Normalized LLM response with token usage |
| `ExecutionEvent` | `events.py` | Observable event type for hooks/SSE |
| `ContextHandler` | `context_handlers/base.py` | Abstract conversation history interface |
| `ContextHandlerLinear` | `context_handlers/linear.py` | Linear history with LLM-based compaction |
| `RetrievedContextHandler` | `context_handlers/retrieved.py` | Linear + TLB-RAG retrieved memory injection |
| Backend Handlers | `fetcher_handlers/` | OpenAI, Anthropic, LiteLLM, ONNX, OpenVINO provider implementations |
| Tool Framework | `tool_handler.py`, `tool_executor.py` | Tool registry + parallel execution |

## Submodule Update

```bash
git submodule update --remote llmfetcher
```
