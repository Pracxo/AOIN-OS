#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

REPORT="examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json"
test -f "$REPORT"
"$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
"$PYTHON_BIN" scripts/lib/knowledge_intelligence_research_operator_evaluation.py --validate-report "$REPORT"

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
REQUIRED_DOCS = [
    "docs/knowledge-intelligence/research-plane-operator-evaluation-closeout.md",
    "docs/knowledge-intelligence/research-plane-operator-evaluation-report.md",
    "docs/knowledge-intelligence/research-plane-evaluation-scenarios.md",
    "docs/knowledge-intelligence/source-provenance-registry-architecture.md",
    "docs/knowledge-intelligence/source-provenance-registry-boundary.md",
    "docs/knowledge-intelligence/source-provenance-registry-data-model.md",
    "docs/knowledge-intelligence/source-provenance-registry-persistence.md",
    "docs/knowledge-intelligence/source-provenance-registry-resource-budgets.md",
    "docs/knowledge-intelligence/source-provenance-registry-threat-model.md",
    "docs/knowledge-intelligence/source-provenance-registry-roadmap.md",
    "docs/release/knowledge-intelligence-research-evaluation-closeout.md",
    "docs/release/knowledge-intelligence-research-evaluation-checklist.md",
    "docs/release/knowledge-intelligence-research-evaluation-evidence-matrix.md",
    "docs/release/knowledge-intelligence-research-evaluation-runtime-hold.md",
    "docs/release/knowledge-intelligence-source-registry-authorization-transaction.md",
    "docs/release/knowledge-intelligence-source-registry-explicit-approval-record.md",
    "docs/release/knowledge-intelligence-source-registry-scope.md",
    "docs/release/knowledge-intelligence-source-registry-runtime-hold.md",
    "docs/release/knowledge-intelligence-source-registry-no-go.md",
    "docs/release/knowledge-intelligence-source-registry-checklist.md",
    "docs/release/knowledge-intelligence-source-registry-evidence-matrix.md",
    "docs/adr/0170-research-acquisition-evaluation-and-source-provenance-registry-authorization.md",
]
REQUIRED_EXAMPLES = [
    "examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json",
    "examples/knowledge-intelligence/research-acquisition-evaluation-scenario-summary.json",
    "examples/knowledge-intelligence/source-registry-authorization.json",
    "examples/knowledge-intelligence/source-registry-record-envelope.json",
    "examples/knowledge-intelligence/source-registry-resource-budget.json",
    "examples/knowledge-intelligence/source-registry-runtime-hold.json",
    "examples/knowledge-intelligence/source-registry-operator-review-item.json",
    "operator-console-static/demo-data/knowledge-intelligence-research-evaluation.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-runtime-hold.json",
]
SOURCE_RUNTIME_PATHS = [
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
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


for relative in REQUIRED_DOCS + REQUIRED_EXAMPLES:
    assert (ROOT / relative).is_file(), relative
for relative in SOURCE_RUNTIME_PATHS:
    assert not (ROOT / relative).exists(), relative

program = read_json("docs/knowledge-intelligence/program-ledger.json")
auth = read_json("docs/knowledge-intelligence/authorization-ledger.json")
report = read_json("examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json")
source_auth = read_json("examples/knowledge-intelligence/source-registry-authorization.json")

assert program["program_id"] == PROGRAM_ID
assert program["program_state"] == "source_provenance_registry_authorized_not_implemented"
assert program["active_knowledge_implementation_authorization"] == AUTH_206
assert program["active_knowledge_implementation_authorization_count"] == 1
assert program["active_knowledge_implementation_task"] == "AION-207"
assert program["formal_closeout_task"] == "AION-208"
assert program["source_provenance_registry_authorized"] is True
assert program["source_provenance_registry_implemented"] is False
assert program["research_plane_implemented"] is True
assert program["research_runtime_enabled"] is False
assert program["network_access_enabled"] is False
assert report["decision"] == DECISION
assert report["scenario_count"] == 28
assert all(item["passed"] for item in report["scenario_results"])
assert report["authorization_closeout"]["authorization_transaction_id"] == AUTH_204
assert report["authorization_closeout"]["authorization_active"] is False
assert report["authorization_closeout"]["authorization_consumed"] is True
assert report["authorization_closeout"]["authorization_expired"] is True
assert report["authorization_closeout"]["authorization_reusable"] is False
active = [record for record in auth["records"] if record.get("authorization_active") is True]
closed = [
    record
    for record in auth["records"]
    if record.get("authorization_transaction_id") == AUTH_204
]
assert len(active) == 1
assert len(closed) == 1
assert active[0]["authorization_transaction_id"] == AUTH_206
assert active[0]["authorization_scope"] == SOURCE_SCOPE
assert active[0]["implementation_task"] == "AION-207"
assert active[0]["formal_closeout_task"] == "AION-208"
assert active[0]["authorization_consumed"] is False
assert active[0]["authorization_expired"] is False
assert active[0]["authorization_reusable"] is False
assert set(active[0]["authorized_capabilities"]) == AUTHORIZED_KEYS
assert all(active[0]["authorized_capabilities"][key] is True for key in AUTHORIZED_KEYS)
assert active[0]["resource_limits"] == RESOURCE_LIMITS
assert all(value is False for value in active[0]["prohibited_capabilities"].values())
assert closed[0]["authorization_active"] is False
assert closed[0]["authorization_consumed"] is True
assert closed[0]["authorization_consumed_by_task"] == "AION-205"
assert closed[0]["authorization_consumed_by_prs"] == [116, 117]
assert closed[0]["authorization_closed_by_task"] == "AION-206"
assert closed[0]["authorization_expired"] is True
assert closed[0]["authorization_reusable"] is False
assert source_auth["authorization_transaction_id"] == AUTH_206
assert source_auth["authorized_capabilities"] == active[0]["authorized_capabilities"]
assert source_auth["prohibited_capabilities"] == active[0]["prohibited_capabilities"]
assert source_auth["resource_limits"] == RESOURCE_LIMITS
for relative in REQUIRED_EXAMPLES:
    payload = read_json(relative)
    assert payload["synthetic"] is True, relative
    assert payload["read_only"] is True, relative
    assert payload["redacted"] is True, relative
    assert payload["research_plane_implemented"] is True, relative
    assert payload["research_runtime_enabled"] is False, relative
    assert payload["network_access_enabled"] is False, relative
PY

./scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh

echo "knowledge intelligence source registry authorization PASS"
