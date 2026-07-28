#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" -m py_compile \
  scripts/lib/governed_learning_memory_local_persistence_operator_evaluation.py

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from scripts.lib.governed_learning_memory_local_persistence_operator_evaluation import (
    SCENARIO_IDS,
    validate_evaluation_report_file,
)

report = Path("examples/governed-learning-memory/local-persistence-operator-evaluation-report.json")
if report.exists():
    payload = validate_evaluation_report_file(report)
    if payload["scenario_count"] != 28 or tuple(payload["scenario_ids"]) != SCENARIO_IDS:
        raise SystemExit("AION-225 evaluation scenario mismatch")
else:
    print("WARN: AION-225 repository evaluation report not present yet")
PY

./scripts/governed-learning-memory-local-persistence-operator-evaluation-no-go-regression.sh
if [[ -f examples/governed-learning-memory/local-persistence-operator-evaluation-report.json ]]; then
  ./scripts/governed-learning-memory-local-persistence-no-go-regression.sh
  ./scripts/governed-learning-memory-local-persistence-check.sh
  ./scripts/governed-learning-memory-local-persistence-pilot-evidence-check.sh
  AION_GLM_LOCAL_PERSISTENCE_RUNTIME_HOLD_SKIP_FULL_CHECK=1 \
    ./scripts/governed-learning-memory-local-persistence-runtime-hold.sh
  ./scripts/governed-learning-memory-promotion-operator-evaluation-check.sh merged-main
  ./scripts/governed-learning-memory-promotion-transaction-check.sh merged-main
  ./scripts/governed-learning-memory-program-authorization-check.sh
  ./scripts/knowledge-intelligence-program-complete-check.sh
  AION_KI_PROGRAM_COMPLETE_RUNTIME_HOLD_SKIP_FULL_CHECK=1 \
    ./scripts/knowledge-intelligence-program-complete-runtime-hold.sh
  AION_AGGREGATE_GATE_RUNNING=1 \
    ./scripts/cognitive-local-offline-pilot-closeout-check.sh
  ./scripts/self-improvement-final-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi
echo "governed learning memory local persistence operator evaluation PASS"
