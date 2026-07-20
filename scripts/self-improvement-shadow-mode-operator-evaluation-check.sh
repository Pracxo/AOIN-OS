#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

REPORT="examples/self-improvement/shadow-mode-operator-evaluation-report.json"
test -f "$REPORT" || {
  echo "missing AION-179 report: $REPORT" >&2
  exit 1
}

"$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/shadow-mode-operator-evaluation-scenario-summary.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/shadow-mode-activation-review-boundary.json >/dev/null
"$PYTHON_BIN" -m json.tool operator-console-static/demo-data/self-improvement-shadow-mode-operator-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool operator-console-static/demo-data/self-improvement-shadow-mode-activation-review-boundary.json >/dev/null

./scripts/self-improvement-shadow-mode-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-operator-evaluation

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_self_improvement_shadow_mode_operator_evaluation.py \
  services/brain-api/tests/test_self_improvement_shadow_mode_operator_evaluation_docs.py \
  services/brain-api/tests/test_self_improvement_shadow_mode_authorization_closeout.py \
  services/brain-api/tests/test_self_improvement_shadow_mode_evaluation_no_runtime_effect.py \
  -q

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-mode-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-mode-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-runtime-hold.sh

echo "self improvement shadow mode operator evaluation PASS"
