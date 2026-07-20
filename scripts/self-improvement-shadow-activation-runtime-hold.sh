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

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-authorization-check.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()
ledger = json.loads((ROOT / "docs/self-improvement/authorization-ledger.json").read_text())
hold = json.loads((ROOT / "examples/self-improvement/shadow-activation-runtime-hold.json").read_text())

active = [record for record in ledger["records"] if record.get("authorization_active") is True]
if len(active) != 1:
    raise SystemExit("exactly one active authorization is required")
record = active[0]
if record["authorization_transaction_id"] != "AION-180-SI-0007":
    raise SystemExit("AION-180-SI-0007 must be the active authorization")
if record["implementation_task"] != "AION-181":
    raise SystemExit("AION-181 must be the active implementation task")
if record["formal_closeout_task"] != "AION-182":
    raise SystemExit("AION-182 must be the formal closeout task")

false_keys = {
    "shadow_activation_control_plane_implemented",
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
    if (ROOT / path).exists():
        raise SystemExit(f"AION-181 runtime source must be absent in AION-180: {path}")

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
- authorization: AION-180-SI-0007 for AION-181 disabled activation control plane
- formal closeout: AION-182
- shadow_activation_control_plane_authorized=true
- shadow_activation_control_plane_implemented=false
- shadow_activation_enabled=false
- shadow_mode_runtime_enabled=false
- source mutation, Git writes, PR creation, merge, deployment, provider calls, connector calls, model training, approval creation, and runtime influence disabled
self improvement shadow activation runtime hold PASS
SUMMARY
