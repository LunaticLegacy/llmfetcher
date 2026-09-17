# llmfetcher/memory/ — Long-Term Memory Contracts INDEX

Provider-neutral contracts for retrieval-backed Agent memory.

| File | Responsibility |
|---|---|
| `base.py` | `MemoryItem` frozen fragment and the `MemoryProvider` runtime-checkable protocol. |
| `__init__.py` | Public exports. |

## Boundaries

- This package defines contracts only; concrete stores (graph memory, vector
  knowledge base) live in their own packages.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [base.py](base.py#L30) | `MemoryProvider.search` | `query: str, limit: int, namespace: str` | `list[MemoryItem]` | Return memories relevant to a query. |
| [base.py](base.py#L33) | `MemoryProvider.add` | `item: MemoryItem, namespace: str` | `None` | Persist one memory item in a namespace. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [base.py](base.py#L10) | `MemoryItem` | `content: str, score: float, memory_id: str, metadata: dict[str, Any]` | `object` | One retrieved or persisted memory fragment. |
| [base.py](base.py#L27) | `MemoryProvider` | `None` | `Protocol` | Protocol implemented by vector, hybrid, or remote memory stores. |

<!-- END GENERATED SYMBOL MAP -->
