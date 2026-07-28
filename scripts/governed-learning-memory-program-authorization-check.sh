#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-program-complete-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-program-complete-runtime-hold.sh
"$PYTHON_BIN" -m scripts.lib.governed_learning_memory_local_persistence_authorization >/dev/null
"$PYTHON_BIN" -m pytest services/brain-api/tests/test_governed_learning_memory_program_authorization.py services/brain-api/tests/test_governed_learning_memory_program_ledger.py services/brain-api/tests/test_governed_learning_memory_authorization_ledger.py services/brain-api/tests/test_governed_learning_memory_program_docs.py services/brain-api/tests/test_governed_learning_memory_cross_program_lineage.py -q
aion_confirm_immutable_v01_tag_history >/dev/null
echo "governed learning memory program authorization PASS"
