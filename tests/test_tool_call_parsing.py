from llmfetcher.agent import Agent


def test_parse_multiple_xml_tool_calls():
    agent = Agent.__new__(Agent)

    text = """
    <think>planning...</think>
    <tool_call>
    {"name": "shell", "arguments": {"command": "lscpu", "timeout": 10}}
    </tool_call>
    <tool_call>
    {"name": "web_fetch", "arguments": {"url": "https://example.com", "mode": "text"}}
    </tool_call>
    """

    calls = Agent._parse_custom_json_tool_calls(agent, text)

    assert calls == [
        {"tool": "shell", "arguments": {"command": "lscpu", "timeout": 10}},
        {"tool": "web_fetch", "arguments": {"url": "https://example.com", "mode": "text"}},
    ]
