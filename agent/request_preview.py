from __future__ import annotations

from typing import Any


def _tool_result_text(value: Any) -> str:
    """Return the complete tool-result string supplied back to the model.

    Args:
        value: Raw value returned by a tool handler.
    Returns:
        Complete string form of ``value`` without a display or persistence limit.

    Notes:
        This model-facing conversion is intentionally separate from lifecycle
        events, which retain their raw value so JSON results reach the UI as
        structured data rather than Python's escaped representation.
    """
    return str(value)
