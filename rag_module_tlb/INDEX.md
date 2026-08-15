# llmfetcher/rag_module_tlb/ — Auditable TLB RAG INDEX

Hierarchical file-tree retrieval over `INDEX.md` files. It uses an isolated
short-lived Agent to navigate the tree, then validates the model's result
against the runtime record of files actually read. It does not use a vector
database or embeddings.

## Files

| File | Current responsibility |
|---|---|
| `core.py` | `TLBRAGHandler`: normalizes query keys; loads, validates, and atomically saves a version-aware TLB cache; creates one fresh worker per cache miss/route hit; validates its claimed result against read-trace evidence. |
| `type.py` | Dataclasses for `NormalizedIntent`, `LeafFile`, `CacheCandidate`, durable `TLBEntry`, `ReadTraceEntry`, and runtime-corrected `TLBResult`. |
| `prompt.py` | Bounded system prompt that instructs the traversal worker to return the `TLBResult` JSON contract. |
| `_read_file_tool.py` | Root-confined `read_file` tool, path resolution, file attributes/hash collection, and the read trace consumed by runtime validation. |
| `tlb_rag_tool.py` | `create_tlb_rag_tool(root, fetcher_instance)`, the public factory that exposes one handler as an Agent tool returning serialized `TLBResult`. |
| `test_helpers.py` | Shared test fixtures/helpers for TLB RAG tests. |
| `__init__.py` | Package exports. |

## Retrieval Lifecycle

```text
query → normalize key → validate persistent cache
                    ├─ validated leaf → resolved result immediately
                    └─ miss / route → fresh isolated worker + read_file tool
                                      → parse JSON → validate against read trace
                                      → validate/cache model cache candidate
```

- A cache entry includes the path, kind (`route` or `leaf`), mtime, size, and
  SHA-256 content hash. Entries are invalidated when any validation fails.
- Default cache location: `<knowledge-root>/.tlb_cache_index.md.json`; writes
  use a temporary replacement file.
- The worker is serialized by an internal agent lock, has no retained context
  between retrievals, and is cleared defensively after each run.
- `visited_indexes` and `leaf_files` are runtime-verified. Rejected branches
  are retained only as model-reported evidence.

## Deliberate Boundaries

- This module navigates documentation/file trees; it is not the graph-memory
  retriever and does not provide semantic/vector search.
- Only files inside the configured root can be resolved or accepted as leaf
  evidence.
- A successful model response is not sufficient: untraced or out-of-root leaf
  paths are discarded.
