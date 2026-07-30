#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" -m py_compile \
  services/brain-api/src/aion_brain/contracts/governed_learning_memory_persistence.py \
  services/brain-api/src/aion_brain/governed_learning_memory/local_persistence_policy.py \
  services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_schema.py \
  services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py \
  services/brain-api/src/aion_brain/governed_learning_memory/persistence_approval.py \
  services/brain-api/src/aion_brain/governed_learning_memory/knowledge_content.py \
  services/brain-api/src/aion_brain/governed_learning_memory/knowledge_persistence.py \
  services/brain-api/src/aion_brain/governed_learning_memory/memory_projection_persistence.py \
  services/brain-api/src/aion_brain/governed_learning_memory/persistence_transactions.py \
  services/brain-api/src/aion_brain/governed_learning_memory/persistence_integrity.py \
  services/brain-api/src/aion_brain/governed_learning_memory/backup_restore.py \
  services/brain-api/src/aion_brain/governed_learning_memory/persistence_evidence.py \
  scripts/governed-learning-memory-local-persistence-run.py \
  scripts/lib/governed_learning_memory_local_persistence_authorization.py

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION224_RESOURCE_LIMITS,
    AION224_SOURCE_SCOPE,
    AION223_AUTHORIZATION_ID,
    CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
    CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    FINAL_GLM_PROGRAM_STATES,
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
    validate_authorization_ledgers,
    validate_delivery_reconciliation,
    validate_evaluation_report,
    validate_future_policy,
)

root = Path.cwd()
program, auth = validate_authorization_ledgers(root)
validate_future_policy(root)
validate_delivery_reconciliation(root)
validate_evaluation_report(root)
implemented_states = {
    IMPLEMENTED_PENDING_CLOSEOUT_STATE,
    ENGAGEMENT_APPLICATION_AUTHORIZED_STATE,
    ENGAGEMENT_APPLICATION_IMPLEMENTED_STATE,
    CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
    CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
    *FINAL_GLM_PROGRAM_STATES,
}
for label, payload in (("program", program), ("authorization", auth)):
    if payload["program_state"] not in implemented_states:
        raise SystemExit(f"{label} implemented state mismatch")
    for key in (
        "local_append_only_knowledge_store_implemented",
        "operator_invoked_local_persistence_available",
        "synthetic_local_persistence_pilot_completed",
    ):
        if payload.get(key) is not True:
            raise SystemExit(f"{label} implementation flag mismatch: {key}")
    if payload["program_state"] not in {
        CONTINUAL_LEARNING_PILOT_AUTHORIZED_STATE,
        CONTINUAL_LEARNING_PILOT_IMPLEMENTED_STATE,
        *FINAL_GLM_PROGRAM_STATES,
    }:
        if payload.get("authorized_source_scope") != AION224_SOURCE_SCOPE:
            raise SystemExit(f"{label} source scope mismatch")
        if payload.get("resource_limits") != AION224_RESOURCE_LIMITS:
            raise SystemExit(f"{label} resource limits mismatch")
historical_authorization = next(
    item
    for item in auth["records"]
    if item["authorization_transaction_id"] == AION223_AUTHORIZATION_ID
)
if historical_authorization.get("authorized_source_scope") != AION224_SOURCE_SCOPE:
    raise SystemExit("historical AION-224 source scope mismatch")
if historical_authorization.get("resource_limits") != AION224_RESOURCE_LIMITS:
    raise SystemExit("historical AION-224 resource limits mismatch")
pilot = json.loads((root / "examples/governed-learning-memory/local-persistence-synthetic-pilot-evidence.json").read_text())
if pilot["transactions_committed"] != 1 or pilot["temporary_database_files_retained"] != 0:
    raise SystemExit("synthetic pilot evidence mismatch")
PY

"$PYTHON_BIN" -m pytest services/brain-api/tests/test_governed_learning_memory_local_persistence_implementation.py -q
./scripts/governed-learning-memory-local-persistence-no-go-regression.sh
./scripts/governed-learning-memory-local-persistence-pilot-evidence-check.sh
echo "governed learning memory local persistence PASS"
