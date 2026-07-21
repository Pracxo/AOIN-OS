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
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-187-world-model-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-187-workspace-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode world-model-closeout

./scripts/cognitive-world-model-closeout-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_predictive_world_model.py \
  services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive world-model closeout pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_predictive_world_model.py \
    services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py \
    services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py \
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
cognitive world-model closeout result:
- evaluation=AION-PWME-001
- closed_authorization=AION-185-CA-0002
- new_authorization=AION-187-CA-0003
- authorized_task=AION-188
- transition_top_1_accuracy>=0.80
- brier_score<=0.20
- probability_sum_error<=0.000000001
- unknown_state_fail_closed=100%
- deterministic_replay=100%
- forbidden_side_effects=0
- runtime_effect=false
cognitive world-model closeout PASS
SUMMARY
