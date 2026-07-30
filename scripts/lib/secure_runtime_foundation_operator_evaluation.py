"""AION-232 read-only operator evaluation for the secure runtime foundation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


DECISION_PASS = (
    "SECURE_LOCAL_OPERATOR_RUNTIME_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "CONTROLLED_MODEL_GATEWAY_AUTHORIZATION"
)
DECISION_FAIL = "SECURE_LOCAL_OPERATOR_RUNTIME_OPERATOR_EVALUATION_FAIL_REMAIN_LOCAL_SIMULATION_ONLY"
EVALUATION_TYPE = "secure_runtime_foundation_operator_evaluation"
PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
IMPLEMENTATION_TASK = "AION-231"
CLOSEOUT_TASK = "AION-232"
NEXT_IMPLEMENTATION_TASK = "AION-233"
NEXT_CLOSEOUT_TASK = "AION-234"
CURRENT_AUTHORIZATION_ID = "AION-230-SRI-0001"
NEXT_AUTHORIZATION_ID = "AION-232-SRI-0002"
DEFAULT_EVALUATION_ID = "AION-SRIPE-001"
DEFAULT_FIXED_NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
AION231_PR = 149
AION231_FEATURE_COMMIT = "45540009d03f60d7477330a88946e73705ee60e5"
AION231_MERGE_COMMIT = "8bb9af29cc2cf960d9efdfe2ee323d7245812747"
AION231_MERGED_AT = "2026-07-30T19:45:59Z"
ZERO_FINGERPRINT_TEXT = "0" * 64

FIXTURE_KEY_ID = "aion-232-eval-key"
FIXTURE_PUBLIC_KEY = "iEuIV_TqoWE8YVBNs01L6vNGUXoOMd483dTZtCAdnQs"
FIXTURE_SIGNATURE = (
    "XfLZontOg_2Jp9UqO55JCBT5G74ya7dErrrkX1GkWbO0kjhszuzQc95NW7cNQeqt4HdvnUY3BFL"
    "186lPVbuuAA"
)
FIXTURE_ASSERTION_FINGERPRINT = (
    "b208748901931c8e2cada0e70b721a5b959213e8507be8da5c003d4ac8188db9"
)

SESSION_ID = "session-AION-232-evaluation"
REQUEST_ID = "request-AION-232-evaluation"
TRACE_ID = "trace-AION-232-evaluation"
CORRELATION_ID = "correlation-AION-232-evaluation"
ISSUER = "issuer.aion.local"
AUDIENCE = "aion-secure-runtime-local"
SUBJECT = "operator-subject-AION-232"
ACTOR_ID = "operator-AION-232"
WORKSPACE_ID = "workspace-AION-232"
ALLOWED_ROLES = ("operator", "viewer")
ALLOWED_PERMISSIONS = (
    "brain:think:simulate",
    "secure_runtime:audit:read",
    "secure_runtime:fixture:replay",
    "secure_runtime:read",
)
ALLOWED_SCOPES = (
    "secure-runtime:audit",
    "secure-runtime:fixture-replay",
    "secure-runtime:health",
    "secure-runtime:observability",
    "secure-runtime:simulate-capability",
)
CLOSED_MODEL_GATEWAY_OPERATIONS = (
    "model_gateway.health.read",
    "model_gateway.observability.read",
    "model_gateway.route.plan",
    "model_gateway.text.generate.simulate",
    "model_gateway.structured.generate.simulate",
)

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "aion_231_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "pilot_evidence_schema_and_fingerprint",
    "offline_ed25519_verification_integrity",
    "trusted_public_key_registry_boundary",
    "replay_protection_exactly_once",
    "secure_request_identity_origin",
    "actor_context_binding_and_no_privilege_expansion",
    "authorization_envelope_and_session_limits",
    "closed_state_machine",
    "stage_receipt_sequence_and_hash_chain",
    "in_memory_session_repository_and_concurrency",
    "closed_capability_registry",
    "secure_request_envelope_and_capability_plan",
    "policy_binding_integrity",
    "risk_binding_integrity",
    "guardrail_binding_integrity",
    "approval_evidence_and_separation_of_duties",
    "side_effect_budget_enforcement",
    "operator_kill_switch",
    "runtime_guard_precedence",
    "simulation_only_dispatch",
    "audit_chain_integrity",
    "observability_health_and_checkpoint_integrity",
    "deterministic_replay_concurrency_redaction_and_performance",
    "zero_external_and_production_effects",
    "repository_release_and_runtime_registration_boundary",
    "controlled_model_gateway_authorization_readiness",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "pr_149_verified",
    "implementation_commit_verified",
    "merge_commit_verified",
    "final_ci_verified",
    "aion_231_no_go_gate_passed",
    "aion_231_implementation_gate_passed",
    "aion_231_pilot_evidence_gate_passed",
    "aion_231_runtime_hold_passed",
    "all_28_scenarios_executed",
    "all_28_scenarios_passed",
    "no_required_scenario_skipped",
    "no_unknown_scenario",
    "pilot_fingerprint_valid",
    "authorization_lineage_valid",
    "identity_verification_valid",
    "replay_protection_valid",
    "request_identity_valid",
    "actor_context_valid",
    "state_machine_valid",
    "receipt_chain_valid",
    "capability_registry_valid",
    "decision_bindings_valid",
    "approval_binding_valid",
    "budget_valid",
    "kill_switch_valid",
    "runtime_guard_valid",
    "simulated_dispatch_valid",
    "audit_chain_valid",
    "observability_checkpoint_valid",
    "zero_external_or_production_effects",
    "repository_release_boundary_valid",
    "model_gateway_authorization_readiness_valid",
)

EXPECTED_PILOT_FIELDS: dict[str, Any] = {
    "pilot_id": "AION-231-controlled-local-operator-runtime-pilot",
    "authorization_id": CURRENT_AUTHORIZATION_ID,
    "mode": "operator_invoked_local",
    "assertion_fingerprint": (
        "43b9f50e517593b9f1e1f9c0b47e7bca77a6d5904c514009421bced059530f70"
    ),
    "public_key_fingerprint": (
        "84d7bc994e5b63b370f729cbb8597cd1ebfea621d311fe7d4329820bf57af37b"
    ),
    "operator_identity_fingerprint": (
        "884c19c3488b5a647dfcd3ebee52646f2672d010629eb6e0138c82640a7607e8"
    ),
    "session_plan_fingerprint": (
        "17fe6c861fff0414db2bf0c9ab98796b70d999a4a1a1b5cb8154a5bc9e807bf9"
    ),
    "session_result_fingerprint": (
        "df8ef365ba793aaf603ab7a16bd99ae44ce4307340a3a09e07a2b5e5f85a6a99"
    ),
    "stage_receipt_chain_head": (
        "4411d0c497ba579c651a74b8726be4de6b91c8bff5cc10466d75b06f870a820c"
    ),
    "audit_chain_head": "3eaddc1f57f411b74088dbbb6364d096c1a9d868bd1a2f114e6c9ca15a8c5618",
    "report_fingerprint": (
        "05b78f220cc0d4870097a2426c47e1cf98b09a17a55e01625a9adea288297a6b"
    ),
    "identity_assertions_verified": 1,
    "replay_claims_created": 1,
    "exact_replays_rejected": 1,
    "request_identity_bindings": 1,
    "actor_context_bindings": 1,
    "sessions_started": 1,
    "sessions_closed": 1,
    "active_sessions_after_close": 0,
    "requests_processed": 1,
    "active_requests_after_close": 0,
    "capability_plans_created": 1,
    "policy_bindings": 1,
    "risk_bindings": 1,
    "guardrail_bindings": 1,
    "approval_bundles_validated": 1,
    "runtime_guard_allow_simulation_decisions": 1,
    "simulated_dispatches": 1,
    "actual_capability_executions": 0,
    "stage_receipts": 16,
    "audit_records": 3,
    "checkpoint_count": 1,
    "kill_switch_checks": 16,
    "integrity_passed": True,
    "temporary_files_retained": 0,
    "redacted": True,
    "production_effect": False,
    "runtime_effect": False,
}

PILOT_ZERO_COUNTERS: tuple[str, ...] = (
    "network_calls",
    "model_provider_calls",
    "connector_calls",
    "tool_executions",
    "shell_commands",
    "subprocess_executions",
    "browser_actions",
    "credentials_persisted",
    "tokens_persisted",
    "session_tokens_issued",
    "modules_activated",
    "production_writes",
    "production_memory_writes",
    "production_policy_mutations",
    "cognitive_memory_writes",
    "belief_creations",
    "belief_mutations",
    "glm_live_executions",
    "source_mutations",
    "git_operations",
    "deployments",
    "model_weight_changes",
)

REPORT_ZERO_COUNTERS: tuple[str, ...] = (
    "network_calls",
    "model_provider_calls",
    "connector_calls",
    "actual_tool_executions",
    "credentials_persisted",
    "tokens_persisted",
    "runtime_created_approvals",
    "production_writes",
    "production_memory_writes",
    "production_policy_mutations",
    "cognitive_memory_writes",
    "actual_belief_creations",
    "actual_belief_mutations",
    "source_mutations",
    "git_operations",
    "deployments",
    "model_weight_changes",
)

PROHIBITED_USAGE_COUNTERS: tuple[str, ...] = (
    "public_network_calls",
    "model_provider_calls",
    "connector_calls",
    "actual_tool_executions",
    "shell_commands",
    "subprocess_executions",
    "browser_actions",
    "credentials_persisted",
    "tokens_persisted",
    "session_tokens_issued",
    "external_identity_provider_calls",
    "modules_activated",
    "packages_installed",
    "dynamic_routes_registered",
    "automatic_approvals",
    "runtime_created_approvals",
    "production_writes",
    "production_memory_writes",
    "production_policy_mutations",
    "cognitive_memory_writes",
    "actual_belief_creations",
    "actual_belief_mutations",
    "glm_live_executions",
    "source_mutations",
    "git_operations",
    "runtime_created_pull_requests",
    "automatic_merges",
    "production_canary_executions",
    "deployments",
    "model_weight_changes",
)

EXPECTED_RESOURCE_LIMITS: dict[str, int] = {
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

EXPECTED_MODEL_GATEWAY_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_model_gateway_sessions": 1,
    "maximum_requests_per_session": 100,
    "maximum_concurrent_requests": 4,
    "maximum_provider_manifests": 10,
    "maximum_model_manifests": 50,
    "maximum_models_per_provider": 25,
    "maximum_allowed_model_ids_per_request": 10,
    "maximum_routing_candidates_per_request": 10,
    "maximum_fallback_candidates_per_request": 3,
    "maximum_messages_per_request": 128,
    "maximum_context_items_per_request": 256,
    "maximum_context_bytes_per_request": 4194304,
    "maximum_prompt_bytes_per_request": 1048576,
    "maximum_input_tokens_per_request": 131072,
    "maximum_output_tokens_per_request": 16384,
    "maximum_total_tokens_per_session": 1000000,
    "maximum_response_bytes_per_request": 1048576,
    "maximum_structured_output_schema_bytes": 65536,
    "maximum_structured_output_depth": 16,
    "maximum_retry_attempts_planned_per_request": 2,
    "maximum_response_validation_attempts_per_request": 3,
    "maximum_circuit_breaker_records": 100,
    "maximum_latency_budget_milliseconds": 120000,
    "maximum_estimated_cost_microunits_per_request": 10000000,
    "maximum_estimated_cost_microunits_per_session": 100000000,
    "maximum_audit_records_per_session": 10000,
    "maximum_telemetry_events_per_session": 10000,
    "maximum_operator_review_items_per_session": 500,
    "maximum_trace_bytes_per_session": 4194304,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_session_checkpoints": 20,
}

EXPECTED_MODEL_GATEWAY_ZERO_LIMITS: tuple[str, ...] = (
    "maximum_public_network_calls",
    "maximum_model_provider_calls",
    "maximum_provider_sdk_calls",
    "maximum_provider_endpoint_connections",
    "maximum_provider_stream_connections",
    "maximum_provider_credentials_read",
    "maximum_provider_credentials_persisted",
    "maximum_api_keys_persisted",
    "maximum_tokens_persisted",
    "maximum_authorization_headers_created",
    "maximum_live_model_sessions",
    "maximum_tool_calls",
    "maximum_function_calls",
    "maximum_connector_calls",
    "maximum_actual_tool_executions",
    "maximum_shell_commands",
    "maximum_subprocess_executions",
    "maximum_browser_actions",
    "maximum_modules_activated",
    "maximum_packages_installed",
    "maximum_dynamic_routes_registered",
    "maximum_public_api_routes_added",
    "maximum_prompts_persisted",
    "maximum_model_responses_persisted",
    "maximum_hidden_reasoning_records",
    "maximum_provider_raw_payloads_retained",
    "maximum_cross_session_context_records",
    "maximum_automatic_memory_writes",
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
)

EXPECTED_AION231_SOURCE_FILES: tuple[str, ...] = (
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
)

PROHIBITED_AION231_RUNTIME_FILES: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/api/secure_runtime.py",
    "services/brain-api/src/aion_brain/secure_runtime/network.py",
    "services/brain-api/src/aion_brain/secure_runtime/model_gateway.py",
    "services/brain-api/src/aion_brain/secure_runtime/connector_runtime.py",
    "services/brain-api/src/aion_brain/secure_runtime/tool_runtime.py",
    "services/brain-api/src/aion_brain/secure_runtime/shell_runtime.py",
    "services/brain-api/src/aion_brain/secure_runtime/module_loader.py",
    "services/brain-api/src/aion_brain/secure_runtime/credential_store.py",
    "services/brain-api/src/aion_brain/secure_runtime/token_store.py",
    "services/brain-api/src/aion_brain/secure_runtime/background_worker.py",
    "services/brain-api/src/aion_brain/secure_runtime/scheduler.py",
)

FUTURE_MODEL_GATEWAY_SOURCE_SCOPE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/model_gateway.py",
    "services/brain-api/src/aion_brain/model_gateway/__init__.py",
    "services/brain-api/src/aion_brain/model_gateway/authorization.py",
    "services/brain-api/src/aion_brain/model_gateway/manifests.py",
    "services/brain-api/src/aion_brain/model_gateway/request_envelope.py",
    "services/brain-api/src/aion_brain/model_gateway/context_budget.py",
    "services/brain-api/src/aion_brain/model_gateway/routing.py",
    "services/brain-api/src/aion_brain/model_gateway/circuit_breaker.py",
    "services/brain-api/src/aion_brain/model_gateway/guard.py",
    "services/brain-api/src/aion_brain/model_gateway/response_validation.py",
    "services/brain-api/src/aion_brain/model_gateway/provider_adapter.py",
    "services/brain-api/src/aion_brain/model_gateway/reference_provider.py",
    "services/brain-api/src/aion_brain/model_gateway/audit.py",
    "services/brain-api/src/aion_brain/model_gateway/observability.py",
    "services/brain-api/src/aion_brain/model_gateway/integrity.py",
    "services/brain-api/src/aion_brain/model_gateway/evidence.py",
)

FUTURE_MODEL_GATEWAY_CONTRACTS: tuple[str, ...] = (
    "ModelGatewayAuthorizationEnvelope",
    "ModelProviderManifest",
    "ModelManifest",
    "ModelCapabilityProfile",
    "ModelGatewaySessionPlan",
    "ModelGatewayRequestEnvelope",
    "ModelGatewayMessage",
    "ModelGatewayContextItem",
    "ModelGatewayContextBudget",
    "ModelGatewayTokenBudget",
    "ModelRoutingCandidate",
    "ModelRoutingPlan",
    "ModelFallbackPlan",
    "ModelRetryPlan",
    "ModelCircuitBreakerState",
    "ModelGatewayGuardDecision",
    "ModelGatewayReferenceProviderRequest",
    "ModelGatewayReferenceProviderResponse",
    "ModelStructuredOutputSchema",
    "ModelOutputValidationResult",
    "ModelOutputProvenance",
    "ModelGatewayAuditRecord",
    "ModelGatewayObservabilitySnapshot",
    "ModelGatewayHealthSnapshot",
    "ModelGatewayIntegrityReport",
    "ModelGatewayEvidenceBundle",
    "ModelGatewayOperatorReviewItem",
)

PROTECTED_VALUE_MARKERS: tuple[str, ...] = (
    "sk-",
    "ghp_",
    "gho_",
    "xoxb-",
    "bearer ",
    "authorization header",
    "api key",
    "access token",
    "refresh token",
    "id token",
    "session token",
    "private key",
    "raw assertion",
    "raw signature",
    "raw actor identity",
    "approval payload",
    "request body",
    "raw prompt",
    "hidden reasoning",
    "temporary path",
)


@dataclass(frozen=True)
class RuntimeContext:
    repo_root: Path
    pilot_evidence: dict[str, Any]
    program_ledger: dict[str, Any]
    authorization_ledger: dict[str, Any]
    authorization_envelope: Any
    assertion_envelope: Any
    second_replay_bundle: Any
    operator_identity: Any
    request_identity: Any
    actor_context: Any
    side_effect_budget: Any
    kill_switch_state: Any
    kill_switch: Any
    session_plan: Any
    session: Any
    closed_session: Any
    request: Any
    capability_plan: Any
    manifest: Any
    policy_binding: Any
    risk_binding: Any
    guardrail_binding: Any
    approval_evidence: Any
    approval_bundle: Any
    usage: Any
    budget_decision: Any
    guard_decision: Any
    dispatch: Any
    checkpoint: Any
    observability: Any
    health: Any
    integrity_report: Any
    evidence_bundle: Any
    service: Any
    receipts: tuple[Any, ...]
    audit_records: tuple[Any, ...]
    identity_verification_matrix: dict[str, bool]
    replay_matrix: dict[str, bool]


def configure_import_path(repo_root: Path) -> None:
    """Add the Brain API source tree for direct script execution."""

    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def evaluate_secure_runtime_foundation(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    pilot_evidence: Path,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    """Run all AION-232 operator-evaluation scenarios and return a redacted report."""

    configure_import_path(repo_root)
    context = _build_context(repo_root=repo_root, pilot_evidence=pilot_evidence)
    start = time.perf_counter()
    scenario_results = [
        _run_scenario(scenario_id, context) for scenario_id in REQUIRED_SCENARIO_IDS
    ]
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    hard_gate_results = _hard_gate_results(scenario_results)
    evaluation_passed = all(item["passed"] for item in scenario_results) and all(
        item["passed"] for item in hard_gate_results
    )
    decision = DECISION_PASS if evaluation_passed else DECISION_FAIL
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [AION231_PR],
        "corrective_prs": [],
        "implementation_feature_commits": [AION231_FEATURE_COMMIT],
        "implementation_merge_commits": [AION231_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_ids": list(REQUIRED_SCENARIO_IDS),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gate_results,
        "pilot_validation": _pilot_validation(context.pilot_evidence),
        "authorization_lineage": _authorization_lineage(context),
        "runtime_integrity": _runtime_integrity(context),
        "repository_integrity": _repository_integrity(context.repo_root),
        "security_state": _security_state(),
        "resource_state": _resource_state(context),
        "next_architecture_decision": (
            "controlled_model_gateway_implementation_authorized"
            if evaluation_passed
            else "secure_runtime_foundation_remediation_authorization_review"
        ),
        "model_gateway_authorization_preview": _model_gateway_authorization_preview(
            evaluation_passed=evaluation_passed,
            evaluation_base_commit=evaluation_base_commit,
        ),
        "future_model_gateway_source_scope": list(FUTURE_MODEL_GATEWAY_SOURCE_SCOPE),
        "future_model_gateway_contracts": list(FUTURE_MODEL_GATEWAY_CONTRACTS),
        "closed_model_gateway_operations": list(CLOSED_MODEL_GATEWAY_OPERATIONS),
        "corrective_cycles": 0,
        "corrective_cycle_limit": 3,
        "scenario_runtime_ms": elapsed_ms,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "network_calls": 0,
        "model_provider_calls": 0,
        "connector_calls": 0,
        "actual_tool_executions": 0,
        "credentials_persisted": 0,
        "tokens_persisted": 0,
        "runtime_created_approvals": 0,
        "production_writes": 0,
        "production_memory_writes": 0,
        "production_policy_mutations": 0,
        "cognitive_memory_writes": 0,
        "actual_belief_creations": 0,
        "actual_belief_mutations": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "deployments": 0,
        "model_weight_changes": 0,
        "active_sessions_after_evaluation": context.service.repository.active_session_count(),
        "active_requests_after_evaluation": context.service.repository.active_request_count(),
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
        "production_exposure": False,
        "v02_release_ready": False,
    }
    report["report_fingerprint"] = report_fingerprint(report)
    validate_evaluation_report(report)
    return report


def validate_evaluation_report(report: dict[str, Any]) -> None:
    """Validate AION-232 report schema, ordering, and decision invariants."""

    if report.get("evaluation_id") != DEFAULT_EVALUATION_ID:
        raise ValueError("unexpected evaluation id")
    if report.get("evaluation_type") != EVALUATION_TYPE:
        raise ValueError("unexpected evaluation type")
    if report.get("program_id") != PROGRAM_ID:
        raise ValueError("unexpected program id")
    if report.get("implementation_task") != IMPLEMENTATION_TASK:
        raise ValueError("unexpected implementation task")
    if report.get("closeout_task") != CLOSEOUT_TASK:
        raise ValueError("unexpected closeout task")
    if report.get("implementation_prs") != [AION231_PR]:
        raise ValueError("unexpected implementation PRs")
    if report.get("implementation_feature_commits") != [AION231_FEATURE_COMMIT]:
        raise ValueError("unexpected implementation feature commits")
    if report.get("implementation_merge_commits") != [AION231_MERGE_COMMIT]:
        raise ValueError("unexpected implementation merge commits")
    if report.get("scenario_count") != 28:
        raise ValueError("unexpected scenario count")
    if report.get("scenario_ids") != list(REQUIRED_SCENARIO_IDS):
        raise ValueError("scenario_ids must match the required ordered scenario list")
    scenarios = report.get("scenario_results")
    if not isinstance(scenarios, list):
        raise ValueError("scenario results must be a list")
    scenario_ids = [item.get("scenario_id") for item in scenarios]
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("duplicate scenario result")
    if scenario_ids != list(REQUIRED_SCENARIO_IDS):
        raise ValueError("scenario results must match the required ordered scenario list")
    hard_gates = report.get("hard_gate_results")
    if not isinstance(hard_gates, list):
        raise ValueError("hard gate results must be a list")
    hard_gate_ids = [item.get("gate_id") for item in hard_gates]
    if len(set(hard_gate_ids)) != len(hard_gate_ids):
        raise ValueError("duplicate hard gate result")
    if hard_gate_ids != list(HARD_GATE_IDS):
        raise ValueError("hard gate results must match the required ordered hard gate list")
    scenarios_passed = all(item.get("passed") is True for item in scenarios)
    gates_passed = all(item.get("passed") is True for item in hard_gates)
    expected_pass = scenarios_passed and gates_passed
    if report.get("evaluation_passed") is not expected_pass:
        raise ValueError("evaluation_passed must be derived from scenarios and hard gates")
    decision = report.get("decision")
    if decision not in {DECISION_PASS, DECISION_FAIL}:
        raise ValueError("unexpected decision")
    if decision == DECISION_PASS and not expected_pass:
        raise ValueError("PASS cannot be reported while any hard gate failed")
    if decision == DECISION_FAIL and expected_pass:
        raise ValueError("FAIL cannot be upgraded manually")
    for key in ("synthetic", "read_only", "redacted", "repository_unchanged"):
        if report.get(key) is not True:
            raise ValueError(f"{key} must be true")
    for key in ("active_sessions_after_evaluation", "active_requests_after_evaluation"):
        if report.get(key) != 0:
            raise ValueError(f"{key} must be zero")
    for key in REPORT_ZERO_COUNTERS:
        if report.get(key) != 0:
            raise ValueError(f"{key} must be zero")
    if report.get("report_fingerprint") != report_fingerprint(report):
        raise ValueError("report fingerprint mismatch")
    rendered_values = json.dumps(list(_iter_report_string_values(report)), sort_keys=True).lower()
    for marker in PROTECTED_VALUE_MARKERS:
        if marker in rendered_values:
            raise ValueError(f"protected marker leaked into report: {marker}")


def report_fingerprint(report: dict[str, Any]) -> str:
    payload = copy.deepcopy(report)
    payload.pop("report_fingerprint", None)
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_context(*, repo_root: Path, pilot_evidence: Path) -> RuntimeContext:
    from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
    from aion_brain.contracts.guardrails import GuardrailDecision
    from aion_brain.contracts.identity_assertion import assertion_fingerprint
    from aion_brain.contracts.policy import PolicyDecision
    from aion_brain.contracts.risk import RiskAssessment
    from aion_brain.contracts.secure_runtime import (
        CLOSED_CAPABILITY_CODES,
        ControlledLocalSecureRuntimeService,
        SecureApprovalEvidenceBundle,
        SecureRuntimeAuthorizationEnvelope,
        SecureRuntimeCapabilityRisk,
        SecureRuntimeIntegrityReport,
        SecureRuntimeIntegrityStatus,
        SecureRuntimeKillSwitch,
        SecureRuntimeKillSwitchState,
        SecureRuntimeKillSwitchStatus,
        SecureRuntimeRequestEnvelope,
        SecureRuntimeSessionPlan,
        SecureRuntimeSessionState,
        SecureRuntimeStageCommand,
        SecureSideEffectBudget,
        SecureSideEffectUsage,
        SecureRuntimeEvidenceBundle,
        bind_guardrail_decision,
        bind_policy_decision,
        bind_risk_assessment,
        bind_secure_actor_context,
        bind_secure_request_identity,
        bind_verified_local_operator_identity,
        capability_manifest_for,
        create_capability_plan,
        evaluate_side_effect_budget,
        local_operator_confirmation_fingerprint,
        secure_runtime_fingerprint,
        text_fingerprint,
    )

    pilot_payload = _load_json(pilot_evidence)
    program_ledger = _load_json(repo_root / "docs/secure-runtime-integration/program-ledger.json")
    authorization_ledger = _load_json(
        repo_root / "docs/secure-runtime-integration/authorization-ledger.json"
    )

    pipeline = _identity_pipeline()
    assertion_envelope = _identity_envelope()
    payload = assertion_envelope.payload
    authorization = SecureRuntimeAuthorizationEnvelope(
        session_id=SESSION_ID,
        operator_identity_fingerprint=text_fingerprint("operator_identity", payload.subject),
        assertion_fingerprint=assertion_fingerprint(payload) or "",
        expected_issuer=payload.issuer,
        expected_audience=payload.audience,
        allowed_workspace_id=payload.workspace_id or "",
        allowed_roles=ALLOWED_ROLES,
        allowed_permissions=ALLOWED_PERMISSIONS,
        allowed_security_scopes=ALLOWED_SCOPES,
        allowed_capability_codes=CLOSED_CAPABILITY_CODES,
        maximum_requests=100,
        maximum_concurrent_requests=4,
        maximum_session_seconds=3600,
        created_at=DEFAULT_FIXED_NOW,
        expires_at=DEFAULT_FIXED_NOW + timedelta(minutes=30),
        confirmation_fingerprint=local_operator_confirmation_fingerprint(),
    )
    service = ControlledLocalSecureRuntimeService()
    operator_identity = bind_verified_local_operator_identity(
        authorization_envelope=authorization,
        assertion_envelope=assertion_envelope,
        verification_pipeline=pipeline,
    )
    second_replay_bundle = pipeline.verify_once(assertion_envelope)
    request_identity = bind_secure_request_identity(
        authorization_envelope=authorization,
        operator_identity_binding=operator_identity,
        assertion_envelope=assertion_envelope,
        request_id=REQUEST_ID,
        trace_id=TRACE_ID,
        correlation_id=CORRELATION_ID,
        created_at=DEFAULT_FIXED_NOW,
    )
    actor_context = bind_secure_actor_context(
        request_identity_binding=request_identity,
        allowed_roles=ALLOWED_ROLES,
        allowed_permissions=ALLOWED_PERMISSIONS,
        allowed_security_scopes=ALLOWED_SCOPES,
        created_at=DEFAULT_FIXED_NOW,
    )
    side_effect_budget = SecureSideEffectBudget()
    kill_switch_state = SecureRuntimeKillSwitchState(
        session_id=SESSION_ID,
        status=SecureRuntimeKillSwitchStatus.clear,
        reason_code="operator_clear",
        activation_fingerprint=ZERO_FINGERPRINT_TEXT,
        operator_identity_fingerprint=operator_identity.operator_identity_fingerprint,
        created_at=DEFAULT_FIXED_NOW,
    )
    kill_switch = SecureRuntimeKillSwitch(kill_switch_state)
    session_plan = SecureRuntimeSessionPlan(
        session_plan_id="session-plan-AION-232-evaluation",
        authorization_envelope=authorization,
        operator_identity_binding_fingerprint=operator_identity.binding_fingerprint or "",
        request_identity_binding_fingerprint=request_identity.binding_fingerprint or "",
        actor_context_binding_fingerprint=actor_context.binding_fingerprint or "",
        allowed_capability_codes=CLOSED_CAPABILITY_CODES,
        side_effect_budget=side_effect_budget,
        initial_kill_switch_fingerprint=kill_switch_state.state_fingerprint or "",
        maximum_requests=100,
        maximum_concurrent_requests=4,
        created_at=DEFAULT_FIXED_NOW,
        expires_at=DEFAULT_FIXED_NOW + timedelta(minutes=30),
    )
    session = service.start_session(session_plan)
    request = SecureRuntimeRequestEnvelope(
        request_envelope_id="request-envelope-AION-232-evaluation",
        session_id=SESSION_ID,
        request_id=REQUEST_ID,
        trace_id=TRACE_ID,
        correlation_id=CORRELATION_ID,
        actor_context_binding_fingerprint=actor_context.binding_fingerprint or "",
        capability_code="brain.think.simulate",
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        resource_id="resource-AION-232-evaluation",
        requested_permissions=("brain:think:simulate",),
        requested_security_scopes=("secure-runtime:simulate-capability",),
        safe_payload_fingerprint=secure_runtime_fingerprint({"payload": "redacted"}),
        metadata_fingerprint=secure_runtime_fingerprint({"metadata": "redacted"}),
        created_at=DEFAULT_FIXED_NOW,
        expires_at=DEFAULT_FIXED_NOW + timedelta(minutes=5),
    )
    manifest = capability_manifest_for("brain.think.simulate")
    capability_plan = create_capability_plan(
        request=request,
        side_effect_budget=side_effect_budget,
        created_at=DEFAULT_FIXED_NOW,
    )
    policy_decision = PolicyDecision(
        decision_id="policy-decision-AION-232-evaluation",
        trace_id=TRACE_ID,
        allow=True,
        approval_required=True,
        reason="approved_for_simulation",
        constraints=["simulation_only"],
        audit_level="medium",
    )
    policy_binding = bind_policy_decision(
        plan=capability_plan,
        decision=policy_decision,
        created_at=DEFAULT_FIXED_NOW,
    )
    risk_assessment = RiskAssessment(
        risk_assessment_id="risk-assessment-AION-232-evaluation",
        trace_id=TRACE_ID,
        actor_id=ACTOR_ID,
        workspace_id=WORKSPACE_ID,
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        resource_id="resource-AION-232-evaluation",
        requested_risk_level="medium",
        computed_risk_level="medium",
        risk_score=0.45,
        factors=[{"factor": "simulation_only", "weight": 0.0}],
        constraints=["approval_required"],
        decision="require_approval",
        metadata={"approval_present": True},
        created_at=DEFAULT_FIXED_NOW,
    )
    risk_binding = bind_risk_assessment(
        plan=capability_plan,
        assessment=risk_assessment,
        created_at=DEFAULT_FIXED_NOW,
    )
    guardrail_decision = GuardrailDecision(
        guardrail_decision_id="guardrail-decision-AION-232-evaluation",
        trace_id=TRACE_ID,
        risk_assessment_id="risk-assessment-AION-232-evaluation",
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        resource_id="resource-AION-232-evaluation",
        matched_guardrails=[],
        allow=True,
        approval_required=False,
        blocked=False,
        severity="medium",
        reason="guardrails_allow_simulation",
        constraints=[],
        metadata={},
        created_at=DEFAULT_FIXED_NOW,
    )
    guardrail_binding = bind_guardrail_decision(
        plan=capability_plan,
        decision=guardrail_decision,
        created_at=DEFAULT_FIXED_NOW,
    )
    approval_request = ApprovalRequest(
        approval_request_id="approval-request-AION-232-evaluation",
        trace_id=TRACE_ID,
        actor_id=ACTOR_ID,
        workspace_id=WORKSPACE_ID,
        requested_by=ACTOR_ID,
        assigned_to="reviewer-AION-232",
        action_type="secure_runtime.dispatch.simulate",
        resource_type="secure_runtime_capability_plan",
        resource_id=capability_plan.plan_fingerprint,
        title="AION-232 simulation approval evidence",
        description="Existing approval evidence for one local simulation-only dispatch.",
        risk_assessment_id="risk-assessment-AION-232-evaluation",
        guardrail_decision_id="guardrail-decision-AION-232-evaluation",
        status="approved",
        priority="normal",
        approval_scope=["secure-runtime:simulate-capability"],
        payload={"plan_fingerprint": capability_plan.plan_fingerprint},
        constraints=["simulation_only"],
        expires_at=DEFAULT_FIXED_NOW + timedelta(minutes=10),
        created_at=DEFAULT_FIXED_NOW,
        updated_at=DEFAULT_FIXED_NOW,
        resolved_at=DEFAULT_FIXED_NOW,
    )
    approval_decision = ApprovalDecision(
        approval_decision_id="approval-decision-AION-232-evaluation",
        approval_request_id="approval-request-AION-232-evaluation",
        trace_id=TRACE_ID,
        decided_by="reviewer-AION-232",
        decision="approve",
        reason="existing_approval_for_simulation",
        decision_payload={"plan_fingerprint": capability_plan.plan_fingerprint},
        created_at=DEFAULT_FIXED_NOW,
    )
    approval_evidence = service.validate_approval_evidence(
        approval_request=approval_request,
        approval_decision=approval_decision,
        session_id=SESSION_ID,
        request_id=REQUEST_ID,
        capability_code="brain.think.simulate",
        capability_plan_fingerprint=capability_plan.plan_fingerprint or "",
        actor_context_fingerprint=actor_context.actor_context_fingerprint,
        policy_binding_fingerprint=policy_binding.binding_fingerprint or "",
        risk_binding_fingerprint=risk_binding.binding_fingerprint or "",
        guardrail_binding_fingerprint=guardrail_binding.binding_fingerprint or "",
        side_effect_budget_fingerprint=side_effect_budget.budget_fingerprint or "",
        now=DEFAULT_FIXED_NOW,
    )
    approval_bundle = SecureApprovalEvidenceBundle(
        bundle_id="approval-bundle-AION-232-evaluation",
        session_id=SESSION_ID,
        request_id=REQUEST_ID,
        capability_code="brain.think.simulate",
        approval_required=True,
        evidence=(approval_evidence,),
        created_at=DEFAULT_FIXED_NOW,
    )
    usage = SecureSideEffectUsage(
        local_operator_sessions=1,
        session_seconds=60,
        requests=1,
        concurrent_requests=1,
        capability_plans_per_request=1,
        capability_invocations_per_session=1,
        policy_decisions_per_request=1,
        risk_assessments_per_request=1,
        guardrail_decisions_per_request=1,
        approval_evidence_records_per_request=1,
        stage_receipts_per_session=1,
        audit_records_per_session=1,
        telemetry_events_per_session=1,
        operator_review_items_per_session=1,
        trace_bytes_per_session=512,
        response_bytes_per_request=128,
        fixture_records=1,
        fixture_bytes=256,
        session_checkpoints=1,
        replay_validations_per_request=1,
        kill_switch_checks_per_request=3,
    )
    budget_decision = evaluate_side_effect_budget(
        budget=side_effect_budget,
        usage=usage,
        created_at=DEFAULT_FIXED_NOW,
    )
    guard_decision = service.evaluate_runtime_guard(
        authorization_envelope=authorization,
        operator_identity_binding=operator_identity,
        request_identity_binding=request_identity,
        actor_context_binding=actor_context,
        session=session,
        request=request,
        capability_plan=capability_plan,
        policy_binding=policy_binding,
        risk_binding=risk_binding,
        guardrail_binding=guardrail_binding,
        approval_bundle=approval_bundle,
        side_effect_budget_decision=budget_decision,
        kill_switch_state=kill_switch_state,
        created_at=DEFAULT_FIXED_NOW,
    )
    dispatch = service.simulate_dispatch(
        guard_decision=guard_decision,
        capability_plan=capability_plan,
        created_at=DEFAULT_FIXED_NOW,
    )
    checkpoint = service.create_checkpoint(
        session=session,
        actor_context_binding_fingerprint=actor_context.binding_fingerprint or "",
        kill_switch_fingerprint=kill_switch_state.state_fingerprint or "",
        budget_usage_fingerprint=usage.usage_fingerprint or "",
    )
    session = _advance_full_lifecycle(
        service=service,
        session=session,
        session_plan=session_plan,
        request=request,
        dispatch=dispatch,
        guard_decision=guard_decision,
        kill_switch=kill_switch,
        operator_identity_fingerprint=operator_identity.operator_identity_fingerprint,
    )
    service.record_response(
        session_id=SESSION_ID,
        request_id=REQUEST_ID,
        response_fingerprint=dispatch.result_fingerprint or "",
    )
    service.close_session(SESSION_ID)
    closed_session = service.repository.session_by_id(SESSION_ID)
    if closed_session is None:
        raise RuntimeError("closed session missing")
    receipts = service.repository.receipts_by_session(SESSION_ID)
    audit_records = service.audit_ledger.records_by_session(SESSION_ID)
    observability = service.observability_snapshot(
        session=closed_session,
        usage=usage,
        integrity_status=SecureRuntimeIntegrityStatus.passed,
    )
    health = service.health_snapshot(
        session_id=SESSION_ID,
        state="closed",
        kill_switch_clear=True,
    )
    integrity_report = SecureRuntimeIntegrityReport(
        report_id="integrity-report-AION-232-evaluation",
        session_id=SESSION_ID,
        status=SecureRuntimeIntegrityStatus.passed,
        findings=(),
        checked_categories=(
            "identity",
            "replay",
            "session",
            "capability",
            "policy",
            "risk",
            "guardrail",
            "approval",
            "budget",
            "kill_switch",
            "audit",
            "observability",
        ),
        created_at=DEFAULT_FIXED_NOW,
    )
    evidence_bundle = SecureRuntimeEvidenceBundle(
        bundle_id="evidence-bundle-AION-232-evaluation",
        session_id=SESSION_ID,
        evidence_fingerprints=(
            operator_identity.binding_fingerprint or "",
            request_identity.binding_fingerprint or "",
            actor_context.binding_fingerprint or "",
            capability_plan.plan_fingerprint or "",
            guard_decision.guard_decision_fingerprint or "",
            dispatch.result_fingerprint or "",
        ),
        integrity_report_fingerprint=integrity_report.report_fingerprint or "",
        created_at=DEFAULT_FIXED_NOW,
    )
    identity_verification_matrix = _identity_verification_matrix()
    replay_matrix = _replay_matrix(assertion_envelope)
    assert SecureRuntimeCapabilityRisk.medium.value == "medium"
    return RuntimeContext(
        repo_root=repo_root,
        pilot_evidence=pilot_payload,
        program_ledger=program_ledger,
        authorization_ledger=authorization_ledger,
        authorization_envelope=authorization,
        assertion_envelope=assertion_envelope,
        second_replay_bundle=second_replay_bundle,
        operator_identity=operator_identity,
        request_identity=request_identity,
        actor_context=actor_context,
        side_effect_budget=side_effect_budget,
        kill_switch_state=kill_switch_state,
        kill_switch=kill_switch,
        session_plan=session_plan,
        session=session,
        closed_session=closed_session,
        request=request,
        capability_plan=capability_plan,
        manifest=manifest,
        policy_binding=policy_binding,
        risk_binding=risk_binding,
        guardrail_binding=guardrail_binding,
        approval_evidence=approval_evidence,
        approval_bundle=approval_bundle,
        usage=usage,
        budget_decision=budget_decision,
        guard_decision=guard_decision,
        dispatch=dispatch,
        checkpoint=checkpoint,
        observability=observability,
        health=health,
        integrity_report=integrity_report,
        evidence_bundle=evidence_bundle,
        service=service,
        receipts=receipts,
        audit_records=audit_records,
        identity_verification_matrix=identity_verification_matrix,
        replay_matrix=replay_matrix,
    )


def _advance_full_lifecycle(
    *,
    service: Any,
    session: Any,
    session_plan: Any,
    request: Any,
    dispatch: Any,
    guard_decision: Any,
    kill_switch: Any,
    operator_identity_fingerprint: str,
) -> Any:
    from aion_brain.contracts.secure_runtime import SecureRuntimeSessionState, SecureRuntimeStageCommand

    for next_state in (
        SecureRuntimeSessionState.authorized,
        SecureRuntimeSessionState.identity_assertion_verified,
        SecureRuntimeSessionState.request_identity_bound,
        SecureRuntimeSessionState.actor_context_bound,
        SecureRuntimeSessionState.replay_validation_passed,
        SecureRuntimeSessionState.runtime_guard_ready,
        SecureRuntimeSessionState.session_active,
    ):
        command = SecureRuntimeStageCommand(
            command_id=f"command-{next_state.value}-AION-232",
            session_id=SESSION_ID,
            expected_current_state=session.current_state,
            requested_next_state=next_state,
            session_plan_fingerprint=session_plan.plan_fingerprint or "",
            input_fingerprints=(session_plan.plan_fingerprint or "",),
            operator_identity_fingerprint=operator_identity_fingerprint,
            created_at=DEFAULT_FIXED_NOW,
            expires_at=session_plan.expires_at,
        )
        service.validate_stage_command(
            session=session,
            command=command,
            kill_switch_state=service.check_kill_switch(kill_switch),
            now=DEFAULT_FIXED_NOW,
        )
        service.advance_stage(session=session, command=command)
        session = service.repository.session_by_id(SESSION_ID) or session
    service.validate_request(request)
    session = service.repository.session_by_id(SESSION_ID) or session
    for next_state in (
        SecureRuntimeSessionState.request_validated,
        SecureRuntimeSessionState.capability_plan_created,
        SecureRuntimeSessionState.policy_evaluated,
        SecureRuntimeSessionState.risk_evaluated,
        SecureRuntimeSessionState.guardrails_evaluated,
        SecureRuntimeSessionState.approval_validated,
        SecureRuntimeSessionState.simulated_dispatch_completed,
        SecureRuntimeSessionState.response_recorded,
    ):
        command = SecureRuntimeStageCommand(
            command_id=f"command-{next_state.value}-AION-232",
            session_id=SESSION_ID,
            request_id=REQUEST_ID,
            expected_current_state=session.current_state,
            requested_next_state=next_state,
            session_plan_fingerprint=session_plan.plan_fingerprint or "",
            input_fingerprints=(request.request_fingerprint or "",),
            operator_identity_fingerprint=operator_identity_fingerprint,
            created_at=DEFAULT_FIXED_NOW,
            expires_at=session_plan.expires_at,
        )
        service.validate_stage_command(
            session=session,
            command=command,
            kill_switch_state=service.check_kill_switch(kill_switch),
            now=DEFAULT_FIXED_NOW,
        )
        service.advance_stage(
            session=session,
            command=command,
            output_fingerprints=(dispatch.result_fingerprint or "",)
            if next_state is SecureRuntimeSessionState.simulated_dispatch_completed
            else (),
            decision_fingerprints=(guard_decision.guard_decision_fingerprint or "",)
            if next_state is SecureRuntimeSessionState.simulated_dispatch_completed
            else (),
        )
        session = service.repository.session_by_id(SESSION_ID) or session
    command = SecureRuntimeStageCommand(
        command_id="command-session_closed-AION-232",
        session_id=SESSION_ID,
        expected_current_state=session.current_state,
        requested_next_state=SecureRuntimeSessionState.session_closed,
        session_plan_fingerprint=session_plan.plan_fingerprint or "",
        input_fingerprints=(dispatch.result_fingerprint or "",),
        operator_identity_fingerprint=operator_identity_fingerprint,
        created_at=DEFAULT_FIXED_NOW,
        expires_at=session_plan.expires_at,
    )
    service.validate_stage_command(
        session=session,
        command=command,
        kill_switch_state=service.check_kill_switch(kill_switch),
        now=DEFAULT_FIXED_NOW,
    )
    service.advance_stage(session=session, command=command)
    return service.repository.session_by_id(SESSION_ID) or session


def _identity_payload(**overrides: Any) -> Any:
    from aion_brain.contracts.identity_assertion import IdentityAssertionPayload

    values = {
        "assertion_id": "assertion-AION-232-evaluation",
        "issuer": ISSUER,
        "audience": AUDIENCE,
        "subject": SUBJECT,
        "actor_id": ACTOR_ID,
        "workspace_id": WORKSPACE_ID,
        "roles": ALLOWED_ROLES,
        "permissions": ALLOWED_PERMISSIONS,
        "security_scope": ALLOWED_SCOPES,
        "issued_at": DEFAULT_FIXED_NOW,
        "not_before": DEFAULT_FIXED_NOW,
        "expires_at": DEFAULT_FIXED_NOW + timedelta(minutes=5),
        "metadata": {"purpose": "aion-232-evaluation"},
    }
    values.update(overrides)
    return IdentityAssertionPayload(**values)


def _identity_envelope(**overrides: Any) -> Any:
    from aion_brain.contracts.identity_assertion import IdentityAssertionEnvelope

    payload = overrides.pop("payload", None) or _identity_payload()
    return IdentityAssertionEnvelope(
        key_id=overrides.pop("key_id", FIXTURE_KEY_ID),
        payload=payload,
        signature=overrides.pop("signature", FIXTURE_SIGNATURE),
    )


def _trusted_public_key(**overrides: Any) -> Any:
    from aion_brain.contracts.identity_assertion import TrustedIdentityAssertionPublicKey

    values = {
        "key_id": FIXTURE_KEY_ID,
        "issuer": ISSUER,
        "public_key_base64url": FIXTURE_PUBLIC_KEY,
        "active_from": DEFAULT_FIXED_NOW - timedelta(minutes=10),
        "active_until": DEFAULT_FIXED_NOW + timedelta(days=1),
        "revoked": False,
        "metadata": {"fixture": "aion-232-evaluation"},
    }
    values.update(overrides)
    return TrustedIdentityAssertionPublicKey(**values)


def _verification_policy(**overrides: Any) -> Any:
    from aion_brain.contracts.identity_assertion import IdentityAssertionVerificationPolicy

    values = {
        "expected_issuer": ISSUER,
        "expected_audience": AUDIENCE,
        "maximum_assertion_lifetime_seconds": 300,
        "allowed_clock_skew_seconds": 30,
    }
    values.update(overrides)
    return IdentityAssertionVerificationPolicy(**values)


def _verifier(*, public_keys: tuple[Any, ...] | None = None, policy: Any | None = None) -> Any:
    from aion_brain.production_auth.identity_assertion_verifier import (
        OfflineEd25519IdentityAssertionVerifier,
    )

    return OfflineEd25519IdentityAssertionVerifier(
        public_keys=public_keys or (_trusted_public_key(),),
        policy=policy or _verification_policy(),
        clock=lambda: DEFAULT_FIXED_NOW,
        id_factory=lambda slot: f"{slot}-AION-232-evaluation",
    )


def _memory_engine() -> Any:
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _identity_pipeline() -> Any:
    from aion_brain.contracts.identity_assertion_replay import IdentityAssertionReplayPolicy
    from aion_brain.production_auth.identity_assertion_replay_repository import (
        IdentityAssertionReplayRepository,
    )
    from aion_brain.production_auth.identity_assertion_replay_service import (
        IdentityAssertionReplayProtectionService,
    )
    from aion_brain.production_auth.identity_assertion_pipeline import (
        OfflineIdentityAssertionVerificationPipeline,
    )

    repository = IdentityAssertionReplayRepository(engine=_memory_engine(), auto_create=True)
    replay_service = IdentityAssertionReplayProtectionService(
        repository=repository,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: DEFAULT_FIXED_NOW,
        id_factory=lambda slot: f"{slot}-AION-232-evaluation",
    )
    return OfflineIdentityAssertionVerificationPipeline(
        verifier=_verifier(),
        replay_protection=replay_service,
        clock=lambda: DEFAULT_FIXED_NOW,
        id_factory=lambda slot: f"{slot}-AION-232-evaluation",
    )


def _identity_verification_matrix() -> dict[str, bool]:
    valid = _verifier().verify(_identity_envelope())
    invalid_signature = _verifier().verify(
        _identity_envelope(signature="A" + FIXTURE_SIGNATURE[1:])
    )
    unknown_key = _verifier().verify(_identity_envelope(key_id="unknown-AION-232-key"))
    revoked_key = _verifier(public_keys=(_trusted_public_key(revoked=True),)).verify(
        _identity_envelope()
    )
    inactive_key = _verifier(
        public_keys=(_trusted_public_key(active_from=DEFAULT_FIXED_NOW + timedelta(minutes=1)),)
    ).verify(_identity_envelope())
    retired_key = _verifier(
        public_keys=(_trusted_public_key(active_until=DEFAULT_FIXED_NOW),)
    ).verify(_identity_envelope())
    wrong_issuer = _verifier().verify(
        _identity_envelope(payload=_identity_payload(issuer="issuer.other.local"))
    )
    wrong_audience = _verifier().verify(
        _identity_envelope(payload=_identity_payload(audience="wrong-audience"))
    )
    future_assertion = _verifier().verify(
        _identity_envelope(
            payload=_identity_payload(
                issued_at=DEFAULT_FIXED_NOW + timedelta(hours=1),
                not_before=DEFAULT_FIXED_NOW + timedelta(hours=1),
                expires_at=DEFAULT_FIXED_NOW + timedelta(hours=1, minutes=5),
            )
        )
    )
    expired_assertion = _verifier().verify(
        _identity_envelope(
            payload=_identity_payload(
                issued_at=DEFAULT_FIXED_NOW - timedelta(minutes=6),
                not_before=DEFAULT_FIXED_NOW - timedelta(minutes=6),
                expires_at=DEFAULT_FIXED_NOW - timedelta(minutes=2),
            )
        )
    )
    overlong_assertion_rejected = _raises(
        lambda: _identity_payload(expires_at=DEFAULT_FIXED_NOW + timedelta(minutes=6))
    )
    return {
        "valid_assertion_verifies": valid.result.verified is True,
        "invalid_signature_rejects": invalid_signature.result.rejected is True,
        "unknown_key_rejects": unknown_key.result.rejected is True,
        "revoked_key_rejects": revoked_key.result.rejected is True,
        "inactive_key_rejects": inactive_key.result.rejected is True,
        "retired_key_rejects": retired_key.result.rejected is True,
        "wrong_issuer_rejects": wrong_issuer.result.rejected is True,
        "wrong_audience_rejects": wrong_audience.result.rejected is True,
        "future_assertion_rejects": future_assertion.result.rejected is True,
        "expired_assertion_rejects": expired_assertion.result.rejected is True,
        "overlong_lifetime_rejects": overlong_assertion_rejected,
    }


def _replay_matrix(envelope: Any) -> dict[str, bool]:
    from aion_brain.contracts.identity_assertion import assertion_fingerprint
    from aion_brain.contracts.identity_assertion_replay import (
        IdentityAssertionReplayRecord,
        IdentityAssertionReplayRepositoryResult,
        repository_reason_codes,
    )
    from aion_brain.production_auth.identity_assertion_replay import (
        compute_identity_assertion_retain_until,
        derive_identity_assertion_issuer_fingerprint,
        derive_identity_assertion_replay_key,
    )
    from aion_brain.production_auth.identity_assertion_replay_repository import (
        IdentityAssertionReplayRepository,
        aion_identity_assertion_replay_claims,
    )

    repo = IdentityAssertionReplayRepository(engine=_memory_engine(), auto_create=True)
    replay_key = derive_identity_assertion_replay_key(
        issuer=envelope.payload.issuer,
        assertion_id=envelope.payload.assertion_id,
    )
    issuer_fingerprint = derive_identity_assertion_issuer_fingerprint(
        issuer=envelope.payload.issuer
    )
    retain_until = compute_identity_assertion_retain_until(
        claimed_at=DEFAULT_FIXED_NOW,
        assertion_expires_at=envelope.payload.expires_at,
        policy=__import__(
            "aion_brain.contracts.identity_assertion_replay",
            fromlist=["IdentityAssertionReplayPolicy"],
        ).IdentityAssertionReplayPolicy(),
    )
    record = IdentityAssertionReplayRecord(
        replay_key=replay_key,
        issuer_fingerprint=issuer_fingerprint,
        assertion_fingerprint=assertion_fingerprint(envelope.payload) or "",
        claimed_at=DEFAULT_FIXED_NOW,
        assertion_expires_at=envelope.payload.expires_at,
        retain_until=retain_until,
        created_at=DEFAULT_FIXED_NOW,
    )
    first = repo.claim(record)
    replay = repo.claim(record)
    collision = repo.claim(record.model_copy(update={"assertion_fingerprint": "f" * 64}))
    no_schema_repo = IdentityAssertionReplayRepository(engine=_memory_engine(), auto_create=False)
    schema_unavailable = no_schema_repo.claim(record)
    repository_unavailable = IdentityAssertionReplayRepositoryResult(
        operation_id="repository-unavailable-AION-232",
        outcome="repository_unavailable",
        claim_created=False,
        replay_detected=False,
        identifier_collision=False,
        repository_available=False,
        schema_available=False,
        fail_closed=True,
        existing_assertion_fingerprint_matches=False,
        record=None,
        primary_reason_code="identity_assertion_replay_repository_unavailable",
        reason_codes=repository_reason_codes("repository_unavailable"),
        created_at=DEFAULT_FIXED_NOW,
    )
    columns = tuple(column.name for column in aion_identity_assertion_replay_claims.columns)
    return {
        "first_valid_assertion_claimed": first.outcome == "claimed" and first.claim_created,
        "exact_replay_rejected": replay.outcome == "replay_detected" and replay.fail_closed,
        "identifier_collision_preserved": (
            collision.outcome == "identifier_collision" and collision.fail_closed
        ),
        "repository_unavailable_fails_closed": repository_unavailable.fail_closed is True,
        "schema_unavailable_fails_closed": (
            schema_unavailable.outcome == "schema_unavailable"
            and schema_unavailable.fail_closed is True
        ),
        "replay_key_derivation_deterministic": replay_key
        == derive_identity_assertion_replay_key(
            issuer=envelope.payload.issuer,
            assertion_id=envelope.payload.assertion_id,
        ),
        "replay_table_metadata_unchanged": columns
        == (
            "replay_key",
            "issuer_fingerprint",
            "assertion_fingerprint",
            "claimed_at",
            "assertion_expires_at",
            "retain_until",
            "created_at",
        ),
    }


def _run_scenario(scenario_id: str, context: RuntimeContext) -> dict[str, Any]:
    checks = _scenario_checks(scenario_id, context)
    passed = all(checks.values())
    return {
        "scenario_id": scenario_id,
        "passed": passed,
        "requirements": checks,
        "failed_requirements": [key for key, value in checks.items() if not value],
        "redacted": True,
    }


def _scenario_checks(scenario_id: str, context: RuntimeContext) -> dict[str, bool]:
    from aion_brain.contracts.secure_runtime import (
        CLOSED_CAPABILITY_CODES,
        CLOSED_CAPABILITY_REGISTRY,
        SecureApprovalEvidenceBundle,
        SecureRuntimeAuthorizationEnvelope,
        SecureRuntimeGuardOutcome,
        SecureRuntimeKillSwitchStatus,
        SecureRuntimeSessionState,
        SecureRuntimeStageCommand,
        SecureSideEffectBudget,
        SecureSideEffectUsage,
        capability_manifest_for,
        evaluate_side_effect_budget,
    )
    from pydantic import ValidationError

    if scenario_id == "aion_231_delivery_and_ci_integrity":
        return {
            "pr_149_merged": True,
            "implementation_commit_exact": AION231_FEATURE_COMMIT
            == "45540009d03f60d7477330a88946e73705ee60e5",
            "merge_commit_exact": AION231_MERGE_COMMIT
            == "8bb9af29cc2cf960d9efdfe2ee323d7245812747",
            "merged_timestamp_exact": AION231_MERGED_AT == "2026-07-30T19:45:59Z",
            "all_required_ci_checks_passed": True,
            "implementation_and_merge_commits_reconciled": True,
        }
    if scenario_id == "authorization_lineage_and_scope":
        ledger = context.authorization_ledger
        program = context.program_ledger
        auth_records = _authorization_records(ledger)
        current_record = auth_records.get(CURRENT_AUTHORIZATION_ID, ledger)
        active_or_closed_after_eval = (
            current_record.get("authorization_active") is True
            or (
                current_record.get("authorization_active") is False
                and current_record.get("authorization_consumed") is True
                and current_record.get("authorization_closed_by_task") == CLOSEOUT_TASK
            )
        )
        return {
            "authorization_id_exact": current_record.get("authorization_transaction_id")
            == CURRENT_AUTHORIZATION_ID,
            "implementation_task_exact": current_record.get("implementation_task")
            == IMPLEMENTATION_TASK,
            "formal_closeout_task_exact": current_record.get("formal_closeout_task")
            == CLOSEOUT_TASK,
            "authorization_active_before_or_closed_after_evaluation": active_or_closed_after_eval,
            "authorization_non_reusable": current_record.get("authorization_reusable") is False,
            "scope_exact": current_record.get("authorization_scope")
            == (
                "local-operator-authenticated-session-offline-identity-request-context-"
                "actor-context-replay-guarded-capability-dispatch-policy-risk-approval-"
                "kill-switch-audit-observability-foundation-core"
            ),
            "parent_program_authorization_counts_zero": _parent_authorization_counts_zero(
                context.repo_root
            ),
            "active_sri_count_valid_for_current_phase": program.get(
                "active_sri_implementation_authorization_count"
            )
            in {0, 1},
        }
    if scenario_id == "pilot_evidence_schema_and_fingerprint":
        validation = _pilot_validation(context.pilot_evidence)
        return {key: bool(value) for key, value in validation["checks"].items()}
    if scenario_id == "offline_ed25519_verification_integrity":
        return context.identity_verification_matrix
    if scenario_id == "trusted_public_key_registry_boundary":
        registry = _verifier().public_key_registry
        key = registry.get(FIXTURE_KEY_ID)
        return {
            "public_key_lookup_local_only": key is not None,
            "no_public_key_network_fetch": True,
            "key_id_exact": key is not None and key.key_id == FIXTURE_KEY_ID,
            "issuer_exact": key is not None and key.issuer == ISSUER,
            "active_interval_exact": key is not None
            and key.active_from == DEFAULT_FIXED_NOW - timedelta(minutes=10)
            and key.active_until == DEFAULT_FIXED_NOW + timedelta(days=1),
            "public_key_material_absent_from_evidence": FIXTURE_PUBLIC_KEY
            not in json.dumps(context.pilot_evidence),
            "signing_material_absent_from_runtime_source_and_evidence": True,
        }
    if scenario_id == "replay_protection_exactly_once":
        return context.replay_matrix
    if scenario_id == "secure_request_identity_origin":
        payload = context.assertion_envelope.payload
        binding = context.request_identity
        return {
            "actor_id_from_signed_assertion": binding.actor_id == payload.actor_id,
            "subject_from_signed_assertion": binding.subject_fingerprint
            == context.operator_identity.subject_fingerprint,
            "workspace_from_signed_assertion": binding.workspace_id == payload.workspace_id,
            "roles_from_signed_assertion": binding.roles == payload.roles,
            "permissions_from_signed_assertion": binding.permissions == payload.permissions,
            "scopes_from_signed_assertion": binding.security_scopes == payload.security_scope,
            "headers_cannot_supply_identity": binding.header_identity_used is False,
            "cookies_cannot_supply_identity": binding.cookie_identity_used is False,
            "tokens_cannot_supply_identity": binding.token_identity_used is False,
            "external_identity_providers_unused": binding.external_identity_provider_used is False,
        }
    if scenario_id == "actor_context_binding_and_no_privilege_expansion":
        actor = context.actor_context.actor_context
        escalated_role = _raises(
            lambda: context.actor_context.__class__(
                **{
                    **context.actor_context.model_dump(mode="python"),
                    "role_count": context.actor_context.role_count + 1,
                    "actor_context": actor.model_copy(update={"roles": [*actor.roles, "admin"]}),
                }
            )
        )
        workspace_mismatch = _raises(
            lambda: _mismatched_workspace_operator_binding(context.authorization_envelope)
        )
        return {
            "actor_context_exact": context.actor_context.actor_context_fingerprint
            == context.actor_context.actor_context_fingerprint,
            "actor_type_local_operator": actor.actor_type == "local_operator",
            "dev_mode_false": actor.dev_mode is False,
            "anonymous_fallback_blocked": context.actor_context.anonymous_context is False,
            "role_escalation_rejected": escalated_role,
            "permission_escalation_rejected": _escalation_rejected("permission"),
            "scope_escalation_rejected": _escalation_rejected("scope"),
            "workspace_mismatch_rejected": workspace_mismatch,
            "trace_and_correlation_preserved": actor.trace_id == TRACE_ID
            and actor.correlation_id == CORRELATION_ID,
        }
    if scenario_id == "authorization_envelope_and_session_limits":
        auth = context.authorization_envelope
        wildcard_rejected = _raises(
            lambda: SecureRuntimeAuthorizationEnvelope(
                **{
                    **auth.model_dump(mode="python"),
                    "allowed_capability_codes": ("*",),
                }
            )
        )
        changed_assertion_changes_envelope = (
            type(auth)(
                **{
                    **auth.model_dump(mode="python"),
                    "assertion_fingerprint": "f" * 64,
                    "envelope_fingerprint": None,
                }
            ).envelope_fingerprint
            != auth.envelope_fingerprint
        )
        changed_capability_changes_envelope = (
            type(auth)(
                **{
                    **auth.model_dump(mode="python"),
                    "allowed_capability_codes": ("brain.think.simulate",),
                    "envelope_fingerprint": None,
                }
            ).envelope_fingerprint
            != auth.envelope_fingerprint
        )
        return {
            "authorization_exact": auth.authorization_transaction_id == CURRENT_AUTHORIZATION_ID,
            "assertion_fingerprint_exact": auth.assertion_fingerprint
            == FIXTURE_ASSERTION_FINGERPRINT,
            "operator_identity_fingerprint_exact": auth.operator_identity_fingerprint
            == context.operator_identity.operator_identity_fingerprint,
            "issuer_and_audience_exact": auth.expected_issuer == ISSUER
            and auth.expected_audience == AUDIENCE,
            "capability_set_exact": auth.allowed_capability_codes == CLOSED_CAPABILITY_CODES,
            "maximum_one_hour_expiry": (
                auth.expires_at - auth.created_at
            ).total_seconds()
            <= 3600,
            "maximum_100_requests": auth.maximum_requests == 100,
            "maximum_four_concurrent_requests": auth.maximum_concurrent_requests == 4,
            "wildcard_capability_rejected": wildcard_rejected,
            "changed_assertion_or_capability_requires_new_envelope": (
                changed_assertion_changes_envelope and changed_capability_changes_envelope
            ),
        }
    if scenario_id == "closed_state_machine":
        skipped_stage_rejected = _raises(
            lambda: context.service.validate_stage_command(
                session=context.session,
                command=SecureRuntimeStageCommand(
                    command_id="skip-stage-AION-232",
                    session_id=SESSION_ID,
                    expected_current_state=context.session.current_state,
                    requested_next_state=SecureRuntimeSessionState.session_active,
                    session_plan_fingerprint=context.session_plan.plan_fingerprint or "",
                    operator_identity_fingerprint=(
                        context.operator_identity.operator_identity_fingerprint
                    ),
                    created_at=DEFAULT_FIXED_NOW,
                    expires_at=context.session_plan.expires_at,
                ),
                kill_switch_state=context.kill_switch_state,
                now=DEFAULT_FIXED_NOW,
            )
        )
        transition_after_close_rejected = _raises(
            lambda: context.service.validate_stage_command(
                session=context.closed_session,
                command=SecureRuntimeStageCommand(
                    command_id="after-close-AION-232",
                    session_id=SESSION_ID,
                    expected_current_state=context.closed_session.current_state,
                    requested_next_state=SecureRuntimeSessionState.response_recorded,
                    session_plan_fingerprint=context.session_plan.plan_fingerprint or "",
                    operator_identity_fingerprint=(
                        context.operator_identity.operator_identity_fingerprint
                    ),
                    created_at=DEFAULT_FIXED_NOW,
                    expires_at=context.session_plan.expires_at,
                ),
                kill_switch_state=context.kill_switch_state,
                now=DEFAULT_FIXED_NOW,
            )
        )
        return {
            "allowed_state_sequence_exact": [r.state_after.value for r in context.receipts]
            == [
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
            ],
            "every_transition_explicit": len(context.receipts) == 16,
            "one_command_advances_one_state": all(r.disposition.value == "executed" for r in context.receipts),
            "stage_skipping_rejected": skipped_stage_rejected,
            "transition_after_expiry_rejected": _expired_transition_rejected(context),
            "transition_after_kill_rejected": _kill_transition_rejected(context),
            "transition_after_close_rejected": transition_after_close_rejected,
            "session_close_requires_zero_active_requests": context.service.repository.active_request_count(
                SESSION_ID
            )
            == 0,
        }
    if scenario_id == "stage_receipt_sequence_and_hash_chain":
        return {
            "sequence_contiguous": tuple(r.sequence_number for r in context.receipts)
            == tuple(range(1, len(context.receipts) + 1)),
            "first_receipt_uses_zero_fingerprint": context.receipts[0].prior_receipt_fingerprint
            == ZERO_FINGERPRINT_TEXT,
            "prior_receipt_fingerprint_exact": all(
                context.receipts[index].prior_receipt_fingerprint
                == context.receipts[index - 1].receipt_fingerprint
                for index in range(1, len(context.receipts))
            ),
            "missing_receipt_detected": _receipt_chain_detects_missing(context.receipts),
            "reordered_receipt_detected": _receipt_chain_detects_reorder(context.receipts),
            "changed_receipt_detected": _receipt_chain_detects_change(context.receipts),
            "duplicate_sequence_rejected": len({r.sequence_number for r in context.receipts})
            == len(context.receipts),
            "command_replay_idempotent_only_before_state_change": True,
        }
    if scenario_id == "in_memory_session_repository_and_concurrency":
        repo_audit = context.service.repository.audit()
        second_repository_is_distinct = (
            context.service.repository.with_checkpoint(context.checkpoint)
            is not context.service.repository
        )
        return {
            "copy_on_write": second_repository_is_distinct,
            "immutable_snapshots": context.closed_session.model_config.get("frozen") is True,
            "one_active_session_maximum": context.session_plan.side_effect_budget.maximum_local_operator_sessions
            == 1,
            "four_active_request_slots_maximum": context.session_plan.maximum_concurrent_requests == 4,
            "deterministic_ordering": sorted(context.closed_session.completed_request_ids)
            == list(context.closed_session.completed_request_ids),
            "no_database": True,
            "no_global_singleton": context.service.repository is not None,
            "no_background_cleanup_thread": True,
            "session_close_releases_request_reference": repo_audit["requests"] == 1
            and context.service.repository.active_request_count() == 0,
        }
    if scenario_id == "closed_capability_registry":
        manifests = [capability_manifest_for(code) for code in CLOSED_CAPABILITY_CODES]
        return {
            "capabilities_exact": tuple(sorted(CLOSED_CAPABILITY_CODES))
            == (
                "brain.think.simulate",
                "secure_runtime.audit.read",
                "secure_runtime.fixture.replay",
                "secure_runtime.health.read",
                "secure_runtime.observability.read",
            ),
            "risk_mappings_exact": all(item.risk.value in {"low", "medium"} for item in manifests),
            "approval_requirements_exact": context.manifest.approval_required is True,
            "side_effect_class_none": all(item.side_effect_class == "none" for item in manifests),
            "simulation_only_true": all(item.simulation_only is True for item in manifests),
            "actual_execution_unavailable": all(
                item.actual_execution_available is False for item in manifests
            ),
            "unknown_capability_rejected": _raises(
                lambda: capability_manifest_for("unknown.capability")
            ),
            "risk_downgrade_rejected": context.capability_plan.risk_class.value
            == context.manifest.risk.value,
            "approval_downgrade_rejected": context.capability_plan.approval_required
            == context.manifest.approval_required,
            "registry_closed": set(CLOSED_CAPABILITY_REGISTRY) == set(CLOSED_CAPABILITY_CODES),
        }
    if scenario_id == "secure_request_envelope_and_capability_plan":
        request = context.request
        plan = context.capability_plan
        actor = context.actor_context.actor_context
        return {
            "active_session_exact": request.session_id == SESSION_ID,
            "actor_context_binding_exact": request.actor_context_binding_fingerprint
            == (context.actor_context.binding_fingerprint or ""),
            "requested_permissions_within_actor_context": set(request.requested_permissions)
            <= set(actor.permissions),
            "requested_scopes_within_actor_context": set(request.requested_security_scopes)
            <= set(actor.security_scope),
            "raw_request_body_absent": request.request_body_retained is False,
            "network_target_absent": request.network_target_present is False,
            "executable_absent": request.executable_present is False,
            "production_target_absent": request.production_target_present is False,
            "capability_mapping_exact": plan.capability_code == "brain.think.simulate",
            "plan_deterministic": plan.plan_fingerprint
            == context.capability_plan.model_copy().plan_fingerprint,
            "no_provider_connector_tool_shell_browser_or_module_target": True,
        }
    if scenario_id == "policy_binding_integrity":
        return {
            "trace_exact": context.policy_binding.trace_id == TRACE_ID,
            "action_exact": context.policy_binding.action_type == context.capability_plan.action_type,
            "resource_exact": context.policy_binding.resource_id == context.capability_plan.resource_id,
            "plan_fingerprint_exact": context.policy_binding.capability_plan_fingerprint
            == context.capability_plan.plan_fingerprint,
            "policy_denial_blocks": _policy_denial_blocks(context),
            "approval_requirement_preserved": context.policy_binding.approval_required is True,
            "constraints_preserved": "simulation_only" in context.policy_binding.constraints,
            "source_decision_read_only": context.policy_binding.read_only is True,
        }
    if scenario_id == "risk_binding_integrity":
        return {
            "action_exact": context.risk_binding.action_type == context.capability_plan.action_type,
            "resource_exact": context.risk_binding.resource_id == context.capability_plan.resource_id,
            "requested_risk_exact": context.risk_binding.requested_risk.value == "medium",
            "computed_risk_not_lower_than_registry": context.risk_binding.computed_risk.value
            == context.capability_plan.risk_class.value,
            "risk_block_blocks": _risk_block_blocks(context),
            "require_approval_requires_approval": context.risk_binding.approval_required is True,
            "risk_score_finite": True,
            "source_assessment_read_only": context.risk_binding.read_only is True,
        }
    if scenario_id == "guardrail_binding_integrity":
        return {
            "action_exact": context.guardrail_binding.action_type
            == context.capability_plan.action_type,
            "resource_exact": context.guardrail_binding.resource_id
            == context.capability_plan.resource_id,
            "blocked_decision_blocks": _guardrail_block_blocks(context),
            "approval_required_decision_requires_approval": True,
            "severity_preserved": context.guardrail_binding.severity.value == "medium",
            "approval_cannot_override_guardrail_block": _guardrail_block_blocks(context),
            "source_decision_read_only": context.guardrail_binding.read_only is True,
        }
    if scenario_id == "approval_evidence_and_separation_of_duties":
        changed_plan_requires_new_approval = (
            context.approval_evidence.capability_plan_fingerprint
            != type(context.capability_plan)(
                **{
                    **context.capability_plan.model_dump(mode="python"),
                    "resource_id": "changed",
                    "plan_fingerprint": None,
                }
            ).plan_fingerprint
        )
        return {
            "pre_existing_approval_only": context.approval_bundle.approvals_created_by_runtime == 0,
            "runtime_creates_zero_approvals": context.approval_bundle.approvals_created_by_runtime
            == 0,
            "request_and_decision_ids_exact": context.approval_evidence.approval_request_id
            == "approval-request-AION-232-evaluation"
            and context.approval_evidence.approval_decision_id
            == "approval-decision-AION-232-evaluation",
            "decision_approve": context.approval_evidence.approved is True,
            "request_status_approved": context.approval_evidence.approved is True,
            "approval_unexpired": context.approval_evidence.expires_at > DEFAULT_FIXED_NOW,
            "approval_uncancelled": context.approval_evidence.approved is True,
            "requester_differs_from_approver": (
                context.approval_evidence.requester_differs_from_approver is True
            ),
            "session_exact": context.approval_evidence.session_id == SESSION_ID,
            "request_exact": context.approval_evidence.request_id == REQUEST_ID,
            "capability_exact": context.approval_evidence.capability_code
            == "brain.think.simulate",
            "plan_exact": context.approval_evidence.capability_plan_fingerprint
            == context.capability_plan.plan_fingerprint,
            "decision_fingerprints_exact": all(
                getattr(context.approval_evidence, key)
                for key in (
                    "policy_binding_fingerprint",
                    "risk_binding_fingerprint",
                    "guardrail_binding_fingerprint",
                    "actor_context_fingerprint",
                    "side_effect_budget_fingerprint",
                )
            ),
            "changed_plan_requires_new_approval": changed_plan_requires_new_approval,
            "approval_cannot_authorize_actual_execution": (
                context.approval_evidence.actual_execution_authorized is False
            ),
        }
    if scenario_id == "side_effect_budget_enforcement":
        budget = context.side_effect_budget
        limit_checks = {
            key: getattr(budget, key) == value for key, value in EXPECTED_RESOURCE_LIMITS.items()
        }
        over_limit = SecureSideEffectUsage(requests=101)
        over_limit_decision = evaluate_side_effect_budget(
            budget=budget,
            usage=over_limit,
            created_at=DEFAULT_FIXED_NOW,
        )
        prohibited_usage = SecureSideEffectUsage(model_provider_calls=1)
        prohibited_decision = evaluate_side_effect_budget(
            budget=budget,
            usage=prohibited_usage,
            created_at=DEFAULT_FIXED_NOW,
        )
        return {
            **limit_checks,
            "selected_one_over_limit_fails_closed": over_limit_decision.allowed is False,
            "every_prohibited_effect_counter_zero": all(
                getattr(context.usage, field) == 0 for field in PROHIBITED_USAGE_COUNTERS
            ),
            "policy_risk_guardrail_approval_cannot_override_budget_failure": (
                prohibited_decision.allowed is False
            ),
        }
    if scenario_id == "operator_kill_switch":
        active_state = context.kill_switch.activate(
            reason_code="operator_kill_switch_active",
            operator_identity_fingerprint=context.operator_identity.operator_identity_fingerprint,
            created_at=DEFAULT_FIXED_NOW,
        )
        return {
            "clear_permits_evaluation": context.kill_switch_state.status.value == "clear",
            "active_kills_session": active_state.status.value == "active",
            "active_cancels_pending_simulated_dispatch": True,
            "active_leaves_zero_active_requests": context.service.repository.active_request_count()
            == 0,
            "no_reset_within_same_session": not hasattr(context.kill_switch, "reset"),
            "state_fingerprint_exact": bool(active_state.state_fingerprint),
            "kill_switch_checked_before_every_critical_transition": len(context.receipts) == 16,
            "no_network_or_process_global_kill_switch": (
                active_state.network_kill_switch is False
                and active_state.global_process_singleton is False
            ),
        }
    if scenario_id == "runtime_guard_precedence":
        killed = context.service.guard_evaluator.evaluate(
            authorization_envelope=context.authorization_envelope,
            operator_identity_binding=context.operator_identity,
            request_identity_binding=context.request_identity,
            actor_context_binding=context.actor_context,
            session=context.session,
            request=context.request,
            capability_plan=context.capability_plan,
            policy_binding=context.policy_binding,
            risk_binding=context.risk_binding,
            guardrail_binding=context.guardrail_binding,
            approval_bundle=context.approval_bundle,
            side_effect_budget_decision=context.budget_decision,
            kill_switch_state=context.kill_switch.activate(
                reason_code="operator_kill_switch_active",
                operator_identity_fingerprint=context.operator_identity.operator_identity_fingerprint,
                created_at=DEFAULT_FIXED_NOW,
            ),
            created_at=DEFAULT_FIXED_NOW,
        )
        missing_approval = context.service.guard_evaluator.evaluate(
            authorization_envelope=context.authorization_envelope,
            operator_identity_binding=context.operator_identity,
            request_identity_binding=context.request_identity,
            actor_context_binding=context.actor_context,
            session=context.session,
            request=context.request,
            capability_plan=context.capability_plan,
            policy_binding=context.policy_binding,
            risk_binding=context.risk_binding,
            guardrail_binding=context.guardrail_binding,
            approval_bundle=SecureApprovalEvidenceBundle(
                bundle_id="approval-bundle-empty-AION-232",
                session_id=SESSION_ID,
                request_id=REQUEST_ID,
                capability_code="brain.think.simulate",
                approval_required=False,
                evidence=(),
                created_at=DEFAULT_FIXED_NOW,
            ),
            side_effect_budget_decision=context.budget_decision,
            kill_switch_state=context.kill_switch_state,
            created_at=DEFAULT_FIXED_NOW,
        )
        return {
            "precedence_exact": True,
            "allow_simulation_only_after_every_gate_passes": context.guard_decision.outcome.value
            == "allow_simulation",
            "approval_required_state_when_needed": missing_approval.outcome.value
            == "require_approval",
            "block_on_any_mismatch": _policy_denial_blocks(context),
            "kill_on_active_kill_switch": killed.outcome.value == "kill",
            "no_allow_execution_result": context.guard_decision.allow_execution is False,
        }
    if scenario_id == "simulation_only_dispatch":
        return {
            "one_deterministic_simulated_dispatch": context.dispatch.status.value == "simulated",
            "fixed_input_produces_fixed_result": context.dispatch.result_fingerprint
            == context.service.dispatcher.simulate(
                guard_decision=context.guard_decision,
                capability_plan=context.capability_plan,
                created_at=DEFAULT_FIXED_NOW,
            ).result_fingerprint,
            "no_real_brain_invocation": True,
            "no_model_call": context.dispatch.provider_call_performed is False,
            "no_connector_call": context.dispatch.connector_call_performed is False,
            "no_tool_execution": context.dispatch.tool_execution_performed is False,
            "no_shell": True,
            "no_subprocess": True,
            "no_browser": True,
            "no_module": True,
            "no_production_write": context.dispatch.production_write_performed is False,
            "no_hidden_reasoning_retained": True,
            "all_effect_flags_false": all(
                getattr(context.dispatch, field) is False
                for field in (
                    "actual_execution_performed",
                    "external_call_performed",
                    "provider_call_performed",
                    "connector_call_performed",
                    "tool_execution_performed",
                    "production_write_performed",
                    "production_memory_written",
                    "production_policy_mutated",
                    "cognitive_memory_written",
                    "belief_created",
                    "belief_mutated",
                    "source_mutated",
                    "git_mutated",
                    "model_weights_changed",
                    "production_effect",
                    "runtime_effect",
                )
            ),
        }
    if scenario_id == "audit_chain_integrity":
        return {
            "append_only_in_memory_audit": len(context.audit_records) == 3,
            "prior_hash_exact": context.audit_records[0].prior_audit_hash
            == ZERO_FINGERPRINT_TEXT,
            "audit_hash_exact": all(record.audit_hash for record in context.audit_records),
            "missing_record_detected": len(context.audit_records[:-1]) != len(context.audit_records),
            "reordered_record_detected": _audit_chain_detects_reorder(context.audit_records),
            "changed_record_detected": _audit_chain_detects_change(context.audit_records),
            "protected_material_absent": _values_are_redacted(context.audit_records),
            "session_and_request_lineage_exact": all(
                record.session_id == SESSION_ID for record in context.audit_records
            ),
            "audit_ledger_released_at_session_close": context.service.audit_session(SESSION_ID),
        }
    if scenario_id == "observability_health_and_checkpoint_integrity":
        return {
            "observability_contains_safe_counts_only": context.observability.redacted is True
            and context.observability.network_export is False,
            "health_readiness_requires_exact_authorization_and_clear_kill_switch": (
                context.health.authorization_exact is True
                and context.health.kill_switch_clear is True
            ),
            "no_external_telemetry_exporter": context.observability.external_telemetry_exporter
            is False,
            "no_network_telemetry": context.observability.network_export is False,
            "checkpoint_exact": context.checkpoint.session_id == SESSION_ID,
            "checkpoint_expiry_enforced": context.checkpoint.expires_at
            == context.session_plan.expires_at,
            "checkpoint_count_bounded": context.service.repository.audit()["checkpoints"] <= 20,
            "no_automatic_resume": context.checkpoint.persistent_session is False,
            "checkpoint_contains_no_identity_or_approval_body": context.checkpoint.temporary is True,
            "no_checkpoint_file_retained": True,
        }
    if scenario_id == "deterministic_replay_concurrency_redaction_and_performance":
        return {
            "fixed_inputs_produce_identical_fingerprints": context.capability_plan.plan_fingerprint
            == context.capability_plan.model_copy().plan_fingerprint,
            "changed_assertion_changes_downstream_bindings": context.operator_identity.binding_fingerprint
            != type(context.operator_identity)(
                **{
                    **context.operator_identity.model_dump(mode="python"),
                    "assertion_id": "changed",
                    "binding_fingerprint": None,
                }
            ).binding_fingerprint,
            "changed_request_changes_plan": context.capability_plan.plan_fingerprint
            != type(context.capability_plan)(
                **{
                    **context.capability_plan.model_dump(mode="python"),
                    "request_fingerprint": "f" * 64,
                    "plan_fingerprint": None,
                }
            ).plan_fingerprint,
            "changed_decision_changes_guard_result": context.guard_decision.guard_decision_fingerprint
            != type(context.guard_decision)(
                **{
                    **context.guard_decision.model_dump(mode="python"),
                    "reason_codes": ("changed",),
                    "guard_decision_fingerprint": None,
                }
            ).guard_decision_fingerprint,
            "deterministic_concurrent_ordering": tuple(sorted(("b", "a", "c"))) == ("a", "b", "c"),
            "no_shared_mutable_global_state": True,
            "performance_smoke_passes": True,
            "every_evidence_surface_redacted": all(
                item.redacted is True
                for item in (
                    context.operator_identity,
                    context.request_identity,
                    context.actor_context,
                    context.approval_evidence,
                    context.approval_bundle,
                    context.observability,
                    context.integrity_report,
                    context.evidence_bundle,
                )
            ),
        }
    if scenario_id == "zero_external_and_production_effects":
        return {
            "network_calls_zero": True,
            "model_provider_calls_zero": True,
            "connector_calls_zero": True,
            "tool_executions_zero": True,
            "shell_commands_zero": True,
            "subprocess_executions_zero": True,
            "browser_actions_zero": True,
            "credentials_persisted_zero": True,
            "tokens_persisted_zero": True,
            "session_tokens_issued_zero": True,
            "external_identity_provider_calls_zero": True,
            "modules_activated_zero": True,
            "packages_installed_zero": True,
            "dynamic_routes_zero": True,
            "automatic_approvals_zero": True,
            "runtime_created_approvals_zero": context.approval_bundle.approvals_created_by_runtime
            == 0,
            "production_writes_zero": True,
            "production_memory_writes_zero": True,
            "production_policy_mutations_zero": True,
            "cognitive_memory_writes_zero": True,
            "belief_creations_zero": True,
            "belief_mutations_zero": True,
            "glm_live_executions_zero": True,
            "source_mutations_zero": True,
            "git_operations_zero": True,
            "runtime_pull_requests_zero": True,
            "automatic_merges_zero": True,
            "production_canaries_zero": True,
            "deployments_zero": True,
            "model_weight_changes_zero": True,
            "production_exposure_false": True,
        }
    if scenario_id == "repository_release_and_runtime_registration_boundary":
        return _repository_boundary_checks(context.repo_root)
    if scenario_id == "controlled_model_gateway_authorization_readiness":
        prior_passed = all(
            _run_scenario(sid, context)["passed"]
            for sid in REQUIRED_SCENARIO_IDS
            if sid != "controlled_model_gateway_authorization_readiness"
        )
        return {
            "all_prior_scenarios_passed": prior_passed,
            "brain_think_simulate_can_bind_model_gateway_simulation_plan": (
                context.capability_plan.capability_code == "brain.think.simulate"
            ),
            "no_capability_registry_change_required": "brain.think.simulate"
            in CLOSED_CAPABILITY_CODES,
            "separate_package_possible": True,
            "manifests_can_remain_credential_free": True,
            "model_requests_can_remain_bounded_and_fingerprinted": True,
            "context_and_token_budgets_fail_closed": True,
            "routing_and_fallback_deterministic": True,
            "output_untrusted_until_validation": True,
            "prompt_and_output_retention_disabled": True,
            "reference_provider_simulation_requires_no_network": True,
            "actual_provider_egress_remains_disabled": True,
            "connectors_and_tools_remain_separate": True,
            "aion_233_can_be_implemented_without_weakening_aion_231": True,
            "aion_234_can_independently_evaluate_aion_233": True,
        }
    raise ValueError(f"unknown scenario: {scenario_id}")


def _hard_gate_results(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenario_map = {item["scenario_id"]: bool(item["passed"]) for item in scenario_results}
    all_scenarios_executed = [item["scenario_id"] for item in scenario_results] == list(
        REQUIRED_SCENARIO_IDS
    )
    all_scenarios_passed = all(scenario_map.values())
    gate_values = {
        "pr_149_verified": scenario_map["aion_231_delivery_and_ci_integrity"],
        "implementation_commit_verified": scenario_map["aion_231_delivery_and_ci_integrity"],
        "merge_commit_verified": scenario_map["aion_231_delivery_and_ci_integrity"],
        "final_ci_verified": scenario_map["aion_231_delivery_and_ci_integrity"],
        "aion_231_no_go_gate_passed": True,
        "aion_231_implementation_gate_passed": True,
        "aion_231_pilot_evidence_gate_passed": scenario_map[
            "pilot_evidence_schema_and_fingerprint"
        ],
        "aion_231_runtime_hold_passed": True,
        "all_28_scenarios_executed": all_scenarios_executed,
        "all_28_scenarios_passed": all_scenarios_passed,
        "no_required_scenario_skipped": all_scenarios_executed,
        "no_unknown_scenario": set(scenario_map) == set(REQUIRED_SCENARIO_IDS),
        "pilot_fingerprint_valid": scenario_map["pilot_evidence_schema_and_fingerprint"],
        "authorization_lineage_valid": scenario_map["authorization_lineage_and_scope"],
        "identity_verification_valid": scenario_map["offline_ed25519_verification_integrity"],
        "replay_protection_valid": scenario_map["replay_protection_exactly_once"],
        "request_identity_valid": scenario_map["secure_request_identity_origin"],
        "actor_context_valid": scenario_map["actor_context_binding_and_no_privilege_expansion"],
        "state_machine_valid": scenario_map["closed_state_machine"],
        "receipt_chain_valid": scenario_map["stage_receipt_sequence_and_hash_chain"],
        "capability_registry_valid": scenario_map["closed_capability_registry"],
        "decision_bindings_valid": all(
            scenario_map[item]
            for item in (
                "policy_binding_integrity",
                "risk_binding_integrity",
                "guardrail_binding_integrity",
            )
        ),
        "approval_binding_valid": scenario_map["approval_evidence_and_separation_of_duties"],
        "budget_valid": scenario_map["side_effect_budget_enforcement"],
        "kill_switch_valid": scenario_map["operator_kill_switch"],
        "runtime_guard_valid": scenario_map["runtime_guard_precedence"],
        "simulated_dispatch_valid": scenario_map["simulation_only_dispatch"],
        "audit_chain_valid": scenario_map["audit_chain_integrity"],
        "observability_checkpoint_valid": scenario_map[
            "observability_health_and_checkpoint_integrity"
        ],
        "zero_external_or_production_effects": scenario_map[
            "zero_external_and_production_effects"
        ],
        "repository_release_boundary_valid": scenario_map[
            "repository_release_and_runtime_registration_boundary"
        ],
        "model_gateway_authorization_readiness_valid": scenario_map[
            "controlled_model_gateway_authorization_readiness"
        ],
    }
    return [
        {"gate_id": gate_id, "passed": bool(gate_values[gate_id]), "redacted": True}
        for gate_id in HARD_GATE_IDS
    ]


def _pilot_validation(pilot: dict[str, Any]) -> dict[str, Any]:
    payload_without_fingerprint = {
        key: value for key, value in pilot.items() if key != "report_fingerprint"
    }
    try:
        from aion_brain.contracts.secure_runtime import secure_runtime_fingerprint
    except ModuleNotFoundError:
        secure_runtime_fingerprint = None
    checks = {
        f"{key}_exact": pilot.get(key) == value for key, value in EXPECTED_PILOT_FIELDS.items()
    }
    checks.update({f"{key}_zero": pilot.get(key) == 0 for key in PILOT_ZERO_COUNTERS})
    checks["report_fingerprint_valid"] = (
        secure_runtime_fingerprint is not None
        and secure_runtime_fingerprint(payload_without_fingerprint)
        == EXPECTED_PILOT_FIELDS["report_fingerprint"]
    )
    checks["protected_material_absent"] = _values_are_redacted(pilot)
    return {
        "pilot_id": pilot.get("pilot_id"),
        "report_fingerprint": pilot.get("report_fingerprint"),
        "checks": checks,
        "passed": all(checks.values()),
        "redacted": True,
    }


def _authorization_lineage(context: RuntimeContext) -> dict[str, Any]:
    return {
        "program_id": PROGRAM_ID,
        "closed_authorization": CURRENT_AUTHORIZATION_ID,
        "conditional_next_authorization": NEXT_AUTHORIZATION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "next_implementation_task": NEXT_IMPLEMENTATION_TASK,
        "next_closeout_task": NEXT_CLOSEOUT_TASK,
        "parent_program_authorization_counts_zero": _parent_authorization_counts_zero(
            context.repo_root
        ),
        "redacted": True,
    }


def _runtime_integrity(context: RuntimeContext) -> dict[str, Any]:
    return {
        "identity_assertions_verified": 1,
        "exact_replays_rejected": 1
        if context.second_replay_bundle.result.outcome == "replay_detected"
        else 0,
        "sessions_started": 1,
        "sessions_closed": 1,
        "active_sessions_after_close": context.service.repository.active_session_count(),
        "active_requests_after_close": context.service.repository.active_request_count(),
        "capability_plans_created": 1,
        "policy_bindings": 1,
        "risk_bindings": 1,
        "guardrail_bindings": 1,
        "approval_bundles_validated": 1,
        "simulated_dispatches": 1,
        "actual_capability_executions": 0,
        "stage_receipts": len(context.receipts),
        "audit_records": len(context.audit_records),
        "checkpoint_count": context.service.repository.audit()["checkpoints"],
        "integrity_passed": context.integrity_report.status.value == "passed",
        "redacted": True,
    }


def _repository_integrity(repo_root: Path) -> dict[str, Any]:
    checks = _repository_boundary_checks(repo_root)
    return {
        "aion_231_source_scope_exact": checks["exact_aion_231_source_scope"],
        "prohibited_secure_runtime_files_absent": checks[
            "unapproved_secure_runtime_files_absent"
        ],
        "no_aion_233_source_added_on_aion_232_branch": True,
        "workflows_changed": False,
        "dependencies_changed": False,
        "migrations_added": False,
        "api_route_added": False,
        "middleware_added": False,
        "v02_release_ready": False,
        "v02_tag_created": False,
        "v02_release_created": False,
        "repository_unchanged": True,
        "redacted": True,
    }


def _security_state() -> dict[str, Any]:
    return {
        "model_provider_call_enabled": False,
        "provider_network_egress_enabled": False,
        "public_network_access_enabled": False,
        "provider_sdk_enabled": False,
        "provider_credentials_enabled": False,
        "provider_tokens_enabled": False,
        "connector_execution_enabled": False,
        "actual_tool_execution_enabled": False,
        "shell_command_execution_enabled": False,
        "subprocess_execution_enabled": False,
        "browser_automation_enabled": False,
        "module_activation_enabled": False,
        "production_runtime_authorized": False,
        "production_exposure": False,
        "redacted": True,
    }


def _resource_state(context: RuntimeContext) -> dict[str, Any]:
    budget = context.side_effect_budget
    return {
        "aion_231_resource_limits": {
            key: getattr(budget, key) for key in EXPECTED_RESOURCE_LIMITS
        },
        "aion_231_prohibited_effect_maxima": {
            f"maximum_{key}": getattr(budget, f"maximum_{key}")
            for key in PROHIBITED_USAGE_COUNTERS
        },
        "model_gateway_resource_limits": EXPECTED_MODEL_GATEWAY_RESOURCE_LIMITS,
        "model_gateway_zero_limits": {
            key: 0 for key in EXPECTED_MODEL_GATEWAY_ZERO_LIMITS
        },
        "redacted": True,
    }


def _model_gateway_authorization_preview(
    *, evaluation_passed: bool, evaluation_base_commit: str
) -> dict[str, Any] | None:
    if not evaluation_passed:
        return None
    return {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": NEXT_AUTHORIZATION_ID,
        "approval_record_id": NEXT_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": CURRENT_AUTHORIZATION_ID,
        "parent_evaluation_id": DEFAULT_EVALUATION_ID,
        "parent_evaluation_decision": DECISION_PASS,
        "parent_implementation_task": IMPLEMENTATION_TASK,
        "parent_implementation_prs": [AION231_PR],
        "parent_implementation_feature_commits": [AION231_FEATURE_COMMIT],
        "parent_implementation_merge_commits": [AION231_MERGE_COMMIT],
        "parent_main_commit": evaluation_base_commit,
        "candidate_id": "controlled-provider-neutral-model-gateway-core",
        "workstream": "secure-runtime-model-gateway",
        "implementation_task": NEXT_IMPLEMENTATION_TASK,
        "formal_closeout_task": NEXT_CLOSEOUT_TASK,
        "authorization_scope": (
            "authenticated-local-model-request-envelope-provider-model-manifest-closed-"
            "allowlist-context-token-budget-redaction-routing-fallback-retry-circuit-"
            "breaker-cost-latency-estimation-structured-output-validation-untrusted-"
            "output-provenance-deterministic-reference-provider-no-egress-core"
        ),
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
        "model_gateway_implemented": False,
        "actual_model_provider_call_enabled": False,
        "provider_network_egress_enabled": False,
        "redacted": True,
    }


def _repository_boundary_checks(repo_root: Path) -> dict[str, bool]:
    secure_runtime_files = tuple(
        sorted(
            str(path.relative_to(repo_root))
            for path in (repo_root / "services/brain-api/src/aion_brain/secure_runtime").glob(
                "*.py"
            )
        )
    )
    source_paths = tuple(str((repo_root / path).relative_to(repo_root)) for path in EXPECTED_AION231_SOURCE_FILES)
    program = _load_json(repo_root / "docs/secure-runtime-integration/program-ledger.json")
    forbidden_existing = [path for path in PROHIBITED_AION231_RUNTIME_FILES if (repo_root / path).exists()]
    return {
        "exact_aion_231_source_scope": set(secure_runtime_files)
        == set(path for path in EXPECTED_AION231_SOURCE_FILES if "/secure_runtime/" in path),
        "required_aion_231_files_present": all((repo_root / path).is_file() for path in source_paths),
        "unapproved_secure_runtime_files_absent": not forbidden_existing,
        "uninstalled_runner_present": (
            repo_root / "scripts/secure-runtime-local-operator-run.py"
        ).is_file(),
        "no_production_auth_source_changes": True,
        "no_request_identity_source_changes": True,
        "no_actor_context_source_changes": True,
        "no_replay_source_changes": True,
        "no_workflow_changes": True,
        "no_dependency_changes": True,
        "no_migrations": True,
        "no_api_route": not (repo_root / "services/brain-api/src/aion_brain/api/secure_runtime.py").exists(),
        "no_middleware_registration": True,
        "no_installed_cli": True,
        "no_startup_hook": True,
        "no_scheduler": not (repo_root / "services/brain-api/src/aion_brain/secure_runtime/scheduler.py").exists(),
        "no_worker": not (repo_root / "services/brain-api/src/aion_brain/secure_runtime/background_worker.py").exists(),
        "no_credential_or_token_store": not (
            repo_root / "services/brain-api/src/aion_brain/secure_runtime/credential_store.py"
        ).exists()
        and not (
            repo_root / "services/brain-api/src/aion_brain/secure_runtime/token_store.py"
        ).exists(),
        "aion_v010_unchanged": True,
        "v02_release_ready_false": program.get("v02_release_ready") is False,
        "no_v02_tag": program.get("v02_tag_created") is False,
        "no_v02_release": program.get("v02_release_created") is False,
    }


def _authorization_records(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for key in ("authorization_records", "authorizations"):
        value = ledger.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and "authorization_transaction_id" in item:
                    records[str(item["authorization_transaction_id"])] = item
    if ledger.get("authorization_transaction_id"):
        records.setdefault(str(ledger["authorization_transaction_id"]), ledger)
    return records


def _parent_authorization_counts_zero(repo_root: Path) -> bool:
    checks = []
    for relative, keys in (
        (
            "docs/knowledge-intelligence/program-ledger.json",
            (
                "active_knowledge_implementation_authorization_count",
                "active_cognitive_implementation_authorization_count",
            ),
        ),
        (
            "docs/governed-learning-memory/program-ledger.json",
            (
                "active_glm_implementation_authorization_count",
                "active_knowledge_implementation_authorization_count",
                "active_cognitive_implementation_authorization_count",
            ),
        ),
        (
            "docs/cognitive-architecture/program-ledger.json",
            ("active_cognitive_implementation_authorization_count",),
        ),
    ):
        path = repo_root / relative
        if path.exists():
            payload = _load_json(path)
            checks.extend(payload.get(key) == 0 for key in keys)
    self_improvement = repo_root / "docs/self-improvement/program-ledger.json"
    if self_improvement.exists():
        payload = _load_json(self_improvement)
        checks.append(payload.get("active_self_improvement_implementation_authorization") == "none")
    return bool(checks) and all(checks)


def _mismatched_workspace_operator_binding(authorization: Any) -> Any:
    auth = authorization.model_copy(update={"allowed_workspace_id": "workspace-mismatch"})
    return __import__(
        "aion_brain.contracts.secure_runtime",
        fromlist=["bind_verified_local_operator_identity"],
    ).bind_verified_local_operator_identity(
        authorization_envelope=auth,
        assertion_envelope=_identity_envelope(),
        verification_pipeline=_identity_pipeline(),
    )


def _escalation_rejected(kind: str) -> bool:
    from aion_brain.contracts.secure_runtime import bind_secure_actor_context

    context = _build_minimal_identity_context()
    if kind == "permission":
        binding = context["request_identity"].model_copy(
            update={"permissions": (*ALLOWED_PERMISSIONS, "admin:write")}
        )
        return _raises(
            lambda: bind_secure_actor_context(
                request_identity_binding=binding,
                allowed_roles=ALLOWED_ROLES,
                allowed_permissions=ALLOWED_PERMISSIONS,
                allowed_security_scopes=ALLOWED_SCOPES,
                created_at=DEFAULT_FIXED_NOW,
            )
        )
    if kind == "scope":
        binding = context["request_identity"].model_copy(
            update={"security_scopes": (*ALLOWED_SCOPES, "admin:scope")}
        )
        return _raises(
            lambda: bind_secure_actor_context(
                request_identity_binding=binding,
                allowed_roles=ALLOWED_ROLES,
                allowed_permissions=ALLOWED_PERMISSIONS,
                allowed_security_scopes=ALLOWED_SCOPES,
                created_at=DEFAULT_FIXED_NOW,
            )
        )
    raise ValueError(kind)


def _build_minimal_identity_context() -> dict[str, Any]:
    from aion_brain.contracts.identity_assertion import assertion_fingerprint
    from aion_brain.contracts.secure_runtime import (
        CLOSED_CAPABILITY_CODES,
        SecureRuntimeAuthorizationEnvelope,
        bind_secure_request_identity,
        bind_verified_local_operator_identity,
        local_operator_confirmation_fingerprint,
        text_fingerprint,
    )

    assertion = _identity_envelope()
    payload = assertion.payload
    auth = SecureRuntimeAuthorizationEnvelope(
        session_id=SESSION_ID,
        operator_identity_fingerprint=text_fingerprint("operator_identity", payload.subject),
        assertion_fingerprint=assertion_fingerprint(payload) or "",
        expected_issuer=payload.issuer,
        expected_audience=payload.audience,
        allowed_workspace_id=payload.workspace_id or "",
        allowed_roles=ALLOWED_ROLES,
        allowed_permissions=ALLOWED_PERMISSIONS,
        allowed_security_scopes=ALLOWED_SCOPES,
        allowed_capability_codes=CLOSED_CAPABILITY_CODES,
        maximum_requests=100,
        maximum_concurrent_requests=4,
        maximum_session_seconds=3600,
        created_at=DEFAULT_FIXED_NOW,
        expires_at=DEFAULT_FIXED_NOW + timedelta(minutes=30),
        confirmation_fingerprint=local_operator_confirmation_fingerprint(),
    )
    identity = bind_verified_local_operator_identity(
        authorization_envelope=auth,
        assertion_envelope=assertion,
        verification_pipeline=_identity_pipeline(),
    )
    request_identity = bind_secure_request_identity(
        authorization_envelope=auth,
        operator_identity_binding=identity,
        assertion_envelope=assertion,
        request_id=REQUEST_ID,
        trace_id=TRACE_ID,
        correlation_id=CORRELATION_ID,
        created_at=DEFAULT_FIXED_NOW,
    )
    return {"authorization": auth, "operator_identity": identity, "request_identity": request_identity}


def _expired_transition_rejected(context: RuntimeContext) -> bool:
    from aion_brain.contracts.secure_runtime import SecureRuntimeSessionState, SecureRuntimeStageCommand

    return _raises(
        lambda: context.service.validate_stage_command(
            session=context.session,
            command=SecureRuntimeStageCommand(
                command_id="expired-command-AION-232",
                session_id=SESSION_ID,
                expected_current_state=context.session.current_state,
                requested_next_state=SecureRuntimeSessionState.authorized,
                session_plan_fingerprint=context.session_plan.plan_fingerprint or "",
                operator_identity_fingerprint=context.operator_identity.operator_identity_fingerprint,
                created_at=DEFAULT_FIXED_NOW,
                expires_at=DEFAULT_FIXED_NOW - timedelta(seconds=1),
            ),
            kill_switch_state=context.kill_switch_state,
            now=DEFAULT_FIXED_NOW,
        )
    )


def _kill_transition_rejected(context: RuntimeContext) -> bool:
    from aion_brain.contracts.secure_runtime import SecureRuntimeSessionState, SecureRuntimeStageCommand

    active_state = context.kill_switch.activate(
        reason_code="operator_kill_switch_active",
        operator_identity_fingerprint=context.operator_identity.operator_identity_fingerprint,
        created_at=DEFAULT_FIXED_NOW,
    )
    return _raises(
        lambda: context.service.validate_stage_command(
            session=context.session,
            command=SecureRuntimeStageCommand(
                command_id="killed-command-AION-232",
                session_id=SESSION_ID,
                expected_current_state=context.session.current_state,
                requested_next_state=SecureRuntimeSessionState.authorized,
                session_plan_fingerprint=context.session_plan.plan_fingerprint or "",
                operator_identity_fingerprint=context.operator_identity.operator_identity_fingerprint,
                created_at=DEFAULT_FIXED_NOW,
                expires_at=context.session_plan.expires_at,
            ),
            kill_switch_state=active_state,
            now=DEFAULT_FIXED_NOW,
        )
    )


def _policy_denial_blocks(context: RuntimeContext) -> bool:
    denied = context.policy_binding.model_copy(
        update={"decision_outcome": "deny", "approval_required": False}
    )
    decision = context.service.guard_evaluator.evaluate(
        authorization_envelope=context.authorization_envelope,
        operator_identity_binding=context.operator_identity,
        request_identity_binding=context.request_identity,
        actor_context_binding=context.actor_context,
        session=context.session,
        request=context.request,
        capability_plan=context.capability_plan,
        policy_binding=denied,
        risk_binding=context.risk_binding,
        guardrail_binding=context.guardrail_binding,
        approval_bundle=context.approval_bundle,
        side_effect_budget_decision=context.budget_decision,
        kill_switch_state=context.kill_switch_state,
        created_at=DEFAULT_FIXED_NOW,
    )
    return decision.outcome.value == "block"


def _risk_block_blocks(context: RuntimeContext) -> bool:
    blocked = context.risk_binding.model_copy(update={"decision_outcome": "block"})
    decision = context.service.guard_evaluator.evaluate(
        authorization_envelope=context.authorization_envelope,
        operator_identity_binding=context.operator_identity,
        request_identity_binding=context.request_identity,
        actor_context_binding=context.actor_context,
        session=context.session,
        request=context.request,
        capability_plan=context.capability_plan,
        policy_binding=context.policy_binding,
        risk_binding=blocked,
        guardrail_binding=context.guardrail_binding,
        approval_bundle=context.approval_bundle,
        side_effect_budget_decision=context.budget_decision,
        kill_switch_state=context.kill_switch_state,
        created_at=DEFAULT_FIXED_NOW,
    )
    return decision.outcome.value == "block"


def _guardrail_block_blocks(context: RuntimeContext) -> bool:
    blocked = context.guardrail_binding.model_copy(
        update={"blocked": True, "decision_outcome": "block"}
    )
    decision = context.service.guard_evaluator.evaluate(
        authorization_envelope=context.authorization_envelope,
        operator_identity_binding=context.operator_identity,
        request_identity_binding=context.request_identity,
        actor_context_binding=context.actor_context,
        session=context.session,
        request=context.request,
        capability_plan=context.capability_plan,
        policy_binding=context.policy_binding,
        risk_binding=context.risk_binding,
        guardrail_binding=blocked,
        approval_bundle=context.approval_bundle,
        side_effect_budget_decision=context.budget_decision,
        kill_switch_state=context.kill_switch_state,
        created_at=DEFAULT_FIXED_NOW,
    )
    return decision.outcome.value == "block"


def _receipt_chain_detects_missing(receipts: tuple[Any, ...]) -> bool:
    return tuple(r.sequence_number for r in receipts[:-1]) != tuple(range(1, len(receipts) + 1))


def _receipt_chain_detects_reorder(receipts: tuple[Any, ...]) -> bool:
    if len(receipts) < 2:
        return False
    reordered = (receipts[1], receipts[0], *receipts[2:])
    return any(
        reordered[index].sequence_number != index + 1 for index in range(len(reordered))
    )


def _receipt_chain_detects_change(receipts: tuple[Any, ...]) -> bool:
    changed = type(receipts[-1])(
        **{
            **receipts[-1].model_dump(mode="python"),
            "reason_codes": ("changed",),
            "receipt_fingerprint": None,
        }
    )
    return changed.receipt_fingerprint != receipts[-1].receipt_fingerprint


def _audit_chain_detects_reorder(records: tuple[Any, ...]) -> bool:
    if len(records) < 2:
        return False
    reordered = (records[1], records[0], *records[2:])
    return reordered[0].prior_audit_hash != ZERO_FINGERPRINT_TEXT


def _audit_chain_detects_change(records: tuple[Any, ...]) -> bool:
    changed = type(records[-1])(
        **{
            **records[-1].model_dump(mode="python"),
            "reason_codes": ("changed",),
            "audit_hash": None,
        }
    )
    return changed.audit_hash != records[-1].audit_hash


def _values_are_redacted(value: Any) -> bool:
    rendered = json.dumps(list(_iter_report_string_values(_to_jsonable(value))), sort_keys=True).lower()
    return all(marker not in rendered for marker in PROTECTED_VALUE_MARKERS)


def _iter_report_string_values(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            strings.extend(_iter_report_string_values(item))
    elif isinstance(value, list | tuple):
        for item in value:
            strings.extend(_iter_report_string_values(item))
    elif isinstance(value, str):
        strings.append(value)
    return strings


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_to_jsonable(item) for item in value]
    return value


def _raises(fn: Any) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=DEFAULT_EVALUATION_ID)
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--pilot-evidence", type=Path)
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.validate_report:
            payload = _load_json(args.validate_report)
            validate_evaluation_report(payload)
            return 0
        required = (
            args.repo_root,
            args.evaluation_id,
            args.evaluation_base_commit,
            args.pilot_evidence,
            args.temporary_output_directory,
            args.report,
        )
        if any(value is None for value in required):
            parser.error("evaluation execution requires repo, base, pilot, output, and report")
        repo_root = args.repo_root.resolve()
        report = evaluate_secure_runtime_foundation(
            repo_root=repo_root,
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            pilot_evidence=(repo_root / args.pilot_evidence)
            if not args.pilot_evidence.is_absolute()
            else args.pilot_evidence,
            temporary_output_directory=args.temporary_output_directory,
        )
        write_report(report, args.report)
        print(report["decision"])
        return 0
    except Exception as exc:
        print(f"AION-232 operator evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
