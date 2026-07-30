#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from aion_brain.contracts.secure_runtime import secure_runtime_fingerprint

root = Path(os.environ["AION_REPO_ROOT"])
path = root / "examples/secure-runtime-integration/local-operator-runtime-pilot-evidence.json"
payload = json.loads(path.read_text(encoding="utf-8"))

expected_zero = (
    "actual_capability_executions",
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
expected_one = (
    "identity_assertions_verified",
    "replay_claims_created",
    "exact_replays_rejected",
    "request_identity_bindings",
    "actor_context_bindings",
    "sessions_started",
    "sessions_closed",
    "requests_processed",
    "capability_plans_created",
    "policy_bindings",
    "risk_bindings",
    "guardrail_bindings",
    "approval_bundles_validated",
    "runtime_guard_allow_simulation_decisions",
    "simulated_dispatches",
    "checkpoint_count",
)

assert payload["pilot_id"] == "AION-231-controlled-local-operator-runtime-pilot"
assert payload["authorization_id"] == "AION-230-SRI-0001"
assert payload["mode"] == "operator_invoked_local"
assert payload["active_sessions_after_close"] == 0
assert payload["active_requests_after_close"] == 0
assert payload["temporary_files_retained"] == 0
assert payload["integrity_passed"] is True
assert payload["redacted"] is True
assert payload["production_effect"] is False
assert payload["runtime_effect"] is False
assert payload["stage_receipts"] >= 1
assert payload["audit_records"] >= 1
assert payload["kill_switch_checks"] >= 3
for key in expected_one:
    assert payload[key] == 1, key
for key in expected_zero:
    assert payload[key] == 0, key
assert payload["production_exposure"] is False

fingerprint_payload = dict(payload)
report_fingerprint = fingerprint_payload.pop("report_fingerprint")
assert report_fingerprint == secure_runtime_fingerprint(fingerprint_payload)

blocked_text = json.dumps(payload, sort_keys=True).lower()
for marker in (
    "private_key",
    "signature",
    "assertion_payload",
    "raw_actor",
    "approval_payload",
    "approval_reason",
    "request_body",
    "cookie",
    "prompt",
    "hidden_reasoning",
    "/tmp/",
):
    assert marker not in blocked_text, marker
PY

echo "secure runtime foundation pilot evidence PASS"
