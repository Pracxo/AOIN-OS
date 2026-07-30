# Secure Runtime Resource Budgets

Every AION-231 limit is exact. Any limit violation must fail closed.

## Positive Limits

- `maximum_local_operator_sessions=1`
- `maximum_session_seconds=3600`
- `maximum_requests_per_session=100`
- `maximum_concurrent_requests=4`
- `maximum_capability_plans_per_request=10`
- `maximum_capability_invocations_per_session=100`
- `maximum_policy_decisions_per_request=20`
- `maximum_risk_assessments_per_request=20`
- `maximum_guardrail_decisions_per_request=20`
- `maximum_approval_evidence_records_per_request=4`
- `maximum_stage_receipts_per_session=1000`
- `maximum_audit_records_per_session=10000`
- `maximum_telemetry_events_per_session=10000`
- `maximum_operator_review_items_per_session=500`
- `maximum_trace_bytes_per_session=4194304`
- `maximum_response_bytes_per_request=1048576`
- `maximum_fixture_records=5000`
- `maximum_fixture_bytes=4194304`
- `maximum_session_checkpoints=20`
- `maximum_replay_validations_per_request=10`
- `maximum_kill_switch_checks_per_request=10`

## Zero Limits

- `maximum_public_network_calls=0`
- `maximum_model_provider_calls=0`
- `maximum_connector_calls=0`
- `maximum_actual_tool_executions=0`
- `maximum_shell_commands=0`
- `maximum_subprocess_executions=0`
- `maximum_browser_actions=0`
- `maximum_credentials_persisted=0`
- `maximum_tokens_persisted=0`
- `maximum_session_tokens_issued=0`
- `maximum_external_identity_provider_calls=0`
- `maximum_modules_activated=0`
- `maximum_packages_installed=0`
- `maximum_dynamic_routes_registered=0`
- `maximum_automatic_approvals=0`
- `maximum_runtime_created_approvals=0`
- `maximum_production_writes=0`
- `maximum_production_memory_writes=0`
- `maximum_production_policy_mutations=0`
- `maximum_cognitive_memory_writes=0`
- `maximum_actual_belief_creations=0`
- `maximum_actual_belief_mutations=0`
- `maximum_glm_live_executions=0`
- `maximum_source_mutations=0`
- `maximum_git_operations=0`
- `maximum_runtime_created_pull_requests=0`
- `maximum_automatic_merges=0`
- `maximum_production_canary_executions=0`
- `maximum_deployments=0`
- `maximum_model_weight_changes=0`
