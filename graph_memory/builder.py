"""GraphBuilder: incremental entity/relation extraction from conversation.

Pipeline per ingest batch:
1. Render the newest N messages as a compact transcript.
2. Ask the LLM for a lightweight JSON extraction (TERAG-style compact schema).
3. On LLM failure / unavailability, fall back to deterministic regex signals.
4. Upsert entities and relations into the GraphStore with timeline metadata
   (first/last_seen, freq, weight, evidence).

The builder never raises: extraction failures degrade to regex mode and are
reported via the returned stats dict.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from .extraction_prompts import (
    EXTRACTION_SYSTEM_PROMPT_COMPACT,
    extract_regex,
)
from .graph_store import GraphStore
from ..usage_ledger import UsageRecord, copy_usage, drain_records


class ExtractionFetcher(Protocol):
    """Minimal LLM interface used for graph extraction."""

    def fetch(
        self,
        msg: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
        context_handler: Any = None,
        backend_name: Optional[str] = None,
        tools: Any = None,
    ) -> Any:
        """Return an object with a ``content`` attribute."""
        ...


@dataclass
class IngestStats:
    """Statistics for one ingest batch."""

    entities_added: int = 0
    relations_added: int = 0
    llm_used: bool = False
    fallback_regex: bool = False
    error: str = ""

    def __str__(self) -> str:
        return (
            f"IngestStats(entities={self.entities_added}, "
            f"relations={self.relations_added}, llm={self.llm_used}, "
            f"regex_fallback={self.fallback_regex}, error={self.error!r})"
        )


def _extract_json_object(text: str) -> Optional[dict[str, Any]]:
    """Extract the first valid JSON object from arbitrary text."""
    fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence:
        candidate = fence.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
            return obj
        except json.JSONDecodeError:
            continue
    return None


class GraphBuilder:
    """Incremental conversation -> memory-graph builder."""

    def __init__(
        self,
        store: GraphStore,
        fetcher: Optional[ExtractionFetcher] = None,
        max_batch_chars: int = 24000,
        max_entities_per_batch: int = 12,
    ) -> None:
        self.store = store
        self.fetcher = fetcher
        self.max_batch_chars = max_batch_chars
        self.max_entities_per_batch = max_entities_per_batch
        from ..llm_types import TokenUsage
        self.extra_usage: TokenUsage = TokenUsage()
        self._usage_records: list[UsageRecord] = []

    def drain_usage_records(self) -> list[UsageRecord]:
        """Return completed graph-extraction calls exactly once."""
        return drain_records(self._usage_records)

    # -- public API --------------------------------------------------------

    def ingest(self, messages: list[Any]) -> IngestStats:
        """Extract and upsert entities/relations from an LLMContext list.

        Args:
            messages: List of LLMContext-like objects (``role``, ``content``,
                ``timeline``). Tool results are ignored to keep the batch
                cheap and deterministic.

        Returns:
            IngestStats describing what happened.
        """
        if not messages:
            return IngestStats()

        transcript = self._render_transcript(messages)
        if not transcript.strip():
            return IngestStats()

        timeline = max(
            (getattr(m, "timeline", 0) or 0) for m in messages
        )

        extraction: Optional[dict[str, Any]] = None
        stats = IngestStats()

        if self.fetcher is not None:
            try:
                result = self.fetcher.fetch(
                    msg=transcript,
                    system_prompt=EXTRACTION_SYSTEM_PROMPT_COMPACT,
                    temperature=0.2,
                    max_tokens=512,
                    context_handler=None,
                )
                usage = getattr(result, "usage", None)
                if usage is not None:
                    self.extra_usage.input_tokens += usage.input_tokens or 0
                    self.extra_usage.output_tokens += usage.output_tokens or 0
                    self.extra_usage.total_tokens += usage.total_tokens or 0
                    self.extra_usage.cached_tokens += usage.cached_tokens or 0
                    self.extra_usage.reasoning_tokens += usage.reasoning_tokens or 0
                self._usage_records.append(UsageRecord("graph_extraction", copy_usage(usage)))
                content = getattr(result, "content", "")
                parsed = _extract_json_object(content) if content else None
                if parsed and parsed.get("entities"):
                    extraction = parsed
                    stats.llm_used = True
                else:
                    stats.error = "LLM returned no usable entities"
            except Exception as exc:  # pragma: no cover - defensive
                stats.error = f"LLM extraction failed: {exc}"

        if extraction is None:
            extraction = extract_regex(transcript)
            stats.fallback_regex = True

        self._apply_extraction(extraction, timeline, stats)
        return stats

    # -- internal ----------------------------------------------------------

    def _render_transcript(self, messages: list[Any]) -> str:
        """Render the newest messages as a bounded transcript."""
        parts: list[str] = []
        used = 0
        for m in reversed(messages):
            role = getattr(m, "role", "")
            content = getattr(m, "content", "") or ""
            if role not in ("user", "assistant") or not content.strip():
                continue
            label = "User" if role == "user" else "Assistant"
            block = f"## {label}\n\n{content.strip()}"
            addition = len(block) + 2
            if parts and used + addition > self.max_batch_chars:
                break
            if not parts and len(block) > self.max_batch_chars:
                block = block[-self.max_batch_chars:]
            parts.append(block)
            used += addition
        parts.reverse()
        return "\n\n".join(parts)

    def _apply_extraction(
        self,
        extraction: dict[str, Any],
        timeline: int,
        stats: IngestStats,
    ) -> None:
        """Upsert extracted entities + relations into the store."""
        entity_map: dict[str, str] = {}  # raw name -> canonical entity id

        entities = extraction.get("entities") or []
        for ent in entities[: self.max_entities_per_batch]:
            if not isinstance(ent, dict):
                continue
            name = str(ent.get("name", "")).strip()
            if not name:
                continue
            etype = str(ent.get("type", "concept")).strip() or "concept"
            aliases = [
                str(a).strip()
                for a in (ent.get("aliases") or [])
                if isinstance(a, str) and a.strip()
            ]
            node = self.store.upsert_entity(
                name=name,
                entity_type=etype,
                aliases=aliases,
                timeline=timeline,
            )
            entity_map[name] = node.id
            stats.entities_added += 1

        relations = extraction.get("relations") or []
        for rel in relations[: self.max_entities_per_batch]:
            if not isinstance(rel, dict):
                continue
            src_name = str(rel.get("src", "")).strip()
            dst_name = str(rel.get("dst", "")).strip()
            relation = str(rel.get("relation", "related_to")).strip() or "related_to"
            if not src_name or not dst_name:
                continue
            src_id = self._resolve_entity_id(src_name, entity_map)
            dst_id = self._resolve_entity_id(dst_name, entity_map)
            if src_id is None or dst_id is None:
                continue
            self.store.upsert_relation(
                source_id=src_id,
                target_id=dst_id,
                relation=relation,
                timeline=timeline,
                weight=1.0,
                valid=True,
                evidence=[timeline] if timeline else None,
            )
            stats.relations_added += 1

    def _resolve_entity_id(
        self,
        name: str,
        entity_map: dict[str, str],
    ) -> Optional[str]:
        """Resolve an entity name to a canonical id, searching by name too."""
        if name in entity_map:
            return entity_map[name]
        node = self.store.find_entity_by_name(name)
        if node is not None:
            return node.id
        # Last resort: upsert as a concept so relation never dangles.
        node = self.store.upsert_entity(name=name, entity_type="concept")
        entity_map[name] = node.id
        return node.id
