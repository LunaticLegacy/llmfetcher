"""Prompts and regex fallbacks for entity/relation extraction.

Two schemas:
- COMPACT (TERAG style): only entity names + types + relations. Low token
  cost, used for incremental conversation ingestion.
- RICH (GraphRAG style): adds aliases and per-entity summary. Used during
  compaction when we already spend tokens on summarisation.

Regex fallback (``extract_regex``) keeps the pipeline working when the LLM
is unavailable or fails: file paths, function/class definitions, imports
and hashtags are cheap, deterministic entity signals.
"""

from __future__ import annotations

import re

ENTITY_TYPES = (
    "person file concept tool framework project decision module class "
    "function package library api database service algorithm other"
)

EXTRACTION_SYSTEM_PROMPT_COMPACT = """You extract a lightweight knowledge graph from a conversation transcript.

Return ONLY a JSON object with this exact shape:
{
  "entities": [{"name": "...", "type": "person|file|concept|tool|framework|project|decision|module|class|function|other", "aliases": ["..."]}],
  "relations": [{"src": "<entity name>", "dst": "<entity name>", "relation": "short verb/noun label"}]
}

Rules:
1. Extract only *important* recurring entities: files, functions, classes, tools, frameworks, projects, key concepts and decisions. Skip greetings and filler.
2. Entity names must be exact strings as they appear (file paths, function names, product names).
3. Relations must connect two entities that both appear in the "entities" list. Use short labels: "fixes", "depends_on", "implements", "uses", "rejects", "replaces", "discusses".
4. "aliases" are optional alternate names for the same entity (max 3).
5. Max 12 entities and 12 relations per batch.
6. Output pure JSON, no commentary."""

EXTRACTION_SYSTEM_PROMPT_RICH = """You build a knowledge graph with entity summaries from a conversation transcript.

Return ONLY a JSON object:
{
  "entities": [{"name": "...", "type": "...", "aliases": [...], "summary": "one sentence"}],
  "relations": [{"src": "...", "dst": "...", "relation": "...", "description": "optional one clause"}]
}

Entity types: person, file, concept, tool, framework, project, decision, module, class, function, package, library, api, database, service, algorithm, other.

Rules:
1. Include important recurring entities and entities central to the discussion.
2. "summary" is a single factual sentence about what this entity is in this conversation.
3. Relations connect entities listed above; labels are short ("fixes", "depends_on", "implements", "uses", "rejects", "replaces", "extends").
4. Max 15 entities and 15 relations.
5. Output pure JSON, no commentary."""

# ---------------------------------------------------------------------------
# Regex fallback
# ---------------------------------------------------------------------------

_FILE_RE = re.compile(
    r"(?<![A-Za-z0-9])[\w./\\-]+\.(?:py|js|ts|jsx|tsx|md|json|yaml|yml|toml|cfg|ini|go|rs|java|c|cpp|cc|h|hpp|sh|bash|sql|xml|html|css|txt)\b",
    re.IGNORECASE,
)
_FUNC_RE = re.compile(
    r"\b(?:def|function|class|struct|interface|trait)\s+([A-Za-z_][A-Za-z0-9_]*)\b"
)
_IMPORT_MODULE_RE = re.compile(r"\b(?:import|from)\s+([A-Za-z_][A-Za-z0-9_.]*)\b")
_HASHTAG_RE = re.compile(r"#([A-Za-z_][A-Za-z0-9_-]{2,})")
_PACKAGE_NAME_RE = re.compile(
    r"\b[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+){1,3}\b"
)

# Tokens that are likely stopwords/too generic for entity extraction.
_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "will",
    "have", "been", "were", "was", "are", "has", "not", "but", "its", "all",
    "can", "you", "your", "our", "their", "about", "what", "when", "where",
    "which", "there", "here", "then", "than", "should", "would", "could",
    "please", "thanks", "thank", "hello", "hi",
}


def extract_regex(text: str) -> dict:
    """Deterministic entity extraction fallback (no LLM required).

    Returns:
        {"entities": [{"name", "type", "aliases"}], "relations": []}
    """
    entities: dict[str, str] = {}  # normalized name -> type
    for m in _FILE_RE.finditer(text):
        entities[m.group(0)] = "file"
    for m in _FUNC_RE.finditer(text):
        entities[m.group(1)] = "function" if m.group(0).startswith(("def", "function")) else "class"
    for m in _IMPORT_MODULE_RE.finditer(text):
        mod = m.group(1).split(".")[0]
        if mod and mod not in _STOPWORDS:
            entities.setdefault(mod, "package")
    for m in _HASHTAG_RE.finditer(text):
        entities.setdefault(m.group(1), "concept")

    entity_list = [
        {"name": name, "type": etype, "aliases": []}
        for name, etype in entities.items()
    ]
    return {"entities": entity_list, "relations": []}

RETRIEVAL_QUERY_EXTRACTION_PROMPT = """You extract the key entities from a user query so they can be matched against a long-term memory knowledge graph.

Return ONLY a JSON object:
{
  "entities": [{"name": "<exact entity name>", "type": "<type>"}]
}

Rules:
1. Extract entities likely stored in memory: files, functions, classes, tools, frameworks, projects, key concepts, decisions, people.
2. Names must be exact (file paths, function names, product names) so they can match graph nodes.
3. Max 5 entities; skip stopwords and generic words.
4. Output pure JSON, no commentary."""
