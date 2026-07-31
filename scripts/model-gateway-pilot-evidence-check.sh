#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from aion_brain.contracts.model_gateway import model_gateway_fingerprint

ROOT = Path(os.environ["AION_REPO_ROOT"])
EVIDENCE = ROOT / "examples/secure-runtime-integration/model-gateway-local-simulation-pilot-evidence.json"
payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))

expected_fingerprint = model_gateway_fingerprint(
    {key: value for key, value in payload.items() if key != "report_fingerprint"}
)
if payload["report_fingerprint"] != expected_fingerprint:
    raise SystemExit("pilot evidence report fingerprint mismatch")

required_exact = {
    "pilot_id": "AION-233-controlled-model-gateway-simulation-pilot",
    "authorization_id": "AION-232-SRI-0002",
    "mode": "deterministic-simulation",
    "provider_manifest_count": 1,
    "model_manifest_count": 2,
    "gateway_sessions_started": 1,
    "gateway_sessions_closed": 1,
    "active_gateway_sessions_after_close": 0,
    "requests_processed": 2,
    "active_requests_after_close": 0,
    "text_simulation_requests": 1,
    "structured_simulation_requests": 1,
    "context_budget_decisions_passed": 2,
    "token_budget_decisions_passed": 2,
    "routing_plans_created": 2,
    "retry_plans_created": 2,
    "automatic_retries_executed": 0,
    "automatic_fallbacks_executed": 0,
    "reference_provider_simulations": 2,
    "response_validations_passed": 2,
    "untrusted_outputs_classified": 2,
    "output_provenance_records": 2,
    "exact_replays_returned": 1,
    "changed_replays_rejected": 1,
    "protected_material_requests_blocked": 1,
    "temporary_files_retained": 0,
    "integrity_passed": True,
    "redacted": True,
    "production_effect": False,
    "runtime_effect": False,
}
for key, expected in required_exact.items():
    if payload.get(key) != expected:
        raise SystemExit(f"pilot evidence mismatch: {key}")

if payload["fallback_plans_created"] < 1:
    raise SystemExit("pilot evidence must include at least one fallback plan")
if payload["circuit_breaker_checks"] < 2:
    raise SystemExit("pilot evidence must include at least two circuit checks")
if payload["smuggled_action_outputs_blocked"] < 1:
    raise SystemExit("pilot evidence must include smuggled action rejection")
if len(payload["provider_manifest_fingerprints"]) != 1:
    raise SystemExit("provider manifest fingerprint count mismatch")
if len(payload["model_manifest_fingerprints"]) != 2:
    raise SystemExit("model manifest fingerprint count mismatch")
if not isinstance(payload["audit_chain_head"], str) or len(payload["audit_chain_head"]) != 64:
    raise SystemExit("audit chain head must be a SHA-256 fingerprint")

for key in (
    "actual_model_provider_calls",
    "network_calls",
    "provider_sdk_calls",
    "provider_credentials_read",
    "provider_credentials_persisted",
    "authorization_headers_created",
    "live_model_sessions",
    "tool_calls",
    "function_calls",
    "connector_calls",
    "actual_tool_executions",
    "prompts_persisted",
    "model_responses_persisted",
    "hidden_reasoning_records",
    "provider_raw_payloads_retained",
    "cross_session_context_records",
    "production_memory_writes",
    "production_policy_mutations",
    "cognitive_memory_writes",
    "belief_creations",
    "belief_mutations",
    "source_mutations",
    "git_operations",
    "deployments",
    "model_weight_changes",
):
    if payload.get(key) != 0:
        raise SystemExit(f"prohibited pilot counter must be zero: {key}")
if payload["production_exposure"] is not False:
    raise SystemExit("production exposure must remain false")

serialized = json.dumps(payload, sort_keys=True).lower()
for marker in (
    "raw_prompt",
    "raw_response",
    "chain_of_thought",
    "api_key",
    "bearer ",
    "sk-",
    "temporary-root",
):
    if marker in serialized:
        raise SystemExit(f"pilot evidence contains prohibited marker: {marker}")
PY

echo "controlled model gateway pilot evidence PASS"
