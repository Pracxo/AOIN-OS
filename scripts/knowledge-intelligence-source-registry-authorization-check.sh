#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json >/dev/null
"$PYTHON_BIN" scripts/lib/knowledge_intelligence_research_operator_evaluation.py \
  --validate-report examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AUTH_204 = "AION-204-KI-0001"
AUTH_206 = "AION-206-KI-0002"
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
DECISION = "RESEARCH_ACQUISITION_OPERATOR_EVALUATION_PASS_RECOMMEND_SOURCE_PROVENANCE_REGISTRY_AUTHORIZATION"
SOURCE_SCOPE = "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
IMPLEMENTED_STATE = "implemented_append_only_in_memory_replay_persistent_write_disabled"
REQUIRED_DOCS = [
    "docs/knowledge-intelligence/source-registry-implementation.md",
    "docs/knowledge-intelligence/source-registry-contracts.md",
    "docs/knowledge-intelligence/source-registry-record-envelope.md",
    "docs/knowledge-intelligence/source-registry-append-only-semantics.md",
    "docs/knowledge-intelligence/source-registry-in-memory-repository.md",
    "docs/knowledge-intelligence/source-registry-fixture-replay.md",
    "docs/knowledge-intelligence/source-registry-indexes-and-queries.md",
    "docs/knowledge-intelligence/source-registry-integrity-audit.md",
    "docs/knowledge-intelligence/source-registry-versioning.md",
    "docs/knowledge-intelligence/source-registry-security-review.md",
    "docs/knowledge-intelligence/source-registry-operator-runbook.md",
    "docs/knowledge-intelligence/aion-207-checklist.md",
    "docs/knowledge-intelligence/source-provenance-registry-architecture.md",
    "docs/knowledge-intelligence/source-provenance-registry-boundary.md",
    "docs/knowledge-intelligence/source-provenance-registry-data-model.md",
    "docs/knowledge-intelligence/source-provenance-registry-persistence.md",
    "docs/knowledge-intelligence/source-provenance-registry-resource-budgets.md",
    "docs/knowledge-intelligence/source-provenance-registry-threat-model.md",
    "docs/knowledge-intelligence/source-provenance-registry-roadmap.md",
    "docs/release/knowledge-intelligence-source-registry-implementation.md",
    "docs/release/knowledge-intelligence-source-registry-security-evidence.md",
    "docs/release/knowledge-intelligence-source-registry-authorization-transaction.md",
    "docs/release/knowledge-intelligence-source-registry-explicit-approval-record.md",
    "docs/release/knowledge-intelligence-source-registry-scope.md",
    "docs/release/knowledge-intelligence-source-registry-runtime-hold.md",
    "docs/release/knowledge-intelligence-source-registry-no-go.md",
    "docs/release/knowledge-intelligence-source-registry-checklist.md",
    "docs/release/knowledge-intelligence-source-registry-evidence-matrix.md",
    "docs/adr/0171-append-only-source-provenance-registry-core.md",
]
REQUIRED_EXAMPLES = [
    "examples/knowledge-intelligence/source-registry-authorization.json",
    "examples/knowledge-intelligence/source-registry-record-envelope.json",
    "examples/knowledge-intelligence/source-registry-record.json",
    "examples/knowledge-intelligence/source-registry-proposed-batch.json",
    "examples/knowledge-intelligence/source-registry-state.json",
    "examples/knowledge-intelligence/source-registry-index.json",
    "examples/knowledge-intelligence/source-registry-query.json",
    "examples/knowledge-intelligence/source-registry-query-result.json",
    "examples/knowledge-intelligence/source-registry-integrity-report.json",
    "examples/knowledge-intelligence/source-registry-fixture-replay.json",
    "examples/knowledge-intelligence/source-registry-incident.json",
    "examples/knowledge-intelligence/source-registry-operator-review.json",
    "examples/knowledge-intelligence/source-registry-operator-review-item.json",
    "examples/knowledge-intelligence/source-registry-resource-budget.json",
    "examples/knowledge-intelligence/source-registry-runtime-hold.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-runtime-hold.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-index.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-integrity.json",
]
REQUIRED_SOURCE = [
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py",
]
PROHIBITED_SOURCE = [
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_service.py",
    "services/brain-api/src/aion_brain/api/source_registry.py",
]
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


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


for relative in REQUIRED_DOCS + REQUIRED_EXAMPLES + REQUIRED_SOURCE:
    assert (ROOT / relative).is_file(), relative
for relative in PROHIBITED_SOURCE:
    assert not (ROOT / relative).exists(), relative

program = read_json("docs/knowledge-intelligence/program-ledger.json")
auth = read_json("docs/knowledge-intelligence/authorization-ledger.json")
report = read_json("examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json")
source_auth = read_json("examples/knowledge-intelligence/source-registry-authorization.json")

assert program["program_id"] == PROGRAM_ID
assert program["program_state"] in {
    "source_provenance_registry_implemented_write_disabled_pending_closeout",
    "temporal_claim_evidence_graph_authorized_not_implemented",
    "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
    "epistemic_truth_engine_authorized_not_implemented",
}
assert program["active_knowledge_implementation_authorization_count"] == 1
if program["program_state"] == "epistemic_truth_engine_authorized_not_implemented":
    assert program["active_knowledge_implementation_authorization"] == "AION-210-KI-0004"
    assert program["active_knowledge_implementation_task"] == "AION-211"
    assert program["formal_closeout_task"] == "AION-212"
