#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from secure_runtime_integration_final_evaluation import (
    AUTHORIZATION_ID,
    CLOSEOUT_TASK,
    EVALUATION_ID,
    FAIL_DECISION,
    IMPLEMENTATION_FEATURE_COMMIT,
    IMPLEMENTATION_MERGE_COMMIT,
    IMPLEMENTATION_PR,
    IMPLEMENTATION_TASK,
    PASS_DECISION,
    validate_report,
)

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads(
    (root / "docs/secure-runtime-integration/program-ledger.json").read_text(
        encoding="utf-8"
    )
)
auth = json.loads(
    (root / "docs/secure-runtime-integration/authorization-ledger.json").read_text(
        encoding="utf-8"
    )
)
report = json.loads(
    (
        root
        / "examples/secure-runtime-integration/"
        / "secure-runtime-integration-final-evaluation-report.json"
    ).read_text(encoding="utf-8")
)

validate_report(report)
if report.get("decision") != PASS_DECISION:
    raise SystemExit(f"final SRI decision is not PASS: {report.get('decision')!r}")
if report.get("scenario_count") != 28:
    raise SystemExit("final SRI evaluation did not execute 28 scenarios")
if any(value != "pass" for value in report.get("scenario_results", {}).values()):
    raise SystemExit("final SRI evaluation has a failed scenario")
if not all(report.get("hard_gate_results", {}).values()):
    raise SystemExit("final SRI evaluation has a failed hard gate")

required_program = {
    "program_id": "AION-SECURE-RUNTIME-INTEGRATION-001",
    "program_state": "secure_runtime_integration_program_complete",
    "secure_runtime_integration_program_complete": True,
    "secure_runtime_integration_final_evaluation_passed": True,
    "secure_runtime_integration_final_evaluation_id": EVALUATION_ID,
    "secure_runtime_integration_final_evaluation_decision": PASS_DECISION,
    "final_completed_task": CLOSEOUT_TASK,
    "active_sri_implementation_authorization_count": 0,
    "active_sri_implementation_authorization": None,
    "active_sri_implementation_task": None,
    "formal_closeout_task": None,
    "next_sri_implementation_task": None,
    "production_runtime_authorized": False,
    "public_listener_enabled": False,
    "external_network_egress_enabled": False,
    "actual_model_provider_call_enabled": False,
    "external_connector_execution_enabled": False,
    "external_tool_execution_enabled": False,
    "production_deployment_enabled": False,
    "production_exposure": False,
    "v02_release_ready": False,
    "v02_tag_created": False,
    "v02_release_created": False,
}
for label, payload in (("program", program), ("authorization", auth)):
    for key, expected in required_program.items():
        if payload.get(key) != expected:
            raise SystemExit(f"{label} mismatch {key}: {payload.get(key)!r}")

if auth.get("active_authorizations") != []:
    raise SystemExit("SRI active authorization list is not empty")
records = auth.get("records", [])
if any(item.get("authorization_active") is True for item in records):
    raise SystemExit("an SRI authorization remains active")
closed = next(
    item for item in records if item.get("authorization_transaction_id") == AUTHORIZATION_ID
)
required_closeout = {
    "approval_record_id": AUTHORIZATION_ID,
    "authorization_active": False,
    "authorization_consumed": True,
    "authorization_consumed_by_task": IMPLEMENTATION_TASK,
    "authorization_consumed_by_prs": [IMPLEMENTATION_PR],
    "authorization_consumed_by_feature_commits": [IMPLEMENTATION_FEATURE_COMMIT],
    "authorization_consumed_by_merge_commits": [IMPLEMENTATION_MERGE_COMMIT],
    "authorization_expired": True,
    "authorization_reusable": False,
    "authorization_closed_by_task": CLOSEOUT_TASK,
    "final_sri_evaluation_id": EVALUATION_ID,
    "final_sri_evaluation_decision": PASS_DECISION,
    "evaluation_reusable": False,
    "evaluation_used_as_production_runtime_approval": False,
    "evaluation_used_as_public_listener_approval": False,
    "evaluation_used_as_external_egress_approval": False,
    "evaluation_used_as_v02_tag_approval": False,
    "evaluation_used_as_v02_release_approval": False,
}
for key, expected in required_closeout.items():
    if closed.get(key) != expected:
        raise SystemExit(f"SRI closeout mismatch {key}: {closed.get(key)!r}")
if FAIL_DECISION in json.dumps((program, auth), sort_keys=True):
    raise SystemExit("FAIL decision leaked into final PASS state")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "secure runtime integration program complete PASS"
