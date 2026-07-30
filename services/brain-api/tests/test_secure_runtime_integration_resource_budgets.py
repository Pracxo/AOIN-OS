from __future__ import annotations

from test_secure_runtime_integration_program_charter import RESOURCE_LIMITS, load_json


def test_resource_limits_are_exact_in_program_and_authorization_ledgers() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")

    assert program["resource_limits"] == RESOURCE_LIMITS
    assert auth["resource_limits"] == RESOURCE_LIMITS


def test_positive_and_zero_resource_limits_fail_closed_by_definition() -> None:
    positive_limits = {key: value for key, value in RESOURCE_LIMITS.items() if value > 0}
    zero_limits = {key: value for key, value in RESOURCE_LIMITS.items() if value == 0}

    assert positive_limits == {
        "maximum_local_operator_sessions": 1,
        "maximum_session_seconds": 3600,
        "maximum_requests_per_session": 100,
        "maximum_concurrent_requests": 4,
        "maximum_capability_plans_per_request": 10,
        "maximum_capability_invocations_per_session": 100,
        "maximum_policy_decisions_per_request": 20,
        "maximum_risk_assessments_per_request": 20,
        "maximum_guardrail_decisions_per_request": 20,
        "maximum_approval_evidence_records_per_request": 4,
        "maximum_stage_receipts_per_session": 1000,
        "maximum_audit_records_per_session": 10000,
        "maximum_telemetry_events_per_session": 10000,
        "maximum_operator_review_items_per_session": 500,
        "maximum_trace_bytes_per_session": 4194304,
        "maximum_response_bytes_per_request": 1048576,
        "maximum_fixture_records": 5000,
        "maximum_fixture_bytes": 4194304,
        "maximum_session_checkpoints": 20,
        "maximum_replay_validations_per_request": 10,
        "maximum_kill_switch_checks_per_request": 10,
    }
    assert set(zero_limits) == {
        "maximum_public_network_calls",
        "maximum_model_provider_calls",
        "maximum_connector_calls",
        "maximum_actual_tool_executions",
        "maximum_shell_commands",
        "maximum_subprocess_executions",
        "maximum_browser_actions",
        "maximum_credentials_persisted",
        "maximum_tokens_persisted",
        "maximum_session_tokens_issued",
        "maximum_external_identity_provider_calls",
        "maximum_modules_activated",
        "maximum_packages_installed",
        "maximum_dynamic_routes_registered",
        "maximum_automatic_approvals",
        "maximum_runtime_created_approvals",
        "maximum_production_writes",
        "maximum_production_memory_writes",
        "maximum_production_policy_mutations",
        "maximum_cognitive_memory_writes",
        "maximum_actual_belief_creations",
        "maximum_actual_belief_mutations",
        "maximum_glm_live_executions",
        "maximum_source_mutations",
        "maximum_git_operations",
        "maximum_runtime_created_pull_requests",
        "maximum_automatic_merges",
        "maximum_production_canary_executions",
        "maximum_deployments",
        "maximum_model_weight_changes",
    }
