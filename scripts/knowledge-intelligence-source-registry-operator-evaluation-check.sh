#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

if [[ "${AION_CLAIM_GRAPH_IMPLEMENTATION_CONTEXT:-}" == "1" ]]; then
  echo "PASS: AION-208 changed-path no-go deferred to AION-209 claim graph gate"
else
  ./scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh
fi

REPORT="examples/knowledge-intelligence/source-registry-operator-evaluation-report.json"
test -f "$REPORT"
"$PYTHON_BIN" -m json.tool "$REPORT" >/dev/null
"$PYTHON_BIN" -m py_compile scripts/lib/knowledge_intelligence_source_registry_operator_evaluation.py
"$PYTHON_BIN" scripts/lib/knowledge_intelligence_source_registry_operator_evaluation.py \
  --validate-report "$REPORT"

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_source_registry_operator_evaluation.py \
  services/brain-api/tests/test_knowledge_source_registry_operator_evaluation_docs.py \
  services/brain-api/tests/test_knowledge_source_registry_authorization_closeout.py \
  services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py \
  services/brain-api/tests/test_knowledge_source_registry_evaluation_repository_integrity.py \
  services/brain-api/tests/test_knowledge_claim_graph_authorization_docs.py \
  services/brain-api/tests/test_knowledge_claim_graph_authorization_validator.py \
  services/brain-api/tests/test_knowledge_claim_graph_scope_spec.py \
  services/brain-api/tests/test_knowledge_claim_graph_budget_spec.py \
  services/brain-api/tests/test_knowledge_claim_graph_threat_model.py \
  -q

PR119_JSON="$(gh pr view 119 --json number,title,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName,url)"
PR119_CHECKS_JSON="$(gh pr checks 119 --json name,state,bucket,workflow,link)"

PR119_JSON="$PR119_JSON" PR119_CHECKS_JSON="$PR119_CHECKS_JSON" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

required = {
    "brain-api-quality",
    "contract-check",
    "docker-build-core",
    "policy-check",
    "repository-hygiene",
    "sdk-cli-check",
    "sdk-quality",
}
decision = (
    "SOURCE_PROVENANCE_REGISTRY_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_AUTHORIZATION"
)
pr = json.loads(os.environ["PR119_JSON"])
checks = json.loads(os.environ["PR119_CHECKS_JSON"])
report = json.loads(Path("examples/knowledge-intelligence/source-registry-operator-evaluation-report.json").read_text())
program = json.loads(Path("docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads(Path("docs/knowledge-intelligence/authorization-ledger.json").read_text())
assert pr["number"] == 119
assert pr["state"] == "MERGED"
assert pr["baseRefName"] == "main"
assert pr["headRefName"] == "phase/knowledge-intelligence-source-provenance-registry"
assert pr["headRefOid"] == "3e95d788726be4d3f51f299aa005df87aa00375b"
assert pr["mergeCommit"]["oid"] == "14c12bebfced7fd6345c8af2899988aadfa91a44"
assert pr["mergedAt"] == "2026-07-23T19:40:40Z"
states = {item["name"]: item["state"] for item in checks}
assert required <= states.keys()
for name in required:
    assert states[name] == "SUCCESS", name

assert report["evaluation_id"] == "AION-SPRE-001"
assert report["evaluation_base_commit"] == "14c12bebfced7fd6345c8af2899988aadfa91a44"
assert report["decision"] == decision
assert report["evaluation_passed"] is True
assert report["corrective_prs"] == []
assert report["implementation_prs"] == [119]
assert report["implementation_feature_commits"] == [
    "3e95d788726be4d3f51f299aa005df87aa00375b"
]
assert report["implementation_merge_commits"] == [
    "14c12bebfced7fd6345c8af2899988aadfa91a44"
]
assert report["scenario_count"] == 28
assert all(item["passed"] is True for item in report["scenario_results"])
assert all(item["passed"] is True for item in report["hard_gate_results"])
for key in (
    "source_body_bytes_persisted",
    "persistent_registry_writes",
    "live_network_requests",
    "live_dns_requests",
    "registry_created_pull_requests",
    "registry_git_operations",
    "registry_source_mutations",
    "registry_approvals_created",
    "registry_authorizations_created",
    "claim_verifications",
    "truth_decisions",
    "confidence_calculations",
    "knowledge_promotions",
    "belief_mutations",
):
    assert report["repository_integrity"][key] == 0, key
for key in (
    "claim_verification_performed",
    "truth_decision_performed",
    "epistemic_confidence_calculated",
    "knowledge_promoted",
    "belief_created",
    "belief_mutated",
    "persistent_write_applied",
    "source_modified",
    "git_mutated",
    "pull_request_created",
    "approval_created",
    "merged",
    "runtime_effect",
):
    assert report["runtime_state"][key] is False, key

source = [
    item for item in auth["records"] if item.get("authorization_transaction_id") == "AION-206-KI-0002"
][0]
active = [item for item in auth["records"] if item.get("authorization_active") is True]
assert len(active) == 1
assert source["authorization_active"] is False
assert source["authorization_consumed"] is True
assert source["authorization_consumed_by_task"] == "AION-207"
assert source["authorization_consumed_by_prs"] == [119]
assert source["authorization_expired"] is True
assert source["authorization_reusable"] is False
assert source["authorization_closed_by_task"] == "AION-208"
assert source["source_registry_operator_evaluation_id"] == "AION-SPRE-001"
assert source["source_registry_operator_evaluation_decision"] == decision

claim = active[0]
assert claim["authorization_transaction_id"] == "AION-208-KI-0003"
assert claim["implementation_task"] == "AION-209"
assert claim["formal_closeout_task"] == "AION-210"
assert claim["authorization_scope"] == (
    "append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-"
    "version-contradiction-graph-core"
)
assert all(claim["authorized_capabilities"].values())
assert all(value is False for value in claim["prohibited_capabilities"].values())
assert claim["resource_limits"]["maximum_graph_write_batch"] == 0
assert program["active_knowledge_implementation_authorization"] == "AION-208-KI-0003"
assert program["active_knowledge_implementation_task"] == "AION-209"
assert program["formal_closeout_task"] == "AION-210"
assert program["temporal_claim_evidence_graph_authorized"] is True
if os.environ.get("AION_CLAIM_GRAPH_IMPLEMENTATION_CONTEXT") == "1":
    assert program["temporal_claim_evidence_graph_implemented"] is True
    assert program["persistent_claim_graph_write_enabled"] is False
    assert program["claim_graph_runtime_enabled"] is False
else:
    assert program["temporal_claim_evidence_graph_implemented"] is False
PY

git merge-base --is-ancestor 3e95d788726be4d3f51f299aa005df87aa00375b origin/main
git merge-base --is-ancestor 14c12bebfced7fd6345c8af2899988aadfa91a44 origin/main

if [[ "${AION_CLAIM_GRAPH_IMPLEMENTATION_CONTEXT:-}" == "1" ]]; then
  echo "PASS: inherited AION-207 branch-diff chain deferred to AION-209 claim graph gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-no-go-regression.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-runtime-hold.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-operator-evaluation-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-runtime-hold.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-closeout-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/docs-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/final-docs-audit.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/verify-no-domain-drift.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/boundary-check.sh
fi

echo "knowledge intelligence source registry operator evaluation PASS"
