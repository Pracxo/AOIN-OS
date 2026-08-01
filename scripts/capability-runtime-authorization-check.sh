#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/capability-runtime-authorization-no-go-regression.sh
"$PYTHON_BIN" scripts/lib/model_gateway_operator_evaluation.py --validate-report examples/secure-runtime-integration/model-gateway-operator-evaluation-report.json
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
spec = importlib.util.spec_from_file_location(
    "aion234_eval",
    ROOT / "scripts/lib/model_gateway_operator_evaluation.py",
)
h = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = h
assert spec.loader is not None
spec.loader.exec_module(h)

program = json.loads((ROOT / "docs/secure-runtime-integration/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((ROOT / "docs/secure-runtime-integration/authorization-ledger.json").read_text(encoding="utf-8"))
example = json.loads((ROOT / "examples/secure-runtime-integration/capability-runtime-authorization.json").read_text(encoding="utf-8"))
report = json.loads((ROOT / "examples/secure-runtime-integration/model-gateway-operator-evaluation-report.json").read_text(encoding="utf-8"))
expected_scope = "authenticated-local-untrusted-model-output-bound-explicit-operator-capability-plan-closed-capability-connector-manifest-schema-validated-in-memory-sandbox-deterministic-reference-execution-policy-risk-guardrail-approval-budget-kill-switch-audit-provenance-rollback-no-external-effect-core"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


require(report["decision"] == h.DECISION_PASS and report["evaluation_passed"] is True, "operator evaluation did not pass")
require(len(report["scenario_results"]) == 28 and all(item["passed"] is True for item in report["scenario_results"]), "scenario failure")
require(all(item["passed"] is True for item in report["hard_gate_results"]), "hard gate failure")
closed = next(item for item in auth["records"] if item.get("authorization_transaction_id") == h.CURRENT_AUTHORIZATION_ID)
require(closed["authorization_active"] is False and closed["authorization_consumed"] is True and closed["authorization_expired"] is True and closed["authorization_reusable"] is False, "AION-232 closeout mismatch")
require(closed["authorization_consumed_by_task"] == h.IMPLEMENTATION_TASK and closed["authorization_closed_by_task"] == h.CLOSEOUT_TASK, "AION-232 lineage mismatch")

capability_authorization = next(
    item
    for item in auth["records"]
    if item.get("authorization_transaction_id") == h.NEXT_AUTHORIZATION_ID
)
for payload in (capability_authorization, example):
    require(payload["authorization_transaction_id"] == h.NEXT_AUTHORIZATION_ID, "auth id mismatch")
    require(payload["implementation_task"] == h.NEXT_IMPLEMENTATION_TASK and payload["formal_closeout_task"] == h.NEXT_CLOSEOUT_TASK, "task mismatch")
    require(payload["authorization_scope"] == expected_scope, "scope mismatch")
    if payload["authorization_active"] is True:
        require(payload["authorization_consumed"] is False and payload["authorization_expired"] is False and payload["authorization_reusable"] is False, "active auth state mismatch")
    else:
        require(payload["authorization_consumed"] is True and payload["authorization_expired"] is True and payload["authorization_reusable"] is False, "closed auth state mismatch")
        require(payload["authorization_consumed_by_task"] == h.NEXT_IMPLEMENTATION_TASK and payload["authorization_closed_by_task"] == h.NEXT_CLOSEOUT_TASK, "closed auth lineage mismatch")

for payload in (program, auth, example):
    runtime_authorized = payload.get(
        "sandboxed_capability_runtime_authorized",
        payload.get("capability_runtime_authorized"),
    )
    runtime_implemented = payload.get(
        "sandboxed_capability_runtime_implemented",
        payload.get("capability_runtime_implemented"),
    )
    require(runtime_authorized is True, "capability runtime not authorized")
    require(runtime_implemented is True, "capability runtime not implemented")
    authorized = payload.get("capability_runtime_authorized_capabilities") or payload.get("authorized_capabilities")
    prohibited = payload.get("capability_runtime_prohibited_capabilities") or payload.get("prohibited_capabilities")
    limits = payload.get("capability_runtime_resource_limits") or payload.get("resource_limits")
    require(set(authorized) == set(h.AUTHORIZED_CAPABILITY_FLAGS) and all(authorized[key] is True for key in h.AUTHORIZED_CAPABILITY_FLAGS), "authorized flags mismatch")
    require(set(prohibited) == set(h.PROHIBITED_CAPABILITY_FLAGS) and all(prohibited[key] is False for key in h.PROHIBITED_CAPABILITY_FLAGS), "prohibited flags mismatch")
    expected_limits = dict(h.CAPABILITY_RESOURCE_LIMITS)
    for key in h.CAPABILITY_ZERO_RESOURCE_LIMITS:
        expected_limits[key] = 0
    require(limits == expected_limits, "resource limits mismatch")
active_authorizations = auth["active_authorizations"]
legacy_active = [{
    "authorization_active": True,
    "authorization_consumed": False,
    "authorization_expired": False,
    "authorization_reusable": False,
    "authorization_transaction_id": h.NEXT_AUTHORIZATION_ID,
    "formal_closeout_task": h.NEXT_CLOSEOUT_TASK,
    "implementation_task": h.NEXT_IMPLEMENTATION_TASK,
}]
post_aion236_active = [{
    "authorization_active": True,
    "authorization_consumed": False,
    "authorization_expired": False,
    "authorization_reusable": False,
    "authorization_transaction_id": "AION-236-SRI-0004",
    "formal_closeout_task": "AION-238",
    "implementation_task": "AION-237",
}]
require(active_authorizations in (legacy_active, post_aion236_active), "active authorization list mismatch")
require(program["aion_234_record"]["ci_result"] == "pass", "AION-234 record is not reconciled")
require(
    program["aion_235_record"]["authorization_state"]
    in {
        "implementation_complete_pending_AION-236_closeout",
        "consumed_by_AION-235_closed_by_AION-236",
    },
    "AION-235 record state mismatch",
)
PY

echo "sandboxed capability runtime authorization PASS"
