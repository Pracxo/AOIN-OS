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

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
PROGRAM_ID = "AION-ADAPTIVE-INTELLIGENCE-001"
A245 = "AION-245-AI-0001"
A247 = "AION-247-AI-0002"
PRE_IMPLEMENTATION_STATE = "adaptive_intelligence_program_authorized_not_implemented"
IMPLEMENTED_DISABLED_STATE = (
    "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout"
)
POST_EVALUATION_STATE = (
    "external_cognition_foundation_evaluated_live_provider_pilot_authorized_not_implemented"
)
IMPLEMENTED_GATEWAY_STATES = {
    "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout",
    "implemented_disabled_deterministic_fixture_only_operator_evaluated_live_provider_pilot_authorized_not_implemented",
}
ROADMAP = [f"AION-{number}" for number in range(245, 261)]
FOUNDATION_APPROVED = {
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
FOUNDATION_PROHIBITED = {
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


def find_record(ledger: dict, auth_id: str) -> dict:
    for record in ledger.get("records", []):
        if record.get("authorization_transaction_id") == auth_id:
            return record
    raise SystemExit(f"authorization record missing: {auth_id}")


program = load("docs/adaptive-intelligence/program-ledger.json")
auth = load("docs/adaptive-intelligence/authorization-ledger.json")
a245_record = find_record(auth, A245)
state = program.get("program_state")
if state not in {PRE_IMPLEMENTATION_STATE, IMPLEMENTED_DISABLED_STATE, POST_EVALUATION_STATE}:
    raise SystemExit(f"program state mismatch: {state!r}")
if program["program_id"] != PROGRAM_ID or auth["program_id"] != PROGRAM_ID:
    raise SystemExit("programme ID mismatch")
if [item["task_id"] for item in program["roadmap"]] != ROADMAP:
    raise SystemExit("roadmap sequence mismatch")
if not FOUNDATION_APPROVED.issubset(program["approved_capabilities"]):
    raise SystemExit("foundation approved capabilities missing from program")
if not FOUNDATION_APPROVED.issubset(a245_record["approved_capabilities"]):
    raise SystemExit("foundation approved capabilities missing from AION-245")
if any(value is not True for value in program["approved_capabilities"].values()):
    raise SystemExit("program approved capability is not true")
if any(value is not True for value in a245_record["approved_capabilities"].values()):
    raise SystemExit("AION-245 approved capability is not true")
for payload_name, payload in (("program", program), ("AION-245", a245_record)):
    for key in FOUNDATION_PROHIBITED:
        if payload["prohibited_capabilities"].get(key) is not False:
            raise SystemExit(f"{payload_name} prohibited capability enabled: {key}")
    if any(value is not False for value in payload["prohibited_capabilities"].values()):
        raise SystemExit(f"{payload_name} prohibited capability is not false")
if program["resource_limits"] != RESOURCE_LIMITS:
    raise SystemExit("foundation resource limits changed")

if state == PRE_IMPLEMENTATION_STATE:
    expected = {
        "active_adaptive_intelligence_authorization": A245,
        "active_adaptive_intelligence_task": "AION-246",
        "formal_closeout_task": "AION-247",
        "external_cognition_gateway_implemented": False,
    }
elif state == IMPLEMENTED_DISABLED_STATE:
    expected = {
        "active_adaptive_intelligence_authorization": A245,
        "active_adaptive_intelligence_task": "AION-246",
        "formal_closeout_task": "AION-247",
        "external_cognition_gateway_implemented": True,
    }
else:
    expected = {
        "active_adaptive_intelligence_authorization": A247,
        "active_adaptive_intelligence_task": "AION-248",
        "formal_closeout_task": "AION-249",
        "external_cognition_gateway_implemented": True,
        "live_provider_pilot_authorized": True,
        "live_provider_pilot_implemented": False,
    }
for key, value in {
    "adaptive_intelligence_program_authorized": True,
    "adaptive_intelligence_program_implemented": False,
    "active_adaptive_intelligence_authorization_count": 1,
    "final_planned_task": "AION-260",
    "external_cognition_gateway_authorized": True,
    "production_runtime_authorized": False,
    **expected,
}.items():
    if program.get(key) != value:
        raise SystemExit(f"program field mismatch {key}: {program.get(key)!r}")

if program.get("external_cognition_gateway_implemented") is True:
    if program.get("external_cognition_gateway_state") not in IMPLEMENTED_GATEWAY_STATES:
        raise SystemExit("external cognition gateway state mismatch")
    for path in FUTURE_SOURCE:
        if not (ROOT / path).is_file():
            raise SystemExit(f"AION-246 source missing after implementation: {path}")
else:
    for path in FUTURE_SOURCE:
        if (ROOT / path).exists():
            raise SystemExit(f"AION-246 source exists before implementation: {path}")

if state == POST_EVALUATION_STATE:
    if a245_record.get("authorization_active") is not False:
        raise SystemExit("AION-245 must be inactive after AION-247")
    if a245_record.get("authorization_consumed") is not True:
        raise SystemExit("AION-245 must be consumed after AION-247")
    if a245_record.get("authorization_expired") is not True:
        raise SystemExit("AION-245 must be expired after AION-247")
    if a245_record.get("authorization_reusable") is not False:
        raise SystemExit("AION-245 must remain non-reusable")
    successor = find_record(auth, A247)
    for key, value in {
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
        "implementation_task": "AION-248",
        "formal_closeout_task": "AION-249",
        "provider_id": "openai",
        "provider_api_family": "responses",
        "allowed_endpoint_host": "api.openai.com",
        "allowed_endpoint_path": "/v1/responses",
        "maximum_selected_models": 1,
    }.items():
        if successor.get(key) != value:
            raise SystemExit(f"AION-247 authorization mismatch {key}: {successor.get(key)!r}")
    if not successor["approved_capabilities"].get("openai_responses_api_adapter_approved"):
        raise SystemExit("OpenAI Responses API adapter approval missing")
    if any(value is not False for value in successor["prohibited_capabilities"].values()):
        raise SystemExit("AION-247 prohibited capability is not false")
else:
    for key, value in {
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
    }.items():
        if a245_record.get(key) != value:
            raise SystemExit(f"AION-245 lifecycle mismatch {key}: {a245_record.get(key)!r}")

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

print("adaptive intelligence programme authorization PASS")
PY
