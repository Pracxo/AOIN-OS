#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/governed-learning-memory-promotion-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" -m py_compile \
  scripts/lib/governed_learning_memory_promotion_operator_evaluation.py

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_governed_learning_memory_promotion_operator_evaluation.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_scenarios.py \
  services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_no_side_effects.py \
  -q

if [[ -f examples/governed-learning-memory/promotion-operator-evaluation-report.json ]]; then
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
from scripts.lib.governed_learning_memory_promotion_operator_evaluation import (
    validate_evaluation_report_file,
)

validate_evaluation_report_file(
    Path("examples/governed-learning-memory/promotion-operator-evaluation-report.json")
)
PY
fi

echo "governed learning memory promotion operator evaluation PASS"
