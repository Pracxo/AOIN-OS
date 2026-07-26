#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh

"$PYTHON_BIN" - <<'PYSCRIPT'
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
AUTH_ID = "AION-210-KI-0004"
NEXT_AUTH_ID = "AION-212-KI-0005"
SUCCESSOR_AUTH_ID = "AION-214-KI-0006"
CURRENT_AUTH_ID = "AION-216-KI-0007"
SCOPE = (
    "deterministic-evidence-corroboration-contradiction-freshness-source-"
    "independence-confidence-assessment-core"
)
NEXT_SCOPE = (
    "deterministic-domain-taxonomy-expert-profile-routing-independent-analysis-"
    "deliberation-disagreement-synthesis-abstention-core"
)
SUCCESSOR_SCOPE = (
    "deterministic-tool-manifest-intent-plan-simulation-verification-"
    "attestation-effect-evidence-rollback-abstention-core"
)
CURRENT_SCOPE = (
    "deterministic-verified-knowledge-candidate-lineage-versioning-"
    "revalidation-operator-review-engagement-learning-abstention-core"
)
ENGINE_STATE = "implemented_deterministic_in_memory_assessment_persistent_write_disabled"


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


program = load("docs/knowledge-intelligence/program-ledger.json")
auth = load("docs/knowledge-intelligence/authorization-ledger.json")
active = [record for record in auth["records"] if record.get("authorization_active") is True]
if len(active) != 1:
    raise SystemExit("exactly one active Knowledge Intelligence authorization is required")
post_aion212 = (
    ROOT / "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json"
).exists()
if post_aion212:
    post_aion216 = program["program_state"] == "verified_knowledge_memory_authorized_not_implemented"
    post_aion214 = program["program_state"] in {"tool_verification_fabric_authorized_not_implemented", "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout"}
    if post_aion216:
        expected_auth = CURRENT_AUTH_ID
        expected_scope = CURRENT_SCOPE
        expected_task = "AION-217"
        expected_closeout = "AION-218"
    elif post_aion214:
        expected_auth = SUCCESSOR_AUTH_ID
        expected_scope = SUCCESSOR_SCOPE
        expected_task = "AION-215"
        expected_closeout = "AION-216"
    else:
        expected_auth = NEXT_AUTH_ID
        expected_scope = NEXT_SCOPE
        expected_task = "AION-213"
        expected_closeout = "AION-214"
    if active[0]["authorization_transaction_id"] != expected_auth:
        raise SystemExit("post-AION-212 active authorization mismatch")
    assert active[0]["approval_record_id"] == expected_auth
    assert active[0]["implementation_task"] == expected_task
    assert active[0]["formal_closeout_task"] == expected_closeout
    assert active[0]["authorization_scope"] == expected_scope
    matches = [
        item for item in auth["records"] if item.get("authorization_transaction_id") == AUTH_ID
    ]
    assert len(matches) == 1
    record = matches[0]
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["authorization_closed_by_task"] == "AION-212"
    assert program["active_knowledge_implementation_authorization"] == expected_auth
    assert program["active_knowledge_implementation_authorization_count"] == 1
    assert program["active_knowledge_implementation_task"] == expected_task
    assert program["formal_closeout_task"] == expected_closeout
else:
    record = active[0]
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
    assert program["active_knowledge_implementation_authorization"] == AUTH_ID
    assert program["active_knowledge_implementation_authorization_count"] == 1
    assert program["active_knowledge_implementation_task"] == "AION-211"
    assert program["formal_closeout_task"] == "AION-212"
assert record["authorization_transaction_id"] == AUTH_ID
assert record["approval_record_id"] == AUTH_ID
assert record["parent_authorization_transaction_id"] == "AION-208-KI-0003"
assert record["parent_closeout_task"] == "AION-210"
assert record["parent_evaluation_id"] == "AION-TCGE-001"
assert record["parent_evaluation_decision"] == (
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "EPISTEMIC_TRUTH_ENGINE_AUTHORIZATION"
)
assert record["implementation_task"] == "AION-211"
assert record["formal_closeout_task"] == "AION-212"
assert record["authorization_scope"] == SCOPE
assert all(record["authorized_capabilities"].values())
assert all(value is False for value in record["prohibited_capabilities"].values())
assert record["resource_limits"]["maximum_persistent_assessment_write_batch"] == 0
expected_program_scope = (
    CURRENT_SCOPE
    if post_aion212 and program["program_state"] == "verified_knowledge_memory_authorized_not_implemented"
    else
    SUCCESSOR_SCOPE
    if post_aion212 and program["program_state"] in {"tool_verification_fabric_authorized_not_implemented", "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout"}
    else NEXT_SCOPE if post_aion212 else SCOPE
)
assert program["authorization_scope"] == expected_program_scope
assert program["epistemic_truth_engine_authorized"] is True
assert program["epistemic_truth_engine_implemented"] is True
assert program["epistemic_truth_engine_state"] == ENGINE_STATE
assert record["epistemic_truth_engine_implemented"] is True
assert record["epistemic_truth_engine_state"] == ENGINE_STATE
for key in (
    "epistemic_truth_engine_runtime_enabled",
    "persistent_assessment_write_enabled",
    "assessment_database_enabled",
    "absolute_truth_oracle_enabled",
    "automatic_claim_acceptance_enabled",
    "automatic_claim_rejection_enabled",
    "contradiction_resolution_enabled",
    "knowledge_promotion_enabled",
    "cognitive_belief_mutation_enabled",
    "network_access_enabled",
    "runtime_effect",
):
    assert program.get(key, False) is False, key
    assert record.get(key, False) is False, key
PYSCRIPT

aion_confirm_immutable_v01_tag_history >/dev/null

echo "knowledge intelligence epistemic truth authorization no-go PASS"
