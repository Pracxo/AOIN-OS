#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()
PROGRAM_ID = "AION-ADAPTIVE-INTELLIGENCE-001"
AUTH_ID = "AION-245-AI-0001"
PRE_IMPLEMENTATION_STATE = "adaptive_intelligence_program_authorized_not_implemented"
IMPLEMENTED_DISABLED_STATE = (
    "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout"
)
IMPLEMENTED_DISABLED_GATEWAY_STATE = (
    "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout"
)
SCOPE = "controlled-provider-neutral-external-cognition-contracts-provider-manifests-model-manifests-request-response-envelopes-routing-budgets-structured-output-redaction-trust-provenance-fixture-replay-circuit-breaker-observability-audit-no-network-no-provider-call-no-credential-value-no-memory-write-no-tool-execution-core"
ROADMAP = [f"AION-{number}" for number in range(245, 261)]
APPROVED = {
    "external_cognition_contract_approved",
    "external_cognition_authorization_envelope_approved",
    "existing_model_gateway_component_binding_approved",
    "secure_runtime_component_binding_approved",
    "provider_manifest_approved",
    "model_manifest_approved",
    "model_capability_manifest_approved",
    "model_request_envelope_approved",
    "model_response_envelope_approved",
    "message_normalization_approved",
    "structured_output_schema_approved",
    "structured_output_validation_approved",
    "model_route_policy_approved",
    "capability_based_routing_approved",
    "declared_context_budget_approved",
    "declared_output_budget_approved",
    "declared_cost_budget_approved",
    "latency_budget_approved",
    "retry_policy_approved",
    "circuit_breaker_policy_approved",
    "response_trust_classification_approved",
    "uncertainty_projection_approved",
    "provider_error_normalization_approved",
    "prompt_redaction_policy_approved",
    "response_redaction_policy_approved",
    "prompt_fingerprint_approved",
    "response_fingerprint_approved",
    "deterministic_fixture_provider_approved",
    "deterministic_replay_approved",
    "changed_replay_rejection_approved",
    "audit_evidence_approved",
    "observability_schema_approved",
    "operator_review_record_approved",
    "static_console_evidence_approved",
    "documentation_approved",
}
PROHIBITED = {
    "actual_model_provider_call_enabled",
    "provider_network_adapter_enabled",
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "provider_credential_input_enabled",
    "provider_credential_read_enabled",
    "provider_credential_generation_enabled",
    "provider_credential_persistence_enabled",
    "provider_token_input_enabled",
    "provider_token_read_enabled",
    "provider_token_persistence_enabled",
    "provider_authorization_header_creation_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "hidden_reasoning_capture_enabled",
    "model_output_triggered_execution_enabled",
    "model_output_tool_call_enabled",
    "persistent_memory_write_enabled",
    "verified_knowledge_promotion_enabled",
    "actual_belief_mutation_enabled",
    "engagement_learning_enabled",
    "adaptive_routing_runtime_enabled",
    "external_connector_execution_enabled",
    "external_tool_execution_enabled",
    "autonomous_background_loop_enabled",
    "scheduled_provider_calls_enabled",
    "source_rewrite_enabled",
    "runtime_git_mutation_enabled",
    "runtime_pull_request_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_runtime_authorized",
    "production_exposure",
}
RESOURCE_LIMITS = {
    "maximum_provider_manifests": 8,
    "maximum_model_manifests": 32,
    "maximum_model_capability_records": 256,
    "maximum_routing_policies": 100,
    "maximum_routing_rules": 500,
    "maximum_request_templates": 100,
    "maximum_structured_output_schemas": 100,
    "maximum_fixture_sessions": 20,
    "maximum_fixture_requests_per_session": 100,
    "maximum_total_fixture_requests": 1000,
    "maximum_messages_per_request": 256,
    "maximum_request_payload_bytes": 2097152,
    "maximum_response_payload_bytes": 4194304,
    "maximum_declared_context_tokens": 2000000,
    "maximum_declared_output_tokens": 262144,
    "maximum_concurrency": 4,
    "maximum_retry_attempts": 3,
    "maximum_circuit_breaker_records": 100,
    "maximum_operator_review_items": 200,
    "maximum_evidence_records": 10000,
    "maximum_evidence_bytes": 104857600,
    "maximum_local_fixture_pilots": 20,
    "maximum_actual_model_provider_calls": 0,
    "maximum_public_network_calls": 0,
    "maximum_external_network_egress_calls": 0,
    "maximum_dns_resolutions": 0,
    "maximum_provider_credentials_generated": 0,
    "maximum_provider_credentials_read": 0,
    "maximum_provider_credentials_persisted": 0,
    "maximum_provider_tokens_read": 0,
    "maximum_provider_tokens_persisted": 0,
    "maximum_authorization_headers_created": 0,
    "maximum_raw_prompts_persisted": 0,
    "maximum_raw_responses_persisted": 0,
    "maximum_hidden_reasoning_records": 0,
    "maximum_memory_writes": 0,
    "maximum_verified_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_external_connector_calls": 0,
    "maximum_external_tool_executions": 0,
    "maximum_background_cycles": 0,
    "maximum_scheduled_provider_calls": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_automatic_merges": 0,
    "maximum_production_deployments": 0,
    "maximum_model_weight_changes": 0,
}
FUTURE_SOURCE = [
    "services/brain-api/src/aion_brain/contracts/external_cognition.py",
    "services/brain-api/src/aion_brain/external_cognition/__init__.py",
    "services/brain-api/src/aion_brain/external_cognition/authorization.py",
    "services/brain-api/src/aion_brain/external_cognition/component_binding.py",
    "services/brain-api/src/aion_brain/external_cognition/provider_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/model_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/request_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/response_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/message_normalization.py",
    "services/brain-api/src/aion_brain/external_cognition/structured_output.py",
    "services/brain-api/src/aion_brain/external_cognition/routing_policy.py",
    "services/brain-api/src/aion_brain/external_cognition/budgets.py",
    "services/brain-api/src/aion_brain/external_cognition/trust.py",
    "services/brain-api/src/aion_brain/external_cognition/redaction.py",
    "services/brain-api/src/aion_brain/external_cognition/circuit_breaker.py",
    "services/brain-api/src/aion_brain/external_cognition/fixture_provider.py",
    "services/brain-api/src/aion_brain/external_cognition/replay.py",
    "services/brain-api/src/aion_brain/external_cognition/observability.py",
    "services/brain-api/src/aion_brain/external_cognition/audit.py",
    "services/brain-api/src/aion_brain/external_cognition/integrity.py",
    "services/brain-api/src/aion_brain/external_cognition/evidence.py",
    "scripts/external-cognition-fixture-local-run.py",
]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


