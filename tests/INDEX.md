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
| [test_multimodal.py](test_multimodal.py#L21) | `NativeVisionTests.context` | `None` | `Any` | Implement `NativeVisionTests.context`. |
| [test_multimodal.py](test_multimodal.py#L29) | `NativeVisionTests.handler` | `None` | `Any` | Implement `NativeVisionTests.handler`. |
| [test_multimodal.py](test_multimodal.py#L37) | `NativeVisionTests.test_openai_both_dispatch_modes_and_tool_order` | `None` | `Any` | Implement `NativeVisionTests.test_openai_both_dispatch_modes_and_tool_order`. |
| [test_multimodal.py](test_multimodal.py#L50) | `NativeVisionTests.test_anthropic_native_tool_use_and_image_result` | `None` | `Any` | Implement `NativeVisionTests.test_anthropic_native_tool_use_and_image_result`. |
| [test_multimodal.py](test_multimodal.py#L61) | `NativeVisionTests.test_anthropic_tool_names_are_openai_compatible` | `None` | `Any` | Implement `NativeVisionTests.test_anthropic_tool_names_are_openai_compatible`. |
| [test_multimodal.py](test_multimodal.py#L72) | `NativeVisionTests.test_anthropic_groups_multiple_tool_results_in_one_user_message` | `None` | `Any` | Implement `NativeVisionTests.test_anthropic_groups_multiple_tool_results_in_one_user_message`. |
| [test_multimodal.py](test_multimodal.py#L89) | `NativeVisionTests.test_checkpoint_and_archive_keep_only_references` | `None` | `Any` | Implement `NativeVisionTests.test_checkpoint_and_archive_keep_only_references`. |
| [test_multimodal.py](test_multimodal.py#L103) | `NativeVisionTests.test_preview_never_resolves_bytes_and_rejects_unsupported` | `None` | `Any` | Implement `NativeVisionTests.test_preview_never_resolves_bytes_and_rejects_unsupported`. |
| [test_multimodal.py](test_multimodal.py#L114) | `NativeVisionTests.test_validation_missing_resolver_and_request_budget` | `None` | `Any` | Implement `NativeVisionTests.test_validation_missing_resolver_and_request_budget`. |
| [test_multimodal.py](test_multimodal.py#L129) | `NativeVisionTests.test_image_only_turn_survives_linear_checkpoint` | `None` | `Any` | Implement `NativeVisionTests.test_image_only_turn_survives_linear_checkpoint`. |
| [test_multimodal.py](test_multimodal.py#L140) | `NativeVisionTests.test_compaction_preview_keeps_marker_never_bytes` | `None` | `Any` | Implement `NativeVisionTests.test_compaction_preview_keeps_marker_never_bytes`. |
| [test_multimodal.py](test_multimodal.py#L145) | `NativeVisionTests.test_graph_handler_preserves_image_references` | `None` | `Any` | Implement `NativeVisionTests.test_graph_handler_preserves_image_references`. |
| [test_multimodal.py](test_multimodal.py#L155) | `NativeVisionTests.test_graph_builder_keeps_image_only_turn_reachable` | `None` | `Any` | Implement `NativeVisionTests.test_graph_builder_keeps_image_only_turn_reachable`. |
| [test_multimodal.py](test_multimodal.py#L166) | `NativeVisionTests.test_archive_retrieval_surfaces_reference_markers` | `None` | `Any` | Implement `NativeVisionTests.test_archive_retrieval_surfaces_reference_markers`. |
| [test_multimodal.py](test_multimodal.py#L175) | `NativeVisionTests.test_retrieved_archival_keeps_reference_markers` | `None` | `Any` | Implement `NativeVisionTests.test_retrieved_archival_keeps_reference_markers`. |
| [test_openai_tool_names.py](test_openai_tool_names.py#L12) | `OpenAIToolNameTests.test_invalid_names_are_normalized_and_reversible` | `None` | `None` | Implement `OpenAIToolNameTests.test_invalid_names_are_normalized_and_reversible`. |
| [test_openai_tool_names.py](test_openai_tool_names.py#L24) | `OpenAIToolNameTests.test_valid_names_are_preserved` | `None` | `None` | Implement `OpenAIToolNameTests.test_valid_names_are_preserved`. |
| [test_openai_tool_names.py](test_openai_tool_names.py#L34) | `OpenAIToolNameTests.test_wire_name_collision_is_rejected` | `None` | `None` | Implement `OpenAIToolNameTests.test_wire_name_collision_is_rejected`. |
| [test_tool_validation.py](test_tool_validation.py#L20) | `ToolCallValidationTests.setUp` | `None` | `None` | Implement `ToolCallValidationTests.setUp`. |
| [test_tool_validation.py](test_tool_validation.py#L29) | `ToolCallValidationTests._execute` | `call: LLMToolCall` | `object` | Implement `ToolCallValidationTests._execute`. |
| [test_tool_validation.py](test_tool_validation.py#L33) | `ToolCallValidationTests.test_missing_required_field_returns_model_visible_error` | `None` | `None` | Implement `ToolCallValidationTests.test_missing_required_field_returns_model_visible_error`. |
| [test_tool_validation.py](test_tool_validation.py#L39) | `ToolCallValidationTests.test_wrong_type_and_unknown_name_return_model_visible_errors` | `None` | `None` | Implement `ToolCallValidationTests.test_wrong_type_and_unknown_name_return_model_visible_errors`. |
| [test_tool_validation.py](test_tool_validation.py#L48) | `ToolCallValidationTests.test_compact_schema_rejects_unexpected_field` | `None` | `None` | Implement `ToolCallValidationTests.test_compact_schema_rejects_unexpected_field`. |
| [test_tool_validation.py](test_tool_validation.py#L58) | `ContextSaveDiagnosticTests.test_agent_chains_handler_save_failure` | `None` | `None` | Implement `ContextSaveDiagnosticTests.test_agent_chains_handler_save_failure`. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L31) | `_ScriptedFetcher.default_backend_config` | `None` | `LLMBackendConfig` | Implement `_ScriptedFetcher.default_backend_config`. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L34) | `_ScriptedFetcher.fetch` | `**_: object` | `LLMOutput` | Implement `_ScriptedFetcher.fetch`. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L48) | `_make_agent` | `fetcher: _ScriptedFetcher` | `Agent` | Implement `_make_agent`. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L71) | `UsageLifetimeTests.test_lifetime_usage_accumulates_across_runs` | `None` | `None` | The per-run counter resets; the lifetime counter keeps growing. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L90) | `UsageLifetimeTests.test_swarm_total_usage_does_not_drop_on_new_lifecycle` | `None` | `None` | The Session aggregate is monotonic across consecutive runs. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L109) | `UsageLifetimeTests.test_swarm_falls_back_to_usage_without_lifetime_counter` | `None` | `None` | Legacy agents expose their per-run counter instead of dropping out. |

## Class Map

| Source | Class | Constructor / field input types | Base(s) | Semantics |
|---|---|---|---|---|
| [test_execution_controller.py](test_execution_controller.py#L19) | `ExecutionControllerTests` | `None` | `unittest.TestCase` | Verify one stop request governs resource cancellation and observation. |
| [test_execution_controller.py](test_execution_controller.py#L164) | `_BlockingHandler` | `None` | `object` | Minimal provider double whose close wakes a blocked completion call. |
| [test_execution_controller.py](test_execution_controller.py#L184) | `_StreamingHandler` | `None` | `_BlockingHandler` | Provider double that emits one chunk then blocks on the transport. |
| [test_multimodal.py](test_multimodal.py#L20) | `NativeVisionTests` | `None` | `unittest.TestCase` | Provide `NativeVisionTests` behavior. |
| [test_openai_tool_names.py](test_openai_tool_names.py#L11) | `OpenAIToolNameTests` | `None` | `unittest.TestCase` | Provide `OpenAIToolNameTests` behavior. |
| [test_tool_validation.py](test_tool_validation.py#L17) | `ToolCallValidationTests` | `None` | `unittest.TestCase` | Ensure malformed model calls become recoverable tool feedback. |
| [test_tool_validation.py](test_tool_validation.py#L55) | `ContextSaveDiagnosticTests` | `None` | `unittest.TestCase` | Retain the actual context-save failure through the Agent boundary. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L20) | `_ScriptedFetcher` | `input_tokens: int, output_tokens: int` | `object` | Return a fixed provider usage for every model round. |
| [test_usage_lifetime.py](test_usage_lifetime.py#L61) | `_LegacyAgent` | `usage: TokenUsage` | `object` | Agent-shaped fake without ``lifetime_usage`` (older builds / hosts). |
| [test_usage_lifetime.py](test_usage_lifetime.py#L68) | `UsageLifetimeTests` | `None` | `unittest.TestCase` | A new lifecycle must not erase the Session's earlier usage. |

<!-- END GENERATED SYMBOL MAP -->
