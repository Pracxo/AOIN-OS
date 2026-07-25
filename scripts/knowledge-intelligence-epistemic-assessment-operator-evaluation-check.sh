#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

./scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation-no-go-regression.sh

if [[ -f examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json ]]; then
  "$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json >/dev/null
  "$PYTHON_BIN" scripts/lib/knowledge_intelligence_epistemic_assessment_operator_evaluation.py \
    --validate-report examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json
else
  echo "AION-EAE-001 repository report pending closeout commit"
fi

echo "knowledge intelligence epistemic assessment operator evaluation PASS"
