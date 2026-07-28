#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
export AION_AGGREGATE_GATE_RUNNING=1
mode="${1:-feature}"
case "$mode" in
  feature|--feature)
    mode="feature"
    ;;
  merged-main|--merged-main)
    mode="merged-main"
    ;;
  *)
    echo "usage: $0 [feature|merged-main]" >&2
    exit 2
    ;;
esac
./scripts/governed-learning-memory-promotion-operator-evaluation-no-go-regression.sh "$mode"
"$PYTHON_BIN" -m py_compile scripts/lib/governed_learning_memory_promotion_operator_evaluation.py scripts/lib/governed_learning_memory_local_persistence_authorization.py
"$PYTHON_BIN" -m pytest services/brain-api/tests/test_governed_learning_memory_promotion_operator_evaluation.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_docs.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_scenarios.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_approvals.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_identity.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_conflicts.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_versions.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_projections.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_rollback.py services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_no_side_effects.py services/brain-api/tests/test_governed_learning_memory_authorization_closeout.py services/brain-api/tests/test_governed_learning_memory_aion222_delivery_reconciliation.py -q
"$PYTHON_BIN" -m scripts.lib.governed_learning_memory_local_persistence_authorization >/dev/null
./scripts/governed-learning-memory-promotion-transaction-no-go-regression.sh "$mode"
./scripts/governed-learning-memory-promotion-transaction-check.sh "$mode"
./scripts/governed-learning-memory-runtime-hold.sh "$mode"
./scripts/governed-learning-memory-program-authorization-check.sh
./scripts/knowledge-intelligence-program-complete-check.sh
./scripts/knowledge-intelligence-program-complete-runtime-hold.sh
./scripts/cognitive-local-offline-pilot-closeout-check.sh
./scripts/self-improvement-final-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
./scripts/repo-health.sh
echo "governed learning memory promotion operator evaluation PASS"
