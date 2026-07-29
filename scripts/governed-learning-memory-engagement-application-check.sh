#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" -m py_compile \
  scripts/lib/governed_learning_memory_engagement_application.py \
  services/brain-api/src/aion_brain/contracts/governed_engagement_learning.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_candidate_binding.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_application_approval.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_adaptation_identity.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_adaptation_planning.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_overlay.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_shadow_application.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_counterfactual_evaluation.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_rollback.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_integrity.py \
  services/brain-api/src/aion_brain/governed_learning_memory/engagement_evidence.py \
  scripts/governed-learning-memory-engagement-shadow-run.py

./scripts/governed-learning-memory-engagement-application-no-go-regression.sh
./scripts/governed-learning-memory-engagement-shadow-pilot-evidence-check.sh
"$PYTHON_BIN" -m scripts.lib.governed_learning_memory_engagement_application
"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_governed_engagement_learning_contracts.py \
  services/brain-api/tests/test_governed_engagement_learning_binding_risk.py \
  services/brain-api/tests/test_governed_engagement_learning_approvals_identity.py \
  services/brain-api/tests/test_governed_engagement_learning_overlay_shadow.py \
  services/brain-api/tests/test_governed_engagement_learning_fixture_runner.py \
  -q
echo "governed learning memory engagement application PASS"
