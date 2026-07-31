#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/model-gateway-no-go-regression.sh
./scripts/model-gateway-pilot-evidence-check.sh
./scripts/model-gateway-authorization-check.sh
./scripts/secure-runtime-foundation-operator-evaluation-check.sh

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_model_gateway_contracts.py \
  services/brain-api/tests/test_model_gateway_authorization.py \
  services/brain-api/tests/test_model_gateway_component_binding.py \
  services/brain-api/tests/test_model_gateway_provider_manifests.py \
  services/brain-api/tests/test_model_gateway_model_manifests.py \
  services/brain-api/tests/test_model_gateway_capability_profiles.py \
  services/brain-api/tests/test_model_gateway_session.py \
  services/brain-api/tests/test_model_gateway_message_normalization.py \
  services/brain-api/tests/test_model_gateway_context_items.py \
  services/brain-api/tests/test_model_gateway_context_budget.py \
  services/brain-api/tests/test_model_gateway_token_budget.py \
  services/brain-api/tests/test_model_gateway_request_envelope.py \
  services/brain-api/tests/test_model_gateway_idempotency.py \
  services/brain-api/tests/test_model_gateway_routing.py \
  services/brain-api/tests/test_model_gateway_fallback_retry.py \
  services/brain-api/tests/test_model_gateway_circuit_breaker.py \
  services/brain-api/tests/test_model_gateway_guard.py \
  services/brain-api/tests/test_model_gateway_reference_provider.py \
  services/brain-api/tests/test_model_gateway_structured_output.py \
  services/brain-api/tests/test_model_gateway_response_validation.py \
  services/brain-api/tests/test_model_gateway_output_provenance.py \
  services/brain-api/tests/test_model_gateway_audit.py \
  services/brain-api/tests/test_model_gateway_observability.py \
  services/brain-api/tests/test_model_gateway_integrity.py \
  services/brain-api/tests/test_model_gateway_redaction.py \
  services/brain-api/tests/test_model_gateway_concurrency.py \
  services/brain-api/tests/test_model_gateway_performance.py \
  services/brain-api/tests/test_model_gateway_pilot_evidence.py \
  services/brain-api/tests/test_model_gateway_aion232_delivery_reconciliation.py \
  services/brain-api/tests/test_model_gateway_current_state_consistency.py \
  services/brain-api/tests/test_model_gateway_source_scope_spec.py \
  -q

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from aion_brain.contracts.model_gateway import (
    AUTHORIZATION_TRANSACTION_ID,
    DETERMINISTIC_PROVIDER_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    LOCAL_MODEL_GATEWAY_CONFIRMATION_TEXT,
    MODEL_GATEWAY_AUTHORIZATION_SCHEMA_VERSION,
    MODEL_GATEWAY_COMPONENT_BINDING_SCHEMA_VERSION,
    MODEL_GATEWAY_CONTRACT_SCHEMA_VERSION,
    MODEL_GATEWAY_EVIDENCE_SCHEMA_VERSION,
    PARENT_CAPABILITY_CODE,
    REFERENCE_JSON_MODEL_ID,
    REFERENCE_TEXT_MODEL_ID,
    TOKEN_ESTIMATOR_VERSION,
    ModelGatewayGuardOutcome,
    ModelProviderType,
)
from aion_brain.model_gateway import (
    ControlledModelGatewayService,
    DeterministicReferenceModelProvider,
    ModelProviderAdapter,
)
from aion_brain.model_gateway.manifests import (
    default_model_manifests,
    deterministic_reference_provider_manifest,
)

ROOT = Path(os.environ["AION_REPO_ROOT"])

