#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/knowledge-intelligence-claim-graph-no-go-regression.sh
./scripts/knowledge-intelligence-claim-graph-authorization-check.sh

"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/unverified-claim-assertion.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-scope.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-evidence-binding.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-relation-edge.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/structural-conflict-candidate.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-record-envelope.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-proposed-batch.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-state.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-index.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-query.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-query-result.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-integrity-report.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-fixture-replay.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-incident.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-operator-review.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/claim-graph-runtime-hold.json >/dev/null

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(".")
adr = (ROOT / "docs/adr/README.md").read_text()
assert "0173-immutable-temporal-claim-evidence-graph-core.md" in adr
for relative in (
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
):
    path = ROOT / relative
    data = json.loads(path.read_text())
    assert data["synthetic"] is True
    assert data["read_only"] is True
    assert data["redacted"] is True
    assert data["program_id"] == "AION-KNOWLEDGE-INTELLIGENCE-001"
    assert data["authorization_transaction_id"] == "AION-208-KI-0003"
    assert data["implementation_task"] == "AION-209"
    assert data["formal_closeout_task"] == "AION-210"
    assert data["temporal_claim_evidence_graph_implemented"] is True
    assert data["claim_graph_runtime_enabled"] is False
    assert data["persistent_claim_graph_write_enabled"] is False
    assert data["truth_decision_enabled"] is False
    assert data["epistemic_confidence_enabled"] is False
    assert data["knowledge_promotion_enabled"] is False
    assert data["belief_mutation_enabled"] is False
PY

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_claim_graph_contracts.py \
  services/brain-api/tests/test_knowledge_claim_graph_object_values.py \
  services/brain-api/tests/test_knowledge_claim_graph_claim_identity.py \
  services/brain-api/tests/test_knowledge_claim_graph_scope.py \
  services/brain-api/tests/test_knowledge_claim_graph_temporal.py \
  services/brain-api/tests/test_knowledge_claim_graph_jurisdiction.py \
  services/brain-api/tests/test_knowledge_claim_graph_versions.py \
  services/brain-api/tests/test_knowledge_claim_graph_evidence_binding.py \
  services/brain-api/tests/test_knowledge_claim_graph_source_independence.py \
  services/brain-api/tests/test_knowledge_claim_graph_relations.py \
  services/brain-api/tests/test_knowledge_claim_graph_structural_conflicts.py \
  services/brain-api/tests/test_knowledge_claim_graph_projection.py \
  services/brain-api/tests/test_knowledge_claim_graph_budget.py \
  services/brain-api/tests/test_knowledge_claim_graph_repository.py \
  services/brain-api/tests/test_knowledge_claim_graph_fixture_replay.py \
  services/brain-api/tests/test_knowledge_claim_graph_indexes.py \
  services/brain-api/tests/test_knowledge_claim_graph_queries.py \
  services/brain-api/tests/test_knowledge_claim_graph_integrity.py \
  services/brain-api/tests/test_knowledge_claim_graph_versioning.py \
  services/brain-api/tests/test_knowledge_claim_graph_idempotency.py \
  services/brain-api/tests/test_knowledge_claim_graph_evidence.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_source_body.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_automatic_extraction.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_truth_decision.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_confidence.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_contradiction_resolution.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_knowledge_promotion.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_belief_mutation.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_persistent_write.py \
  services/brain-api/tests/test_knowledge_claim_graph_no_runtime_registration.py \
  services/brain-api/tests/test_knowledge_claim_graph_determinism.py \
  services/brain-api/tests/test_knowledge_claim_graph_concurrency.py \
  services/brain-api/tests/test_knowledge_claim_graph_performance.py \
  -q

AION_CLAIM_GRAPH_IMPLEMENTATION_CONTEXT=1 AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-closeout-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/docs-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/final-docs-audit.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/verify-no-domain-drift.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/boundary-check.sh

echo "knowledge intelligence claim graph PASS"
