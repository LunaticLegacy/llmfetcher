import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pack.agent import Agent
from pack.llm_context import LLMContextHandler
from pack.llm_handler import LLMFetcher
from pack.tool import Tool, ToolParam


# ---------------------------------------------------------------------------
# Helper: create a mock tool that records start and end timestamps
# ---------------------------------------------------------------------------
class TimestampTool(Tool):
    def __init__(self, name: str, delay: float = 0.1):
        super().__init__(
            name=name,
            description="timestamp tool",
            parameters=[ToolParam(name="delay", type="float", required=False)],
            function=self._run,
        )
        self.delay = delay
        self.start_times = []
        self.end_times = []

    async def _run(self, delay: float = None) -> str:
        if delay is None:
            delay = self.delay
        self.start_times.append(time.monotonic())
        await asyncio.sleep(delay)
        self.end_times.append(time.monotonic())
        return f"{self.name} done"


# ---------------------------------------------------------------------------
# Helper: create a mock LLM fetcher with configurable backends
# ---------------------------------------------------------------------------
class MockLLMFetcher(LLMFetcher):
    def __init__(self, backends: dict):
        # backends: dict mapping backend name to (callable or raise Exception)
        self.backends = backends
        super().__init__(backends={})  # avoid real init

    def fetch(self, backend: str, *args, **kwargs):
        if backend not in self.backends:
            raise ValueError(f"Unknown backend: {backend}")
        fn = self.backends[backend]
        if asyncio.iscoroutinefunction(fn):
            return fn(*args, **kwargs)
        else:
            return fn(*args, **kwargs)


# ---------------------------------------------------------------------------
# Tests for Agent.round_call parallel tool execution
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_round_call_parallel_tool_execution():
    """Verify that tools are executed concurrently when max_concurrent_tools > 1."""
    tool1 = TimestampTool("tool1", delay=0.3)
    tool2 = TimestampTool("tool2", delay=0.3)
    tool3 = TimestampTool("tool3", delay=0.3)
    agent = Agent(
        max_concurrent_tools=3,
        tools=[tool1, tool2, tool3],
        llm_fetcher=MockLLMFetcher({}),
        # We'll mock the _process function to simulate a tool call response
    )

    # We need to simulate a round_call that triggers multiple tool calls.
    # To do this, we mock agent._process to return a response that contains tool calls.
    # This is a bit involved; instead, we can directly test the _handle_tool_calls logic.
    # However, we want to test from round_call entry point.
    # We'll set up a mock for the LLM fetcher that returns a tool call message.
    async def fake_llm_response(messages, tools, **kwargs):
        # Return a mock response with tool_calls for the three tools
        tool_calls = [
            {"id": "call1", "function": {"name": "tool1", "arguments": "{}"}},
            {"id": "call2", "function": {"name": "tool2", "arguments": "{}"}},
            {"id": "call3", "function": {"name": "tool3", "arguments": "{}"}},
        ]
        return AsyncMock(choices=[AsyncMock(message=AsyncMock(tool_calls=tool_calls, content=None))])

    agent.llm_fetcher = MockLLMFetcher({"valid": fake_llm_response})
    # Disable memory/compression for simplicity
    agent.memory_enabled = False
    agent.max_messages = 1000

    start_time = time.monotonic()
    user_message = "run all tools"
    # We need to call round_call with a user message; the agent will use the mocked LLM
    # and then execute tool calls.
    # But round_call expects a state object. We'll create a minimal state.
    from pack.state import AgentState
    state = AgentState(agent_id="test")
    await agent.round_call(user_message, state=state)
    end_time = time.monotonic()

    # Check that all tools started within a short window
    # Note: due to async execution, they should all start nearly simultaneously
    # Use a tolerance of 0.1s (allowing for overhead)
    all_start = tool1.start_times + tool2.start_times + tool3.start_times
    if all_start:
        min_start = min(all_start)
        max_start = max(all_start)
        assert max_start - min_start < 0.1, f"Tool start times not parallel: {all_start}"
    else:
        pytest.fail("No tools were executed")

    # Total time should be less than sum of individual delays (0.9s) because parallel
    # With 3 tools each 0.3s, max single delay ~0.3s + overhead
    total_time = end_time - start_time
    assert total_time < 0.5, f"Total time {total_time}s is too high (parallel execution expected)"


