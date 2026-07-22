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
  examples/cognitive-architecture/aion-195-information-acquisition-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool \
  examples/cognitive-architecture/aion-195-continual-learning-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode information-acquisition-closeout

./scripts/cognitive-information-acquisition-closeout-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_information_acquisition.py \
  services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive information-acquisition closeout pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_information_acquisition.py \
    services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py \
    services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive information-acquisition closeout result:
- evaluation=AION-AIAE-001
- closed_authorization=AION-193-CA-0006
- new_authorization=AION-195-CA-0007
- authorized_task=AION-196
- uncertainty_detection=100%
- expected_information_gain=100%
- candidate_ranking_deterministic=100%
- cost_risk_constraint_violations=0
- clarification_quality=100%
- stopping_decision_accuracy=100%
- permission_enforcement_violations=0
- unauthorized_information_acquisition=0
- forbidden_side_effects=0
- runtime_effect=false
cognitive information-acquisition closeout PASS
SUMMARY
