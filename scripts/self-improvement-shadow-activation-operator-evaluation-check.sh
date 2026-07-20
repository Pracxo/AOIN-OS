#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

REPORT="examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json"
test -f "$REPORT" || {
  echo "missing AION-182 report: $REPORT" >&2
  exit 1
}

"$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/shadow-activation-control-plane-evaluation-scenario-summary.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/self-improvement/actual-shadow-activation-review-boundary.json >/dev/null
"$PYTHON_BIN" -m json.tool operator-console-static/demo-data/self-improvement-shadow-activation-control-plane-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool operator-console-static/demo-data/self-improvement-actual-shadow-activation-review-boundary.json >/dev/null
"$PYTHON_BIN" scripts/lib/self_improvement_shadow_activation_operator_evaluation.py \
  --validate-report "$REPORT"

./scripts/self-improvement-shadow-activation-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-activation-operator-evaluation

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_self_improvement_shadow_activation_operator_evaluation.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_operator_evaluation_docs.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_authorization_closeout.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_no_runtime_effect.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py \
  -q

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-control-plane-no-go-regression.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-control-plane-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-activation-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-mode-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/docs-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/final-docs-audit.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/verify-no-domain-drift.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/boundary-check.sh

decision="$("$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("examples/self-improvement/shadow-activation-control-plane-operator-evaluation-report.json").read_text())
print(payload["decision"])
PY
)"

if [[ "$decision" == "SHADOW_ACTIVATION_CONTROL_PLANE_EVALUATION_PASS_RECOMMEND_ACTUAL_ACTIVATION_AUTHORIZATION_REVIEW" ]]; then
  echo "self improvement shadow activation operator evaluation PASS"
else
  echo "self improvement shadow activation operator evaluation FAIL RECORDED"
fi
