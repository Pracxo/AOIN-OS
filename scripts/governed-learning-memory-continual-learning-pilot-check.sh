#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" -m py_compile \
  services/brain-api/src/aion_brain/contracts/governed_continual_learning.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_authorization.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_cycle.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_intake.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_research.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_knowledge_pipeline.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_persistence.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_shadow.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_outcome.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_integrity.py \
  services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_evidence.py \
  scripts/governed-learning-memory-controlled-local-continual-learning-run.py \
  scripts/lib/governed_learning_memory_continual_learning_pilot_authorization.py

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_governed_learning_memory_continual_learning_implementation.py \
  services/brain-api/tests/test_governed_learning_memory_continual_learning_live_pilot_evidence.py \
  services/brain-api/tests/test_governed_learning_memory_continual_learning_scope_spec.py \
  services/brain-api/tests/test_governed_learning_memory_continual_learning_authorization_validator.py \
  -q

./scripts/governed-learning-memory-continual-learning-pilot-no-go-regression.sh
./scripts/governed-learning-memory-continual-learning-live-pilot-evidence-check.sh
./scripts/governed-learning-memory-continual-learning-pilot-authorization-check.sh

"$PYTHON_BIN" - <<'PY'
from aion_brain.governed_learning_memory.continual_learning_cycle import (
    build_deterministic_evidence_bundle,
    deterministic_three_cycle_session,
)

result, receipts = deterministic_three_cycle_session()
if result.cycle_count != 3 or result.abstained_cycle_count != 1:
    raise SystemExit("deterministic session result mismatch")
if len(receipts) != result.stage_receipt_count:
    raise SystemExit("deterministic receipt count mismatch")
bundle = build_deterministic_evidence_bundle()
if bundle.source_bodies_retained != 0 or bundle.runtime_effect:
    raise SystemExit("deterministic evidence boundary mismatch")
PY

echo "governed learning memory continual learning pilot PASS"
