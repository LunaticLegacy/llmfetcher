# llmfetcher/rag_module/knowledge/ — Knowledge Base INDEX

Local Markdown knowledge base with a facade-oriented public API, deterministic
keyword retrieval, and an optional ChromaDB vector index.

| File | Responsibility |
|---|---|
| `facade.py` | `KnowledgeBase`: public indexing/retrieval facade. |
| `config.py` | `KnowledgeConfig` immutable runtime configuration. |
| `models.py` | Shared value objects (`KnowledgeHit`, `KnowledgeDocument`, `KnowledgeChunk`, `RetrievalQuery`, `VectorHit`, `ManifestMeta`, ...). |
| `markdown_loader.py` | `MarkdownKnowledgeLoader` filesystem scan and title parsing. |
| `manifest_store.py` | `KnowledgeManifestStore` manifest persistence and freshness checks. |
| `embedding_model.py` | `EmbeddingModelProvider` sentence-transformers wrapper. |
| `vector_store.py` | `ChromaVectorStore` adapter. |
| `keyword_retriever.py` | `KeywordRetriever` deterministic keyword scoring. |
| `hybrid_retriever.py` | `HybridRetriever` keyword/vector score fusion. |
| `task_policy.py` | `TaskRetrievalPolicy` task-specific retrieval policy. |
| `index_manager.py` | `VectorIndexManager` vector-index lifecycle orchestration. |
| `context_builder.py` | `TaskContextBuilder` prompt-context formatting. |
| `text_utils.py` | `TextTools` normalization/excerpt helpers. |
| `prompt.py` | Retrieval prompt text constants. |
| `__init__.py` | Public exports. |

## Boundaries

- The vector index is optional; keyword retrieval and Markdown loading work
  without a vector store.
