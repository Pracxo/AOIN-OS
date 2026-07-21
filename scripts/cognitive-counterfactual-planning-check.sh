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
  examples/cognitive-architecture/aion-192-counterfactual-planning.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode counterfactual-planning

./scripts/cognitive-counterfactual-planning-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/src/aion_brain/contracts/planning.py \
  services/brain-api/src/aion_brain/planning \
  services/brain-api/tests/test_cognitive_counterfactual_planning.py \
  services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive counterfactual-planning pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_counterfactual_planning.py \
    services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py \
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
cognitive counterfactual-planning result:
- authorization=AION-191-CA-0005
- implementation_task=AION-192
- closeout_task=AION-193
- planning=hierarchical goal strategy milestone task action proposal
- counterfactual_rollouts=bounded world-model simulations only
- score_dimensions=goal_progress information_gain confidence risk resource reversibility policy uncertainty time_horizon
- hard_policy_override=true
- hard_safety_override=true
- runtime_effect=false
- api_route_added=false
- kernel_registration_added=false
- background_loop_added=false
- network_calls=0
- connector_calls=0
- model_provider_calls=0
- model_calls_by_default=0
- action_execution=false
- external_dispatch=false
- source_rewrite=false
cognitive counterfactual-planning PASS
SUMMARY
