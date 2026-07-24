#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

program = json.loads(Path("docs/knowledge-intelligence/program-ledger.json").read_text())
raise SystemExit(0 if program.get("program_state") == "epistemic_truth_engine_authorized_not_implemented" else 1)
PY
then
  export AION_KNOWLEDGE_POST_AION210_CONTEXT=1
fi

./scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(".")
DECISION = (
    "SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_AUTHORIZATION"
)
SCOPE = (
    "append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-"
    "version-contradiction-graph-core"
)
STATE = "implemented_append_only_in_memory_unverified_persistent_write_disabled"
POST_AION210_STATE = "epistemic_truth_engine_authorized_not_implemented"
REQUIRED_SOURCE = [
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
]
TRUE_FLAGS = [
    "temporal_claim_evidence_graph_authorized",
    "temporal_claim_evidence_graph_implemented",
    "unverified_claim_assertion_contract_available",
    "claim_scope_contract_available",
    "valid_time_interval_contract_available",
    "jurisdiction_scope_contract_available",
    "version_scope_contract_available",
    "claim_evidence_binding_available",
    "source_registry_binding_available",
    "citation_binding_available",
    "source_lineage_binding_available",
    "source_independence_group_propagation_available",
    "claim_relation_edge_available",
    "structural_conflict_candidate_detection_available",
    "temporal_overlap_detection_available",
    "jurisdiction_mismatch_detection_available",
    "version_mismatch_detection_available",
    "append_only_graph_projection_available",
    "immutable_claim_versioning_available",
    "immutable_evidence_binding_versioning_available",
    "in_memory_claim_graph_repository_available",
    "synthetic_claim_graph_fixture_replay_available",
    "deterministic_claim_graph_indexes_available",
    "bounded_claim_graph_queries_available",
    "claim_graph_integrity_audit_available",
    "claim_graph_operator_review_item_available",
]
FALSE_FLAGS = [
    "claim_graph_runtime_enabled",
    "temporal_claim_graph_runtime_enabled",
    "persistent_claim_graph_write_enabled",
    "claim_graph_persistent_write_enabled",
    "graph_database_enabled",
    "automatic_claim_extraction_enabled",
    "source_body_parsing_enabled",
    "claim_verification_enabled",
    "truth_decision_enabled",
    "epistemic_confidence_enabled",
    "contradiction_resolution_enabled",
    "automatic_claim_acceptance_enabled",
    "automatic_claim_rejection_enabled",
    "automatic_correction_effect_enabled",
    "automatic_retraction_effect_enabled",
    "knowledge_promotion_enabled",
    "verified_knowledge_creation_enabled",
    "cognitive_belief_creation_enabled",
    "cognitive_belief_mutation_enabled",
    "belief_mutation_enabled",
    "network_access_enabled",
    "public_network_fetch_enabled",
    "runtime_effect",
    "new_knowledge_implementation_authorization_created",
]

required_docs = [
    "docs/knowledge-intelligence/claim-graph-implementation.md",
    "docs/knowledge-intelligence/claim-graph-contracts.md",
    "docs/knowledge-intelligence/claim-identity-and-normalization.md",
    "docs/knowledge-intelligence/claim-scope-model.md",
    "docs/knowledge-intelligence/claim-time-model.md",
    "docs/knowledge-intelligence/claim-jurisdiction-model.md",
    "docs/knowledge-intelligence/claim-version-model.md",
    "docs/knowledge-intelligence/claim-evidence-bindings.md",
    "docs/knowledge-intelligence/claim-source-independence.md",
    "docs/knowledge-intelligence/claim-relations.md",
    "docs/knowledge-intelligence/structural-conflict-candidates.md",
    "docs/knowledge-intelligence/claim-graph-append-only-semantics.md",
    "docs/knowledge-intelligence/claim-graph-in-memory-repository.md",
    "docs/knowledge-intelligence/claim-graph-fixture-replay.md",
    "docs/knowledge-intelligence/claim-graph-indexes-and-queries.md",
    "docs/knowledge-intelligence/claim-graph-integrity-audit.md",
    "docs/knowledge-intelligence/claim-graph-security-review.md",
    "docs/knowledge-intelligence/claim-graph-operator-runbook.md",
    "docs/knowledge-intelligence/aion-209-checklist.md",
    "docs/release/knowledge-intelligence-claim-graph-implementation.md",
    "docs/release/knowledge-intelligence-claim-graph-security-evidence.md",
    "docs/release/knowledge-intelligence-claim-graph-runtime-hold.md",
    "docs/release/knowledge-intelligence-claim-graph-no-go.md",
    "docs/release/knowledge-intelligence-claim-graph-checklist.md",
    "docs/release/knowledge-intelligence-claim-graph-evidence-matrix.md",
    "docs/adr/0173-immutable-temporal-claim-evidence-graph-core.md",
]
required_examples = [
    "examples/knowledge-intelligence/unverified-claim-assertion.json",
    "examples/knowledge-intelligence/claim-scope.json",
    "examples/knowledge-intelligence/claim-evidence-binding.json",
    "examples/knowledge-intelligence/claim-relation-edge.json",
    "examples/knowledge-intelligence/structural-conflict-candidate.json",
    "examples/knowledge-intelligence/claim-graph-record-envelope.json",
    "examples/knowledge-intelligence/claim-graph-proposed-batch.json",
    "examples/knowledge-intelligence/claim-graph-state.json",
    "examples/knowledge-intelligence/claim-graph-index.json",
    "examples/knowledge-intelligence/claim-graph-query.json",
    "examples/knowledge-intelligence/claim-graph-query-result.json",
    "examples/knowledge-intelligence/claim-graph-integrity-report.json",
    "examples/knowledge-intelligence/claim-graph-fixture-replay.json",
    "examples/knowledge-intelligence/claim-graph-incident.json",
    "examples/knowledge-intelligence/claim-graph-operator-review.json",
    "examples/knowledge-intelligence/claim-graph-runtime-hold.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-index.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-integrity.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-conflict-candidates.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-runtime-hold.json",
]
for relative in [*REQUIRED_SOURCE, *required_docs, *required_examples]:
    assert (ROOT / relative).is_file(), relative

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
source = [
    record
    for record in auth["records"]
    if record.get("authorization_transaction_id") == "AION-206-KI-0002"
][0]
assert source["authorization_active"] is False
assert source["authorization_consumed"] is True
assert source["authorization_expired"] is True
assert len(active) == 1
if program["program_state"] == POST_AION210_STATE:
    assert active[0]["authorization_transaction_id"] == "AION-210-KI-0004"
    claim_matches = [
        record
        for record in auth["records"]
        if record.get("authorization_transaction_id") == "AION-208-KI-0003"
    ]
    assert len(claim_matches) == 1
    claim = claim_matches[0]
    assert claim["authorization_active"] is False
    assert claim["authorization_consumed"] is True
    assert claim["authorization_expired"] is True
    assert claim["authorization_closed_by_task"] == "AION-210"
    assert claim["claim_graph_operator_evaluation_id"] == "AION-TCGE-001"
