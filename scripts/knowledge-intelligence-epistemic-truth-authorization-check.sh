#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh

"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-truth-authorization.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-scorecard.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-resource-budget.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-runtime-hold.json >/dev/null

"$PYTHON_BIN" - <<'PYSCRIPT'
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AUTH_ID = "AION-210-KI-0004"
SCOPE = (
    "deterministic-evidence-corroboration-contradiction-freshness-source-"
    "independence-confidence-assessment-core"
)
RESOURCE_LIMITS = {
    "maximum_claims_per_assessment_batch": 500,
    "maximum_evidence_bindings_per_claim": 100,
    "maximum_source_registry_references_per_claim": 50,
    "maximum_citation_references_per_claim": 50,
    "maximum_lineage_groups_per_claim": 20,
    "maximum_relation_edges_per_claim": 100,
    "maximum_reason_codes_per_assessment": 50,
    "maximum_operator_review_items": 500,
    "maximum_epistemic_assessments": 500,
    "maximum_confidence_calculations": 500,
    "maximum_benchmark_cases": 1000,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrent_assessments": 4,
    "maximum_persistent_assessment_write_batch": 0,
    "maximum_source_body_bytes": 0,
    "maximum_automatic_claim_extractions": 0,
    "maximum_absolute_truth_decisions": 0,
    "maximum_automatic_claim_acceptances": 0,
    "maximum_automatic_claim_rejections": 0,
    "maximum_contradiction_resolutions": 0,
    "maximum_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


program = load("docs/knowledge-intelligence/program-ledger.json")
auth = load("docs/knowledge-intelligence/authorization-ledger.json")
example = load("examples/knowledge-intelligence/epistemic-truth-authorization.json")
runtime = load("examples/knowledge-intelligence/epistemic-runtime-hold.json")
records = auth["records"]
active = [record for record in records if record.get("authorization_active") is True]
assert len(active) == 1
record = active[0]
assert record["authorization_transaction_id"] == AUTH_ID
assert record["approval_record_id"] == AUTH_ID
assert record["candidate_id"] == "epistemic-truth-engine-core"
assert record["workstream"] == "knowledge-intelligence-epistemic-truth-engine"
assert record["implementation_task"] == "AION-211"
assert record["formal_closeout_task"] == "AION-212"
assert record["authorization_scope"] == SCOPE
assert record["resource_limits"] == RESOURCE_LIMITS
assert record["authorization_active"] is True
assert record["authorization_consumed"] is False
assert record["authorization_expired"] is False
assert record["authorization_reusable"] is False
assert all(record["authorized_capabilities"].values())
assert all(value is False for value in record["prohibited_capabilities"].values())
assert program["active_knowledge_implementation_authorization"] == AUTH_ID
assert program["active_knowledge_implementation_authorization_count"] == 1
assert program["active_knowledge_implementation_task"] == "AION-211"
assert program["formal_closeout_task"] == "AION-212"
assert program["epistemic_truth_engine_authorized"] is True
assert program["epistemic_truth_engine_implemented"] is True
assert example["authorization_transaction_id"] == AUTH_ID
assert example["authorization_scope"] == SCOPE
assert example["epistemic_truth_engine_implemented"] is True
assert example["epistemic_truth_engine_runtime_enabled"] is False
assert runtime["epistemic_truth_engine_implemented"] is True
assert runtime["epistemic_truth_engine_runtime_enabled"] is False
assert runtime["persistent_assessment_write_enabled"] is False
PYSCRIPT

if is_nested_gate_context; then
  echo "PASS: focused epistemic truth pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_knowledge_epistemic_truth_authorization_docs.py \
    services/brain-api/tests/test_knowledge_epistemic_truth_authorization_validator.py \
    services/brain-api/tests/test_knowledge_epistemic_truth_scope_spec.py \
    services/brain-api/tests/test_knowledge_epistemic_truth_budget_spec.py \
    services/brain-api/tests/test_knowledge_epistemic_truth_scorecard_spec.py \
    services/brain-api/tests/test_knowledge_epistemic_truth_threat_model.py \
    -q
fi

echo "knowledge intelligence epistemic truth authorization PASS"