elif program["program_state"] in {
    "temporal_claim_evidence_graph_authorized_not_implemented",
    "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
}:
    assert program["active_knowledge_implementation_authorization"] == "AION-208-KI-0003"
    assert program["active_knowledge_implementation_task"] == "AION-209"
    assert program["formal_closeout_task"] == "AION-210"
else:
    assert program["active_knowledge_implementation_authorization"] == AUTH_206
    assert program["active_knowledge_implementation_task"] == "AION-207"
    assert program["formal_closeout_task"] == "AION-208"
assert program["source_provenance_registry_authorized"] is True
assert program["source_provenance_registry_implemented"] is True
assert program["source_provenance_registry_state"] == IMPLEMENTED_STATE
assert program["source_registry_runtime_enabled"] is False
assert program["source_registry_persistent_write_enabled"] is False
assert program["research_plane_implemented"] is True
assert program["research_runtime_enabled"] is False
assert program["network_access_enabled"] is False
assert program["source_body_persistence_enabled"] is False
assert program["claim_verification_enabled"] is False
assert program["knowledge_promotion_enabled"] is False
assert program["belief_mutation_enabled"] is False
assert report["decision"] == DECISION
assert report["scenario_count"] == 28
assert all(item["passed"] for item in report["scenario_results"])

active = [record for record in auth["records"] if record.get("authorization_active") is True]
closed = [
    record
    for record in auth["records"]
    if record.get("authorization_transaction_id") == AUTH_204
]
assert len(active) == 1
assert len(closed) == 1
source_records = [
    record for record in auth["records"] if record.get("authorization_transaction_id") == AUTH_206
]
assert len(source_records) == 1
record = source_records[0]
assert record["authorization_transaction_id"] == AUTH_206
assert record["approval_record_id"] == AUTH_206
assert record["candidate_id"] == "source-provenance-registry-core"
assert record["authorization_scope"] == SOURCE_SCOPE
assert record["implementation_task"] == "AION-207"
assert record["formal_closeout_task"] == "AION-208"
if program["program_state"] in {
    "temporal_claim_evidence_graph_authorized_not_implemented",
    "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
    "epistemic_truth_engine_authorized_not_implemented",
}:
    assert active[0]["authorization_transaction_id"] in {
        "AION-208-KI-0003",
        "AION-210-KI-0004",
    }
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_closed_by_task"] == "AION-208"
else:
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
assert record["authorization_reusable"] is False
assert record["parent_authorization_transaction_id"] == AUTH_204
assert record["parent_authorization_closed"] is True
assert record["parent_evaluation_id"] == "AION-RAE-001"
assert record["parent_evaluation_decision"] == DECISION
assert record["parent_main_commit"] == "a775fb18bb0027d30834d8ab2507f461013753e2"
assert set(record["authorized_capabilities"]) == AUTHORIZED_KEYS
assert all(record["authorized_capabilities"][key] is True for key in AUTHORIZED_KEYS)
assert record["resource_limits"] == RESOURCE_LIMITS
assert all(value is False for value in record["prohibited_capabilities"].values())
assert record["source_provenance_registry_implemented"] is True
assert record["source_provenance_registry_state"] == IMPLEMENTED_STATE
assert record["source_registry_runtime_enabled"] is False
assert record["source_registry_persistent_write_enabled"] is False
assert record["source_body_persistence_enabled"] is False
assert record["claim_verification_enabled"] is False
assert record["knowledge_promotion_enabled"] is False
assert record["belief_mutation_enabled"] is False
assert record["network_access_enabled"] is False
assert closed[0]["authorization_active"] is False
assert closed[0]["authorization_consumed"] is True
assert closed[0]["authorization_consumed_by_prs"] == [116, 117]
assert closed[0]["authorization_expired"] is True
assert closed[0]["authorization_reusable"] is False
assert source_auth["authorization_transaction_id"] == AUTH_206
assert source_auth["authorized_capabilities"] == record["authorized_capabilities"]
assert source_auth["prohibited_capabilities"] == record["prohibited_capabilities"]
assert source_auth["resource_limits"] == RESOURCE_LIMITS
assert "0171-append-only-source-provenance-registry-core.md" in (
    ROOT / "docs/adr/README.md"
).read_text()

for relative in REQUIRED_EXAMPLES:
    payload = read_json(relative)
    assert payload["synthetic"] is True, relative
    assert payload["read_only"] is True, relative
    assert payload["redacted"] is True, relative
    assert payload["program_id"] == PROGRAM_ID, relative
    assert payload["authorization_transaction_id"] == AUTH_206, relative
    assert payload["implementation_task"] == "AION-207", relative
    assert payload["formal_closeout_task"] == "AION-208", relative
    assert payload["source_provenance_registry_authorized"] is True, relative
    assert payload["source_provenance_registry_implemented"] is True, relative
    assert payload["source_registry_runtime_enabled"] is False, relative
    assert payload["source_registry_persistent_write_enabled"] is False, relative
    assert payload["source_body_persistence_enabled"] is False, relative
    assert payload["claim_verification_enabled"] is False, relative
    assert payload["knowledge_promotion_enabled"] is False, relative
    assert payload["belief_mutation_enabled"] is False, relative
    assert payload["runtime_effect"] is False, relative
PY

./scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh

echo "knowledge intelligence source registry authorization PASS"