else:
    claim = active[0]
    assert claim["authorization_active"] is True
    assert claim["authorization_consumed"] is False
    assert claim["authorization_expired"] is False
assert claim["authorization_transaction_id"] == "AION-208-KI-0003"
assert claim["approval_record_id"] == "AION-208-KI-0003"
assert claim["parent_authorization_transaction_id"] == "AION-206-KI-0002"
assert claim["parent_evaluation_id"] == "AION-SPRE-001"
assert claim["parent_evaluation_decision"] == DECISION
assert claim["candidate_id"] == "temporal-claim-evidence-graph-core"
assert claim["workstream"] == "knowledge-intelligence-temporal-claim-evidence-graph"
assert claim["implementation_task"] == "AION-209"
assert claim["formal_closeout_task"] == "AION-210"
assert claim["authorization_scope"] == SCOPE
assert claim["authorization_reusable"] is False
assert claim["temporal_claim_evidence_graph_state"] == STATE
assert program["program_state"] in {
    "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
    POST_AION210_STATE,
}
if program["program_state"] == POST_AION210_STATE:
    assert program["active_knowledge_implementation_authorization"] == "AION-210-KI-0004"
    assert program["active_knowledge_implementation_task"] == "AION-211"
    assert program["formal_closeout_task"] == "AION-212"
    assert program["new_knowledge_implementation_authorization_created"] is True
else:
    assert program["active_knowledge_implementation_authorization"] == "AION-208-KI-0003"
    assert program["active_knowledge_implementation_task"] == "AION-209"
    assert program["formal_closeout_task"] == "AION-210"
assert program["active_knowledge_implementation_authorization_count"] == 1
assert program["active_cognitive_implementation_authorization_count"] == 0
for key in TRUE_FLAGS:
    assert program.get(key) is True, key
    assert claim.get(key) is True, key
for key in FALSE_FLAGS:
    if key == "new_knowledge_implementation_authorization_created" and program["program_state"] == POST_AION210_STATE:
        assert program[key] is True, key
    else:
        assert program.get(key, False) is False, key
    assert claim.get(key, False) is False, key
assert all(claim["authorized_capabilities"].values())
assert all(value is False for value in claim["prohibited_capabilities"].values())
limits = claim["resource_limits"]
assert limits["maximum_graph_write_batch"] == 0
assert limits["maximum_source_body_bytes"] == 0
assert limits["maximum_automatic_claim_extractions"] == 0
assert limits["maximum_claim_verifications"] == 0
assert limits["maximum_truth_decisions"] == 0
assert limits["maximum_confidence_calculations"] == 0
assert limits["maximum_knowledge_promotions"] == 0
assert limits["maximum_belief_mutations"] == 0
assert limits["maximum_network_calls"] == 0

records = {record["task_id"]: record for record in program["records"]}
a208 = records["AION-208"]
assert a208["ci_result"] == "pass"
assert a208["pull_requests"] == [120]
assert a208["feature_commits"] == [
    "9450e56c31f1dd00332aa28f55b8e4f39c3aeb78",
    "94bfe497c63ec789942331e9a5aec479f8cf13cd",
]
assert a208["merge_commits"] == ["f4193e2b05da7c88031a9144181989b1ee1db7bc"]
assert a208["completion_timestamp"] == "2026-07-24T02:06:23Z"
a209 = records["AION-209"]
assert a209["branch"] == "phase/knowledge-intelligence-temporal-claim-evidence-graph"
assert a209["ci_result"] in {"pending", "pass"}
assert a209["runtime_state"] in {
    "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
    "temporal_claim_evidence_graph_implemented_write_disabled",
}
PY

echo "knowledge intelligence claim graph authorization PASS"
