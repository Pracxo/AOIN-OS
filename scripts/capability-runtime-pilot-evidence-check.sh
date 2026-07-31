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

from aion_brain.contracts.sandboxed_capability_runtime import (
    PROHIBITED_EFFECT_COUNTERS,
    AUTHORIZATION_TRANSACTION_ID,
    capability_runtime_fingerprint,
)

ROOT = Path(os.environ["AION_REPO_ROOT"])
path = ROOT / "examples/secure-runtime-integration/capability-runtime-local-sandbox-pilot-evidence.json"
payload = json.loads(path.read_text(encoding="utf-8"))
expected = {
    "pilot_id": "AION-235-controlled-sandboxed-capability-runtime-pilot",
    "authorization_id": AUTHORIZATION_TRANSACTION_ID,
    "mode": "operator-invoked-local",
    "capability_manifest_count": 8,
    "connector_manifest_count": 1,
    "sessions_started": 1,
    "sessions_closed": 1,
    "active_sessions_after_close": 0,
    "requests_processed": 8,
    "active_requests_after_close": 0,
    "operator_selections_validated": 8,
    "policy_bindings": 8,
    "risk_bindings": 8,
    "guardrail_bindings": 8,
    "approval_bundles_validated": 3,
    "budget_decisions_passed": 8,
    "sandbox_allow_decisions": 8,
    "pure_reference_capability_executions": 6,
    "synthetic_reference_connector_simulations": 2,
    "write_previews_created": 1,
    "execution_receipts_created": 8,
    "output_validations_passed": 8,
    "execution_provenance_records": 8,
    "rollback_plans_created": 1,
    "rollbacks_completed": 1,
    "exact_replays_returned": 1,
    "changed_replays_rejected": 1,
    "model_output_triggered_executions_blocked": 1,
    "unknown_capabilities_blocked": 1,
    "schema_invalid_requests_blocked": 1,
    "integrity_passed": True,
    "temporary_files_retained": 0,
    "redacted": True,
    "production_effect": False,
    "runtime_effect": False,
}
for key, value in expected.items():
    if payload.get(key) != value:
        raise SystemExit(f"pilot evidence mismatch for {key}: {payload.get(key)!r}")
if payload["kill_switch_checks"] < 16:
    raise SystemExit("pilot evidence kill-switch checks below required minimum")
if len(payload["capability_manifest_fingerprints"]) != 8:
    raise SystemExit("capability manifest fingerprint count mismatch")
for key in (
    "secure_runtime_component_binding_fingerprint",
    "model_gateway_proposal_binding_fingerprint",
    "connector_manifest_fingerprint",
    "receipt_chain_head",
    "audit_chain_head",
):
    value = payload.get(key)
    if not isinstance(value, str) or len(value) != 64:
        raise SystemExit(f"missing fingerprint field: {key}")
for key in PROHIBITED_EFFECT_COUNTERS:
    if payload.get(key) != 0:
        raise SystemExit(f"prohibited effect counter is non-zero: {key}")
report = dict(payload)
fingerprint = report.pop("report_fingerprint", None)
if fingerprint != capability_runtime_fingerprint(report):
    raise SystemExit("pilot evidence report fingerprint mismatch")
PY

echo "sandboxed capability runtime pilot evidence PASS"
