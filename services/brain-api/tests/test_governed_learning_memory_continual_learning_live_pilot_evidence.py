from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts.governed_continual_learning import continual_fingerprint

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = (
    REPO_ROOT
    / "examples/governed-learning-memory/"
    / "controlled-local-continual-learning-live-pilot-evidence.json"
)


def test_live_pilot_evidence_schema_and_zero_effects() -> None:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    report_fingerprint = payload.pop("report_fingerprint")
    assert report_fingerprint == continual_fingerprint(payload)
    assert payload["pilot_id"] == "AION-228-controlled-local-continual-learning-live-pilot"
    assert payload["authorization_id"] == "AION-227-GLM-0004"
    assert payload["mode"] == "operator_invoked_live"
    assert payload["cycle_count"] == 3
    assert payload["cycle_outcomes"] == ["completed", "completed", "abstained"]
    assert payload["external_read_performed"] is True
    assert payload["dns_resolution_count"] > 0
    assert payload["public_https_request_count"] > 0
    assert payload["source_fetch_count"] >= 3
    assert payload["source_body_purge_count"] == payload["source_fetch_count"]
    assert payload["source_bodies_retained"] == 0
    assert payload["eligible_verified_candidate_count"] == 1
    assert payload["promotion_dry_run_pass_count"] == 1
    assert payload["temporary_persistence_transaction_count"] == 1
    assert payload["knowledge_version_write_count"] == 1
    assert payload["cross_cycle_context_read_count"] >= 1
    assert payload["shadow_application_count"] == 1
    assert payload["receipt_chain_integrity_passed"] is True
    assert payload["store_integrity_passed"] is True
    assert payload["overlay_integrity_passed"] is True
    assert payload["cleanup_integrity_passed"] is True
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
        assert payload[field] == 0
    assert payload["production_exposure"] is False
    assert payload["runtime_effect"] is False
    assert payload["redacted"] is True
