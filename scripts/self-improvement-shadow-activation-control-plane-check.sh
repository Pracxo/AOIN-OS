#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib
import json
from pathlib import Path

ROOT = Path.cwd()
importlib.import_module("pytest")
importlib.import_module("pydantic")

required_json = [
    "examples/self-improvement/shadow-activation-control-plane-candidate.json",
    "examples/self-improvement/shadow-activation-control-plane-request.json",
    "examples/self-improvement/shadow-activation-control-plane-approval-binding.json",
    "examples/self-improvement/shadow-activation-control-plane-current-facts.json",
    "examples/self-improvement/shadow-activation-control-plane-budget-decision.json",
    "examples/self-improvement/shadow-activation-control-plane-monitoring-plan.json",
    "examples/self-improvement/shadow-activation-control-plane-health-snapshot.json",
    "examples/self-improvement/shadow-activation-control-plane-deactivation-plan.json",
    "examples/self-improvement/shadow-activation-control-plane-incident.json",
    "examples/self-improvement/shadow-activation-control-plane-simulation-pass.json",
    "examples/self-improvement/shadow-activation-control-plane-simulation-fail.json",
    "examples/self-improvement/shadow-activation-control-plane-operator-review-item.json",
    "examples/self-improvement/shadow-activation-control-plane-runtime-hold.json",
    "operator-console-static/demo-data/self-improvement-shadow-activation-control-plane.json",
    "operator-console-static/demo-data/self-improvement-shadow-activation-simulation.json",
    "operator-console-static/demo-data/self-improvement-shadow-activation-runtime-hold.json",
]
for relative in required_json:
    payload = json.loads((ROOT / relative).read_text())
    if payload.get("synthetic") is not True:
        raise SystemExit(f"synthetic flag missing: {relative}")
    if payload.get("read_only") is not True or payload.get("redacted") is not True:
        raise SystemExit(f"read-only redacted flags missing: {relative}")
    if payload.get("shadow_activation_enabled") is not False:
        raise SystemExit(f"shadow activation must remain disabled: {relative}")
    if payload.get("runtime_effect") is not False:
        raise SystemExit(f"runtime effect must remain false: {relative}")

ledger = json.loads((ROOT / "docs/self-improvement/authorization-ledger.json").read_text())
if ledger["current_stage"] != "shadow_activation_control_plane_implemented_disabled_pending_closeout":
    raise SystemExit("AION-181 current stage mismatch")
if ledger["active_self_improvement_implementation_authorization"] != "AION-180-SI-0007":
    raise SystemExit("AION-180-SI-0007 must remain active")
record = [
    item for item in ledger["records"]
    if item.get("authorization_transaction_id") == "AION-180-SI-0007"
][0]
if record["authorization_scope"] != "disabled-shadow-activation-request-approval-monitoring-deactivation-control-plane":
    raise SystemExit("AION-181 authorization scope mismatch")
for key in (
    "shadow_activation_control_plane_implemented",
    "activation_candidate_validation_available",
    "activation_request_validation_available",
    "activation_approval_binding_validation_available",
    "activation_state_machine_available",
    "activation_resource_budget_validation_available",
    "activation_monitoring_validation_available",
    "activation_deactivation_decision_available",
    "activation_kill_switch_decision_available",
    "activation_local_evidence_adapter_available",
    "activation_in_memory_adapter_available",
    "activation_simulation_available",
):
    if record.get(key) is not True:
        raise SystemExit(f"{key} must be true")
for key in (
    "shadow_activation_enabled",
    "shadow_mode_runtime_enabled",
    "actual_activation_available",
    "runtime_effect",
    "network_calls_enabled",
    "connector_calls_enabled",
    "provider_calls_enabled",
    "model_calls_enabled",
    "source_mutation_enabled",
    "worktree_creation_enabled",
    "git_push_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_enabled",
    "automatic_merge_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
):
    if record.get(key) is not False:
        raise SystemExit(f"{key} must be false")

program = json.loads((ROOT / "docs/self-improvement/program-ledger.json").read_text())
by_task = {item["task_id"]: item for item in program["records"]}
if by_task["AION-180"]["ci_result"] != "pass":
    raise SystemExit("AION-180 must be reconciled as pass")
if by_task["AION-181"]["ci_result"] != "pending":
    raise SystemExit("AION-181 must remain pending before merge")
PY

grep -q "0166-controlled-shadow-activation-control-plane.md" docs/adr/README.md || {
  echo "ADR 0166 is not indexed" >&2
  exit 1
}

./scripts/self-improvement-shadow-activation-control-plane-no-go-regression.sh

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-activation-control-plane

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_self_improvement_shadow_activation_contracts.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_candidate.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_request.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_state_machine.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_policy.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_approval.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_separation_of_duties.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_local_evidence_adapter.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_output_boundary.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_resource_budget.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_monitoring.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_deactivation.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_evidence.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_incident.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_simulator.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_determinism.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_concurrency.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_no_runtime_enablement.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_no_network_git_or_pr.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_performance.py \
  -q

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-mode-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-mode-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

if [[ "${AION_SHADOW_ACTIVATION_RUNTIME_HOLD_RUNNING:-}" != "1" ]]; then
  AION_SHADOW_ACTIVATION_CONTROL_PLANE_CHECK_RUNNING=1 \
    AION_SHADOW_ACTIVATION_RUNTIME_HOLD_SKIP_FULL_CHECK=1 \
    ./scripts/self-improvement-shadow-activation-runtime-hold.sh
fi

echo "self improvement shadow activation control plane PASS"
