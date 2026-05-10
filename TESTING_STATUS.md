# Testing Status

## Current State

The test suite is **outdated** and needs to be rewritten to match the current API.

### Issues Identified:

1. **Import errors**: Tests import non-existent modules (`pack.llm_handler`, `ToolParam`, `pack.state.AgentState`)
2. **API mismatches**: Tests use old constructor signatures (e.g., `Agent(llm_fetcher=...)` instead of `Agent(llm_handler=..., system_prompt=...)`)
3. **Missing fixtures**: No proper test fixtures for LLM backend configuration

## Planned Fixes

### Priority 1: Basic Unit Tests
- [ ] Fix imports in all test files
- [ ] Update Agent initialization to use new API
- [ ] Add proper async test support with pytest-asyncio
- [ ] Create mock LLM responses for offline testing

### Priority 2: Integration Tests
- [ ] Test LLMFetcher with real backends (OpenAI, Anthropic, DeepSeek)
- [ ] Test Tool execution and schema conversion
- [ ] Test Agent round_call with tools

### Priority 3: End-to-End Tests
- [ ] Test complete AgentSwarm workflows
- [ ] Test ThinkingGraph integration
- [ ] Test ExecutionGraph DAG execution

## Temporary Workaround

For now, you can manually test basic functionality:

```bash
# Set up environment
export DEEPSEEK_API_KEY="your-key"

# Run simple tests
python test_deepseek_api.py
python test_deepseek_tool.py
python test_deepseek_no_tools.py
```

## Contributing to Tests

If you'd like to help fix tests, please:

1. Start with one test file at a time
2. Ensure all imports are correct
3. Use the current API (check `pack/agent.py`, `pack/tool.py`, etc.)
4. Add pytest markers for tests requiring API keys:
   ```python
   @pytest.mark.skipif(not os.environ.get("DEEPSEEK_API_KEY"), reason="No API key")
   ```
5. Run with: `pytest pack/tests/test_file.py -v`
