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

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [_read_file_tool.py](_read_file_tool.py#L14) | `resolve_inside_root` | `root: Path, candidate: str \| Path` | `Path` | Resolve *candidate* and verify it lies inside *root*. |
| [_read_file_tool.py](_read_file_tool.py#L45) | `_compute_file_attrs` | `path: Path` | `tuple[int, int, str]` | Return (mtime_ns, byte_size, sha256_hex) for a file. |
| [_read_file_tool.py](_read_file_tool.py#L62) | `create_read_file_tool` | `root: Path` | `tuple[Tool, list]` | Create a sandboxed traced ``read_file`` tool for TLB traversal. |
| [core.py](core.py#L40) | `_extract_json` | `text: str` | `str` | Extract the first valid JSON object from arbitrary text. |
| [core.py](core.py#L78) | `_validate_normalized_intent` | `data: dict[str, Any]` | `NormalizedIntent \| None` | Validate and construct a NormalizedIntent from a JSON dict. |
| [core.py](core.py#L107) | `_validate_leaf_files` | `data: Any` | `list[LeafFile]` | Validate leaf_files list from model output. |
| [core.py](core.py#L130) | `_validate_tlb_result` | `data: dict[str, Any]` | `TLBResult` | Validate and construct a TLBResult from a parsed JSON dict. |
| [core.py](core.py#L198) | `normalize_query_key` | `query: str` | `str` | Produce a deterministic normalized key for TLB cache lookup. |
| [core.py](core.py#L256) | `TLBRAGHandler.put_cache_entry` | `query_key: str, node_path: str \| Path, entry_kind: str` | `TLBEntry \| None` | Create and store a validated TLB cache entry. |
| [core.py](core.py#L310) | `TLBRAGHandler.invalidate_cache_entry` | `query_key: str` | `bool` | Remove one cache entry by its normalized query key. |
| [core.py](core.py#L325) | `TLBRAGHandler.clear_cache` | `None` | `int` | Remove all TLB cache entries. |
| [core.py](core.py#L338) | `TLBRAGHandler.save_cache` | `None` | `None` | Persist the TLB cache to disk as JSON. |
| [core.py](core.py#L369) | `TLBRAGHandler._load_cache` | `None` | `None` | Load a previously persisted TLB cache from disk (if present). |
| [core.py](core.py#L400) | `TLBRAGHandler.retrieve` | `query: str` | `TLBResult` | Execute a TLB-like hierarchical retrieval for *query*. |
| [core.py](core.py#L488) | `TLBRAGHandler._run_worker` | `query: str, query_key: str, known_start_node: str \| None` | `TLBResult` | Create a fresh worker, run it, validate results against trace. |
| [core.py](core.py#L559) | `TLBRAGHandler._apply_trace_corrections` | `result: TLBResult, trace: list[ReadTraceEntry]` | `TLBResult` | Override model-reported fields with runtime read-trace evidence. |
| [core.py](core.py#L618) | `TLBRAGHandler._validate_cache_entry` | `entry: TLBEntry` | `TLBEntry \| None` | Check whether a cached TLB entry is still valid. |
| [prompt.py](prompt.py#L132) | `build_base_prompt` | `base_dir: str \| Path, index_file_name: str` | `str` | Build the TLB RAG system prompt for a specific file tree root. |
| [test_helpers.py](test_helpers.py#L6) | `_extract_json` | `text: Any` | `Any` | Implement `_extract_json`. |
| [test_helpers.py](test_helpers.py#L27) | `_dict_to_tlb_result` | `data: Any` | `Any` | Implement `_dict_to_tlb_result`. |
| [tlb_rag_tool.py](tlb_rag_tool.py#L15) | `_serialize` | `value: object` | `object` | Recursively convert dataclass instances to plain dicts and lists. |
| [tlb_rag_tool.py](tlb_rag_tool.py#L35) | `create_tlb_rag_tool` | `root: str \| Path, fetcher_instance: LLMFetcher` | `Tool` | Create a ``tlb_rag`` tool for hierarchical TLB-like RAG retrieval. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [core.py](core.py#L218) | `TLBRAGHandler` | `root: str \| Path, fetcher_instance: LLMFetcher, index_file_name: str, cache_path: str \| Path \| None` | `object` | Handler for TLB-like hierarchical RAG retrieval over a file tree. |
| [type.py](type.py#L11) | `NormalizedIntent` | `namespace: str \| None, entity_type: str \| None, entity: str \| None, information_type: str, aspects: list[str]` | `object` | A normalized retrieval intent decomposed into structured fields. |
| [type.py](type.py#L36) | `LeafFile` | `path: str, reason: str` | `object` | A resolved leaf file containing the requested information. |
| [type.py](type.py#L51) | `CacheCandidate` | `intent_key: str, node_path: str` | `object` | A model-reported suggestion for a TLB cache entry. |
| [type.py](type.py#L66) | `TLBEntry` | `query_key: str, node_path: str, entry_kind: str, file_mtime_ns: int, file_size: int, file_hash: str, created_at: float` | `object` | A verified runtime TLB cache entry mapping a query key to a file path. |
| [type.py](type.py#L90) | `ReadTraceEntry` | `resolved_path: str, is_index: bool, byte_size: int, mtime_ns: int, sha256: str, success: bool, error: str \| None` | `object` | A single file read recorded by the runtime during a worker traversal. |
| [type.py](type.py#L127) | `TLBResult` | `status: str, normalized_intent: NormalizedIntent \| None, tlb_hit: bool, resolved: bool, start_node: str \| None, visited_indexes: list[str], rejected_branches: list[str], leaf_files: list[LeafFile], cache_candidate: CacheCandidate \| None, error: str \| None` | `object` | The complete result of a TLB-like hierarchical RAG retrieval. |

<!-- END GENERATED SYMBOL MAP -->
