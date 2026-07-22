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
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-197-integrated-cognitive-evaluation.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode integrated-evaluation

./scripts/cognitive-integrated-evaluation-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py \
  services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py \
  services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive integrated evaluation pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/cognitive-continual-learning-check.sh
  ./scripts/cognitive-architecture-authorization-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive integrated evaluation result:
- evaluation=AION-CAE-001
- closed_authorization=AION-195-CA-0007
- evaluated_task=AION-196
- implementation_pr=107
- implementation_merge_commit=31a20cffc845944a198d1a7e261ceaefc2c9fe89
- cognitive_architecture_implemented=true
- cognitive_architecture_integrated=true
- active_cognitive_implementation_authorization_count=0
- runtime_effect=false
- policy_violations=0
- forbidden_side_effects=0
- unauthorized_promotion=0
- deterministic_replay=1.0
- state_continuity=1.0
- transition_accuracy=0.86
- brier_score=0.12
- plan_success=0.88
- critical_memory_retention=1.0
- catastrophic_forgetting=0.02
- recommendation=integrated_cognitive_shadow_runtime_authorization_review
- new_authorization_created=false
cognitive integrated evaluation PASS
SUMMARY