# ---------------------------------------------------------------------------
# Tests for fallback order in Agent.round_call
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_round_call_fallback_working_backend():
    """When the first backend fails, the agent should fall back to the next."""
    call_count = []

    async def broken_backend(*args, **kwargs):
        call_count.append("broken")
        raise Exception("simulated failure")

    async def working_backend(*args, **kwargs):
        call_count.append("working")
        return AsyncMock(choices=[AsyncMock(message=AsyncMock(content="success", tool_calls=None))])

    fetcher = MockLLMFetcher({"broken": broken_backend, "working": working_backend})
    agent = Agent(
        llm_fetcher=fetcher,
        fallback_order=["broken", "working"],
        max_concurrent_tools=1,
        memory_enabled=False,
    )

    from pack.state import AgentState
    state = AgentState(agent_id="test")
    # We'll send a simple message that triggers an LLM call (no tools)
    # Ensure the LLM call goes through fallback
    await agent.round_call("hello", state=state)

    assert call_count == ["broken", "working"], "Fallback order not followed"


@pytest.mark.asyncio
async def test_round_call_fallback_all_broken():
    """If all backends fail, the agent should raise an appropriate exception."""
    async def always_broken(*args, **kwargs):
        raise Exception("failed")

    fetcher = MockLLMFetcher({"b1": always_broken, "b2": always_broken})
    agent = Agent(
        llm_fetcher=fetcher,
        fallback_order=["b1", "b2"],
        max_concurrent_tools=1,
        memory_enabled=False,
    )

    from pack.state import AgentState
    state = AgentState(agent_id="test")
    with pytest.raises(Exception, match="All LLM backends failed"):
        await agent.round_call("hello", state=state)


# ---------------------------------------------------------------------------
# Tests for fallback order in LLMContextHandler.compress_context
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_compress_context_fallback_working():
    """LLMContextHandler.compress_context should use fallback_order."""
    call_count = []

    async def broken_backend(*args, **kwargs):
        call_count.append("broken")
        raise Exception("simulated failure")

    async def working_backend(*args, **kwargs):
        call_count.append("working")
        return "compressed result"

    fetcher = MockLLMFetcher({"broken": broken_backend, "working": working_backend})
    handler = LLMContextHandler(
        fetcher=fetcher,
        fallback_order=["broken", "working"],
        max_tokens=1000,
    )

    # We need a context to compress; create a mock one
    context = [{"role": "user", "content": "test"}]
    # compress_context returns the compressed string
    result = await handler.compress_context(context)
    assert call_count == ["broken", "working"], "Fallback not used in compress_context"
    assert result == "compressed result"


@pytest.mark.asyncio
async def test_compress_context_fallback_all_broken():
    """If all backends fail, compress_context should raise."""
    async def always_broken(*args, **kwargs):
        raise Exception("fail")

    fetcher = MockLLMFetcher({"b1": always_broken, "b2": always_broken})
    handler = LLMContextHandler(
        fetcher=fetcher,
        fallback_order=["b1", "b2"],
        max_tokens=1000,
    )

    context = [{"role": "user", "content": "test"}]
    with pytest.raises(Exception, match="All LLM backends failed"):
        await handler.compress_context(context)


# ---------------------------------------------------------------------------
# Tests for parallel tool execution with partial failures
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_round_call_parallel_partial_failure():
    """One tool failure should not affect the others; errors returned as strings."""
    good_tool = TimestampTool("good", delay=0.1)
    bad_tool = Tool(
        name="bad",
        description="always fails",
        parameters=[],
        function=lambda: (_ for _ in ()).throw(Exception("oops")),
    )

    agent = Agent(
        max_concurrent_tools=2,
        tools=[good_tool, bad_tool],
        llm_fetcher=MockLLMFetcher({}),
        memory_enabled=False,
    )

    async def fake_llm_response(*args, **kwargs):
        tool_calls = [
            {"id": "call1", "function": {"name": "good", "arguments": "{}"}},
            {"id": "call2", "function": {"name": "bad", "arguments": "{}"}},
        ]
        return AsyncMock(choices=[AsyncMock(message=AsyncMock(tool_calls=tool_calls, content=None))])

    agent.llm_fetcher = MockLLMFetcher({"valid": fake_llm_response})
    from pack.state import AgentState
    state = AgentState(agent_id="test")
    result = await agent.round_call("run", state=state)

    # The 'good' tool should have run (its start/end recorded)
    assert len(good_tool.start_times) == 1
    # The 'bad' tool error should be converted to a string in the result
    assert "Error" in result or "oops" in result


# ---------------------------------------------------------------------------
# Test that default parameters maintain backward compatibility
# ---------------------------------------------------------------------------
def test_default_parameters_backward_compatible():
    """Agent and LLMContextHandler instantiated without new parameters should work."""
    from pack.agent import Agent
    from pack.llm_context import LLMContextHandler

    agent = Agent()
    assert agent.max_concurrent_tools == 1
    assert agent.fallback_order is None

    fetcher = MockLLMFetcher({})
    handler = LLMContextHandler(fetcher=fetcher)
    assert handler.fallback_order is None