- Index freshness is tracked by the manifest, not by scanning on every query.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [config.py](config.py#L52) | `KnowledgeConfig.from_environment` | `root: Path \| str \| None` | `'KnowledgeConfig'` | Build configuration from environment variables and defaults. |
| [config.py](config.py#L99) | `KnowledgeConfig.index_path` | `None` | `Path` | Return the manifest path inside the configured knowledge root. |
| [config.py](config.py#L110) | `KnowledgeConfig.chroma_path` | `None` | `Path` | Return the Chroma persistence directory path. |
| [context_builder.py](context_builder.py#L28) | `TaskContextBuilder.build` | `hits: List[KnowledgeHit]` | `str` | Build system-prompt context from ranked knowledge hits. |
| [embedding_model.py](embedding_model.py#L39) | `EmbeddingModelProvider.dependencies_available` | `None` | `tuple[bool, str]` | Check whether sentence-transformers can be imported. |
| [embedding_model.py](embedding_model.py#L67) | `EmbeddingModelProvider.get_model` | `None` | `Any` | Load and return the configured embedding model. |
| [embedding_model.py](embedding_model.py#L99) | `EmbeddingModelProvider.resolve_model_source` | `None` | `str` | Resolve the configured model name to a local path when possible. |
| [embedding_model.py](embedding_model.py#L136) | `EmbeddingModelProvider.encode_documents` | `documents: Sequence[str]` | `list[list[float]]` | Encode document texts into normalized embedding vectors. |
| [embedding_model.py](embedding_model.py#L174) | `EmbeddingModelProvider.encode_query` | `query_text: str` | `list[float]` | Encode a query string into one normalized embedding vector. |
| [embedding_model.py](embedding_model.py#L209) | `EmbeddingModelProvider.format_error` | `exc: Exception` | `str` | Format an exception into a compact diagnostic string. |
| [facade.py](facade.py#L102) | `KnowledgeBase.available` | `None` | `bool` | Return whether the knowledge-base directory exists. |
| [facade.py](facade.py#L113) | `KnowledgeBase.search` | `query: str, limit: int` | `list[KnowledgeHit]` | Search the knowledge base by freeform query text. |
| [facade.py](facade.py#L137) | `KnowledgeBase.search_for_task` | `task_name: str, task_type: str, target: str, file_descriptions: str, limit: int` | `list[KnowledgeHit]` | Prefetch knowledge entries relevant to a task. |
| [facade.py](facade.py#L185) | `KnowledgeBase.build_task_context` | `task_name: str, task_type: str, target: str, file_descriptions: str, limit: int` | `str` | Build prompt-ready knowledge context for a task. |
| [facade.py](facade.py#L217) | `KnowledgeBase.ensure_vector_index` | `force: bool` | `dict[str, KnowledgeIndexEntry]` | Ensure the vector index manifest exists and is fresh. |
| [facade.py](facade.py#L230) | `KnowledgeBase.rebuild_vector_index` | `None` | `dict[str, KnowledgeIndexEntry]` | Rebuild the vector index and manifest from source documents. |
| [facade.py](facade.py#L242) | `KnowledgeBase.vector_status` | `None` | `JsonObject` | Return semantic index and dependency status. |
| [facade.py](facade.py#L252) | `KnowledgeBase.get_full_text` | `path: str` | `str \| None` | Retrieve full text content of a knowledge document by its path. |
| [facade.py](facade.py#L277) | `KnowledgeBase._resolve_document_path` | `path: str` | `Path \| None` | Resolve either root-relative or repository-relative document paths. |
| [facade.py](facade.py#L305) | `KnowledgeBase.get_documents_by_paths` | `paths: list[str]` | `dict[str, str]` | Retrieve full text content for multiple documents by their paths. |
| [facade.py](facade.py#L322) | `KnowledgeBase.get_chunk` | `path: str, chunk_key: str, chunk_index: int \| None` | `KnowledgeChunk \| None` | Retrieve one chunk from a knowledge document. |
| [facade.py](facade.py#L372) | `KnowledgeBase.get_chunk_text` | `path: str, chunk_key: str, chunk_index: int \| None` | `str \| None` | Retrieve the raw Markdown content for one chunk. |
| [facade.py](facade.py#L392) | `KnowledgeBase.get_chunk_text_from_hit` | `hit: KnowledgeHit` | `str \| None` | Retrieve chunk text for one ranked retrieval hit. |
| [hybrid_retriever.py](hybrid_retriever.py#L54) | `HybridRetriever.search` | `query: RetrievalQuery` | `list[KnowledgeHit]` | Search documents with hybrid lexical and semantic ranking. |
| [hybrid_retriever.py](hybrid_retriever.py#L128) | `HybridRetriever.fallback_hits_for_task_type` | `task_type: str, limit: int` | `list[KnowledgeHit]` | Build fallback hits for sparse task-aware retrieval. |
| [index_manager.py](index_manager.py#L55) | `VectorIndexManager.ensure_vector_index` | `force: bool` | `dict[str, KnowledgeIndexEntry]` | Ensure the vector manifest exists and matches current documents. |
| [index_manager.py](index_manager.py#L87) | `VectorIndexManager.rebuild_vector_index` | `documents: list \| None` | `dict[str, KnowledgeIndexEntry]` | Rebuild vector index entries and the Chroma collection. |
| [index_manager.py](index_manager.py#L165) | `VectorIndexManager.vector_status` | `None` | `JsonObject` | Return the current vector-index status payload. |
| [index_manager.py](index_manager.py#L203) | `VectorIndexManager.semantic_candidate_limit` | `limit: int, chunk_count: int` | `int` | Calculate the number of vector candidates to request. |
| [index_manager.py](index_manager.py#L219) | `VectorIndexManager.format_error` | `exc: Exception` | `str` | Format an exception into a compact diagnostic string. |
| [keyword_retriever.py](keyword_retriever.py#L28) | `KeywordRetriever.extract_terms` | `values: list[str]` | `list[str]` | Extract searchable keyword terms from text values. |
| [keyword_retriever.py](keyword_retriever.py#L42) | `KeywordRetriever.score_document` | `document: KnowledgeDocument, terms: list[str]` | `int` | Score a document using deterministic keyword matching. |
| [keyword_retriever.py](keyword_retriever.py#L72) | `KeywordRetriever.score_chunk` | `chunk: KnowledgeChunk, terms: list[str]` | `int` | Score a chunk using deterministic keyword matching. |
| [manifest_store.py](manifest_store.py#L33) | `KnowledgeManifestStore.load` | `path: Path \| None` | `dict[str, KnowledgeIndexEntry] \| None` | Load index entries from the manifest file. |
| [manifest_store.py](manifest_store.py#L89) | `KnowledgeManifestStore.save` | `entries: dict[str, KnowledgeIndexEntry], chunk_count: int, backend_ready: bool, last_error: str` | `None` | Write the vector-index manifest to disk. |
| [manifest_store.py](manifest_store.py#L127) | `KnowledgeManifestStore.build_meta` | `entry_count: int, chunk_count: int, backend_ready: bool, last_error: str` | `ManifestMeta` | Build manifest metadata using configured constants. |
| [manifest_store.py](manifest_store.py#L151) | `KnowledgeManifestStore.is_fresh` | `loaded: dict[str, KnowledgeIndexEntry], documents: list[KnowledgeDocument]` | `bool` | Return whether a loaded manifest matches the current documents. |
| [manifest_store.py](manifest_store.py#L181) | `KnowledgeManifestStore.fingerprint_document` | `document: KnowledgeDocument` | `str` | Calculate the manifest fingerprint for a parsed document. |
| [manifest_store.py](manifest_store.py#L195) | `KnowledgeManifestStore.fingerprint_text` | `title: str, content: str` | `str` | Calculate a stable fingerprint from title and content. |
| [manifest_store.py](manifest_store.py#L210) | `KnowledgeManifestStore.document_id` | `relative_path: str` | `str` | Build the stable vector-store document ID for a path. |
| [markdown_loader.py](markdown_loader.py#L30) | `MarkdownKnowledgeLoader.available` | `None` | `bool` | Return whether the configured knowledge root exists. |
| [markdown_loader.py](markdown_loader.py#L40) | `MarkdownKnowledgeLoader.iter_entry_files` | `None` | `Iterable[Path]` | Yield Markdown files that should be treated as knowledge entries. |
| [markdown_loader.py](markdown_loader.py#L72) | `MarkdownKnowledgeLoader.read_document` | `path: Path` | `KnowledgeDocument` | Read and parse a single Markdown knowledge document. |
| [markdown_loader.py](markdown_loader.py#L101) | `MarkdownKnowledgeLoader.load_documents` | `None` | `list[KnowledgeDocument]` | Load every knowledge entry document under the root. |
| [markdown_loader.py](markdown_loader.py#L111) | `MarkdownKnowledgeLoader.extract_title` | `path: Path, content: str` | `str` | Extract a document title from Markdown content. |
| [markdown_loader.py](markdown_loader.py#L140) | `MarkdownKnowledgeLoader._load_ignore_patterns` | `None` | `list[str]` | Load repository-level `.kbignore` patterns. |
| [markdown_loader.py](markdown_loader.py#L161) | `MarkdownKnowledgeLoader._is_ignored_path` | `root_relative: str, patterns: list[str]` | `bool` | Return whether a path matches any configured `.kbignore` pattern. |
| [markdown_loader.py](markdown_loader.py#L168) | `MarkdownKnowledgeLoader._match_ignore_pattern` | `path: str, pattern: str` | `bool` | Match one path against a `.kbignore` pattern. |
| [models.py](models.py#L69) | `KnowledgeIndexEntry.to_dict` | `None` | `JsonObject` | Convert the index entry to a JSON-serializable dictionary. |
| [models.py](models.py#L236) | `ManifestMeta.to_dict` | `None` | `dict[str, Any]` | Convert manifest metadata into a JSON-compatible dictionary. |
| [task_policy.py](task_policy.py#L32) | `TaskRetrievalPolicy.build_freeform_query` | `query: str, limit: int, max_limit: int` | `RetrievalQuery \| None` | Build a normalized retrieval query for direct user search. |
| [task_policy.py](task_policy.py#L60) | `TaskRetrievalPolicy.build_task_query` | `task_name: str, task_type: str, target: str, file_descriptions: str, limit: int` | `RetrievalQuery \| None` | Build a normalized retrieval query from task metadata. |
| [task_policy.py](task_policy.py#L107) | `TaskRetrievalPolicy.default_topic_keywords` | `task_type: str` | `list[str]` | Return default query keywords for a task type. |
| [task_policy.py](task_policy.py#L135) | `TaskRetrievalPolicy.boost_for_task_type` | `document: KnowledgeDocument, task_type: str` | `int` | Return an additional deterministic boost for task-aware search. |
| [task_policy.py](task_policy.py#L151) | `TaskRetrievalPolicy.boost_for_chunk` | `chunk: KnowledgeChunk, task_type: str` | `int` | Return an additional deterministic boost for a chunk hit. |
| [task_policy.py](task_policy.py#L167) | `TaskRetrievalPolicy._boost_for_path_and_text` | `task_type: str, relative_path: str, combined_text: str` | `int` | Apply the old task-specific heuristic to path and text metadata. |
| [task_policy.py](task_policy.py#L190) | `TaskRetrievalPolicy.fallback_paths` | `task_type: str` | `list[Path]` | Return fallback documents for a task type. |
| [text_utils.py](text_utils.py#L40) | `TextTools.extract_terms` | `values: Sequence[str]` | `list[str]` | Extract normalized keyword terms from arbitrary text values. |
| [text_utils.py](text_utils.py#L73) | `TextTools.build_excerpt` | `content: str, terms: Sequence[str]` | `str` | Build a short excerpt from Markdown content. |
| [text_utils.py](text_utils.py#L112) | `TextTools.chunk_document` | `document: KnowledgeDocument` | `list[KnowledgeChunk]` | Split one Markdown document into retrieval chunks. |
| [text_utils.py](text_utils.py#L216) | `TextTools.should_skip_excerpt_line` | `line: str` | `bool` | Return whether a line is unsuitable for excerpt display. |
| [text_utils.py](text_utils.py#L229) | `TextTools.should_skip_excerpt_block` | `block: MarkdownBlock` | `bool` | Return whether a parsed Markdown block is unsuitable for excerpts. |
| [text_utils.py](text_utils.py#L260) | `TextTools.trim_excerpt` | `text: str` | `str` | Normalize and trim an excerpt string. |
| [text_utils.py](text_utils.py#L279) | `TextTools.build_chunk_semantic_document` | `chunk: KnowledgeChunk` | `str` | Build the text payload stored for one semantic chunk. |
| [text_utils.py](text_utils.py#L302) | `TextTools.build_semantic_document` | `title: str, relative_path: str, content: str` | `str` | Build the text payload stored in the semantic vector index. |
| [text_utils.py](text_utils.py#L323) | `TextTools.excerpt_from_semantic_document` | `document: str` | `str` | Extract a display excerpt from a stored semantic document payload. |
| [text_utils.py](text_utils.py#L341) | `TextTools._markdown_blocks` | `content: str` | `list[MarkdownBlock]` | Split raw markdown into heading and body blocks. |
| [text_utils.py](text_utils.py#L363) | `TextTools._markdown_blocks_from_tokens` | `tokens: list[Token], lines: list[str], line_offset: int` | `list[MarkdownBlock]` | Convert markdown-it tokens into logical Markdown blocks. |
| [text_utils.py](text_utils.py#L441) | `TextTools._fallback_markdown_blocks` | `content: str, line_offset: int` | `list[MarkdownBlock]` | Split markdown with a conservative line-based fallback parser. |
| [text_utils.py](text_utils.py#L490) | `TextTools._block_from_token` | `token: Token, lines: list[str], line_offset: int, kind: str, text: str \| None, level: int \| None, info: str \| None` | `MarkdownBlock \| None` | Build a `MarkdownBlock` from a markdown-it token. |
| [text_utils.py](text_utils.py#L512) | `TextTools._token_lines` | `token: Token, line_offset: int, line_count: int` | `tuple[int, int]` | Return 1-based original line numbers for a token. |
| [text_utils.py](text_utils.py#L523) | `TextTools._raw_block_text` | `token: Token, lines: list[str], default: str` | `str` | Extract the source slice for a token when line information exists. |
| [text_utils.py](text_utils.py#L535) | `TextTools._next_inline_token` | `tokens: list[Token], index: int` | `Token \| None` | Return the next inline token after a block opener, if present. |
| [text_utils.py](text_utils.py#L541) | `TextTools._skip_until` | `tokens: list[Token], index: int, token_type: str` | `int` | Advance the token index until the matching close token is seen. |
| [text_utils.py](text_utils.py#L549) | `TextTools._inline_text` | `token: Token \| None` | `str` | Render inline markdown tokens as readable text. |
| [text_utils.py](text_utils.py#L563) | `TextTools._heading_level` | `token: Token` | `int \| None` | Convert a markdown-it heading token tag into a numeric level. |
| [text_utils.py](text_utils.py#L569) | `TextTools._strip_yaml_frontmatter` | `content: str` | `tuple[str, int]` | Remove a leading YAML frontmatter block before Markdown parsing. |
| [text_utils.py](text_utils.py#L594) | `TextTools._chunk_key` | `source_path: str, chunk_index: int, start_line: int, end_line: int, heading_path: str, chunk_title: str, content: str` | `str` | Build a stable chunk identifier for vector storage. |
| [vector_store.py](vector_store.py#L40) | `ChromaVectorStore.dependencies_available` | `None` | `tuple[bool, str]` | Check whether ChromaDB can be imported. |
| [vector_store.py](vector_store.py#L67) | `ChromaVectorStore.rebuild` | `ids: Sequence[str], documents: Sequence[str], metadatas: Sequence[dict[str, str]]` | `bool` | Rebuild the Chroma collection with supplied documents. |
| [vector_store.py](vector_store.py#L104) | `ChromaVectorStore.query` | `query_text: str, limit: int` | `dict[str, VectorHit]` | Query the Chroma collection for semantic candidates. |
| [vector_store.py](vector_store.py#L170) | `ChromaVectorStore.get_client` | `None` | `Any` | Return the persistent ChromaDB client. |
| [vector_store.py](vector_store.py#L192) | `ChromaVectorStore.get_collection` | `recreate: bool` | `Any \| None` | Return the configured Chroma collection. |
| [vector_store.py](vector_store.py#L235) | `ChromaVectorStore.create_collection` | `client: Any` | `Any` | Create or fetch the configured Chroma collection. |
| [vector_store.py](vector_store.py#L268) | `ChromaVectorStore.distance_to_similarity` | `distance: Any` | `float` | Convert Chroma cosine distance to bounded similarity. |
| [vector_store.py](vector_store.py#L289) | `ChromaVectorStore.format_error` | `exc: Exception` | `str` | Format an exception into a compact diagnostic string. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [config.py](config.py#L11) | `KnowledgeConfig` | `root: Path, embedding_model_name: str, local_files_only: bool, result_limit: int, context_limit: int, excerpt_chars: int, embedding_max_chars: int, chunk_max_chars: int, chunk_overlap_chars: int, semantic_candidates: int, strategy_prefix: str, index_filename: str, chroma_dirname: str, collection_name: str, manifest_version: int, semantic_backend: str` | `object` | Stores runtime configuration for knowledge-base indexing and retrieval. |
| [context_builder.py](context_builder.py#L10) | `TaskContextBuilder` | `strategy_prefix: str` | `object` | Formats retrieval results into task-oriented prompt context. |
| [embedding_model.py](embedding_model.py#L14) | `EmbeddingModelProvider` | `config: KnowledgeConfig` | `object` | Loads and uses the configured sentence-transformers embedding model. |
| [facade.py](facade.py#L25) | `KnowledgeBase` | `root: Path \| None` | `object` | Facade for local Markdown knowledge-base retrieval and indexing. |
| [hybrid_retriever.py](hybrid_retriever.py#L15) | `HybridRetriever` | `config: KnowledgeConfig, loader: MarkdownKnowledgeLoader, keyword: KeywordRetriever, vector_store: ChromaVectorStore, index_manager: VectorIndexManager, policy: TaskRetrievalPolicy, text: TextTools` | `object` | Merges keyword scores, vector scores, and task-policy boosts. |
| [index_manager.py](index_manager.py#L18) | `VectorIndexManager` | `config: KnowledgeConfig, loader: MarkdownKnowledgeLoader, manifest: KnowledgeManifestStore, vector_store: ChromaVectorStore, embeddings: EmbeddingModelProvider, text: TextTools` | `object` | Coordinates manifest freshness checks and vector-index rebuilds. |
| [keyword_retriever.py](keyword_retriever.py#L11) | `KeywordRetriever` | `text: TextTools` | `object` | Scores documents using deterministic title, path, and content matches. |
| [manifest_store.py](manifest_store.py#L14) | `KnowledgeManifestStore` | `config: KnowledgeConfig` | `object` | Reads, writes, and validates the `.vector_index.json` manifest. |
| [markdown_loader.py](markdown_loader.py#L12) | `MarkdownKnowledgeLoader` | `root: Path` | `object` | Loads Markdown knowledge documents from a configured root directory. |
| [models.py](models.py#L13) | `KnowledgeHit` | `path: str, title: str, score: float, excerpt: str, chunk_key: str, chunk_index: int, chunk_title: str, heading_path: str, start_line: int, end_line: int, keyword_score: float, vector_score: float` | `object` | Represents one final knowledge-base retrieval result. |
| [models.py](models.py#L49) | `KnowledgeIndexEntry` | `path: str, title: str, fingerprint: str, excerpt: str, document_id: str` | `object` | Represents one document entry stored in the vector-index manifest. |
| [models.py](models.py#L84) | `KnowledgeDocument` | `absolute_path: Path, root_relative_path: str, repository_relative_path: str, title: str, content: str` | `object` | Represents one parsed Markdown document from the knowledge root. |
| [models.py](models.py#L106) | `KnowledgeChunk` | `source_path: str, source_title: str, chunk_key: str, chunk_index: int, chunk_title: str, heading_path: str, start_line: int, end_line: int, content: str` | `object` | Represents one chunk produced from a source Markdown document. |
| [models.py](models.py#L136) | `MarkdownBlock` | `kind: str, text: str, start_line: int, end_line: int, level: int \| None, info: str \| None` | `object` | Represent one logical block extracted from Markdown content. |
| [models.py](models.py#L159) | `VectorHit` | `path: str, chunk_key: str, chunk_index: int, chunk_title: str, heading_path: str, start_line: int, end_line: int, score: float, excerpt: str` | `object` | Represents one semantic retrieval result from the vector backend. |
| [models.py](models.py#L189) | `RetrievalQuery` | `query_text: str, terms: list[str], limit: int, task_type: str, semantic_multiplier: float` | `object` | Represents a normalized retrieval request. |
| [models.py](models.py#L212) | `ManifestMeta` | `version: int, backend: str, embedding_model: str, backend_ready: bool, entry_count: int, chunk_count: int, last_error: str` | `object` | Represents manifest-level metadata stored beside vector entries. |
| [task_policy.py](task_policy.py#L11) | `TaskRetrievalPolicy` | `keyword: KeywordRetriever, root: Path` | `object` | Builds retrieval queries and task-specific boosts. |
| [text_utils.py](text_utils.py#L16) | `TextTools` | `excerpt_chars: int, embedding_max_chars: int, chunk_max_chars: int` | `object` | Provides reusable text extraction and excerpt helpers. |
| [vector_store.py](vector_store.py#L13) | `ChromaVectorStore` | `config: KnowledgeConfig, embeddings: EmbeddingModelProvider, text: TextTools` | `object` | Wraps ChromaDB collection management and semantic querying. |

<!-- END GENERATED SYMBOL MAP -->
