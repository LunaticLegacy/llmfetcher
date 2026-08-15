"""Bounded lexical retrieval over raw, compacted conversation records.

Compaction is a prompt-size optimisation, not a deletion policy.  Callers can
keep the raw :class:`~llmfetcher.llm_types.LLMContext` values that left the
active context in an archive and use this module to retrieve a small,
auditable evidence set.  It deliberately does not read files or invoke an
LLM, so persistence format and semantic/graph retrieval remain separate
concerns.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re
from typing import Iterable, Sequence

from ..llm_types import LLMContext


_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
_CJK_RE = re.compile(r"^[\u3400-\u9fff]+$")


@dataclass(frozen=True)
class ArchiveRetrievalConfig:
    """Hard bounds for local archive retrieval and returned evidence."""

    max_results: int = 5
    max_chars_per_record: int = 2_000
    min_score: float = 0.0

    def __post_init__(self) -> None:
        if self.max_results <= 0:
            raise ValueError("max_results must be greater than zero")
        if self.max_chars_per_record <= 0:
            raise ValueError("max_chars_per_record must be greater than zero")
        if self.min_score < 0:
            raise ValueError("min_score cannot be negative")


@dataclass(frozen=True)
class ArchiveEvidence:
    """A bounded, display-safe projection of one archived context record.

    ``timeline_start`` and ``timeline_end`` make provenance explicit even
    when future archive adapters return a multi-message evidence window.  In
    this minimal in-memory retriever they are equal because each hit maps to
    exactly one immutable source record.
    """

    timeline_start: int
    timeline_end: int
    role: str
    score: float
    text: str
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class ArchiveRetrievalResult:
    """Result metadata plus bounded evidence suitable for later injection."""

    query: str
    evidence: tuple[ArchiveEvidence, ...]
    scanned_records: int


def retrieve_archive(
    query: str,
    records: Sequence[LLMContext] | Iterable[LLMContext],
    *,
    config: ArchiveRetrievalConfig | None = None,
) -> ArchiveRetrievalResult:
    """Lexically retrieve relevant raw archived records without mutation.

    The function accepts any sequence/iterable of ``LLMContext`` rather than
    a concrete handler or persistence layout.  This lets a graph handler (or
    a future event-store adapter) retrieve records from its own archive
    projection without coupling retrieval to compaction internals.

    Tool names, arguments and results participate in lexical matching because
    they often contain the only evidence for an earlier operation.  Returned
    text is nevertheless capped by ``max_chars_per_record``; callers needing
    a full record should explicitly resolve it from their archive by timeline.
    """
    cfg = config or ArchiveRetrievalConfig()
    archived = tuple(records)
    query_terms = _tokenize(query)
    if not query_terms or not archived:
        return ArchiveRetrievalResult(query=query, evidence=(), scanned_records=len(archived))

    query_counts = Counter(query_terms)
    documents = [_record_search_text(record) for record in archived]
    document_terms = [Counter(_tokenize(document)) for document in documents]
    document_frequency = Counter(
        term for counts in document_terms for term in counts.keys()
    )
    total_documents = len(documents)

    scored: list[tuple[float, int, tuple[str, ...]]] = []
    for index, counts in enumerate(document_terms):
        score = 0.0
        matched: list[str] = []
        for term, query_frequency in query_counts.items():
            frequency = counts.get(term, 0)
            if not frequency:
                continue
            # A compact TF-IDF score is deterministic, local, and avoids an
            # LLM or an embedding model.  Query repetition is intentionally
            # respected, but only logarithmically.
            inverse_frequency = math.log((total_documents + 1) / (document_frequency[term] + 1)) + 1
            score += (1 + math.log(frequency)) * inverse_frequency * (1 + math.log(query_frequency))
            matched.append(term)
        if score > cfg.min_score:
            scored.append((score, index, tuple(sorted(matched))))

    # Stable tie-breaking favours later evidence, which is normally more
    # useful in a continuing conversation while remaining deterministic.
    scored.sort(key=lambda item: (-item[0], -archived[item[1]].timeline, item[1]))
    evidence = tuple(
        ArchiveEvidence(
            timeline_start=archived[index].timeline,
            timeline_end=archived[index].timeline,
            role=archived[index].role,
            score=round(score, 6),
            text=_bounded_record_text(archived[index], cfg.max_chars_per_record),
            matched_terms=matched,
        )
        for score, index, matched in scored[:cfg.max_results]
    )
    return ArchiveRetrievalResult(
        query=query,
        evidence=evidence,
        scanned_records=len(archived),
    )


def _tokenize(text: str) -> list[str]:
    """Return case-insensitive lexical tokens, with useful CJK fallback."""
    tokens: list[str] = []
    for word in _WORD_RE.findall(text.casefold()):
        tokens.append(word)
        # Regex treats a Chinese sentence as one word; including its
        # characters permits useful overlap for short Chinese queries.
        if _CJK_RE.fullmatch(word):
            tokens.extend(word)
    return tokens


def _record_search_text(record: LLMContext) -> str:
    """Construct the local lexical index text for one raw context record."""
    parts = [record.content, record.content_reasoning]
    for tool_info in record.tool_calls:
        parts.append(tool_info.call.name)
        parts.append(str(tool_info.call.arguments))
        if tool_info.result:
            parts.append(tool_info.result)
    return "\n".join(part for part in parts if part)


def _bounded_record_text(record: LLMContext, limit: int) -> str:
    """Render a source record with one total character cap."""
    parts = [f"[{record.role} @ timeline {record.timeline}]", record.content]
    if record.content_reasoning:
        parts.extend(("Reasoning:", record.content_reasoning))
    for tool_info in record.tool_calls:
        parts.append(f"Tool {tool_info.call.name}: {tool_info.call.arguments}")
        if tool_info.result:
            parts.append(f"Result: {tool_info.result}")
    text = "\n".join(part for part in parts if part)
    if len(text) <= limit:
        return text
    if limit == 1:
        return "…"
    return f"{text[:limit - 1]}…"
