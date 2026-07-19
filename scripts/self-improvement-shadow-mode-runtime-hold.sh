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
  [[ "${AION_SHADOW_MODE_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_SHADOW_MODE_RUNTIME_HOLD_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py --repo-root "$ROOT_DIR" --mode no-go

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()
authorization = json.loads((ROOT / "docs/self-improvement/authorization-ledger.json").read_text())
hold = json.loads((ROOT / "examples/self-improvement/shadow-mode-runtime-hold.json").read_text())

records = authorization["records"]
active = [record for record in records if record.get("authorization_active") is True]
if len(active) != 1:
    raise SystemExit("exactly one active shadow-mode authorization is required")
record = active[0]
if record["authorization_transaction_id"] != "AION-177-SI-0006":
    raise SystemExit("active authorization must be AION-177-SI-0006")
if record["implementation_task"] != "AION-178":
    raise SystemExit("active implementation task must be AION-178")

false_keys = {
    "shadow_mode_implemented",
    "shadow_mode_runtime_enabled",
    "shadow_mode_source_rewrite_enabled",
    "shadow_mode_git_write_enabled",
    "shadow_mode_pr_creation_enabled",
    "shadow_mode_auto_merge_enabled",
    "shadow_mode_production_canary_enabled",
    "shadow_mode_deployment_enabled",
    "shadow_mode_provider_call_enabled",
    "shadow_mode_connector_runtime_enabled",
    "shadow_mode_model_training_enabled",
    "shadow_mode_approval_creation_enabled",
    "shadow_mode_self_approval_enabled",
    "shadow_mode_protected_core_bypass_enabled",
    "shadow_mode_user_traffic_enabled",
    "self_improvement_runtime_enabled",
    "self_rewrite_runtime_enabled",
    "source_mutation_enabled",
    "git_commits_enabled",
    "branch_creation_enabled",
    "pull_request_creation_enabled",
    "merge_enabled",
    "automatic_merge_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
}
for key in false_keys:
    if record.get(key) is not False:
        raise SystemExit(f"authorization ledger {key} must be false")
for key in false_keys & hold.keys():
    if hold.get(key) is not False:
        raise SystemExit(f"shadow runtime hold {key} must be false")

for relative in hold["prohibited_source_files_absent"]:
    if (ROOT / relative).exists():
        raise SystemExit(f"AION-178 runtime source must be absent: {relative}")

print("shadow-mode authorization runtime hold disabled-default checks PASS")
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
self-improvement shadow-mode runtime hold result:
- active authorization: AION-177-SI-0006 for AION-178
- shadow_mode_authorized=true
- shadow_mode_implemented=false
- shadow_mode_runtime_enabled=false
- source mutation, Git writes, PR creation, merge, deployment, provider calls, connector calls, model training, approval creation, and self approval disabled
- AION-178 runtime source absent
self-improvement shadow-mode runtime hold PASS
SUMMARY
