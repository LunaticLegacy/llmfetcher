from enum import Enum
from dataclasses import dataclass, field
from typing import override, Optional, List, Dict, Any
from pathlib import Path

from .base import ContextHandler
from ..rag_module_tlb.core import TLBRAGHandler
from ..llm_fetcher import LLMFetcher
from ..llm_types import LLMOutput


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
        message: str,
    ) -> None:
        """
        Append an User input to conversation history.

        Args:
            message: The original user input.
        """
        

    @override
    def add_assistant_message(
        self,
        message: LLMOutput,
        tool_results: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record an LLM response into the conversation history.

        Args:
            message: The output produced by the LLM (includes content,
                     tool calls, usage, etc.).
            tool_results:
                Mapping from ``call_id`` to execution result text.
                When provided, each tool call in *message* is paired
                with its result so that future ``build_messages`` calls
                can emit the ``{"role": "tool", ...}`` feedback turn.
        """

    @override
    def build_messages(self) -> List[Dict[str, Any]]:
        """Build context messages for an LLM request.

        Returns the stored conversation history (excluding system prompt
        and the current user message) as a list of API-compatible dicts.
        The caller (``LLMFetcher``) is responsible for prepending the
        system prompt and appending the current user message.

        Returns:
            A list of message dicts (``{"role": ..., "content": ...}``),
            with ``tool_calls`` embedded where applicable.
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
