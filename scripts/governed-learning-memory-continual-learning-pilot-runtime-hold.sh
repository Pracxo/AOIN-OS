#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [ -n "${PYTEST_CURRENT_TEST:-}" ] && return 0
  [ "${AION_GLM_CONTINUAL_LEARNING_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" = "1" ] && return 0
  [ "${AION_AGGREGATE_GATE_RUNNING:-}" = "1" ] && return 0
  [ "${AION_CHECK_RUNNING:-}" = "1" ] && return 0
  return 1
}

./scripts/governed-learning-memory-continual-learning-pilot-authorization-check.sh

"$PYTHON_BIN" - <<'PY'
from pathlib import Path

from scripts.lib.governed_learning_memory_continual_learning_pilot_authorization import (
    FUTURE_AION228_SOURCE_SCOPE,
    REPO_ROOT,
    load_json,
)

program = load_json("docs/governed-learning-memory/program-ledger.json")
for field in (
    "controlled_local_continual_learning_pilot_implemented",
    "operator_invoked_continual_learning_pilot_available",
    "background_continual_learning_enabled",
    "scheduled_continual_learning_enabled",
    "automatic_candidate_approval_enabled",
    "automatic_knowledge_promotion_enabled",
    "production_memory_write_enabled",
    "production_policy_mutation_enabled",
    "cognitive_memory_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "model_weight_training_enabled",
    "production_exposure",
):
    if program.get(field) is not False:
        raise SystemExit(f"runtime hold flag mismatch: {field}")
for relative in FUTURE_AION228_SOURCE_SCOPE:
    if (REPO_ROOT / relative).exists():
        raise SystemExit(f"AION-228 source exists during runtime hold: {relative}")
if list(Path("/tmp").glob("aion-glm-continual-learning*")):
    raise SystemExit("temporary continual-learning store/session artifact exists")
PY

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "governed learning memory continual learning pilot runtime hold PASS"
