#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" -m py_compile scripts/lib/knowledge_intelligence_claim_graph_operator_evaluation.py

TMP_DIR="${TMPDIR:-/tmp}/aion-claim-graph-evaluation-check"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
"$PYTHON_BIN" scripts/lib/knowledge_intelligence_claim_graph_operator_evaluation.py \
  --repo-root "$ROOT_DIR" \
  --evaluation-id AION-TCGE-001 \
  --evaluation-base-commit "$(git rev-parse HEAD)" \
  --temporary-output-directory "$TMP_DIR" \
  --report "$TMP_DIR/AION-TCGE-001.json"
"$PYTHON_BIN" -m json.tool "$TMP_DIR/AION-TCGE-001.json" >/dev/null
"$PYTHON_BIN" scripts/lib/knowledge_intelligence_claim_graph_operator_evaluation.py \
  --validate-report "$TMP_DIR/AION-TCGE-001.json"

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_claim_graph_operator_evaluation.py \
  -q

rm -rf "$TMP_DIR"

echo "knowledge intelligence claim graph operator evaluation PASS"
