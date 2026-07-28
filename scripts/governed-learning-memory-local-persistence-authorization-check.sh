#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
./scripts/governed-learning-memory-local-persistence-authorization-no-go-regression.sh
"$PYTHON_BIN" -m py_compile scripts/lib/governed_learning_memory_promotion_operator_evaluation.py scripts/lib/governed_learning_memory_local_persistence_authorization.py
"$PYTHON_BIN" -m pytest   services/brain-api/tests/test_governed_learning_memory_promotion_operator_evaluation.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_docs.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_scenarios.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_approvals.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_identity.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_conflicts.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_versions.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_projections.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_rollback.py   services/brain-api/tests/test_governed_learning_memory_promotion_evaluation_no_side_effects.py   services/brain-api/tests/test_governed_learning_memory_authorization_closeout.py   services/brain-api/tests/test_governed_learning_memory_local_persistence_authorization_docs.py   services/brain-api/tests/test_governed_learning_memory_local_persistence_authorization_validator.py   services/brain-api/tests/test_governed_learning_memory_local_persistence_scope_spec.py   services/brain-api/tests/test_governed_learning_memory_local_persistence_budget_spec.py   services/brain-api/tests/test_governed_learning_memory_local_persistence_sqlite_policy.py   services/brain-api/tests/test_governed_learning_memory_local_persistence_approval_policy.py   services/brain-api/tests/test_governed_learning_memory_local_persistence_threat_model.py   services/brain-api/tests/test_governed_learning_memory_aion222_delivery_reconciliation.py   services/brain-api/tests/test_governed_learning_memory_current_state_consistency.py -q
"$PYTHON_BIN" -m scripts.lib.governed_learning_memory_local_persistence_authorization >/dev/null
echo "governed learning memory local persistence authorization PASS"
