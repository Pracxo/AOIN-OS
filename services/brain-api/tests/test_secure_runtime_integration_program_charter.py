from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
PROGRAM_STATE = "controlled_model_gateway_implemented_reference_simulation_only_pending_closeout"
AUTH_ID = "AION-230-SRI-0001"
IMPLEMENTATION_TASK = "AION-231"
CLOSEOUT_TASK = "AION-232"
CURRENT_AUTH_ID = "AION-232-SRI-0002"
CURRENT_IMPLEMENTATION_TASK = "AION-233"
CURRENT_CLOSEOUT_TASK = "AION-234"
FINAL_TASK = "AION-238"
AUTH_SCOPE = (
    "local-operator-authenticated-session-offline-identity-request-context-"
    "actor-context-replay-guarded-capability-dispatch-policy-risk-approval-"
    "kill-switch-audit-observability-foundation-core"
)
GLM_DECISION = (
    "CONTROLLED_LOCAL_CONTINUAL_LEARNING_PILOT_FINAL_EVALUATION_PASS_COMPLETE_"
    "GOVERNED_LEARNING_MEMORY_PROGRAM"
)
PARENT_PROGRAMS = [
    "AION-COGNITIVE-ARCHITECTURE-001",
    "AION-KNOWLEDGE-INTELLIGENCE-001",
    "AION-GOVERNED-LEARNING-MEMORY-001",
    "AION-SELF-IMPROVEMENT-001",
]
AUTHORIZED_CAPABILITIES = [
    "secure_runtime_contract_approved",
    "local_operator_runtime_authorization_envelope_approved",
    "offline_ed25519_identity_assertion_composition_approved",
    "public_key_registry_read_approved",
    "request_identity_context_projection_approved",
    "actor_context_binding_approved",
    "persistent_replay_protection_validation_approved",
    "ephemeral_operator_session_lifecycle_approved",
    "explicit_session_start_approved",
    "explicit_session_close_approved",
    "deterministic_runtime_state_machine_approved",
    "runtime_request_envelope_approved",
    "capability_invocation_plan_approved",
    "closed_capability_allowlist_approved",
    "policy_decision_binding_approved",
    "risk_assessment_binding_approved",
    "guardrail_decision_binding_approved",
    "existing_approval_evidence_validation_approved",
    "side_effect_budget_enforcement_approved",
    "runtime_guard_approved",
    "operator_kill_switch_approved",
    "request_trace_correlation_approved",
    "runtime_audit_projection_approved",
    "runtime_observability_snapshot_approved",
    "runtime_health_readiness_approved",
    "deterministic_runtime_fixture_replay_approved",
    "local_operator_runtime_pilot_approved",
    "read_only_operator_console_projection_approved",
    "operator_review_item_approved",
    "redacted_runtime_evidence_approved",
    "documentation_and_static_evidence_approved",
]
PROHIBITED_CAPABILITIES = [
    "production_auth_runtime_enabled",
    "public_auth_endpoint_enabled",
    "external_identity_provider_enabled",
    "password_authentication_enabled",
    "credential_persistence_enabled",
    "token_persistence_enabled",
    "session_token_issuance_enabled",
    "refresh_token_enabled",
    "public_key_network_retrieval_enabled",
    "general_network_access_enabled",
    "public_network_access_enabled",
    "model_provider_integration_enabled",
    "model_provider_call_enabled",
    "connector_integration_enabled",
    "connector_execution_enabled",
    "actual_tool_execution_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "browser_automation_enabled",
    "module_activation_enabled",
    "module_code_loading_enabled",
    "package_installation_enabled",
    "dynamic_route_registration_enabled",
    "automatic_capability_execution_enabled",
    "automatic_approval_enabled",
    "runtime_approval_creation_enabled",
    "production_write_execution_enabled",
    "production_memory_write_enabled",
    "production_policy_mutation_enabled",
    "cognitive_memory_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "glm_live_execution_enabled",
    "repeat_continual_learning_pilot_enabled",
    "self_improvement_runtime_enabled",
    "source_rewrite_enabled",
    "git_mutation_enabled",
    "runtime_pull_request_creation_enabled",
    "automatic_merge_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_exposure",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
]
RESOURCE_LIMITS = {
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
    "maximum_public_network_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_credentials_persisted": 0,
    "maximum_tokens_persisted": 0,
    "maximum_session_tokens_issued": 0,
    "maximum_external_identity_provider_calls": 0,
    "maximum_modules_activated": 0,
    "maximum_packages_installed": 0,
    "maximum_dynamic_routes_registered": 0,
    "maximum_automatic_approvals": 0,
    "maximum_runtime_created_approvals": 0,
    "maximum_production_writes": 0,
    "maximum_production_memory_writes": 0,
    "maximum_production_policy_mutations": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_actual_belief_creations": 0,
    "maximum_actual_belief_mutations": 0,
    "maximum_glm_live_executions": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_automatic_merges": 0,
    "maximum_production_canary_executions": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}
