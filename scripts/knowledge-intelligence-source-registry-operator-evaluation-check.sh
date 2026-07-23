#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" -m py_compile \
  scripts/lib/knowledge_intelligence_source_registry_operator_evaluation.py

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_source_registry_operator_evaluation.py \
  -q

echo "knowledge intelligence source registry operator evaluation PASS"
