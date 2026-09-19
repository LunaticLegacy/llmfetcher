# llmfetcher/graph_memory/ — Graph Long-Term Memory INDEX

Persistent entity/relation memory (GraphRAG-style) layered on top of durable
linear context.

| File | Responsibility |
|---|---|
| `handler.py` | `GraphContextHandler`: linear context plus graph long-term memory; atomically commits graph generations. |
| `graph_store.py` | `GraphStore` and `normalize_entity_id`: temporal entity/relation persistence. |
| `builder.py` | `GraphBuilder` incremental extraction; `ExtractionFetcher`, `IngestStats`. |
| `retriever.py` | `GraphRetriever` hybrid four-channel retrieval; `RetrievalConfig`, `GraphRetrievalResult`, `render_graph_memory`. |
| `semantic.py` | `SemanticGraphWorker`: stateless adapter for extraction/reranking LLM calls. |
| `models.py` | Dataclasses: `EntityNode`, `RelationEdge`, `CommunitySummary`, `GraphHit`, `GraphMemoryState`. |
| `extraction_prompts.py` | Prompts and regex fallbacks for entity/relation extraction. |
| `__init__.py` | Public exports. |

## Boundaries

- Extraction and reranking calls are isolated from the primary Agent's tools
  and transcript.
- A generation graph is written first, then its filename is committed through
  the primary context JSON; legacy `<context-path>.graph.json` remains readable.

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [builder.py](builder.py#L33) | `ExtractionFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Any, backend_name: Optional[str], tools: Any` | `Any` | Return an object with a ``content`` attribute. |
| [builder.py](builder.py#L57) | `IngestStats.__str__` | `None` | `str` | Implement `IngestStats.__str__`. |
| [builder.py](builder.py#L65) | `_extract_json_object` | `text: str` | `Optional[dict[str, Any]]` | Extract the first valid JSON object from arbitrary text. |
| [builder.py](builder.py#L102) | `GraphBuilder.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed graph-extraction calls exactly once. |
| [builder.py](builder.py#L108) | `GraphBuilder.ingest` | `messages: list[Any]` | `IngestStats` | Extract and upsert entities/relations from an LLMContext list. |
| [builder.py](builder.py#L169) | `GraphBuilder._render_transcript` | `messages: list[Any]` | `str` | Render the newest messages as a bounded transcript. |
| [builder.py](builder.py#L195) | `GraphBuilder._apply_extraction` | `extraction: dict[str, Any], timeline: int, stats: IngestStats` | `None` | Upsert extracted entities + relations into the store. |
| [builder.py](builder.py#L250) | `GraphBuilder._resolve_entity_id` | `name: str, entity_map: dict[str, str]` | `Optional[str]` | Resolve an entity name to a canonical id, searching by name too. |
| [extraction_prompts.py](extraction_prompts.py#L83) | `extract_regex` | `text: str` | `dict` | Deterministic entity extraction fallback (no LLM required). |
| [graph_store.py](graph_store.py#L31) | `normalize_entity_id` | `name: str, entity_type: str` | `str` | Produce a deterministic stable id for an entity name. |
| [graph_store.py](graph_store.py#L51) | `personalized_pagerank` | `adjacency: dict[str, list[str]], seed_ids: Iterable[str], alpha: float, max_iter: int, tol: float` | `dict[str, float]` | Personalized PageRank over an undirected adjacency map. |
| [graph_store.py](graph_store.py#L118) | `GraphStore.upsert_entity` | `name: str, entity_type: str, aliases: Optional[list[str]], timeline: Optional[int], summary: Optional[str], embedding: Optional[list[float]]` | `EntityNode` | Insert or merge an entity. |
| [graph_store.py](graph_store.py#L173) | `GraphStore._find_same_as` | `entity_id: str, name: str, aliases: list[str]` | `Optional[EntityNode]` | Find an existing node that should be merged with the new entity. |
| [graph_store.py](graph_store.py#L190) | `GraphStore.get_entity` | `entity_id: str` | `Optional[EntityNode]` | Implement `GraphStore.get_entity`. |
| [graph_store.py](graph_store.py#L193) | `GraphStore.find_entity_by_name` | `name: str, entity_type: str` | `Optional[EntityNode]` | Find an entity by (possibly partial) name or alias match. |
| [graph_store.py](graph_store.py#L219) | `GraphStore.upsert_relation` | `source_id: str, target_id: str, relation: str, timeline: Optional[int], weight: float, valid: bool, evidence: Optional[list[int]]` | `Optional[RelationEdge]` | Insert or merge an undirected relation edge. |
| [graph_store.py](graph_store.py#L269) | `GraphStore._iter_edges_between` | `a: str, b: str` | `Iterable[RelationEdge]` | Implement `GraphStore._iter_edges_between`. |
| [graph_store.py](graph_store.py#L274) | `GraphStore.edges` | `None` | `list[RelationEdge]` | Implement `GraphStore.edges`. |
| [graph_store.py](graph_store.py#L277) | `GraphStore.edges_for` | `entity_id: str` | `list[RelationEdge]` | Implement `GraphStore.edges_for`. |
| [graph_store.py](graph_store.py#L284) | `GraphStore.neighbors` | `entity_id: str, max_hop: int` | `dict[str, int]` | Return neighbor entity ids at exact hop distance <= max_hop. |
| [graph_store.py](graph_store.py#L305) | `GraphStore.invalidate_relation` | `source_id: str, target_id: str` | `int` | Mark all relations between two entities invalid (fact superseded). |
| [graph_store.py](graph_store.py#L316) | `GraphStore._adjacency` | `valid_only: bool` | `dict[str, list[str]]` | Implement `GraphStore._adjacency`. |
| [graph_store.py](graph_store.py#L325) | `GraphStore.pagerank` | `seed_ids: Iterable[str], alpha: float, max_iter: int, tol: float` | `dict[str, float]` | Personalized PageRank from seed entities (graph diffusion). |
| [graph_store.py](graph_store.py#L337) | `GraphStore.detect_communities` | `seed: int` | `list[list[str]]` | Community detection via NetworkX Louvain. |
| [graph_store.py](graph_store.py#L364) | `GraphStore._communities_connected_components` | `None` | `list[list[str]]` | Implement `GraphStore._communities_connected_components`. |
| [graph_store.py](graph_store.py#L393) | `GraphStore.time_decay` | `age: int, lam: float` | `float` | Recency weight for an entity/relation of given timeline age. |
| [graph_store.py](graph_store.py#L404) | `GraphStore.subgraph` | `entity_ids: Iterable[str], hop: int` | `tuple[dict[str, EntityNode], list[RelationEdge]]` | Export nodes + edges within ``hop`` hops of the given seeds. |
| [graph_store.py](graph_store.py#L438) | `GraphStore.to_state` | `None` | `GraphMemoryState` | Implement `GraphStore.to_state`. |
| [graph_store.py](graph_store.py#L449) | `GraphStore.clear` | `None` | `None` | Reset the graph to an empty state (keeps the lock alive). |
| [graph_store.py](graph_store.py#L461) | `GraphStore.from_state` | `state: GraphMemoryState` | `None` | Implement `GraphStore.from_state`. |
| [graph_store.py](graph_store.py#L472) | `GraphStore.to_dict` | `None` | `dict[str, Any]` | Implement `GraphStore.to_dict`. |
| [graph_store.py](graph_store.py#L475) | `GraphStore.from_dict` | `data: dict[str, Any]` | `None` | Implement `GraphStore.from_dict`. |
| [graph_store.py](graph_store.py#L478) | `GraphStore.save` | `path: str \| Path` | `bool` | Serialize the graph to JSON. Returns True on success. |
| [graph_store.py](graph_store.py#L511) | `GraphStore.load` | `path: str \| Path` | `bool` | Deserialize the graph from JSON. Returns True on success. |
| [graph_store.py](graph_store.py#L525) | `GraphStore.__len__` | `None` | `int` | Implement `GraphStore.__len__`. |
| [handler.py](handler.py#L106) | `GraphContextHandler._init_session_state` | `None` | `None` | (Re)set all per-session transient state (keeps long-term graph). |
| [handler.py](handler.py#L117) | `GraphContextHandler.has_retrieved` | `None` | `bool` | True once a retrieval has been performed this session. |
| [handler.py](handler.py#L122) | `GraphContextHandler.graph_memory` | `None` | `str` | Last rendered ``<graph_memory>`` block (empty when none). |
| [handler.py](handler.py#L127) | `GraphContextHandler.compaction_generation` | `None` | `int` | Number of compactions observed since the session started. |
| [handler.py](handler.py#L132) | `GraphContextHandler.compress_threshold` | `None` | `int` | Compaction threshold forwarded from the inner linear handler. |
| [handler.py](handler.py#L142) | `GraphContextHandler.extra_usage` | `None` | `Any` | Aggregate token usage from linear compaction + graph LLM calls. |
| [handler.py](handler.py#L162) | `GraphContextHandler.record_usage` | `usage: Optional[Any]` | `None` | Forward one internal LLM call's usage to the inner linear handler. |
| [handler.py](handler.py#L166) | `GraphContextHandler.drain_usage_records` | `None` | `list[UsageRecord]` | Drain child internal-call records in the order their components run. |
| [handler.py](handler.py#L180) | `GraphContextHandler.retrieve` | `query: str` | `GraphRetrievalResult` | Run hybrid graph retrieval and store the rendered context block. |
| [handler.py](handler.py#L198) | `GraphContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append a user message and trigger retrieval when due. |
| [handler.py](handler.py#L217) | `GraphContextHandler.add_assistant_message` | `message: LLMOutput, tool_results: Optional[dict[str, str]], usage: Optional[dict[str, int]], model_duration_ms: Optional[int], round_duration_ms: Optional[int], created_at: Optional[float]` | `None` | Append an assistant output, detect compaction and flush the graph. |
| [handler.py](handler.py#L255) | `GraphContextHandler.build_messages` | `None` | `list[dict[str, Any]]` | Build messages: graph memory block (user), then linear history. |
| [handler.py](handler.py#L266) | `GraphContextHandler.save` | `path: str \| Path` | `bool` | Save the conversation AND the companion graph file. |
| [handler.py](handler.py#L308) | `GraphContextHandler.load` | `path: str \| Path` | `bool` | Restore the conversation and its companion graph. |
| [handler.py](handler.py#L379) | `GraphContextHandler.clear_context` | `None` | `bool` | Clear the session but keep the long-term memory graph. |
| [handler.py](handler.py#L387) | `GraphContextHandler._retrieve_archive_evidence` | `query: str` | `str` | Render small, provenance-labelled raw evidence for a new query. |
| [handler.py](handler.py#L420) | `GraphContextHandler._should_retrieve` | `None` | `bool` | Decide whether this newly stored user message should retrieve. |
| [handler.py](handler.py#L437) | `GraphContextHandler._flush_pending` | `None` | `None` | Ingest buffered messages into the graph and clear the buffer. |
| [models.py](models.py#L42) | `EntityNode.to_dict` | `None` | `dict[str, Any]` | Implement `EntityNode.to_dict`. |
| [models.py](models.py#L46) | `EntityNode.from_dict` | `data: dict[str, Any]` | `'EntityNode'` | Implement `EntityNode.from_dict`. |
| [models.py](models.py#L86) | `RelationEdge.key` | `None` | `tuple[str, str]` | Undirected canonical edge key (sorted pair). |
| [models.py](models.py#L91) | `RelationEdge.to_dict` | `None` | `dict[str, Any]` | Implement `RelationEdge.to_dict`. |
| [models.py](models.py#L95) | `RelationEdge.from_dict` | `data: dict[str, Any]` | `'RelationEdge'` | Implement `RelationEdge.from_dict`. |
| [models.py](models.py#L122) | `CommunitySummary.to_dict` | `None` | `dict[str, Any]` | Implement `CommunitySummary.to_dict`. |
| [models.py](models.py#L126) | `CommunitySummary.from_dict` | `data: dict[str, Any]` | `'CommunitySummary'` | Implement `CommunitySummary.from_dict`. |
| [models.py](models.py#L145) | `GraphHit.to_dict` | `None` | `dict[str, Any]` | Implement `GraphHit.to_dict`. |
| [models.py](models.py#L164) | `GraphMemoryState.to_dict` | `None` | `dict[str, Any]` | Implement `GraphMemoryState.to_dict`. |
| [models.py](models.py#L177) | `GraphMemoryState.from_dict` | `data: dict[str, Any]` | `'GraphMemoryState'` | Implement `GraphMemoryState.from_dict`. |
| [retriever.py](retriever.py#L53) | `_tokenize` | `text: str` | `list[str]` | Casefolded alnum/underscore tokens (keeps ``graph_store`` intact). |
| [retriever.py](retriever.py#L58) | `_alnum` | `text: str` | `str` | Strip every non-alphanumeric char (for fuzzy exact-name matching). |
| [retriever.py](retriever.py#L63) | `_cosine` | `a: list[float], b: list[float]` | `float` | Implement `_cosine`. |
| [retriever.py](retriever.py#L74) | `_jaccard` | `a: Iterable[str], b: Iterable[str]` | `float` | Implement `_jaccard`. |
| [retriever.py](retriever.py#L82) | `_bm25_scores` | `docs: list[list[str]], query_tokens: list[str], k1: float, b: float` | `list[float]` | Classic BM25 term-scores for each document against the query. |
| [retriever.py](retriever.py#L119) | `_normalize` | `scores: dict[str, float]` | `dict[str, float]` | Divide by the channel max -> [0, 1]. All-zero -> all zero. |
| [retriever.py](retriever.py#L158) | `RetrievalConfig.effective_weights` | `None` | `tuple[float, float, float, float]` | Implement `RetrievalConfig.effective_weights`. |
| [retriever.py](retriever.py#L189) | `GraphRetrievalResult.empty` | `None` | `bool` | Implement `GraphRetrievalResult.empty`. |
| [retriever.py](retriever.py#L192) | `GraphRetrievalResult.to_dict` | `None` | `dict[str, Any]` | Implement `GraphRetrievalResult.to_dict`. |
| [retriever.py](retriever.py#L207) | `GraphRetrievalResult.from_dict` | `data: dict[str, Any]` | `'GraphRetrievalResult'` | Implement `GraphRetrievalResult.from_dict`. |
| [retriever.py](retriever.py#L243) | `render_graph_memory` | `query: str, seed_entities: Optional[list[EntityNode]], hits: Optional[list[GraphHit]], expanded: Optional[dict[str, EntityNode]], relations: Optional[list[RelationEdge]], communities: Optional[list[CommunitySummary]]` | `str` | Render retrieval results as a user-role ``<graph_memory>`` block. |
| [retriever.py](retriever.py#L356) | `GraphRetriever.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed graph-query calls exactly once. |
| [retriever.py](retriever.py#L362) | `GraphRetriever.retrieve` | `query: str, current_timeline: Optional[int]` | `GraphRetrievalResult` | Run the hybrid retrieval pipeline and render the context block. |
| [retriever.py](retriever.py#L416) | `GraphRetriever._semantic_rerank` | `query: str, hits: list[GraphHit]` | `list[GraphHit]` | Optionally let a stateless semantic worker reorder fused hits. |
| [retriever.py](retriever.py#L456) | `GraphRetriever._extract_seed_entities` | `query: str` | `list[EntityNode]` | Resolve query entities to graph nodes (LLM then regex fallback). |
| [retriever.py](retriever.py#L500) | `GraphRetriever._channel_vector` | `query: str, seed_nodes: list[EntityNode], node_ids: list[str]` | `dict[str, float]` | Seed-anchored cosine over embeddings; token Jaccard fallback. |
| [retriever.py](retriever.py#L529) | `GraphRetriever._channel_ppr` | `seed_nodes: list[EntityNode], node_ids: list[str]` | `dict[str, float]` | Implement `GraphRetriever._channel_ppr`. |
| [retriever.py](retriever.py#L539) | `GraphRetriever._channel_keyword` | `query: str, node_ids: list[str]` | `dict[str, float]` | BM25 + exact/substring bonus over name/aliases/summary. |
| [retriever.py](retriever.py#L569) | `GraphRetriever._channel_time` | `node_ids: list[str], current_timeline: int` | `dict[str, float]` | Implement `GraphRetriever._channel_time`. |
| [retriever.py](retriever.py#L582) | `GraphRetriever._fuse` | `query: str, seed_nodes: list[EntityNode], current_timeline: int` | `list[GraphHit]` | Implement `GraphRetriever._fuse`. |
| [retriever.py](retriever.py#L618) | `GraphRetriever._expand` | `hits: list[GraphHit]` | `dict[str, EntityNode]` | Top-K hits + their neighbors; annotate hit metadata. |
| [retriever.py](retriever.py#L650) | `GraphRetriever._collect_relations` | `expanded: dict[str, EntityNode]` | `list[RelationEdge]` | Implement `GraphRetriever._collect_relations`. |
| [retriever.py](retriever.py#L662) | `GraphRetriever._select_communities` | `hits: list[GraphHit]` | `list[CommunitySummary]` | Implement `GraphRetriever._select_communities`. |
| [semantic.py](semantic.py#L33) | `SemanticGraphWorker.drain_rerank_usage_records` | `None` | `list[UsageRecord]` | Return usage from direct reranking calls exactly once. |
| [semantic.py](semantic.py#L42) | `SemanticGraphWorker.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Any, backend_name: Optional[str], tools: Any` | `Any` | Make one isolated completion, discarding caller history/tools. |
| [semantic.py](semantic.py#L63) | `SemanticGraphWorker.rerank` | `query: str, candidates: list[dict[str, Any]], max_tokens: int` | `list[str]` | Return valid candidate IDs in semantic relevance order. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [builder.py](builder.py#L30) | `ExtractionFetcher` | `None` | `Protocol` | Minimal LLM interface used for graph extraction. |
| [builder.py](builder.py#L48) | `IngestStats` | `entities_added: int, relations_added: int, llm_used: bool, fallback_regex: bool, error: str` | `object` | Statistics for one ingest batch. |
| [builder.py](builder.py#L84) | `GraphBuilder` | `store: GraphStore, fetcher: Optional[ExtractionFetcher], max_batch_chars: int, max_entities_per_batch: int` | `object` | Incremental conversation -> memory-graph builder. |
| [graph_store.py](graph_store.py#L104) | `GraphStore` | `None` | `object` | In-memory entity-relation graph with temporal + provenance metadata. |
| [handler.py](handler.py#L42) | `GraphContextHandler` | `compacting_fetcher: CompactionFetcher, extraction_fetcher: Optional[ExtractionFetcher], query_fetcher: Optional[ExtractionFetcher], store: Optional[GraphStore], retriever_config: Optional[RetrievalConfig], retrieval_trigger: str, graph_update_every: int, max_context_threshold: int, compaction_output_max_tokens: int, graph_save_suffix: str` | `ContextHandler` | A context handler with an entity-relation long-term memory graph. |
| [models.py](models.py#L15) | `EntityNode` | `id: str, name: str, entity_type: str, aliases: list[str], summary: str, first_seen: int, last_seen: int, freq: int, embedding: Optional[list[float]]` | `object` | A single entity in the memory graph. |
| [models.py](models.py#L61) | `RelationEdge` | `source_id: str, target_id: str, relation: str, weight: float, first_seen: int, last_seen: int, valid: bool, evidence: list[int]` | `object` | A relation between two entities with temporal attributes. |
| [models.py](models.py#L109) | `CommunitySummary` | `level: int, community_id: str, summary: str, member_entity_ids: list[str], source_timelines: list[int]` | `object` | Summary of one community (cluster) of the memory graph. |
| [models.py](models.py#L137) | `GraphHit` | `entity: EntityNode, score: float, matched_relation: Optional[str], neighbor_ids: list[str]` | `object` | One retrieval hit: an entity plus its fused score. |
| [models.py](models.py#L155) | `GraphMemoryState` | `version: int, nodes: dict[str, EntityNode], edges: list[RelationEdge], communities: dict[int, list[CommunitySummary]], next_id: int` | `object` | Serialization container for the whole memory graph. |
| [retriever.py](retriever.py#L135) | `RetrievalConfig` | `w_vec: float, w_ppr: float, w_kw: float, w_time: float, top_k: int, max_relations: int, max_communities: int, hop: int, time_decay_lambda: float, min_fused_score: float, include_neighbors: bool, include_communities: bool` | `object` | Weights and limits for the four-channel fusion retrieval. |
| [retriever.py](retriever.py#L176) | `GraphRetrievalResult` | `query: str, seed_entities: list[EntityNode], hits: list[GraphHit], expanded_entities: dict[str, EntityNode], relations: list[RelationEdge], community_summaries: list[CommunitySummary], rendered: str, current_timeline: int` | `object` | Output of :meth:`GraphRetriever.retrieve`. |
| [retriever.py](retriever.py#L329) | `GraphRetriever` | `store: GraphStore, query_fetcher: Optional[ExtractionFetcher], config: Optional[RetrievalConfig], query_prompt: str` | `object` | Four-channel hybrid retrieval over a :class:`GraphStore`. |
| [semantic.py](semantic.py#L19) | `SemanticGraphWorker` | `fetcher: Any, backend_name: Optional[str]` | `object` | A no-history, no-tools adapter for graph semantic work. |

<!-- END GENERATED SYMBOL MAP -->
