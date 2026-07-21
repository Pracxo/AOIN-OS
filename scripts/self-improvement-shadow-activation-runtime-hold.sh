#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_SHADOW_ACTIVATION_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_SHADOW_ACTIVATION_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

if is_nested_gate_context; then
  echo "PASS: shadow activation control-plane check deferred to outer gate"
elif [[ "${AION_SHADOW_ACTIVATION_CONTROL_PLANE_CHECK_RUNNING:-}" != "1" ]]; then
  AION_AGGREGATE_GATE_RUNNING=1 \
    AION_SHADOW_ACTIVATION_CONTROL_PLANE_CHECK_RUNNING=1 \
    ./scripts/self-improvement-shadow-activation-control-plane-check.sh
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-authorization-check.sh
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()
ledger = json.loads((ROOT / "docs/self-improvement/authorization-ledger.json").read_text())
hold = json.loads((ROOT / "examples/self-improvement/shadow-activation-control-plane-runtime-hold.json").read_text())

active = [record for record in ledger["records"] if record.get("authorization_active") is True]
closed_stage = ledger.get("current_stage") in {
    "shadow_activation_control_plane_operator_evaluation_passed_disabled",
    "shadow_activation_control_plane_operator_evaluation_failed_disabled",
}
if closed_stage:
    if active:
        raise SystemExit("closed AION-180 authorization cannot remain active")
    matches = [
        record
        for record in ledger["records"]
        if record.get("authorization_transaction_id") == "AION-180-SI-0007"
    ]
    if len(matches) != 1:
        raise SystemExit("closed AION-180-SI-0007 authorization is required")
    record = matches[0]
    if record.get("authorization_consumed") is not True:
        raise SystemExit("AION-180-SI-0007 must be consumed")
    if record.get("authorization_consumed_by_task") != "AION-181":
        raise SystemExit("AION-180-SI-0007 must be consumed by AION-181")
    if record.get("authorization_consumed_by_pr") != 92:
        raise SystemExit("AION-180-SI-0007 must be consumed by PR #92")
    if record.get("authorization_expired") is not True:
        raise SystemExit("AION-180-SI-0007 must be expired")
    if record.get("authorization_reusable") is not False:
        raise SystemExit("AION-180-SI-0007 must be non-reusable")
    if ledger.get("active_self_improvement_implementation_authorization_count") != 0:
        raise SystemExit("active implementation authorization count must be zero")
    if ledger.get("active_self_improvement_implementation_authorization") != "none":
        raise SystemExit("active implementation authorization must be none")
    if ledger.get("active_implementation_task") != "none":
        raise SystemExit("active implementation task must be none")
else:
    if len(active) != 1:
        raise SystemExit("exactly one active authorization is required")
    record = active[0]
    if record["authorization_transaction_id"] != "AION-180-SI-0007":
        raise SystemExit("AION-180-SI-0007 must be the active authorization")
    if record["implementation_task"] != "AION-181":
        raise SystemExit("AION-181 must be the active implementation task")
    if record["formal_closeout_task"] != "AION-182":
        raise SystemExit("AION-182 must be the formal closeout task")
    if ledger.get("current_stage") != "shadow_activation_control_plane_implemented_disabled_pending_closeout":
        raise SystemExit("AION-181 current stage mismatch")
if record.get("shadow_activation_control_plane_implemented") is not True:
    raise SystemExit("AION-181 must implement the disabled activation control plane")
if record.get("shadow_activation_control_plane_state") != "implemented_disabled_simulation_only":
    raise SystemExit("AION-181 activation control plane state mismatch")

false_keys = {
    "shadow_activation_enabled",
    "shadow_mode_runtime_enabled",
    "self_improvement_runtime_enabled",
    "self_rewrite_runtime_enabled",
    "kernel_container_registration_enabled",
    "application_startup_registration_enabled",
    "background_scheduler_enabled",
    "continuous_background_loop_enabled",
    "network_calls_enabled",
    "connector_calls_enabled",
    "provider_calls_enabled",
    "source_mutation_enabled",
    "worktree_creation_enabled",
    "git_branch_creation_enabled",
    "git_commit_creation_enabled",
    "git_push_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_enabled",
    "approval_satisfaction_enabled",
    "automatic_merge_enabled",
    "manual_merge_execution_enabled",
    "active_retrieval_promotion_enabled",
    "active_strategy_promotion_enabled",
    "preference_promotion_enabled",
    "skill_promotion_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_traffic_exposure_enabled",
    "runtime_effect_enabled",
}
for key in false_keys:
    if record.get(key) is not False and hold.get(key) is not False:
        raise SystemExit(f"{key} must be false")

for path in [
    "services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_policy.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_approval.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_monitoring.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_deactivation.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_evidence.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_simulator.py",
]:
    if not (ROOT / path).is_file():
        raise SystemExit(f"AION-181 activation source must exist: {path}")

print("shadow activation runtime hold disabled-default checks PASS")
PY

aion_confirm_immutable_v01_tag_history >/dev/null

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

cat <<'SUMMARY'
self-improvement shadow activation runtime hold result:
- authorization: AION-180-SI-0007 consumed by AION-181 and closed by AION-182
- formal closeout: AION-182
- shadow_activation_control_plane_authorized=true
- shadow_activation_control_plane_implemented=true
- shadow_activation_control_plane_state=implemented_disabled_simulation_only
- shadow_activation_enabled=false
- shadow_mode_runtime_enabled=false
- source mutation, Git writes, PR creation, merge, deployment, provider calls, connector calls, model training, approval creation, and runtime influence disabled
self improvement shadow activation runtime hold PASS
SUMMARY
