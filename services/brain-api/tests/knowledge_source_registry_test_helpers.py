from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
CLOSED_AUTH_ID = "AION-204-KI-0001"
SOURCE_AUTH_ID = "AION-206-KI-0002"
CLAIM_GRAPH_AUTH_ID = "AION-208-KI-0003"
EVALUATION_ID = "AION-RAE-001"
DECISION = (
    "RESEARCH_ACQUISITION_OPERATOR_EVALUATION_PASS_RECOMMEND_SOURCE_PROVENANCE_REGISTRY_AUTHORIZATION"
)
SOURCE_SCOPE = "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
EVALUATED_MAIN = "a775fb18bb0027d30834d8ab2507f461013753e2"
AUTHORIZED_KEYS = {
    "source_registry_contract_approved",
    "source_record_envelope_approved",
    "source_snapshot_digest_reference_approved",
    "source_provenance_lineage_index_approved",
    "citation_reference_index_approved",
    "append_only_persistence_approved",
    "immutable_record_versioning_approved",
    "canonical_json_fingerprint_approved",
    "synthetic_fixture_replay_approved",
    "operator_review_item_approved",
    "redacted_metadata_storage_approved",
    "record_integrity_audit_approved",
    "resource_budget_enforcement_approved",
    "no_source_body_storage_enforcement_approved",
    "no_claim_verification_enforcement_approved",
    "no_knowledge_promotion_enforcement_approved",
    "no_belief_mutation_enforcement_approved",
    "no_network_fetch_enforcement_approved",
    "documentation_and_static_evidence_approved",
    "runtime_hold_enforcement_approved",
}
RESOURCE_LIMITS = {
    "maximum_registry_records_per_plan": 100,
    "maximum_record_envelope_bytes": 8192,
    "maximum_metadata_bytes_per_record": 4096,
    "maximum_lineage_edges_per_record": 20,
    "maximum_citation_references_per_record": 20,
    "maximum_registry_write_batch": 0,
    "maximum_persisted_source_body_bytes": 0,
    "maximum_repository_source_body_bytes": 0,
    "maximum_claim_verifications": 0,
    "maximum_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_network_calls": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created_by_runtime": 0,
    "maximum_background_crawls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
}
SOURCE_RUNTIME_PATHS = [
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py",
]
PROHIBITED_SOURCE_RUNTIME_PATHS = [
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_service.py",
    "services/brain-api/src/aion_brain/api/source_registry.py",
]


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text()


def active_source_record() -> dict:
    return source_authorization_record()


def source_authorization_record() -> dict:
    records = read_json("docs/knowledge-intelligence/authorization-ledger.json")["records"]
    matches = [
        record
        for record in records
        if record.get("authorization_transaction_id") == SOURCE_AUTH_ID
    ]
    assert len(matches) == 1
    return matches[0]


def active_knowledge_authorization_record() -> dict:
    records = read_json("docs/knowledge-intelligence/authorization-ledger.json")["records"]
    active = [record for record in records if record.get("authorization_active") is True]
    assert len(active) == 1
    return active[0]


def closed_research_record() -> dict:
    records = read_json("docs/knowledge-intelligence/authorization-ledger.json")["records"]
    closed = [
        record
        for record in records
        if record.get("authorization_transaction_id") == CLOSED_AUTH_ID
    ]
    assert len(closed) == 1
    return closed[0]


def validate_source_authorization(record: dict) -> None:
    assert record["program_id"] == PROGRAM_ID
    assert record["authorization_transaction_id"] == SOURCE_AUTH_ID
    assert record["approval_record_id"] == SOURCE_AUTH_ID
    assert record["authorization_scope"] == SOURCE_SCOPE
    assert record["implementation_task"] == "AION-207"
    assert record["formal_closeout_task"] == "AION-208"
    if record["authorization_active"] is True:
        assert record["authorization_consumed"] is False
        assert record["authorization_expired"] is False
    else:
        assert record["authorization_consumed"] is True
        assert record["authorization_expired"] is True
        assert record["authorization_consumed_by_task"] == "AION-207"
        assert record["authorization_consumed_by_prs"] == [119]
        assert record["authorization_closed_by_task"] == "AION-208"
        assert record["source_registry_operator_evaluation_id"] == "AION-SPRE-001"
    assert record["authorization_reusable"] is False
    assert set(record["authorized_capabilities"]) == AUTHORIZED_KEYS
    assert all(record["authorized_capabilities"][key] is True for key in AUTHORIZED_KEYS)
    assert record["resource_limits"] == RESOURCE_LIMITS
    assert all(value is False for value in record["prohibited_capabilities"].values())
    for key in (
        "research_runtime_enabled",
        "network_access_enabled",
        "public_network_fetch_available",
        "source_body_persistence_enabled",
        "claim_verification_enabled",
        "knowledge_promotion_enabled",
        "belief_mutation_enabled",
        "runtime_effect",
    ):
        assert record[key] is False, key
    assert record["source_provenance_registry_implemented"] is True
    assert (
        record["source_provenance_registry_state"]
        == "implemented_append_only_in_memory_replay_persistent_write_disabled"
    )


def assert_source_authorization_rejects(mutator) -> None:
    record = copy.deepcopy(active_source_record())
    mutator(record)
    try:
        validate_source_authorization(record)
    except AssertionError:
        return
    raise AssertionError("invalid source registry authorization was accepted")


def changed_files() -> set[str]:
    base = None
    for ref in ("origin/main", "main"):
        exists = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if exists.returncode == 0:
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", ref],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                base = merge_base.stdout.strip()
                break
    if base is None:
        return set()
    diff = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in diff.stdout.splitlines() if line.strip()}