program = load("docs/adaptive-intelligence/program-ledger.json")
auth = load("docs/adaptive-intelligence/authorization-ledger.json")
record = auth["records"][0]

if program["program_id"] != PROGRAM_ID or auth["program_id"] != PROGRAM_ID:
    raise SystemExit("programme ID mismatch")
if record["authorization_transaction_id"] != AUTH_ID or record["approval_record_id"] != AUTH_ID:
    raise SystemExit("authorization ID mismatch")
if [item["task_id"] for item in program["roadmap"]] != ROADMAP:
    raise SystemExit("roadmap sequence mismatch")
if record["authorization_scope"] != SCOPE:
    raise SystemExit("authorization scope mismatch")

for key in APPROVED:
    if program["approved_capabilities"].get(key) is not True:
        raise SystemExit(f"approved capability missing or false in program: {key}")
    if record["approved_capabilities"].get(key) is not True:
        raise SystemExit(f"approved capability missing or false in authorization: {key}")
if set(program["approved_capabilities"]) != APPROVED:
    raise SystemExit("approved capability key set changed")

for key in PROHIBITED:
    if program["prohibited_capabilities"].get(key) is not False:
        raise SystemExit(f"prohibited capability enabled in program: {key}")
    if record["prohibited_capabilities"].get(key) is not False:
        raise SystemExit(f"prohibited capability enabled in authorization: {key}")
if set(program["prohibited_capabilities"]) != PROHIBITED:
    raise SystemExit("prohibited capability key set changed")

if program["resource_limits"] != RESOURCE_LIMITS:
    raise SystemExit("resource limits changed")

state = program.get("program_state")
if state not in {PRE_IMPLEMENTATION_STATE, IMPLEMENTED_DISABLED_STATE}:
    raise SystemExit(f"program state mismatch: {state!r}")

