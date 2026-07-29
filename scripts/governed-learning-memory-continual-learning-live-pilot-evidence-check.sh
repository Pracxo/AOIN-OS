#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

from aion_brain.contracts.governed_continual_learning import continual_fingerprint

path = Path("examples/governed-learning-memory/controlled-local-continual-learning-live-pilot-evidence.json")
payload = json.loads(path.read_text(encoding="utf-8"))
report_fingerprint = payload.pop("report_fingerprint")
if report_fingerprint != continual_fingerprint(payload):
    raise SystemExit("live-pilot report fingerprint mismatch")
expected = {
    "pilot_id": "AION-228-controlled-local-continual-learning-live-pilot",
    "authorization_id": "AION-227-GLM-0004",
    "mode": "operator_invoked_live",
    "cycle_count": 3,
    "cycle_outcomes": ["completed", "completed", "abstained"],
    "completed_cycle_count": 2,
    "abstained_cycle_count": 1,
    "failed_cycle_count": 0,
    "source_bodies_retained": 0,
    "eligible_verified_candidate_count": 1,
    "promotion_dry_run_pass_count": 1,
    "temporary_persistence_transaction_count": 1,
    "knowledge_version_write_count": 1,
    "shadow_application_count": 1,
    "receipt_chain_integrity_passed": True,
    "store_integrity_passed": True,
    "overlay_integrity_passed": True,
    "cleanup_integrity_passed": True,
    "redacted": True,
    "runtime_effect": False,
}
for key, value in expected.items():
    if payload.get(key) != value:
        raise SystemExit(f"live-pilot evidence mismatch: {key}")
if payload["dns_resolution_count"] <= 0 or payload["public_https_request_count"] <= 0:
    raise SystemExit("live-pilot external read counts missing")
if payload["source_fetch_count"] < 3:
    raise SystemExit("live-pilot source fetch count too low")
if payload["source_body_purge_count"] != payload["source_fetch_count"]:
    raise SystemExit("live-pilot source bodies were not all purged")
zero_fields = (
    "active_overlay_records_after_close",
    "retained_database_files",
    "retained_wal_files",
    "retained_shm_files",
    "retained_backup_files",
    "retained_manifest_files",
    "retained_checkpoint_files",
    "retained_approval_fixture_files",
    "retained_raw_plan_files",
    "retained_source_body_files",
    "background_cycles",
    "scheduled_cycles",
    "automatic_cycle_continuations",
    "automatic_source_discoveries",
    "crawler_requests",
    "search_provider_calls",
    "connector_calls",
    "model_provider_calls",
    "automatic_candidate_approvals",
    "automatic_knowledge_promotions",
    "automatic_persistence_transactions",
    "production_memory_writes",
    "production_policy_mutations",
    "cognitive_memory_writes",
    "actual_belief_creations",
    "actual_belief_mutations",
    "persistent_engagement_overlay_writes",
    "source_mutations",
    "git_operations",
    "runtime_created_pull_requests",
    "runtime_created_approvals",
    "deployments",
    "model_weight_changes",
    "temporary_files_retained",
)
for field in zero_fields:
    if payload.get(field) != 0:
        raise SystemExit(f"live-pilot prohibited counter nonzero: {field}")
if payload.get("production_exposure") is not False:
    raise SystemExit("live-pilot production exposure must be false")
PY

echo "governed learning memory continual learning live pilot evidence PASS"
