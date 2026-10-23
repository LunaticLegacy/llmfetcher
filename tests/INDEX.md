# llmfetcher/tests/ — Submodule Regression INDEX

Submodule-local regression coverage. Root-level integration tests belong to the
Angelus superproject.

| File | Responsibility |
|---|---|
| `test_execution_controller.py` | Graceful/forced stop control (`ExecutionController`). |
| `test_multimodal.py` | Native image wire payloads, reference persistence and observer byte isolation. |
| `test_tool_validation.py` | Malformed model tool calls and context save diagnostics. |
| `test_usage_lifetime.py` | Lifecycle-safe lifetime usage aggregation. |

<!-- BEGIN GENERATED SYMBOL MAP -->

## Function Map

| Source | Function / method | Input types | Output type | Semantics |
|---|---|---|---|---|
| [test_codex_handler.py](test_codex_handler.py#L6) | `_handler` | `None` | `Any` | Implement `_handler`. |
| [test_codex_handler.py](test_codex_handler.py#L12) | `test_codex_moves_system_messages_to_instructions_and_tool_feedback` | `None` | `Any` | Implement `test_codex_moves_system_messages_to_instructions_and_tool_feedback`. |
| [test_codex_handler.py](test_codex_handler.py#L26) | `test_codex_normalizes_response_function_calls` | `None` | `Any` | Implement `test_codex_normalizes_response_function_calls`. |
| [test_compaction_tail.py](test_compaction_tail.py#L29) | `_ScriptedCompactor.default_backend_config` | `None` | `LLMBackendConfig` | Describe the single backend this compactor reports as. |
| [test_compaction_tail.py](test_compaction_tail.py#L33) | `_ScriptedCompactor.fetch_stream` | `**_: object` | `Any` | Yield the scripted summary body as one streamed chunk. |
| [test_compaction_tail.py](test_compaction_tail.py#L38) | `_assistant` | `content: str` | `AssistantTurnInput` | Build one assistant turn with the fields the handler requires. |
| [test_compaction_tail.py](test_compaction_tail.py#L54) | `CompactionTailTests.test_handler_policy_applies_to_automatic_compaction` | `None` | `None` | A configured default governs the compaction the handler raises. |
| [test_compaction_tail.py](test_compaction_tail.py#L69) | `CompactionTailTests.test_call_argument_overrides_the_handler_policy` | `None` | `None` | An explicit count wins over the configured default. |
| [test_compaction_tail.py](test_compaction_tail.py#L79) | `CompactionTailTests.test_registry_forwards_keep_recent_to_the_composed_handler` | `None` | `None` | The shared configuration reaches the handlers that expose it. |
| [test_compaction_tail.py](test_compaction_tail.py#L93) | `CompactionTailTests.test_keep_recent_leaves_a_verbatim_tail_outside_provenance` | `None` | `None` | Only the entries before the boundary are summarised and archived. |
| [test_compaction_tail.py](test_compaction_tail.py#L105) | `CompactionTailTests.test_retained_tail_suppresses_the_derived_resume_turn` | `None` | `None` | A retained tail is already the user-visible turn. |
| [test_compaction_tail.py](test_compaction_tail.py#L117) | `CompactionTailTests.test_retained_rows_never_duplicate_a_timeline_in_the_checkpoint` | `None` | `None` | Retained rows must not also be archived, so pages stay unique. |
| [test_compaction_tail.py](test_compaction_tail.py#L133) | `CompactionTailTests.test_default_still_archives_everything_and_resumes` | `None` | `None` | ``keep_recent=0`` keeps the original behaviour. |
| [test_compaction_tail.py](test_compaction_tail.py#L146) | `CompactionTailTests.test_keep_recent_beyond_the_transcript_archives_everything` | `None` | `None` | An oversized retention count degrades to a full compaction. |
| [test_compaction_tail.py](test_compaction_tail.py#L158) | `CompactionTailTests.test_graph_handler_forwards_keep_recent` | `None` | `None` | The composing handler passes the retention boundary down. |
| [test_compaction_tail.py](test_compaction_tail.py#L170) | `CompactionTailTests.test_graph_preview_retrieves_for_empty_next_input` | `None` | `None` | An empty preview uses the latest user turn as its graph query. |
| [test_context_assembly.py](test_context_assembly.py#L27) | `_result` | `index: int, call_id: str` | `ToolResultRecord` | Implement `_result`. |
| [test_context_assembly.py](test_context_assembly.py#L40) | `_call` | `call_id: str, result_id: ToolResultId \| None` | `ToolCallRecord` | Implement `_call`. |
| [test_context_assembly.py](test_context_assembly.py#L49) | `_assistant` | `index: int, calls: list[ToolCallRecord], reasoning: str` | `AssistantContextItem` | Implement `_assistant`. |
| [test_context_assembly.py](test_context_assembly.py#L63) | `_user` | `index: int, content: str` | `UserContextItem` | Implement `_user`. |
| [test_context_assembly.py](test_context_assembly.py#L76) | `_Store.resolve_tool_result` | `result_id: ToolResultId` | `ToolResultRecord` | Implement `_Store.resolve_tool_result`. |
| [test_context_assembly.py](test_context_assembly.py#L81) | `ContextAssemblyTests._items` | `None` | `tuple[tuple[UserContextItem \| AssistantContextItem, ...], ToolResultRecord, ToolResultRecord]` | Implement `ContextAssemblyTests._items`. |
| [test_context_assembly.py](test_context_assembly.py#L92) | `ContextAssemblyTests.test_interleaved_puts_each_result_after_its_assistant` | `None` | `None` | Implement `ContextAssemblyTests.test_interleaved_puts_each_result_after_its_assistant`. |
| [test_context_assembly.py](test_context_assembly.py#L109) | `ContextAssemblyTests.test_interleaved_folds_reasoning_into_content` | `None` | `None` | Implement `ContextAssemblyTests.test_interleaved_folds_reasoning_into_content`. |
| [test_context_assembly.py](test_context_assembly.py#L116) | `ContextAssemblyTests.test_deferred_merges_every_result_into_one_system_block` | `None` | `None` | Implement `ContextAssemblyTests.test_deferred_merges_every_result_into_one_system_block`. |
| [test_context_assembly.py](test_context_assembly.py#L136) | `ContextAssemblyTests.test_deferred_rejects_repeated_call_ids` | `None` | `None` | Implement `ContextAssemblyTests.test_deferred_rejects_repeated_call_ids`. |
| [test_context_assembly.py](test_context_assembly.py#L150) | `ContextAssemblyTests.test_missing_result_fails_instead_of_emptying` | `None` | `None` | Implement `ContextAssemblyTests.test_missing_result_fails_instead_of_emptying`. |
| [test_context_assembly.py](test_context_assembly.py#L156) | `ContextAssemblyTests.test_observations_mark_the_result_source_per_mode` | `None` | `None` | Implement `ContextAssemblyTests.test_observations_mark_the_result_source_per_mode`. |
| [test_context_assembly.py](test_context_assembly.py#L189) | `ContextAssemblyTests.test_pending_resume_stays_last` | `None` | `None` | Implement `ContextAssemblyTests.test_pending_resume_stays_last`. |
| [test_context_checkpoint_replace.py](test_context_checkpoint_replace.py#L27) | `ContextCheckpointReplaceTests.test_save_survives_a_reader_holding_the_pointer` | `None` | `None` | A concurrent read handle delays the rename instead of failing it. |
| [test_context_checkpoint_replace.py](test_context_checkpoint_replace.py#L58) | `ContextCheckpointReplaceTests.test_persistent_denial_is_reported_not_hidden` | `None` | `None` | A rename that never succeeds fails the save and keeps the cause. |
| [test_context_checkpoint_replace.py](test_context_checkpoint_replace.py#L73) | `ContextCheckpointReplaceTests.test_paging_reader_waits_for_the_commit_lock` | `None` | `None` | A reader cannot observe the pointer while a write holds its lock. |
| [test_context_composer.py](test_context_composer.py#L19) | `_Compactor.default_backend_config` | `None` | `LLMBackendConfig` | Implement `_Compactor.default_backend_config`. |
| [test_context_composer.py](test_context_composer.py#L37) | `_Provider.source_id` | `None` | `str` | Implement `_Provider.source_id`. |
| [test_context_composer.py](test_context_composer.py#L40) | `_Provider.build_blocks` | `snapshot: ContextSnapshot` | `Any` | Implement `_Provider.build_blocks`. |
| [test_context_composer.py](test_context_composer.py#L49) | `ContextComposerTests.test_orders_blocks_and_skips_disabled_or_empty` | `None` | `None` | Implement `ContextComposerTests.test_orders_blocks_and_skips_disabled_or_empty`. |
| [test_context_composer.py](test_context_composer.py#L68) | `ContextComposerTests.test_provider_injection_is_rendered_without_becoming_history` | `None` | `None` | Implement `ContextComposerTests.test_provider_injection_is_rendered_without_becoming_history`. |
| [test_context_composer.py](test_context_composer.py#L87) | `ContextComposerTests.test_handler_is_a_source_and_composer_controls_position` | `None` | `None` | Implement `ContextComposerTests.test_handler_is_a_source_and_composer_controls_position`. |
| [test_context_composer.py](test_context_composer.py#L103) | `ContextComposerTests.test_tool_result_limit_keeps_newest_results_and_pairs_calls` | `None` | `None` | Implement `ContextComposerTests.test_tool_result_limit_keeps_newest_results_and_pairs_calls`. |
| [test_context_composer.py](test_context_composer.py#L148) | `ContextComposerTests.test_priority_precedes_position` | `None` | `None` | Implement `ContextComposerTests.test_priority_precedes_position`. |
| [test_context_composer.py](test_context_composer.py#L162) | `ContextComposerTests.test_source_priority_overrides_position_and_missing_sources_are_ignored` | `None` | `None` | Implement `ContextComposerTests.test_source_priority_overrides_position_and_missing_sources_are_ignored`. |
| [test_context_composer.py](test_context_composer.py#L181) | `ContextComposerTests.test_unlisted_source_takes_the_slot_after_the_saved_order` | `None` | `None` | Implement `ContextComposerTests.test_unlisted_source_takes_the_slot_after_the_saved_order`. |
| [test_context_composer.py](test_context_composer.py#L203) | `ContextComposerTests.test_empty_table_keeps_slot_order` | `None` | `None` | Implement `ContextComposerTests.test_empty_table_keeps_slot_order`. |
| [test_context_composer.py](test_context_composer.py#L215) | `ContextComposerTests.test_answered_user_turn_stays_ahead_of_its_assistant_reply` | `None` | `None` | Implement `ContextComposerTests.test_answered_user_turn_stays_ahead_of_its_assistant_reply`. |
| [test_context_composer.py](test_context_composer.py#L279) | `ContextComposerTests.test_answered_turns_stay_chronological_across_rounds` | `None` | `None` | Implement `ContextComposerTests.test_answered_turns_stay_chronological_across_rounds`. |
| [test_context_composer.py](test_context_composer.py#L311) | `ContextComposerTests.test_new_trailing_user_turn_is_the_current_input` | `None` | `None` | Implement `ContextComposerTests.test_new_trailing_user_turn_is_the_current_input`. |
| [test_context_composer.py](test_context_composer.py#L343) | `ContextComposerTests.test_compacted_window_still_declares_current_input` | `None` | `None` | Implement `ContextComposerTests.test_compacted_window_still_declares_current_input`. |
| [test_context_handler_registry.py](test_context_handler_registry.py#L23) | `_Fetcher.default_backend_config` | `None` | `LLMBackendConfig` | Describe the one backend this fetcher reports. |
| [test_context_handler_registry.py](test_context_handler_registry.py#L31) | `ContextHandlerRegistryTests.test_catalog_is_sorted_and_fully_described` | `None` | `None` | Every selectable handler carries a title and a description. |
| [test_context_handler_registry.py](test_context_handler_registry.py#L42) | `ContextHandlerRegistryTests.test_default_handler_is_registered` | `None` | `None` | The fallback a host uses before a user chooses must exist. |
| [test_context_handler_registry.py](test_context_handler_registry.py#L46) | `ContextHandlerRegistryTests.test_each_entry_builds_its_handler` | `None` | `None` | A registry entry must be constructible from the shared config. |
| [test_context_handler_registry.py](test_context_handler_registry.py#L59) | `ContextHandlerRegistryTests.test_unknown_name_reports_the_available_ids` | `None` | `None` | A bad profile value must fail loudly and list the options. |
| [test_context_record_types.py](test_context_record_types.py#L32) | `_Store.resolve_tool_result` | `result_id: ToolResultId` | `ToolResultRecord` | Implement `_Store.resolve_tool_result`. |
| [test_context_record_types.py](test_context_record_types.py#L39) | `ContextRecordTests.test_generated_ids_are_distinct_and` | `None` | `None` | Implement `ContextRecordTests.test_generated_ids_are_distinct_and`. |
| [test_context_record_types.py](test_context_record_types.py#L47) | `ContextRecordTests.test_an_empty_id_is_rejected` | `None` | `None` | Implement `ContextRecordTests.test_an_empty_id_is_rejected`. |
| [test_context_record_types.py](test_context_record_types.py#L53) | `ContextRecordTests.test_tool_call_holds_a_reference_instead_of_result_text` | `None` | `None` | Implement `ContextRecordTests.test_tool_call_holds_a_reference_instead_of_result_text`. |
| [test_context_record_types.py](test_context_record_types.py#L66) | `ContextRecordTests.test_assistant_item_never_embeds_the_tool_output` | `None` | `None` | Implement `ContextRecordTests.test_assistant_item_never_embeds_the_tool_output`. |
| [test_context_record_types.py](test_context_record_types.py#L89) | `ContextRecordTests.test_summary_records_the_ranges_it_collapsed` | `None` | `None` | Implement `ContextRecordTests.test_summary_records_the_ranges_it_collapsed`. |
| [test_context_record_types.py](test_context_record_types.py#L102) | `ContextRecordTests.test_items_are_frozen` | `None` | `None` | Implement `ContextRecordTests.test_items_are_frozen`. |
| [test_context_record_types.py](test_context_record_types.py#L113) | `ContextRecordTests.test_store_resolves_a_reference_to_the_complete_result` | `None` | `None` | Implement `ContextRecordTests.test_store_resolves_a_reference_to_the_complete_result`. |
| [test_context_sqlite_concurrency.py](test_context_sqlite_concurrency.py#L22) | `ContextSQLiteConcurrencyTests.test_concurrent_appends_keep_every_row` | `None` | `None` | Six parallel writers commit six distinct timelines. |
| [test_context_sqlite_concurrency.py](test_context_sqlite_concurrency.py#L40) | `ContextSQLiteConcurrencyTests.test_writer_waits_for_an_open_write_transaction` | `None` | `None` | A writer blocked by another transaction commits once it releases. |
| [test_context_store_v2.py](test_context_store_v2.py#L41) | `_result` | `index: int` | `ToolResultRecord` | Implement `_result`. |
| [test_context_store_v2.py](test_context_store_v2.py#L54) | `_assistant` | `index: int, result_id: ToolResultId \| None` | `AssistantContextItem` | Implement `_assistant`. |
| [test_context_store_v2.py](test_context_store_v2.py#L76) | `CodecV2Tests.test_assistant_item_round_trips_a_reference_only` | `None` | `None` | Implement `CodecV2Tests.test_assistant_item_round_trips_a_reference_only`. |
| [test_context_store_v2.py](test_context_store_v2.py#L85) | `CodecV2Tests.test_user_and_summary_round_trip` | `None` | `None` | Implement `CodecV2Tests.test_user_and_summary_round_trip`. |
| [test_context_store_v2.py](test_context_store_v2.py#L104) | `CodecV2Tests.test_missing_field_is_rejected_instead_of_defaulted` | `None` | `None` | Implement `CodecV2Tests.test_missing_field_is_rejected_instead_of_defaulted`. |
| [test_context_store_v2.py](test_context_store_v2.py#L111) | `CodecV2Tests.test_unknown_kind_is_rejected` | `None` | `None` | Implement `CodecV2Tests.test_unknown_kind_is_rejected`. |
| [test_context_store_v2.py](test_context_store_v2.py#L117) | `CodecV2Tests.test_tool_result_round_trips_status_and_duration` | `None` | `None` | Implement `CodecV2Tests.test_tool_result_round_trips_status_and_duration`. |
| [test_context_store_v2.py](test_context_store_v2.py#L126) | `TurnInputTests.test_turn_input_carries_tool_status_and_duration` | `None` | `None` | Implement `TurnInputTests.test_turn_input_carries_tool_status_and_duration`. |
| [test_context_store_v2.py](test_context_store_v2.py#L150) | `TurnInputTests.test_duplicate_call_ids_are_rejected` | `None` | `None` | Implement `TurnInputTests.test_duplicate_call_ids_are_rejected`. |
| [test_context_store_v2.py](test_context_store_v2.py#L166) | `StorageV2Tests.test_item_and_result_commit_together` | `None` | `None` | Implement `StorageV2Tests.test_item_and_result_commit_together`. |
| [test_context_store_v2.py](test_context_store_v2.py#L193) | `StorageV2Tests.test_a_missing_reference_is_absent_not_empty` | `None` | `None` | Implement `StorageV2Tests.test_a_missing_reference_is_absent_not_empty`. |
| [test_context_store_v2.py](test_context_store_v2.py#L201) | `StorageV2Tests.test_concurrent_writers_keep_every_result` | `None` | `None` | Implement `StorageV2Tests.test_concurrent_writers_keep_every_result`. |
| [test_execution_controller.py](test_execution_controller.py#L22) | `ExecutionControllerTests.test_graceful_stop_wakes_waiters_without_closing_resources` | `None` | `None` | Graceful mode shares the request path but preserves active I/O. |
| [test_execution_controller.py](test_execution_controller.py#L34) | `ExecutionControllerTests.test_force_stop_escalates_and_closes_existing_and_late_resources` | `None` | `None` | Force mode upgrades graceful intent and closes every registered resource. |
| [test_execution_controller.py](test_execution_controller.py#L47) | `ExecutionControllerTests.test_force_stop_closes_active_fetcher_transport` | `None` | `None` | A fetch request registers its transport and exits as cancellation. |
| [test_execution_controller.py](test_execution_controller.py#L72) | `ExecutionControllerTests.test_force_stop_closes_an_active_stream` | `None` | `None` | The stream keeps its registration until its generator is closed. |
| [test_execution_controller.py](test_execution_controller.py#L97) | `ExecutionControllerTests.test_force_stop_cancels_a_tool_batch_and_binds_its_controller` | `None` | `None` | A running tool can close its resource through the bound controller. |
| [test_execution_controller.py](test_execution_controller.py#L131) | `ExecutionControllerTests.test_force_stop_kills_a_shell_tool_process_group` | `None` | `None` | Shell tools register their spawned process group with the controller. |
| [test_execution_controller.py](test_execution_controller.py#L171) | `_BlockingHandler.prepare_tools` | `tools: object` | `object` | Implement `_BlockingHandler.prepare_tools`. |
| [test_execution_controller.py](test_execution_controller.py#L174) | `_BlockingHandler.create_completion` | `**_kwargs: object` | `object` | Implement `_BlockingHandler.create_completion`. |
| [test_execution_controller.py](test_execution_controller.py#L179) | `_BlockingHandler.abort_active_request` | `None` | `int` | Implement `_BlockingHandler.abort_active_request`. |
| [test_execution_controller.py](test_execution_controller.py#L191) | `_StreamingHandler.create_completion` | `**_kwargs: object` | `object` | Implement `_StreamingHandler.create_completion`. |
| [test_execution_controller.py](test_execution_controller.py#L194) | `_StreamingHandler.iter_stream_text` | `_raw: object, **_kwargs: object` | `Any` | Implement `_StreamingHandler.iter_stream_text`. |
| [test_execution_controller.py](test_execution_controller.py#L201) | `_fetch_in_thread` | `fetcher: LLMFetcher, controller: ExecutionController, errors: list[BaseException]` | `None` | Implement `_fetch_in_thread`. |
| [test_execution_controller.py](test_execution_controller.py#L212) | `_advance_stream` | `stream: object, errors: list[BaseException]` | `None` | Implement `_advance_stream`. |
| [test_execution_controller.py](test_execution_controller.py#L219) | `_run_tool_batch` | `executor: ToolExecutor, controller: ExecutionController, handler: object, errors: list[BaseException], arguments: dict[str, object] \| None` | `None` | Implement `_run_tool_batch`. |
| [test_graph_save_concurrency.py](test_graph_save_concurrency.py#L23) | `_agent` | `None` | `Agent` | Build a tool-free Agent the default serializer accepts. |
| [test_graph_save_concurrency.py](test_graph_save_concurrency.py#L43) | `ExecutionGraphSaveConcurrencyTests.test_concurrent_saves_leave_one_valid_document` | `None` | `None` | Six parallel saves leave one parseable document and no temp files. |
| [test_graph_snapshot_roundtrip.py](test_graph_snapshot_roundtrip.py#L17) | `_agent` | `None` | `Agent` | Build a tool-free Agent the default serializer accepts. |
| [test_graph_snapshot_roundtrip.py](test_graph_snapshot_roundtrip.py#L30) | `ExecutionGraphSnapshotTests.test_snapshot_json_round_trip` | `None` | `None` | One writer field set decodes back into an equal record. |
| [test_graph_snapshot_roundtrip.py](test_graph_snapshot_roundtrip.py#L40) | `ExecutionGraphSnapshotTests.test_saved_graph_reloads_with_the_same_view` | `None` | `None` | ``save`` and ``load`` agree on topology and node state. |
| [test_graph_snapshot_roundtrip.py](test_graph_snapshot_roundtrip.py#L54) | `ExecutionGraphSnapshotTests.test_snapshot_rejects_an_unknown_field` | `None` | `None` | A field the writer never emits is a decode error. |
| [test_graph_tools.py](test_graph_tools.py#L14) | `_Compactor.default_backend_config` | `None` | `LLMBackendConfig` | Implement `_Compactor.default_backend_config`. |
| [test_graph_tools.py](test_graph_tools.py#L19) | `GraphToolTests.test_context_build_order_is_previous_graph_last_round_current_user` | `None` | `None` | Implement `GraphToolTests.test_context_build_order_is_previous_graph_last_round_current_user`. |
| [test_graph_tools.py](test_graph_tools.py#L47) | `GraphToolTests.test_graph_tools_edit_and_read_the_bound_store` | `None` | `None` | Implement `GraphToolTests.test_graph_tools_edit_and_read_the_bound_store`. |
| [test_graph_tools.py](test_graph_tools.py#L78) | `GraphToolTests.test_graph_search_returns_retrieval_projection` | `None` | `None` | Implement `GraphToolTests.test_graph_search_returns_retrieval_projection`. |
| [test_image_budget_compaction.py](test_image_budget_compaction.py#L25) | `FakeContext.build_messages` | `None` | `Any` | Implement `FakeContext.build_messages`. |
| [test_image_budget_compaction.py](test_image_budget_compaction.py#L28) | `FakeContext.add_user_message` | `message: Any` | `Any` | Implement `FakeContext.add_user_message`. |
| [test_image_budget_compaction.py](test_image_budget_compaction.py#L34) | `ImageBudgetCompactionTests.test_compacts_at_limit_and_replays_latest_image` | `None` | `Any` | Implement `ImageBudgetCompactionTests.test_compacts_at_limit_and_replays_latest_image`. |
| [test_image_budget_compaction.py](test_image_budget_compaction.py#L51) | `ImageBudgetCompactionTests.test_no_compaction_below_limit` | `None` | `Any` | Implement `ImageBudgetCompactionTests.test_no_compaction_below_limit`. |
| [test_image_budget_compaction.py](test_image_budget_compaction.py#L56) | `ImageBudgetCompactionTests.test_failed_compaction_preserves_images` | `None` | `Any` | Implement `ImageBudgetCompactionTests.test_failed_compaction_preserves_images`. |
| [test_multimodal.py](test_multimodal.py#L33) | `NativeVisionTests.context` | `None` | `Any` | Implement `NativeVisionTests.context`. |
| [test_multimodal.py](test_multimodal.py#L62) | `NativeVisionTests.handler` | `None` | `Any` | Implement `NativeVisionTests.handler`. |
| [test_multimodal.py](test_multimodal.py#L70) | `NativeVisionTests.test_openai_both_dispatch_modes_and_tool_order` | `None` | `Any` | Implement `NativeVisionTests.test_openai_both_dispatch_modes_and_tool_order`. |
| [test_multimodal.py](test_multimodal.py#L83) | `NativeVisionTests.test_anthropic_native_tool_use_and_image_result` | `None` | `Any` | Implement `NativeVisionTests.test_anthropic_native_tool_use_and_image_result`. |
| [test_multimodal.py](test_multimodal.py#L95) | `NativeVisionTests.test_anthropic_tool_names_are_openai_compatible` | `None` | `Any` | Implement `NativeVisionTests.test_anthropic_tool_names_are_openai_compatible`. |
| [test_multimodal.py](test_multimodal.py#L106) | `NativeVisionTests.test_checkpoint_and_archive_keep_only_references` | `None` | `Any` | Implement `NativeVisionTests.test_checkpoint_and_archive_keep_only_references`. |
| [test_multimodal.py](test_multimodal.py#L124) | `NativeVisionTests.test_preview_never_resolves_bytes_and_rejects_unsupported` | `None` | `Any` | Implement `NativeVisionTests.test_preview_never_resolves_bytes_and_rejects_unsupported`. |
| [test_multimodal.py](test_multimodal.py#L141) | `NativeVisionTests.test_validation_missing_resolver_and_request_budget` | `None` | `Any` | Implement `NativeVisionTests.test_validation_missing_resolver_and_request_budget`. |
| [test_multimodal.py](test_multimodal.py#L158) | `NativeVisionTests.test_image_only_turn_survives_linear_checkpoint` | `None` | `Any` | Implement `NativeVisionTests.test_image_only_turn_survives_linear_checkpoint`. |
| [test_multimodal.py](test_multimodal.py#L169) | `NativeVisionTests.test_compaction_preview_keeps_marker_never_bytes` | `None` | `Any` | Implement `NativeVisionTests.test_compaction_preview_keeps_marker_never_bytes`. |
| [test_multimodal.py](test_multimodal.py#L174) | `NativeVisionTests.test_graph_handler_preserves_image_references` | `None` | `Any` | Implement `NativeVisionTests.test_graph_handler_preserves_image_references`. |
| [test_multimodal.py](test_multimodal.py#L184) | `NativeVisionTests.test_graph_builder_keeps_image_only_turn_reachable` | `None` | `Any` | Implement `NativeVisionTests.test_graph_builder_keeps_image_only_turn_reachable`. |
| [test_multimodal.py](test_multimodal.py#L200) | `NativeVisionTests.test_archive_retrieval_surfaces_reference_markers` | `None` | `Any` | Implement `NativeVisionTests.test_archive_retrieval_surfaces_reference_markers`. |
| [test_multimodal.py](test_multimodal.py#L214) | `NativeVisionTests.test_retrieved_archival_keeps_reference_markers` | `None` | `Any` | Implement `NativeVisionTests.test_retrieved_archival_keeps_reference_markers`. |
| [test_openai_tool_names.py](test_openai_tool_names.py#L12) | `OpenAIToolNameTests.test_invalid_names_are_normalized_and_reversible` | `None` | `None` | Implement `OpenAIToolNameTests.test_invalid_names_are_normalized_and_reversible`. |
| [test_openai_tool_names.py](test_openai_tool_names.py#L24) | `OpenAIToolNameTests.test_valid_names_are_preserved` | `None` | `None` | Implement `OpenAIToolNameTests.test_valid_names_are_preserved`. |
| [test_openai_tool_names.py](test_openai_tool_names.py#L34) | `OpenAIToolNameTests.test_wire_name_collision_is_rejected` | `None` | `None` | Implement `OpenAIToolNameTests.test_wire_name_collision_is_rejected`. |
| [test_sage_context.py](test_sage_context.py#L26) | `_Compactor.fetch` | `**_: object` | `LLMOutput` | Implement `_Compactor.fetch`. |
| [test_sage_context.py](test_sage_context.py#L30) | `_assistant` | `content: str` | `AssistantTurnInput` | Implement `_assistant`. |
| [test_sage_context.py](test_sage_context.py#L43) | `SageContextTests.test_append_tracks_active_context_and_worktree` | `None` | `None` | Implement `SageContextTests.test_append_tracks_active_context_and_worktree`. |
| [test_sage_context.py](test_sage_context.py#L56) | `SageContextTests.test_request_preview_labels_persisted_and_synthetic_messages` | `None` | `None` | Implement `SageContextTests.test_request_preview_labels_persisted_and_synthetic_messages`. |
| [test_sage_context.py](test_sage_context.py#L75) | `SageContextTests.test_compaction_creates_sage_summary_and_keeps_raw_rows` | `None` | `None` | Implement `SageContextTests.test_compaction_creates_sage_summary_and_keeps_raw_rows`. |
| [test_sage_context.py](test_sage_context.py#L91) | `SageContextTests.test_failed_compaction_preserves_active_projection` | `None` | `None` | Implement `SageContextTests.test_failed_compaction_preserves_active_projection`. |
| [test_sage_context.py](test_sage_context.py#L100) | `SageContextTests.test_branch_tool_queue_and_apply` | `None` | `None` | Implement `SageContextTests.test_branch_tool_queue_and_apply`. |
| [test_sage_context.py](test_sage_context.py#L110) | `SageContextTests.test_save_and_load_restore_worktree_and_summary` | `None` | `None` | Implement `SageContextTests.test_save_and_load_restore_worktree_and_summary`. |
| [test_sage_context.py](test_sage_context.py#L129) | `SageContextTests.test_tool_results_are_stored_by_reference_and_restored` | `None` | `None` | Implement `SageContextTests.test_tool_results_are_stored_by_reference_and_restored`. |
| [test_tool_validation.py](test_tool_validation.py#L20) | `ToolCallValidationTests.setUp` | `None` | `None` | Implement `ToolCallValidationTests.setUp`. |
| [test_tool_validation.py](test_tool_validation.py#L29) | `ToolCallValidationTests._execute` | `call: LLMToolCall` | `object` | Implement `ToolCallValidationTests._execute`. |
| [test_tool_validation.py](test_tool_validation.py#L33) | `ToolCallValidationTests.test_missing_required_field_returns_model_visible_error` | `None` | `None` | Implement `ToolCallValidationTests.test_missing_required_field_returns_model_visible_error`. |
| [test_tool_validation.py](test_tool_validation.py#L39) | `ToolCallValidationTests.test_wrong_type_and_unknown_name_return_model_visible_errors` | `None` | `None` | Implement `ToolCallValidationTests.test_wrong_type_and_unknown_name_return_model_visible_errors`. |
| [test_tool_validation.py](test_tool_validation.py#L48) | `ToolCallValidationTests.test_compact_schema_rejects_unexpected_field` | `None` | `None` | Implement `ToolCallValidationTests.test_compact_schema_rejects_unexpected_field`. |
| [test_tool_validation.py](test_tool_validation.py#L58) | `ContextSaveDiagnosticTests.test_agent_chains_handler_save_failure` | `None` | `None` | Implement `ContextSaveDiagnosticTests.test_agent_chains_handler_save_failure`. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L31) | `_ScriptedFetcher.default_backend_config` | `None` | `LLMBackendConfig` | Implement `_ScriptedFetcher.default_backend_config`. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L34) | `_ScriptedFetcher.fetch` | `**_: object` | `LLMOutput` | Implement `_ScriptedFetcher.fetch`. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L48) | `_make_agent` | `fetcher: _ScriptedFetcher` | `Agent` | Implement `_make_agent`. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L69) | `_LegacyAgent.add_hook` | `hook: object` | `None` | Accept the event hook an ExecutionGraph attaches on registration. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L73) | `_LegacyAgent.remove_hook` | `hook: object` | `None` | Drop a previously attached event hook. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L82) | `UsageLifetimeTests.test_lifetime_usage_accumulates_across_runs` | `None` | `None` | The per-run counter resets; the lifetime counter keeps growing. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L101) | `UsageLifetimeTests.test_swarm_total_usage_does_not_drop_on_new_lifecycle` | `None` | `None` | The Session aggregate is monotonic across consecutive runs. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L120) | `UsageLifetimeTests.test_swarm_falls_back_to_usage_without_lifetime_counter` | `None` | `None` | Legacy agents expose their per-run counter instead of dropping out. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [test_compaction_tail.py](test_compaction_tail.py#L21) | `_ScriptedCompactor` | `raw: str` | `object` | Yield one fixed ``<context_abstract>`` body for every summary request. |
| [test_compaction_tail.py](test_compaction_tail.py#L51) | `CompactionTailTests` | `None` | `unittest.TestCase` | The retained tail keeps its timelines and its turn in the request. |
| [test_context_assembly.py](test_context_assembly.py#L72) | `_Store` | `*records: ToolResultRecord` | `object` | Provide `_Store` behavior. |
| [test_context_assembly.py](test_context_assembly.py#L80) | `ContextAssemblyTests` | `None` | `unittest.TestCase` | Provide `ContextAssemblyTests` behavior. |
| [test_context_checkpoint_replace.py](test_context_checkpoint_replace.py#L26) | `ContextCheckpointReplaceTests` | `None` | `unittest.TestCase` | Provide `ContextCheckpointReplaceTests` behavior. |
| [test_context_composer.py](test_context_composer.py#L17) | `_Compactor` | `None` | `object` | Provide `_Compactor` behavior. |
| [test_context_composer.py](test_context_composer.py#L23) | `_Provider` | `provider_id: str, position: ContextPosition, priority: int, content: str` | `object` | Provide `_Provider` behavior. |
| [test_context_composer.py](test_context_composer.py#L48) | `ContextComposerTests` | `None` | `unittest.TestCase` | Provide `ContextComposerTests` behavior. |
| [test_context_handler_registry.py](test_context_handler_registry.py#L19) | `_Fetcher` | `None` | `object` | Stand in for the compaction fetcher every handler is built with. |
| [test_context_handler_registry.py](test_context_handler_registry.py#L28) | `ContextHandlerRegistryTests` | `None` | `unittest.TestCase` | The registry is the single list a host offers and builds from. |
| [test_context_record_types.py](test_context_record_types.py#L26) | `_Store` | `record: ToolResultRecord` | `object` | Minimal ContextStore used to prove references resolve by identity. |
| [test_context_record_types.py](test_context_record_types.py#L38) | `ContextRecordTests` | `None` | `unittest.TestCase` | Provide `ContextRecordTests` behavior. |
| [test_context_sqlite_concurrency.py](test_context_sqlite_concurrency.py#L21) | `ContextSQLiteConcurrencyTests` | `None` | `unittest.TestCase` | Provide `ContextSQLiteConcurrencyTests` behavior. |
| [test_context_store_v2.py](test_context_store_v2.py#L75) | `CodecV2Tests` | `None` | `unittest.TestCase` | Provide `CodecV2Tests` behavior. |
| [test_context_store_v2.py](test_context_store_v2.py#L125) | `TurnInputTests` | `None` | `unittest.TestCase` | Provide `TurnInputTests` behavior. |
| [test_context_store_v2.py](test_context_store_v2.py#L165) | `StorageV2Tests` | `None` | `unittest.TestCase` | Provide `StorageV2Tests` behavior. |
| [test_execution_controller.py](test_execution_controller.py#L19) | `ExecutionControllerTests` | `None` | `unittest.TestCase` | Verify one stop request governs resource cancellation and observation. |
| [test_execution_controller.py](test_execution_controller.py#L164) | `_BlockingHandler` | `None` | `object` | Minimal provider double whose close wakes a blocked completion call. |
| [test_execution_controller.py](test_execution_controller.py#L184) | `_StreamingHandler` | `None` | `_BlockingHandler` | Provider double that emits one chunk then blocks on the transport. |
| [test_graph_save_concurrency.py](test_graph_save_concurrency.py#L42) | `ExecutionGraphSaveConcurrencyTests` | `None` | `unittest.TestCase` | Provide `ExecutionGraphSaveConcurrencyTests` behavior. |
| [test_graph_snapshot_roundtrip.py](test_graph_snapshot_roundtrip.py#L29) | `ExecutionGraphSnapshotTests` | `None` | `unittest.TestCase` | Provide `ExecutionGraphSnapshotTests` behavior. |
| [test_graph_tools.py](test_graph_tools.py#L12) | `_Compactor` | `None` | `object` | Provide `_Compactor` behavior. |
| [test_graph_tools.py](test_graph_tools.py#L18) | `GraphToolTests` | `None` | `unittest.TestCase` | Provide `GraphToolTests` behavior. |
| [test_image_budget_compaction.py](test_image_budget_compaction.py#L11) | `FakeContext` | `count: Any` | `object` | Provide `FakeContext` behavior. |
| [test_image_budget_compaction.py](test_image_budget_compaction.py#L33) | `ImageBudgetCompactionTests` | `None` | `unittest.TestCase` | Provide `ImageBudgetCompactionTests` behavior. |
| [test_multimodal.py](test_multimodal.py#L32) | `NativeVisionTests` | `None` | `unittest.TestCase` | Provide `NativeVisionTests` behavior. |
| [test_openai_tool_names.py](test_openai_tool_names.py#L11) | `OpenAIToolNameTests` | `None` | `unittest.TestCase` | Provide `OpenAIToolNameTests` behavior. |
| [test_sage_context.py](test_sage_context.py#L22) | `_Compactor` | `body: str` | `object` | Provide `_Compactor` behavior. |
| [test_sage_context.py](test_sage_context.py#L42) | `SageContextTests` | `None` | `unittest.TestCase` | Provide `SageContextTests` behavior. |
| [test_tool_validation.py](test_tool_validation.py#L17) | `ToolCallValidationTests` | `None` | `unittest.TestCase` | Ensure malformed model calls become recoverable tool feedback. |
| [test_tool_validation.py](test_tool_validation.py#L55) | `ContextSaveDiagnosticTests` | `None` | `unittest.TestCase` | Retain the actual context-save failure through the Agent boundary. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L20) | `_ScriptedFetcher` | `input_tokens: int, output_tokens: int` | `object` | Return a fixed provider usage for every model round. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L62) | `_LegacyAgent` | `usage: TokenUsage` | `object` | Agent-shaped fake without ``lifetime_usage`` (older builds / hosts). |
| [test_usage_lifetime.py](test_usage_lifetime.py#L79) | `UsageLifetimeTests` | `None` | `unittest.TestCase` | A new lifecycle must not erase the Session's earlier usage. |

<!-- END GENERATED SYMBOL MAP -->
