from enum import Enum
from dataclasses import dataclass, field
from typing import override, List, Sequence
from pathlib import Path

from .base import ContextHandler
from ..rag_module_tlb.core import TLBRAGHandler
from ..llm_fetcher import LLMFetcher
from ..llm_types import AssistantTurnInput, RequestMessage, ToolResultInput
from ..multimodal import UserMessage
from ..execution.control import ExecutionController


class PathStatus(Enum):
    """
    An enumerate about paths.
    """
    NOT_PROCEEDING  = 0     # Not proceeding at all.
    PROCEEDING      = 1     # Proceeding.
    COMPLETED       = 2     # COmpleted.
    

@dataclass
class WorkingStatus:
    current_focusing: str = ""
    other_path_names: List[str] = field(default_factory=list)
    path_status: List[str] = field(default_factory=list)


class TLBContextHandler(ContextHandler):
    def __init__(
            self,
            context_save_path: str | Path,
            llm_fetcher_instance: LLMFetcher
        ) -> None:
        super().__init__()

        self.llm_fetcher_instance = llm_fetcher_instance
        self.context_save_path: str | Path = context_save_path

        self.tlb_rag_handler_instance = TLBRAGHandler(
            context_save_path,
            fetcher_instance=self.llm_fetcher_instance
        )

        self.current_status: str = ""

    @override
    def add_user_message(
        self,
        message: "str | UserMessage",
    ) -> None:
        """
        Append an User input to conversation history.

        Args:
            message: The original user input (plain text or a
                :class:`~llmfetcher.multimodal.UserMessage`).
        """
        

    @override
    def add_assistant_message(
        self,
        turn: AssistantTurnInput,
        tool_results: Sequence[ToolResultInput] = (),
        *,
        controller: ExecutionController | None = None,
    ) -> None:
        """Record an LLM response into the conversation history.

        This handler is a placeholder and intentionally stores nothing.

        Args:
            turn: The output produced by the LLM, with its calls, usage and
                timing.
            tool_results: Completed results for the calls in *turn*.
            controller: Optional cancellation source.
        """

    @override
    def build_messages(self, *, system_prompt: str | None = None) -> List[RequestMessage]:
        """Build context messages for an LLM request.

        Returns the complete provider-neutral request sequence. The system
        prompt is included here so composed handlers control semantic order.

        Returns:
            A complete provider-neutral request message sequence.
        """


    @override
    def save(self, path: str | Path) -> bool:
        """
        Save context from disk.

        Args:
            path: The path of saving the file.

        Returns:
            A boolean for indicate whether successfully saved or not.
        """
        # TLB RAG handler will save everything in the disk.
        return True

    @override
    def load(self, path: str | Path) -> bool:
        """
        Load context from disk.

        Args:
            path: Path to file.

        Returns:
            A boolean for indicate whether successfully loaded or not.
        """
        # TLB RAG handler will save everything in the disk.
        return True

    @override
    def clear_context(self) -> bool:
        """
        Clear context.
        
        Returns:
            A boolean for indicate whether successfully clear or not.
        """

        # TLB RAG Context Handler will save this in the disk.
        return False
