#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_GLM_ENGAGEMENT_APPLICATION_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/governed-learning-memory-engagement-application-authorization-check.sh
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from scripts.lib.governed_learning_memory_engagement_application_authorization import (
    AION226_SOURCE_SCOPE,
    REPO_ROOT,
    load_json,
)

for rel in AION226_SOURCE_SCOPE:
    if (REPO_ROOT / rel).exists():
        raise SystemExit(f"AION-226 source must not exist: {rel}")
program = load_json("docs/governed-learning-memory/program-ledger.json")
for key in (
    "engagement_learning_application_implemented",
    "operator_invoked_engagement_shadow_application_available",
    "automatic_engagement_learning_application_enabled",
    "persistent_engagement_overlay_write_enabled",
    "production_policy_mutation_enabled",
    "engagement_signal_as_fact_enabled",
    "engagement_confidence_effect_enabled",
    "engagement_knowledge_effect_enabled",
    "cognitive_memory_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "network_access_enabled",
    "production_exposure",
):
    if program.get(key) is not False:
        raise SystemExit(f"runtime hold flag must remain false: {key}")
PY

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi
echo "governed learning memory engagement application runtime hold PASS"
