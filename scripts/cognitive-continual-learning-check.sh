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
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-196-continual-learning.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode continual-learning

./scripts/cognitive-continual-learning-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/src/aion_brain/contracts/continual_learning.py \
  services/brain-api/src/aion_brain/continual_learning \
  services/brain-api/tests/test_cognitive_continual_learning.py \
  services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_information_acquisition_closeout_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive continual-learning pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_continual_learning.py \
    services/brain-api/tests/test_cognitive_continual_learning_no_runtime_effect.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/cognitive-information-acquisition-closeout-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive continual-learning result:
- authorization=AION-195-CA-0007
- implementation_task=AION-196
- closeout_task=AION-197
- learning_levels=memory,retrieval_policy,planning_policy,procedural_skill,world_model_adapter,strategy
- immutable_baseline=true
- protected_holdout=true
- deterministic_replay=true
- candidate_isolation=true
- promotion_requires_approval=true
- automatic_promotion=false
- self_approval=0
- unauthorized_promotion=0
- rollback_available=true
- model_weight_training=0
- runtime_effect=false
cognitive continual-learning PASS
SUMMARY
