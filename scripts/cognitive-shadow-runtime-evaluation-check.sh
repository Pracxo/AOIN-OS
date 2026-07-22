#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

"$PYTHON_BIN" -m json.tool docs/cognitive-architecture/program-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool docs/cognitive-architecture/authorization-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool \
  examples/cognitive-architecture/aion-200-cognitive-shadow-runtime-evaluation.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-runtime-evaluation

./scripts/cognitive-shadow-runtime-evaluation-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_shadow_runtime_evaluation_closeout.py \
  services/brain-api/tests/test_cognitive_shadow_runtime.py \
  services/brain-api/tests/test_cognitive_shadow_runtime_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py \
  services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive shadow-runtime evaluation pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_shadow_runtime_evaluation_closeout.py \
    services/brain-api/tests/test_cognitive_shadow_runtime.py \
    services/brain-api/tests/test_cognitive_shadow_runtime_no_runtime_effect.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-shadow-runtime-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-shadow-runtime-authorization-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-integrated-evaluation-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive shadow-runtime evaluation result:
- evaluation=AION-CSE-001
- closed_authorization=AION-198-CA-0008
- evaluated_task=AION-199
- implementation_pr=110
- implementation_merge_commit=cf1fd2ca6a45aeb3e034a95799edf9833ca24b14
- result=PASS
- active_cognitive_implementation_authorization_count=0
- restart_continuity=1.0
- hundred_cycle_state_persistence=1.0
- deterministic_replay=1.0
- kill_switch_block_rate=1.0
- budget_violation_block_rate=1.0
- corrupted_state_block_rate=1.0
- stale_state_rejection_rate=1.0
- concurrency_conflict_rejection_rate=1.0
- forbidden_side_effects=0
- policy_violations=0
- unauthorized_promotions=0
- recommendation=controlled_local_offline_cognitive_pilot_authorization_review
- new_authorization_created=false
cognitive shadow-runtime evaluation PASS
SUMMARY
