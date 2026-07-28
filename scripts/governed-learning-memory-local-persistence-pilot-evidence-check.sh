#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts.governed_learning_memory_persistence import persistence_fingerprint

path = Path("examples/governed-learning-memory/local-persistence-synthetic-pilot-evidence.json")
payload = json.loads(path.read_text(encoding="utf-8"))
expected = {
    "authorization_id": "AION-223-GLM-0002",
    "mode": "synthetic_test",
    "transactions_committed": 1,
    "idempotent_replays": 1,
    "changed_replays_rejected": 1,
    "knowledge_identities_written": 1,
    "knowledge_versions_written": 1,
    "semantic_projection_records_written": 1,
    "episodic_projection_records_written": 1,
    "procedural_projection_records_written": 1,
    "belief_candidate_records_written": 1,
    "actual_beliefs_created": 0,
    "actual_beliefs_mutated": 0,
    "production_memory_writes": 0,
    "automatic_promotions": 0,
    "update_attempts_rejected": 1,
    "delete_attempts_rejected": 1,
    "global_hash_chain_passed": True,
    "transaction_hash_chain_passed": True,
    "backup_integrity_passed": True,
    "restore_integrity_passed": True,
    "restored_logical_state_equal": True,
    "temporary_database_files_retained": 0,
    "source_bodies_persisted": 0,
    "confidential_content_persisted": 0,
    "raw_approval_payloads_persisted": 0,
    "redacted": True,
}
for key, value in expected.items():
    if payload.get(key) != value:
        raise SystemExit(f"pilot evidence mismatch: {key}")
fingerprint = persistence_fingerprint({k: v for k, v in payload.items() if k != "report_fingerprint"})
if payload.get("report_fingerprint") != fingerprint:
    raise SystemExit("pilot evidence fingerprint mismatch")
PY
echo "governed learning memory local persistence pilot evidence PASS"
