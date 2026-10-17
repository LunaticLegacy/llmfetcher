from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..llm_types import LLMOutput


class AgentRunTermination(str, Enum):
    """Explicit terminal classifications for one completed Agent invocation."""

    FINAL_RESPONSE = "final_response"
    STOP_TURN = "stop_turn"
    WORKFLOW_COMPLETION = "workflow_completion"
    USER_STOPPED = "user_stopped"
    EMPTY_RESPONSE = "empty_response"
    ROUND_LIMIT = "round_limit"


@dataclass(frozen=True)
class AgentRunOutcome:
    """Inspectable terminal state for an Agent run.

    Args:
        termination: Explicit reason the run stopped progressing.
        rounds: Number of completed model rounds.
        detail: Optional model- or control-provided terminal explanation.
        output: Last completed model response, if one exists.

    ``output`` is retained in-process for hosts that need the exact response;
    lifecycle events use :meth:`to_dict` and therefore never serialize it.
    """

    termination: AgentRunTermination
    rounds: int
    detail: str = ""
    output: LLMOutput | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the credential-free terminal fields for lifecycle events."""
        return {
            "termination": self.termination.value,
            "rounds": self.rounds,
            "detail": self.detail,
            "has_output": self.output is not None,
        }


@dataclass(frozen=True)
class RequestIndex:
    """Content-free index for one remote LLM request.

    Args:
        request_id: Opaque identifier distinct from any provider response id.
        round: One-based Agent round the request belongs to.
        model: Provider model identifier the request targeted.
        stream: Whether the request asked for a streaming response.
        message_count: Number of context messages sent.
        message_roles: Count of messages per role.
        source_ids: Durable provenance identifiers copied from messages.
        input_characters: Total characters across message content.
        estimated_input_tokens: Rough token estimate used for sizing only.
        input_sha256: Hash of the canonical serialized message body.
        tool_count: Number of registered tools sent.
        tool_schema_hashes: Truncated hash per serialized tool schema.
        temperature: Sampling temperature supplied to the provider.
        max_tokens: Completion budget supplied to the provider.
    """

    request_id: str
    round: int
    model: str
    stream: bool
    message_count: int
    message_roles: dict[str, int]
    source_ids: list[str]
    input_characters: int
    estimated_input_tokens: int
    input_sha256: str
    tool_count: int
    tool_schema_hashes: list[str]
    temperature: Any
    max_tokens: Any
    thinking_mode: str = "auto"
    reasoning_effort: str = "auto"


@dataclass(frozen=True)
class RequestContentMessage:
    """One capped context message retained only for the console ledger.

    Args:
        role: Message role supplied to the model.
        content: Capped textual rendering of the message content.
        characters: Full character count before capping.
        truncated: Whether ``content`` was shortened for the ledger.
    """

    role: str
    content: str
    characters: int
    truncated: bool


@dataclass(frozen=True)
class RequestContent:
    """Capped, readable preview of one dispatch-ready request.

    Args:
        round: One-based Agent round the request belongs to.
        model: Provider model identifier the request targeted.
        messages: Capped tail of context messages sent to the provider.
        omitted_messages: Count of earlier messages dropped from that tail.
    """

    round: int
    model: str
    messages: list[RequestContentMessage]
    omitted_messages: int
