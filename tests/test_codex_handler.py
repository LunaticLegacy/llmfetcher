from types import SimpleNamespace

from llmfetcher.fetcher_handlers.codex import CodexHandler


def _handler():
    handler = CodexHandler.__new__(CodexHandler)
    handler.backend = SimpleNamespace(provider="codex", name="codex", model="gpt-5-codex")
    return handler


def test_codex_moves_system_messages_to_instructions_and_tool_feedback():
    instructions, items = CodexHandler._input_items([
        {"role": "system", "content": "You are a coding agent."},
        {"role": "user", "content": "Fix it."},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1", "name": "read_file", "arguments": {"path": "a.py"}}]},
        {"role": "tool", "tool_call_id": "call-1", "content": "print('ok')"},
    ])
    assert instructions == "You are a coding agent."
    assert items[0] == {"role": "user", "content": "Fix it."}
    assert items[1]["type"] == "function_call"
    assert items[1]["name"] == "read_file"
    assert items[2]["type"] == "function_call_output"


def test_codex_normalizes_response_function_calls():
    response = SimpleNamespace(
        output_text="Done",
        output=[SimpleNamespace(type="function_call", name="read_file", arguments='{"path":"a.py"}', call_id="call-1")],
        usage={"input_tokens": 4, "output_tokens": 2, "total_tokens": 6},
        status="completed",
    )
    output = _handler().normalize_completion_response(response)
    assert output.content == "Done"
    assert output.tool_calls[0].name == "read_file"
    assert output.tool_calls[0].arguments == {"path": "a.py"}
    assert output.usage.total_tokens == 6

