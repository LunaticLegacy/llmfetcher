"""Sage context: a handler whose history is indexed as context trees.

``SageContext`` (``sage.py``) is the public entry point.  It composes
``ContextHandlerLinear`` for durable rows, compaction and usage accounting,
and keeps a ``tree.py`` index over the active transcript.
"""

from __future__ import annotations

from .sage import SageContext
from .commands import SageBranchCommand
from .tools import SageToolProvider, create_sage_tools
from .compaction import SageCompactionFetcher, SageCompactionRequest

__all__ = [
    "SageContext", "SageBranchCommand", "SageToolProvider", "create_sage_tools",
    "SageCompactionFetcher", "SageCompactionRequest",
]
