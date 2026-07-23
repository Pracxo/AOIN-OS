#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

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
required_docs = [
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-architecture.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-boundary.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-data-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-relations.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-time-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-jurisdiction-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-version-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-resource-budgets.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-threat-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-roadmap.md",
    "docs/release/knowledge-intelligence-claim-graph-authorization-transaction.md",
    "docs/release/knowledge-intelligence-claim-graph-explicit-approval-record.md",
    "docs/release/knowledge-intelligence-claim-graph-scope.md",
    "docs/release/knowledge-intelligence-claim-graph-runtime-hold.md",
    "docs/release/knowledge-intelligence-claim-graph-no-go.md",
    "docs/release/knowledge-intelligence-claim-graph-checklist.md",
    "docs/release/knowledge-intelligence-claim-graph-evidence-matrix.md",
    "docs/adr/0172-source-provenance-registry-evaluation-and-temporal-claim-evidence-graph-authorization.md",
]
required_examples = [
    "examples/knowledge-intelligence/claim-graph-authorization.json",
    "examples/knowledge-intelligence/unverified-claim-assertion.json",
    "examples/knowledge-intelligence/claim-evidence-binding.json",
    "examples/knowledge-intelligence/claim-relation-edge.json",
    "examples/knowledge-intelligence/temporal-claim-evidence-graph.json",
    "examples/knowledge-intelligence/claim-graph-resource-budget.json",
    "examples/knowledge-intelligence/claim-graph-runtime-hold.json",
    "examples/knowledge-intelligence/claim-graph-operator-review-item.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-runtime-hold.json",
]
for relative in required_docs + required_examples:
    assert (ROOT / relative).is_file(), relative
program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
report = json.loads((ROOT / "examples/knowledge-intelligence/source-registry-operator-evaluation-report.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
source = [
    record for record in auth["records"] if record.get("authorization_transaction_id") == "AION-206-KI-0002"
][0]
assert report["decision"] == DECISION
assert source["authorization_active"] is False
assert source["authorization_consumed"] is True
assert source["authorization_expired"] is True
assert source["authorization_reusable"] is False
assert source["authorization_closed_by_task"] == "AION-208"
assert len(active) == 1
claim = active[0]
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
assert claim["authorization_active"] is True
assert claim["authorization_consumed"] is False
assert claim["authorization_expired"] is False
assert claim["authorization_reusable"] is False
assert all(claim["authorized_capabilities"].values())
assert all(value is False for value in claim["prohibited_capabilities"].values())
assert claim["resource_limits"]["maximum_graph_write_batch"] == 0
assert claim["resource_limits"]["maximum_source_body_bytes"] == 0
assert claim["resource_limits"]["maximum_claim_verifications"] == 0
assert claim["resource_limits"]["maximum_truth_decisions"] == 0
assert claim["resource_limits"]["maximum_confidence_calculations"] == 0
assert claim["resource_limits"]["maximum_knowledge_promotions"] == 0
assert claim["resource_limits"]["maximum_belief_mutations"] == 0
assert claim["resource_limits"]["maximum_network_calls"] == 0
assert program["active_knowledge_implementation_authorization"] == "AION-208-KI-0003"
assert program["active_knowledge_implementation_task"] == "AION-209"
assert program["formal_closeout_task"] == "AION-210"
assert program["temporal_claim_evidence_graph_authorized"] is True
assert program["temporal_claim_evidence_graph_implemented"] is False
for relative in (
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
):
    assert not (ROOT / relative).exists(), relative
PY

echo "knowledge intelligence claim graph authorization PASS"
