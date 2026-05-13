"""Built-in tools for Agent lifecycle management."""

from typing import Any, List

from ..tool import Tool


def create_builtin_tools() -> List[Tool]:
    """Create Agent built-in meta-tools (e.g., round_end)."""

    async def _round_end(**kwargs: Any) -> str:
        """结束当前 round_call。"""
        return "Round ended."

    return [
        Tool(
            name="round_end",
            description=(
                "结束当前轮次。当你认为已经完成了本轮所有必要的思考、"
                "工具调用和论点记录后，调用此工具来明确结束本轮对话。"
            ),
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            handler=_round_end,
        ),
    ]


# ============================================================================
# TROUBLESHOOTING GUIDE: Tool Instability Issues
# ============================================================================
# 
# If you experience unstable tool calling behavior, check these common causes:
#
# 1. PROVIDER CONFIGURATION
#    - Default provider is "custom_json" which relies on text-based parsing
#    - For better stability, use native provider support:
#      * DeepSeek/OpenAI/GPT → provider="openai" (requires 'openai' package)
#      * Claude → provider="anthropic" (requires 'anthropic' package)
#      * Custom APIs → provider="custom_json" (no extra packages needed)
#
# 2. PACKAGE INSTALLATION
#    To use native tool calling with DeepSeek or OpenAI-compatible APIs:
#    ```bash
#    pip install openai
#    ```
#    
#    Then set: Agent(..., provider="openai")
#
# 3. CUSTOM JSON MODE LIMITATIONS
#    When using provider="custom_json" (default):
#    - No structured schemas sent to LLM (only text descriptions)
#    - Relies on LLM outputting valid JSON in specific format
#    - Parsing can fail if LLM formatting is inconsistent
#    - Improved with _relaxed_json_extract() fallback strategies
#
# 4. DEBUGGING TIPS
#    - Enable verbose_info=True to see tool schema count and calls
#    - Check logs for "Tool schemas count: 0" (means custom_json mode)
#    - Look for "Warning: Failed to parse JSON" messages
#    - Monitor if tool_calls count matches expected behavior
#
# 5. RECOMMENDED SETUP FOR DEEPSEEK
#    ```python
#    # Install: pip install openai
#    
#    fetcher = LLMFetcher(
#        api_url="https://api.deepseek.com",
#        api_key="your-key",
#        model="deepseek-chat",  # or deepseek-coder, etc.
#        timeout=180.0
#    )
#    
#    agent = Agent(
#        llm_handler=fetcher,
#        system_prompt="Your prompt here",
#        tools=your_tools,
#        provider="openai"  # ← This enables stable native tool calling
#    )
#    ```
#
# 6. FALLBACK TO CUSTOM JSON
#    If you cannot install the openai package:
#    - The improved JSON parsing should be more robust now
#    - Consider simplifying your system prompt to emphasize JSON format
#    - Test with simpler tasks first to verify stability
#
# ============================================================================