for key, value in {
    "adaptive_intelligence_program_authorized": True,
    "adaptive_intelligence_program_implemented": False,
    "active_adaptive_intelligence_authorization_count": 1,
    "active_adaptive_intelligence_authorization": AUTH_ID,
    "active_adaptive_intelligence_task": "AION-246",
    "formal_closeout_task": "AION-247",
    "final_planned_task": "AION-260",
    "external_cognition_gateway_authorized": True,
    "production_runtime_authorized": False,
}.items():
    if program.get(key) != value:
        raise SystemExit(f"program field mismatch {key}: {program.get(key)!r}")

if state == PRE_IMPLEMENTATION_STATE:
    if program.get("external_cognition_gateway_implemented") is not False:
        raise SystemExit("external cognition gateway must be unimplemented before AION-246")
    expected_gateway_state = "authorized_not_implemented"
    if program.get("external_cognition_gateway_state") not in {None, expected_gateway_state}:
        raise SystemExit("unexpected pre-implementation external cognition gateway state")
else:
    for key, value in {
        "external_cognition_gateway_implemented": True,
        "external_cognition_gateway_state": IMPLEMENTED_DISABLED_GATEWAY_STATE,
        "deterministic_fixture_pilot_completed": True,
        "external_cognition_contract_available": True,
        "external_cognition_authorization_envelope_available": True,
        "existing_model_gateway_component_binding_available": True,
        "secure_runtime_component_binding_available": True,
        "provider_manifest_available": True,
        "model_manifest_available": True,
        "model_capability_manifest_available": True,
        "request_envelope_available": True,
        "response_envelope_available": True,
        "message_normalization_available": True,
        "structured_output_schema_available": True,
        "structured_output_validation_available": True,
        "model_route_policy_available": True,
        "capability_based_routing_available": True,
        "context_budget_available": True,
        "output_budget_available": True,
        "cost_budget_available": True,
        "latency_budget_available": True,
        "retry_policy_available": True,
        "circuit_breaker_policy_available": True,
        "response_trust_classification_available": True,
        "uncertainty_projection_available": True,
        "provider_error_normalization_available": True,
        "prompt_redaction_available": True,
        "response_redaction_available": True,
        "prompt_fingerprint_available": True,
        "response_fingerprint_available": True,
        "deterministic_fixture_provider_available": True,
        "deterministic_replay_available": True,
        "changed_replay_rejection_available": True,
        "audit_evidence_available": True,
        "observability_schema_available": True,
        "operator_review_record_available": True,
        "external_cognition_integrity_audit_available": True,
    }.items():
        if program.get(key) != value:
            raise SystemExit(f"implemented AION-246 program field mismatch {key}: {program.get(key)!r}")

for key, value in {
    "authorization_transaction_approved": True,
    "explicit_approval_record_approval": True,
    "implementation_authorization_approved": True,
    "implementation_go_status": True,
    "implementation_no_go_status": False,
    "authorization_active": True,
    "authorization_consumed": False,
    "authorization_expired": False,
    "authorization_reusable": False,
}.items():
    if record.get(key) != value:
        raise SystemExit(f"authorization lifecycle mismatch {key}: {record.get(key)!r}")

if state == PRE_IMPLEMENTATION_STATE:
    for path in FUTURE_SOURCE:
        if (ROOT / path).exists():
            raise SystemExit(f"AION-246 source exists before implementation: {path}")
else:
    for path in FUTURE_SOURCE:
        if not (ROOT / path).is_file():
            raise SystemExit(f"AION-246 source missing after implementation: {path}")

for relative in (
    "examples/adaptive-intelligence/program-authorization.json",
    "examples/adaptive-intelligence/program-roadmap.json",
    "examples/adaptive-intelligence/external-cognition-foundation-authorization.json",
    "examples/adaptive-intelligence/runtime-hold.json",
    "examples/adaptive-intelligence/external-cognition-runtime-hold.json",
    "examples/adaptive-intelligence/external-cognition-contract-examples.json",
    "operator-console-static/demo-data/adaptive-intelligence-program.json",
    "operator-console-static/demo-data/external-cognition-authorization.json",
    "operator-console-static/demo-data/adaptive-intelligence-runtime-hold.json",
    "operator-console-static/demo-data/external-cognition-foundation.json",
    "operator-console-static/demo-data/external-cognition-static-console-evidence.json",
):
    if not (ROOT / relative).is_file():
        raise SystemExit(f"missing adaptive intelligence artifact: {relative}")

if state == IMPLEMENTED_DISABLED_STATE:
    if not (ROOT / "examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json").is_file():
        raise SystemExit("missing AION-246 committed fixture pilot evidence")

print("adaptive intelligence programme authorization PASS")
PY
