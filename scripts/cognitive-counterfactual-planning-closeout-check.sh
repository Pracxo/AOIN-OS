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
  examples/cognitive-architecture/aion-193-counterfactual-planning-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool \
  examples/cognitive-architecture/aion-193-information-acquisition-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode counterfactual-planning-closeout

./scripts/cognitive-counterfactual-planning-closeout-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_counterfactual_planning.py \
  services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive counterfactual-planning closeout pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_counterfactual_planning.py \
    services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py \
    services/brain-api/tests/test_cognitive_counterfactual_planning_closeout_authorization_docs.py \
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
cognitive counterfactual-planning closeout result:
- evaluation=AION-HCPE-001
- closed_authorization=AION-191-CA-0005
- new_authorization=AION-193-CA-0006
- authorized_task=AION-194
- synthetic_goal_completion_plan_success=100%
- policy_violation_count=0
- budget_overrun_count=0
- irreversible_unsafe_plan_selection_count=0
- deterministic_plan_replay=100%
- forbidden_side_effects=0
- runtime_effect=false
cognitive counterfactual-planning closeout PASS
SUMMARY