PROGRAM_STATES = {
    "controlled_model_gateway_implemented_reference_simulation_only_pending_closeout",
    "model_gateway_evaluated_sandboxed_capability_runtime_authorized_not_implemented",
    "sandboxed_capability_runtime_implemented_reference_only_pending_closeout",
}
POST_CLOSEOUT_STATES = {
    "model_gateway_evaluated_sandboxed_capability_runtime_authorized_not_implemented",
    "sandboxed_capability_runtime_implemented_reference_only_pending_closeout",
}
GATEWAY_STATES = {
    "implemented_provider_neutral_reference_simulation_only_pending_AION-234_closeout",
    "implemented_provider_neutral_reference_simulation_only",
}
SOURCE = [
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
    "services/brain-api/src/aion_brain/model_gateway/provider_registry.py",
    "services/brain-api/src/aion_brain/model_gateway/provider_adapter.py",
    "services/brain-api/src/aion_brain/model_gateway/reference_provider.py",
    "services/brain-api/src/aion_brain/model_gateway/audit.py",
    "services/brain-api/src/aion_brain/model_gateway/observability.py",
    "services/brain-api/src/aion_brain/model_gateway/integrity.py",
    "services/brain-api/src/aion_brain/model_gateway/evidence.py",
]
PROHIBITED = [
    "services/brain-api/src/aion_brain/model_gateway/network.py",
    "services/brain-api/src/aion_brain/model_gateway/live_provider.py",
    "services/brain-api/src/aion_brain/model_gateway/openai.py",
    "services/brain-api/src/aion_brain/model_gateway/anthropic.py",
    "services/brain-api/src/aion_brain/model_gateway/google.py",
    "services/brain-api/src/aion_brain/model_gateway/credential_store.py",
    "services/brain-api/src/aion_brain/model_gateway/token_store.py",
    "services/brain-api/src/aion_brain/model_gateway/tool_runtime.py",
    "services/brain-api/src/aion_brain/model_gateway/connector_runtime.py",
    "services/brain-api/src/aion_brain/model_gateway/background_worker.py",
    "services/brain-api/src/aion_brain/model_gateway/scheduler.py",
]
DOCS = [
    "docs/secure-runtime-integration/model-gateway-implementation.md",
    "docs/secure-runtime-integration/model-gateway-contracts.md",
    "docs/secure-runtime-integration/model-gateway-component-composition.md",
    "docs/secure-runtime-integration/model-gateway-provider-registry.md",
    "docs/secure-runtime-integration/model-gateway-model-registry.md",
    "docs/secure-runtime-integration/model-gateway-session.md",
    "docs/secure-runtime-integration/model-gateway-message-normalization.md",
    "docs/secure-runtime-integration/model-gateway-system-instruction-policy.md",
    "docs/secure-runtime-integration/model-gateway-context-budget-implementation.md",
    "docs/secure-runtime-integration/model-gateway-token-budget-implementation.md",
    "docs/secure-runtime-integration/model-gateway-request-idempotency.md",
    "docs/secure-runtime-integration/model-gateway-routing-implementation.md",
    "docs/secure-runtime-integration/model-gateway-fallback-retry-implementation.md",
    "docs/secure-runtime-integration/model-gateway-circuit-breaker-implementation.md",
    "docs/secure-runtime-integration/model-gateway-guard-implementation.md",
    "docs/secure-runtime-integration/model-gateway-reference-provider.md",
    "docs/secure-runtime-integration/model-gateway-structured-output-implementation.md",
    "docs/secure-runtime-integration/model-gateway-response-validation-implementation.md",
    "docs/secure-runtime-integration/model-gateway-output-provenance-implementation.md",
    "docs/secure-runtime-integration/model-gateway-audit-implementation.md",
    "docs/secure-runtime-integration/model-gateway-observability-implementation.md",
    "docs/secure-runtime-integration/model-gateway-integrity-implementation.md",
    "docs/secure-runtime-integration/model-gateway-security-review.md",
    "docs/secure-runtime-integration/model-gateway-operator-runbook.md",
    "docs/secure-runtime-integration/model-gateway-local-simulation-pilot.md",
    "docs/secure-runtime-integration/aion-233-checklist.md",
    "docs/release/model-gateway-implementation.md",
    "docs/release/model-gateway-security-evidence.md",
    "docs/release/model-gateway-local-simulation-pilot.md",
    "docs/release/model-gateway-runtime-hold.md",
    "docs/release/model-gateway-no-go.md",
    "docs/release/model-gateway-checklist.md",
    "docs/release/model-gateway-evidence-matrix.md",
    "docs/adr/0197-controlled-provider-neutral-model-gateway-and-deterministic-reference-provider.md",
]


