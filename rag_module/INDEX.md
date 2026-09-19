# llmfetcher/rag_module/ — Local Knowledge RAG INDEX

Legacy knowledge-base entry point and its refactored subpackage.

| File | Responsibility |
|---|---|
| `knowledge_base.py` | Backward-compatible import shim re-exporting the refactored `knowledge/` package. |
| [`knowledge/INDEX.md`](knowledge/INDEX.md) | Local filesystem + ChromaDB knowledge base (facade, index lifecycle, retrieval). |
| `__init__.py` | `from .knowledge_base import *`. |

## Boundaries

- This is the knowledge/vector RAG path; it is unrelated to
  [`../rag_module_tlb/INDEX.md`](../rag_module_tlb/INDEX.md), the auditable
  `INDEX.md`-tree traversal.
- `README_REFACTOR.md` and `TODO` are developer notes, not runtime authority.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| — | — | `None` | `None` | 本索引范围不直接拥有可执行函数；沿 Route Map 进入下级索引。 |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| — | — | `None` | `object` | 本索引范围不直接声明类；沿 Route Map 进入下级索引。 |

<!-- END GENERATED SYMBOL MAP -->
