#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" -m py_compile \
  scripts/lib/governed_learning_memory_engagement_application_operator_evaluation.py

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from scripts.lib.governed_learning_memory_engagement_application_operator_evaluation import (
    SCENARIO_IDS,
    validate_evaluation_report_file,
)

report = Path("examples/governed-learning-memory/engagement-application-operator-evaluation-report.json")
if report.exists():
    payload = validate_evaluation_report_file(report)
    if payload["scenario_count"] != 28 or tuple(payload["scenario_ids"]) != SCENARIO_IDS:
        raise SystemExit("AION-227 evaluation scenario mismatch")
else:
    print("WARN: AION-227 repository evaluation report not present yet")
PY

./scripts/governed-learning-memory-engagement-application-operator-evaluation-no-go-regression.sh
echo "governed learning memory engagement application operator evaluation PASS"
