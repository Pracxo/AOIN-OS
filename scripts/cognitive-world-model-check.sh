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
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-186-predictive-world-model.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode world-model

./scripts/cognitive-world-model-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/src/aion_brain/contracts/world_model.py \
  services/brain-api/src/aion_brain/world_model \
  services/brain-api/tests/test_cognitive_predictive_world_model.py \
  services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive world-model pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_predictive_world_model.py \
    services/brain-api/tests/test_cognitive_predictive_world_model_no_runtime_effect.py \
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
cognitive world-model result:
- authorization=AION-185-CA-0002
- implementation_task=AION-186
- closeout_task=AION-187
- model=deterministic observed-transition counts with bounded smoothing
- outcomes=probability-normalized
- unknown_state=fail_closed
- counterfactual_rollout=deterministic
- runtime_effect=false
- api_route_added=false
- kernel_registration_added=false
- network_calls=0
- connector_calls=0
- model_provider_calls=0
- model_weight_training=false
cognitive world-model PASS
SUMMARY
