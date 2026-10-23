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
| [builder.py](builder.py#L54) | `_tool_evidence_allowed` | `name: str` | `bool` | Return whether a tool result is useful as graph extraction evidence. |
| [builder.py](builder.py#L65) | `_is_noise_entity` | `name: str, entity_type: str` | `bool` | Reject transient artifacts and generic runtime vocabulary. |
| [builder.py](builder.py#L89) | `ExtractionFetcher.fetch` | `msg: str, system_prompt: Optional[str], temperature: float, max_tokens: int, context_handler: Any, backend_name: Optional[str], tools: Any` | `Any` | Return an object with a ``content`` attribute. |
| [builder.py](builder.py#L113) | `IngestStats.__str__` | `None` | `str` | Implement `IngestStats.__str__`. |
| [builder.py](builder.py#L121) | `_extract_json_object` | `text: str` | `Optional[dict[str, Any]]` | Extract the first valid JSON object from arbitrary text. |
| [builder.py](builder.py#L158) | `GraphBuilder.drain_usage_records` | `None` | `list[UsageRecord]` | Return completed graph-extraction calls exactly once. |
| [builder.py](builder.py#L164) | `GraphBuilder.ingest` | `messages: list[ContextItem], results: Mapping[str, ToolResultRecord]` | `IngestStats` | Extract and upsert entities/relations from a context-item list. |
| [builder.py](builder.py#L239) | `GraphBuilder._render_transcript` | `messages: list[ContextItem], results: Mapping[str, ToolResultRecord], include_tool_evidence: bool` | `str` | Render newest messages plus bounded tool evidence. |
| [builder.py](builder.py#L315) | `GraphBuilder._apply_extraction` | `extraction: dict[str, Any], timeline: int, stats: IngestStats` | `None` | Upsert extracted entities + relations into the store. |
| [builder.py](builder.py#L374) | `GraphBuilder._resolve_entity_id` | `name: str, entity_map: dict[str, str]` | `Optional[str]` | Resolve an entity name to a canonical id, searching by name too. |
| [extraction_prompts.py](extraction_prompts.py#L85) | `extract_regex` | `text: str` | `dict` | Deterministic entity extraction fallback (no LLM required). |
| [graph_store.py](graph_store.py#L32) | `normalize_entity_id` | `name: str, entity_type: str` | `str` | Produce a deterministic stable id for an entity name. |
| [graph_store.py](graph_store.py#L59) | `personalized_pagerank` | `adjacency: dict[str, list[str]], seed_ids: Iterable[str], alpha: float, max_iter: int, tol: float` | `dict[str, float]` | Personalized PageRank over an undirected adjacency map. |
| [graph_store.py](graph_store.py#L126) | `GraphStore.upsert_entity` | `name: str, entity_type: str, aliases: Optional[list[str]], timeline: Optional[int], summary: Optional[str], embedding: Optional[list[float]]` | `EntityNode` | Insert or merge an entity. |
| [graph_store.py](graph_store.py#L181) | `GraphStore._find_same_as` | `entity_id: str, name: str, aliases: list[str]` | `Optional[EntityNode]` | Find an existing node that should be merged with the new entity. |
| [graph_store.py](graph_store.py#L198) | `GraphStore.get_entity` | `entity_id: str` | `Optional[EntityNode]` | Implement `GraphStore.get_entity`. |
| [graph_store.py](graph_store.py#L201) | `GraphStore.find_entity_by_name` | `name: str, entity_type: str` | `Optional[EntityNode]` | Find an entity by (possibly partial) name or alias match. |
| [graph_store.py](graph_store.py#L227) | `GraphStore.upsert_relation` | `source_id: str, target_id: str, relation: str, timeline: Optional[int], weight: float, valid: bool, evidence: Optional[list[int]]` | `Optional[RelationEdge]` | Insert or merge an undirected relation edge. |
| [graph_store.py](graph_store.py#L277) | `GraphStore._iter_edges_between` | `a: str, b: str` | `Iterable[RelationEdge]` | Implement `GraphStore._iter_edges_between`. |
| [graph_store.py](graph_store.py#L282) | `GraphStore.edges` | `None` | `list[RelationEdge]` | Implement `GraphStore.edges`. |
| [graph_store.py](graph_store.py#L285) | `GraphStore.edges_for` | `entity_id: str` | `list[RelationEdge]` | Implement `GraphStore.edges_for`. |
| [graph_store.py](graph_store.py#L292) | `GraphStore.neighbors` | `entity_id: str, max_hop: int` | `dict[str, int]` | Return neighbor entity ids at exact hop distance <= max_hop. |
| [graph_store.py](graph_store.py#L313) | `GraphStore.invalidate_relation` | `source_id: str, target_id: str` | `int` | Mark all relations between two entities invalid (fact superseded). |
| [graph_store.py](graph_store.py#L322) | `GraphStore.delete_relation` | `source_id: str, target_id: str, relation: Optional[str]` | `int` | Hard-delete matching edges and return the number removed. |
| [graph_store.py](graph_store.py#L342) | `GraphStore.delete_entity` | `entity_id: str` | `dict[str, int]` | Hard-delete one node and all incident edges. |
| [graph_store.py](graph_store.py#L358) | `GraphStore._adjacency` | `valid_only: bool` | `dict[str, list[str]]` | Implement `GraphStore._adjacency`. |
| [graph_store.py](graph_store.py#L367) | `GraphStore.pagerank` | `seed_ids: Iterable[str], alpha: float, max_iter: int, tol: float` | `dict[str, float]` | Personalized PageRank from seed entities (graph diffusion). |
| [graph_store.py](graph_store.py#L379) | `GraphStore.detect_communities` | `seed: int` | `list[list[str]]` | Community detection via NetworkX Louvain. |
| [graph_store.py](graph_store.py#L406) | `GraphStore._communities_connected_components` | `None` | `list[list[str]]` | Implement `GraphStore._communities_connected_components`. |
| [graph_store.py](graph_store.py#L435) | `GraphStore.time_decay` | `age: int, lam: float` | `float` | Recency weight for an entity/relation of given timeline age. |
| [graph_store.py](graph_store.py#L446) | `GraphStore.subgraph` | `entity_ids: Iterable[str], hop: int` | `tuple[dict[str, EntityNode], list[RelationEdge]]` | Export nodes + edges within ``hop`` hops of the given seeds. |
| [graph_store.py](graph_store.py#L480) | `GraphStore.to_state` | `None` | `GraphMemoryState` | Implement `GraphStore.to_state`. |
| [graph_store.py](graph_store.py#L491) | `GraphStore.clear` | `None` | `None` | Reset the graph to an empty state (keeps the lock alive). |
| [graph_store.py](graph_store.py#L503) | `GraphStore.from_state` | `state: GraphMemoryState` | `None` | Implement `GraphStore.from_state`. |
| [graph_store.py](graph_store.py#L514) | `GraphStore.to_dict` | `None` | `dict[str, Any]` | Implement `GraphStore.to_dict`. |
| [graph_store.py](graph_store.py#L517) | `GraphStore.from_dict` | `data: dict[str, Any]` | `None` | Implement `GraphStore.from_dict`. |
| [graph_store.py](graph_store.py#L520) | `GraphStore.save` | `path: str \| Path` | `bool` | Serialize the graph to JSON. Returns True on success. |
| [graph_store.py](graph_store.py#L553) | `GraphStore.load` | `path: str \| Path` | `bool` | Deserialize the graph from JSON. Returns True on success. |
| [graph_store.py](graph_store.py#L567) | `GraphStore.__len__` | `None` | `int` | Implement `GraphStore.__len__`. |
| [handler.py](handler.py#L130) | `GraphContextHandler._init_session_state` | `None` | `None` | (Re)set all per-session transient state (keeps long-term graph). |
| [handler.py](handler.py#L146) | `GraphContextHandler.has_retrieved` | `None` | `bool` | True once a retrieval has been performed this session. |
| [handler.py](handler.py#L151) | `GraphContextHandler.graph_memory` | `None` | `str` | Last rendered ``<graph_memory>`` block (empty when none). |
| [handler.py](handler.py#L156) | `GraphContextHandler.compaction_generation` | `None` | `int` | Number of compactions observed since the session started. |
| [handler.py](handler.py#L161) | `GraphContextHandler.compress_threshold` | `None` | `int` | Compaction threshold forwarded from the inner linear handler. |
| [handler.py](handler.py#L171) | `GraphContextHandler.extra_usage` | `None` | `Any` | Aggregate token usage from linear compaction + graph LLM calls. |
| [handler.py](handler.py#L191) | `GraphContextHandler.record_usage` | `usage: Optional[Any]` | `None` | Forward one internal LLM call's usage to the inner linear handler. |
| [handler.py](handler.py#L195) | `GraphContextHandler.drain_usage_records` | `None` | `list[UsageRecord]` | Drain child internal-call records in the order their components run. |
| [handler.py](handler.py#L209) | `GraphContextHandler.retrieve` | `query: str` | `GraphRetrievalResult` | Run hybrid graph retrieval and store the rendered context block. |
| [handler.py](handler.py#L225) | `GraphContextHandler.graph_projection` | `None` | `ContextGraphProjection` | Return the console projection of this Agent's entity graph. |
| [handler.py](handler.py#L236) | `GraphContextHandler.compact` | `controller: ExecutionController \| None, keep_recent: int \| None` | `bool` | Compact the linear context and flush pending graph evidence. |
| [handler.py](handler.py#L258) | `GraphContextHandler.add_user_message` | `message: 'str \| UserMessage'` | `None` | Append a user message and trigger retrieval when due. |
| [handler.py](handler.py#L284) | `GraphContextHandler.add_assistant_message` | `turn: AssistantTurnInput, tool_results: Sequence[ToolResultInput], controller: ExecutionController \| None` | `None` | Append an assistant output, detect compaction and flush the graph. |
| [handler.py](handler.py#L346) | `GraphContextHandler.build_messages` | `system_prompt: str \| None` | `list[RequestMessage]` | Build messages in stable previous/graph/recent/current order. |
| [handler.py](handler.py#L371) | `GraphContextHandler.build_blocks` | `snapshot: ContextSnapshot` | `list[ContextBlock]` | Expose Graph context sections to the shared Composer. |
| [handler.py](handler.py#L425) | `GraphContextHandler._render_items` | `items: Sequence[ContextItem], pending_resume: bool` | `list[RequestMessage]` | Render context items through the linear handler's assembler. |
| [handler.py](handler.py#L439) | `GraphContextHandler._linear_message_sections` | `None` | `tuple[list[ContextItem], list[ContextItem], list[ContextItem]]` | Split linear context into previous, last assistant, and current user. |
| [handler.py](handler.py#L476) | `GraphContextHandler.save` | `path: str \| Path` | `bool` | Save the conversation AND the companion graph file. |
| [handler.py](handler.py#L491) | `GraphContextHandler._save_locked` | `target: Path` | `bool` | Implement `GraphContextHandler._save_locked`. |
| [handler.py](handler.py#L522) | `GraphContextHandler.load` | `path: str \| Path` | `bool` | Restore the conversation and its companion graph. |
| [handler.py](handler.py#L595) | `GraphContextHandler.clear_context` | `None` | `bool` | Clear the session but keep the long-term memory graph. |
| [handler.py](handler.py#L603) | `GraphContextHandler._archive_records` | `None` | `list[ContextItem]` | Return the archived context items the linear handler owns. |
| [handler.py](handler.py#L613) | `GraphContextHandler._retrieve_archive_evidence` | `query: str` | `str` | Render small, provenance-labelled raw evidence for a new query. |
| [handler.py](handler.py#L647) | `GraphContextHandler._should_retrieve` | `None` | `bool` | Decide whether this newly stored user message should retrieve. |
| [handler.py](handler.py#L664) | `GraphContextHandler._latest_user_query` | `None` | `str` | Return the newest non-empty user turn for empty previews. |
| [handler.py](handler.py#L675) | `GraphContextHandler._flush_pending` | `None` | `None` | Ingest buffered items into the graph and clear the buffer. |
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
| [projection.py](projection.py#L35) | `ProjectedEntity.from_node` | `node: EntityNode` | `'ProjectedEntity'` | Project one stored node, dropping its embedding vector. |
| [projection.py](projection.py#L48) | `ProjectedEntity.to_json` | `None` | `JsonObject` | Return this node in the wire shape the console declares. |
| [projection.py](projection.py#L79) | `ProjectedRelation.from_edge` | `edge: RelationEdge` | `'ProjectedRelation'` | Project one stored relation. |
| [projection.py](projection.py#L92) | `ProjectedRelation.to_json` | `None` | `JsonObject` | Return this edge in the wire shape the console declares. |
| [projection.py](projection.py#L119) | `ProjectedCommunity.from_summary` | `summary: CommunitySummary` | `'ProjectedCommunity'` | Project one stored community summary. |
| [projection.py](projection.py#L128) | `ProjectedCommunity.to_json` | `None` | `JsonObject` | Return this summary in the wire shape the console declares. |
| [projection.py](projection.py#L164) | `ContextGraphProjection.node_count` | `None` | `int` | Return the number of projected entities. |
| [projection.py](projection.py#L169) | `ContextGraphProjection.edge_count` | `None` | `int` | Return the number of projected relations. |
| [projection.py](projection.py#L174) | `ContextGraphProjection.community_count` | `None` | `int` | Return the number of projected community summaries. |
| [projection.py](projection.py#L179) | `ContextGraphProjection.empty` | `None` | `'ContextGraphProjection'` | Return the projection for a handler that has no entity graph. |
| [projection.py](projection.py#L191) | `ContextGraphProjection.from_state` | `state: GraphMemoryState, stale: bool` | `'ContextGraphProjection'` | Project one decoded graph state. |
| [projection.py](projection.py#L214) | `ContextGraphProjection.to_json` | `None` | `JsonObject` | Return the projection in the console's declared wire shape. |
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
| [tools.py](tools.py#L17) | `GraphToolProvider.tools` | `None` | `list[Tool]` | Implement `GraphToolProvider.tools`. |
| [tools.py](tools.py#L87) | `GraphToolProvider._timeline` | `None` | `int` | Implement `GraphToolProvider._timeline`. |
| [tools.py](tools.py#L90) | `GraphToolProvider._entity` | `value: str` | `Any` | Implement `GraphToolProvider._entity`. |
| [tools.py](tools.py#L101) | `GraphToolProvider._dump` | `value: object` | `str` | Implement `GraphToolProvider._dump`. |
| [tools.py](tools.py#L104) | `GraphToolProvider.search` | `query: str` | `str` | Implement `GraphToolProvider.search`. |
| [tools.py](tools.py#L109) | `GraphToolProvider.get_neighbors` | `entity: str, hop: int` | `str` | Implement `GraphToolProvider.get_neighbors`. |
| [tools.py](tools.py#L123) | `GraphToolProvider.upsert_entity` | `name: str, entity_type: str, aliases: list[str] \| None, summary: str` | `str` | Implement `GraphToolProvider.upsert_entity`. |
| [tools.py](tools.py#L139) | `GraphToolProvider.upsert_relation` | `source: str, target: str, relation: str, evidence: list[int] \| None` | `str` | Implement `GraphToolProvider.upsert_relation`. |
| [tools.py](tools.py#L159) | `GraphToolProvider.invalidate_relation` | `source: str, target: str` | `str` | Implement `GraphToolProvider.invalidate_relation`. |
| [tools.py](tools.py#L168) | `GraphToolProvider.delete_relation` | `source: str, target: str, relation: str` | `str` | Implement `GraphToolProvider.delete_relation`. |
| [tools.py](tools.py#L181) | `GraphToolProvider.delete_entity` | `entity: str` | `str` | Implement `GraphToolProvider.delete_entity`. |
| [tools.py](tools.py#L187) | `create_graph_tools` | `context: Any` | `list[Tool]` | Return graph tools bound to one ``GraphContextHandler``. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [builder.py](builder.py#L86) | `ExtractionFetcher` | `None` | `Protocol` | Minimal LLM interface used for graph extraction. |
| [builder.py](builder.py#L104) | `IngestStats` | `entities_added: int, relations_added: int, llm_used: bool, fallback_regex: bool, error: str` | `object` | Statistics for one ingest batch. |
| [builder.py](builder.py#L140) | `GraphBuilder` | `store: GraphStore, fetcher: Optional[ExtractionFetcher], max_batch_chars: int, max_entities_per_batch: int` | `object` | Incremental conversation -> memory-graph builder. |
| [graph_store.py](graph_store.py#L112) | `GraphStore` | `None` | `object` | In-memory entity-relation graph with temporal + provenance metadata. |
| [handler.py](handler.py#L58) | `GraphContextHandler` | `compacting_fetcher: CompactionFetcher, extraction_fetcher: Optional[ExtractionFetcher], query_fetcher: Optional[ExtractionFetcher], store: Optional[GraphStore], retriever_config: Optional[RetrievalConfig], retrieval_trigger: str, graph_update_every: int, max_context_threshold: int, compaction_output_max_tokens: int, graph_save_suffix: str, storage: ContextStorage \| None, keep_recent: int` | `ContextHandler` | A context handler with an entity-relation long-term memory graph. |
| [models.py](models.py#L15) | `EntityNode` | `id: str, name: str, entity_type: str, aliases: list[str], summary: str, first_seen: int, last_seen: int, freq: int, embedding: Optional[list[float]]` | `object` | A single entity in the memory graph. |
| [models.py](models.py#L61) | `RelationEdge` | `source_id: str, target_id: str, relation: str, weight: float, first_seen: int, last_seen: int, valid: bool, evidence: list[int]` | `object` | A relation between two entities with temporal attributes. |
| [models.py](models.py#L109) | `CommunitySummary` | `level: int, community_id: str, summary: str, member_entity_ids: list[str], source_timelines: list[int]` | `object` | Summary of one community (cluster) of the memory graph. |
| [models.py](models.py#L137) | `GraphHit` | `entity: EntityNode, score: float, matched_relation: Optional[str], neighbor_ids: list[str]` | `object` | One retrieval hit: an entity plus its fused score. |
| [models.py](models.py#L155) | `GraphMemoryState` | `version: int, nodes: dict[str, EntityNode], edges: list[RelationEdge], communities: dict[int, list[CommunitySummary]], next_id: int` | `object` | Serialization container for the whole memory graph. |
| [projection.py](projection.py#L22) | `ProjectedEntity` | `id: str, name: str, entity_type: str, summary: str, aliases: tuple[str, ...], first_seen: int, last_seen: int, freq: int` | `object` | One graph node as a console renders it. |
| [projection.py](projection.py#L66) | `ProjectedRelation` | `source_id: str, target_id: str, relation: str, weight: float, first_seen: int, last_seen: int, valid: bool, evidence: tuple[int, ...]` | `object` | One graph edge as a console renders it. |
| [projection.py](projection.py#L110) | `ProjectedCommunity` | `level: int, community_id: str, summary: str, member_entity_ids: tuple[str, ...]` | `object` | One community summary as a console renders it. |
| [projection.py](projection.py#L142) | `ContextGraphProjection` | `available: bool, stale: bool, truncated: bool, nodes: tuple[ProjectedEntity, ...], edges: tuple[ProjectedRelation, ...], communities: tuple[ProjectedCommunity, ...]` | `object` | The complete entity-graph view for one Agent context. |
| [retriever.py](retriever.py#L135) | `RetrievalConfig` | `w_vec: float, w_ppr: float, w_kw: float, w_time: float, top_k: int, max_relations: int, max_communities: int, hop: int, time_decay_lambda: float, min_fused_score: float, include_neighbors: bool, include_communities: bool` | `object` | Weights and limits for the four-channel fusion retrieval. |
| [retriever.py](retriever.py#L176) | `GraphRetrievalResult` | `query: str, seed_entities: list[EntityNode], hits: list[GraphHit], expanded_entities: dict[str, EntityNode], relations: list[RelationEdge], community_summaries: list[CommunitySummary], rendered: str, current_timeline: int` | `object` | Output of :meth:`GraphRetriever.retrieve`. |
| [retriever.py](retriever.py#L329) | `GraphRetriever` | `store: GraphStore, query_fetcher: Optional[ExtractionFetcher], config: Optional[RetrievalConfig], query_prompt: str` | `object` | Four-channel hybrid retrieval over a :class:`GraphStore`. |
| [semantic.py](semantic.py#L19) | `SemanticGraphWorker` | `fetcher: Any, backend_name: Optional[str]` | `object` | A no-history, no-tools adapter for graph semantic work. |
| [tools.py](tools.py#L11) | `GraphToolProvider` | `context: Any` | `object` | Bind graph operations to one ``GraphContextHandler`` instance. |

<!-- END GENERATED SYMBOL MAP -->