FUTURE_SOURCE_SCOPE = [
    "services/brain-api/src/aion_brain/contracts/secure_runtime.py",
    "services/brain-api/src/aion_brain/secure_runtime/__init__.py",
    "services/brain-api/src/aion_brain/secure_runtime/authorization.py",
    "services/brain-api/src/aion_brain/secure_runtime/identity_binding.py",
    "services/brain-api/src/aion_brain/secure_runtime/session_lifecycle.py",
    "services/brain-api/src/aion_brain/secure_runtime/request_pipeline.py",
    "services/brain-api/src/aion_brain/secure_runtime/capability_dispatch.py",
    "services/brain-api/src/aion_brain/secure_runtime/runtime_guard.py",
    "services/brain-api/src/aion_brain/secure_runtime/kill_switch.py",
    "services/brain-api/src/aion_brain/secure_runtime/audit.py",
    "services/brain-api/src/aion_brain/secure_runtime/observability.py",
    "services/brain-api/src/aion_brain/secure_runtime/integrity.py",
    "services/brain-api/src/aion_brain/secure_runtime/evidence.py",
]
FUTURE_CONTRACTS = [
    "SecureRuntimeAuthorizationEnvelope",
    "SecureOperatorIdentityBinding",
    "SecureRequestIdentityBinding",
    "SecureActorContextBinding",
    "SecureRuntimeSessionPlan",
    "SecureRuntimeSession",
    "SecureRuntimeStageCommand",
    "SecureRuntimeStageReceipt",
    "SecureRuntimeRequestEnvelope",
    "SecureCapabilityInvocationPlan",
    "SecurePolicyBinding",
    "SecureRiskBinding",
    "SecureGuardrailBinding",
    "SecureApprovalEvidenceBundle",
    "SecureSideEffectBudget",
    "SecureRuntimeGuardDecision",
    "SecureRuntimeKillSwitchState",
    "SecureRuntimeAuditRecord",
    "SecureRuntimeObservabilitySnapshot",
    "SecureRuntimeHealthSnapshot",
    "SecureRuntimeSessionCheckpoint",
    "SecureRuntimeSessionResult",
    "SecureRuntimeIntegrityReport",
    "SecureRuntimeEvidenceBundle",
    "SecureRuntimeOperatorReviewItem",
]
STATE_MACHINE_STATES = [
    "drafted",
    "authorized",
    "identity_assertion_verified",
    "request_identity_bound",
    "actor_context_bound",
    "replay_validation_passed",
    "runtime_guard_ready",
    "session_active",
    "request_validated",
    "capability_plan_created",
    "policy_evaluated",
    "risk_evaluated",
    "guardrails_evaluated",
    "approval_validated",
    "simulated_dispatch_completed",
    "response_recorded",
    "session_closed",
]
TERMINAL_STATES = ["abstained", "blocked", "killed", "expired", "failed"]
RELEASE_BLOCKERS = [
    "Production-auth runtime integration",
    "Production replay-ledger provisioning",
    "Request-level verified identity integration",
    "Identity-provider integration",
    "Public-key operational provisioning and rotation",
    "Protected-material lifecycle",
    "Credential lifecycle",
    "Token lifecycle",
    "Session lifecycle",
    "Deployment artifact",
    "Rollback operations",
    "Production observability",
    "Threat-model review",
    "Runtime guard release decision",
    "Release-candidate validation",
    "Explicit v0.2 tag and release authorization",
]


def load_json(relative: str) -> dict[str, Any]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def read_text(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_program_charter_creates_separate_sri_program() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    charter = read_text("docs/secure-runtime-integration/program-charter.md")

    assert program["program_id"] == PROGRAM_ID
    assert program["program_name"] == "AION Secure Runtime Integration Program"
    assert program["created_by_task"] == "AION-230"
    assert program["program_state"] == PROGRAM_STATE
    assert program["program_authorized"] is True
    assert program["secure_runtime_integration_program_authorized"] is True
    assert program["parent_completed_programs"] == PARENT_PROGRAMS
    assert program["parent_glm_evaluation_id"] == "AION-GLMPE-004"
    assert program["parent_glm_evaluation_decision"] == GLM_DECISION
    assert program["active_sri_implementation_authorization_count"] == 1
    assert program["active_sri_implementation_authorization"] == CURRENT_AUTH_ID
    assert program["active_sri_implementation_task"] == CURRENT_IMPLEMENTATION_TASK
    assert program["formal_closeout_task"] == CURRENT_CLOSEOUT_TASK
    assert program["final_planned_task"] == FINAL_TASK
    assert program["secure_runtime_foundation_operator_evaluation_passed"] is True
    assert program["secure_runtime_foundation_operator_evaluation_id"] == "AION-SRIPE-001"
    assert program["model_gateway_authorized"] is True
    assert program["model_gateway_implemented"] is True
    assert program["model_gateway_state"] == (
        "implemented_provider_neutral_reference_simulation_only_pending_AION-234_closeout"
    )

    assert "Program ID: `AION-SECURE-RUNTIME-INTEGRATION-001`" in charter
    assert "does not reopen any parent program" in charter
    assert "inherits no active parent-program implementation authorization" in charter
    assert "AION-230-SRI-0001` is closed" in charter
    assert "AION-232-SRI-0002` is the sole active" in charter
    assert "AION-231 remains implemented" in charter