def load(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


for path in SOURCE + DOCS + [
    "scripts/model-gateway-local-simulation-run.py",
    "scripts/model-gateway-check.sh",
    "scripts/model-gateway-no-go-regression.sh",
    "scripts/model-gateway-pilot-evidence-check.sh",
    "examples/secure-runtime-integration/model-gateway-contract-examples.json",
    "examples/secure-runtime-integration/model-gateway-static-console-evidence.json",
    "examples/secure-runtime-integration/model-gateway-local-simulation-pilot-evidence.json",
    "operator-console-static/demo-data/model-gateway-static-console-evidence.json",
]:
    if not (ROOT / path).exists():
        raise SystemExit(f"required AION-233 artifact missing: {path}")
for path in PROHIBITED:
    if (ROOT / path).exists():
        raise SystemExit(f"prohibited AION-233 runtime surface exists: {path}")

program = load("docs/secure-runtime-integration/program-ledger.json")
auth = load("docs/secure-runtime-integration/authorization-ledger.json")
pilot = load("examples/secure-runtime-integration/model-gateway-local-simulation-pilot-evidence.json")
contract_examples = load("examples/secure-runtime-integration/model-gateway-contract-examples.json")
static_evidence = load("examples/secure-runtime-integration/model-gateway-static-console-evidence.json")

assert AUTHORIZATION_TRANSACTION_ID == "AION-232-SRI-0002"
assert IMPLEMENTATION_TASK == "AION-233"
assert FORMAL_CLOSEOUT_TASK == "AION-234"
assert PARENT_CAPABILITY_CODE == "brain.think.simulate"
assert DETERMINISTIC_PROVIDER_ID == "deterministic-reference-provider"
assert REFERENCE_TEXT_MODEL_ID == "reference-text-sim-v1"
assert REFERENCE_JSON_MODEL_ID == "reference-json-sim-v1"
assert LOCAL_MODEL_GATEWAY_CONFIRMATION_TEXT == "RUN_CONTROLLED_MODEL_GATEWAY_SIMULATION"
assert TOKEN_ESTIMATOR_VERSION == "utf8-ceil-div-3/v1"
assert MODEL_GATEWAY_CONTRACT_SCHEMA_VERSION == "aion-model-gateway/v1"
assert MODEL_GATEWAY_AUTHORIZATION_SCHEMA_VERSION == "aion-model-gateway-authorization/v1"
assert MODEL_GATEWAY_COMPONENT_BINDING_SCHEMA_VERSION == "aion-model-gateway-component-binding/v1"
assert MODEL_GATEWAY_EVIDENCE_SCHEMA_VERSION == "aion-model-gateway-evidence/v1"
assert ModelProviderType.reference_simulation.value == "reference_simulation"
assert ModelGatewayGuardOutcome.allow_reference_simulation.value == "allow_reference_simulation"

provider = deterministic_reference_provider_manifest()
models = default_model_manifests()
if provider.provider_id != DETERMINISTIC_PROVIDER_ID:
    raise SystemExit("provider manifest registry mismatch")
if {model.model_id for model in models} != {REFERENCE_TEXT_MODEL_ID, REFERENCE_JSON_MODEL_ID}:
    raise SystemExit("model manifest registry mismatch")
if DeterministicReferenceModelProvider().validate_adapter_state() is not True:
    raise SystemExit("reference provider adapter state mismatch")
for forbidden_method in (
    "send",
    "call",
    "connect",
    "stream",
    "authenticate",
    "load_credentials",
    "create_authorization_header",
    "invoke_tool",
    "invoke_function",
):
    if hasattr(ModelProviderAdapter, forbidden_method) or hasattr(ControlledModelGatewayService, forbidden_method):
        raise SystemExit(f"forbidden provider-adapter method exposed: {forbidden_method}")
for required_method in (
    "validate_authorization",
    "bind_secure_runtime_component",
    "load_provider_manifests",
    "load_model_manifests",
    "create_session_plan",
    "start_session",
    "normalize_messages",
    "normalize_context",
    "evaluate_context_budget",
    "evaluate_token_budget",
    "build_request_envelope",
    "check_request_idempotency",
    "plan_route",
    "plan_fallback",
    "plan_retry",
    "evaluate_circuit_breaker",
    "evaluate_guard",
    "simulate_reference_provider",
    "validate_response",
    "classify_untrusted_output",
    "build_output_provenance",
    "record_audit",
    "observability_snapshot",
    "health_snapshot",
    "audit_integrity",
    "replay_fixture",
    "close_request",
    "close_session",
    "reject_live_provider_call",
    "reject_external_effect",
):
    if not hasattr(ControlledModelGatewayService, required_method):
        raise SystemExit(f"gateway service method missing: {required_method}")

for payload in (program, auth):
    post_closeout = payload["program_state"] in POST_CLOSEOUT_STATES
    if payload["program_state"] not in PROGRAM_STATES:
        raise SystemExit("program state mismatch")
    if payload["model_gateway_authorized"] is not True or payload["model_gateway_implemented"] is not True:
        raise SystemExit("model gateway authorization/implementation mismatch")
    if payload["model_gateway_state"] not in GATEWAY_STATES:
        raise SystemExit("model gateway state mismatch")
    if not all(payload["model_gateway_authorized_capabilities"].values()):
        raise SystemExit("not every gateway capability is available")
    if any(payload["model_gateway_prohibited_capabilities"].values()):
        raise SystemExit("prohibited gateway capability enabled")
    if payload["active_sri_implementation_authorization_count"] != 1:
        raise SystemExit("there must be exactly one active SRI authorization")
    expected_auth = "AION-234-SRI-0003" if post_closeout else "AION-232-SRI-0002"
    expected_task = "AION-235" if post_closeout else "AION-233"
    expected_closeout = "AION-236" if post_closeout else "AION-234"
    if payload["active_sri_implementation_authorization"] != expected_auth:
        raise SystemExit("active SRI authorization mismatch")
    if payload["active_sri_implementation_task"] != expected_task:
        raise SystemExit("active SRI task mismatch")
    if payload["formal_closeout_task"] != expected_closeout:
        raise SystemExit("formal closeout task mismatch")
    for key in (
        "actual_model_provider_call_enabled",
        "provider_network_egress_enabled",
        "provider_credential_read_enabled",
        "provider_credential_persistence_enabled",
        "api_key_persistence_enabled",
        "token_persistence_enabled",
        "authorization_header_creation_enabled",
        "live_model_session_enabled",
        "tool_calling_enabled",
        "function_calling_enabled",
        "connector_execution_enabled",
        "prompt_persistence_enabled",
        "model_response_persistence_enabled",
        "hidden_reasoning_retention_enabled",
        "provider_raw_payload_retention_enabled",
        "production_memory_write_enabled",
        "production_policy_mutation_enabled",
        "actual_belief_creation_enabled",
        "actual_belief_mutation_enabled",
        "production_deployment_enabled",
        "model_weight_training_enabled",
        "production_exposure",
        "v02_release_ready",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload[key] is not False:
            raise SystemExit(f"runtime boundary flag must remain false: {key}")

if program["secure_runtime_integration_program_authorized"] is not True:
    raise SystemExit("SRI program must remain authorized")
if program["secure_runtime_foundation_implemented"] is not True:
    raise SystemExit("AION-231 foundation must remain implemented")
if program["secure_runtime_foundation_operator_evaluation_passed"] is not True:
    raise SystemExit("AION-232 evaluation pass must remain recorded")

record = program["aion_233_record"]
if record["task_id"] != "AION-233" or record["branch"] != "phase/controlled-model-gateway":
    raise SystemExit("AION-233 record identity mismatch")
if program["program_state"] in POST_CLOSEOUT_STATES:
    if record["feature_commits"] != [
        "39b886614fa8d6961492c1c076dd25d7eb16f5f5",
        "9612d9d7455a7e504cd5def5ae71f7fe6bb9fa65",
        "86a39a5fe92c1eade97b82d35fcd53a5e2379b8c",
        "d268b56cb4c52458e3927c9f87bd88c099f162f6",
        "10de8fadb9cf3eb689e653a007d5e8ce3516e860",
        "e2a4a8056d14b2f38d086fa50c8a3f93052465be",
    ]:
        raise SystemExit("AION-233 feature commits mismatch")
    if record["pull_requests"] != [151, 152]:
        raise SystemExit("AION-233 PR reconciliation mismatch")
    if record["merge_commits"] != [
        "555459ab86f714ccaa0a05e60d306fa3cc61c043",
        "48e9daebcac77aa48aa2336323c40eae948f3ac2",
    ]:
        raise SystemExit("AION-233 merge reconciliation mismatch")
    if record["ci_result"] != "pass" or record["completion_timestamp"] != "2026-07-31T14:54:41Z":
        raise SystemExit("AION-233 completion fields mismatch")
    if record["authorization_state"] != "consumed_by_AION-233_closed_by_AION-234":
        raise SystemExit("AION-233 authorization state mismatch")
else:
    if record["feature_commits"] or record["pull_requests"] or record["merge_commits"]:
        raise SystemExit("AION-233 Git delivery fields must remain pending for AION-234")
    if record["ci_result"] != "pending" or record["completion_timestamp"] is not None:
        raise SystemExit("AION-233 completion fields must remain pending for AION-234")
    if record["authorization_state"] != "implementation_complete_pending_AION-234_closeout":
        raise SystemExit("AION-233 authorization state mismatch")

if pilot["report_fingerprint"] != "d911ecc911b0f5833770629eb77fdfb42e6718c80c894984fb43f0e0a11d0982":
    raise SystemExit("pilot report fingerprint mismatch")
if contract_examples["contracts"]["provider_manifest"]["provider_id"] != DETERMINISTIC_PROVIDER_ID:
    raise SystemExit("contract example provider mismatch")
if static_evidence["temporary_files_retained"] != 0 or static_evidence["redacted"] is not True:
    raise SystemExit("static evidence must be redacted with zero retained temporary files")

pyproject = (ROOT / "services/brain-api/pyproject.toml").read_text(encoding="utf-8")
if "model-gateway-local-simulation-run" in pyproject:
    raise SystemExit("runner must not be installed as a CLI entry point")
PY

echo "controlled model gateway PASS"
