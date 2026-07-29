#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" -m py_compile \
  scripts/lib/governed_learning_memory_engagement_application_operator_evaluation.py \
  scripts/lib/governed_learning_memory_continual_learning_pilot_authorization.py

"$PYTHON_BIN" -m scripts.lib.governed_learning_memory_continual_learning_pilot_authorization
./scripts/governed-learning-memory-continual-learning-pilot-authorization-no-go-regression.sh
echo "governed learning memory continual learning pilot authorization PASS"
