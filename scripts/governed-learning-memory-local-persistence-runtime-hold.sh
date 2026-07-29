#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
is_nested_gate_context(){ [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0; [[ "${AION_GLM_LOCAL_PERSISTENCE_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0; [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0; [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0; return 1; }
./scripts/governed-learning-memory-local-persistence-check.sh
"$PYTHON_BIN" - <<'PY'
from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
    CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
    REPO_ROOT,
    validate_authorization_ledgers,
    validate_no_aion224_source,
)
program,_=validate_authorization_ledgers(REPO_ROOT); validate_no_aion224_source(REPO_ROOT)
if program.get("program_state") in {
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
    CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
}:
    for key in ["local_append_only_knowledge_store_implemented","operator_invoked_local_persistence_available","synthetic_local_persistence_pilot_completed"]:
        if program.get(key) is not True: raise SystemExit(f"implemented local persistence flag must be true: {key}")
else:
    for key in ["local_append_only_knowledge_store_implemented","operator_invoked_local_persistence_available"]:
        if program.get(key) is not False: raise SystemExit(f"preimplementation flag must remain false: {key}")
for key in ["general_persistent_knowledge_write_enabled","background_persistent_knowledge_write_enabled","production_persistent_knowledge_write_enabled","semantic_memory_write_enabled","episodic_memory_write_enabled","procedural_memory_write_enabled","cognitive_memory_write_enabled","actual_belief_creation_enabled","actual_belief_mutation_enabled","automatic_knowledge_promotion_enabled","runtime_enabled"]:
    if program.get(key) is not False: raise SystemExit(f"runtime hold flag must remain false: {key}")
PY
if is_nested_gate_context; then echo "PASS: full repository check deferred to outer gate"; else AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh; fi
echo "governed learning memory local persistence runtime hold PASS"
