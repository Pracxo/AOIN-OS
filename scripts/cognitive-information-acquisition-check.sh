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
  examples/cognitive-architecture/aion-194-information-acquisition.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode information-acquisition

./scripts/cognitive-information-acquisition-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/src/aion_brain/contracts/information_acquisition.py \
  services/brain-api/src/aion_brain/information_acquisition \
  services/brain-api/tests/test_cognitive_information_acquisition.py \
  services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive information-acquisition pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_information_acquisition.py \
    services/brain-api/tests/test_cognitive_information_acquisition_no_runtime_effect.py \
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
cognitive information-acquisition result:
- authorization=AION-193-CA-0006
- implementation_task=AION-194
- closeout_task=AION-195
- knowledge_gap_detection=deterministic bounded uncertainty gaps
- candidate_generation=clarification retrieval observation synthetic experiment asks only
- ranking=expected information gain minus bounded cost and risk
- permission_enforcement=true
- stopping_rule=value_must_exceed_cost_and_risk
- runtime_effect=false
- api_route_added=false
- kernel_registration_added=false
- background_loop_added=false
- network_calls=0
- connector_calls=0
- model_provider_calls=0
- model_calls_by_default=0
- tool_execution=false
- information_acquired=false
- unauthorized_information_acquisition=0
- source_rewrite=false
cognitive information-acquisition PASS
SUMMARY
