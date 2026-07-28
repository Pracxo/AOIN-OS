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
fi
echo "governed learning memory local persistence operator evaluation PASS"
