#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh

"$PYTHON_BIN" - <<'PYSCRIPT'
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
sys.path.insert(0, str(ROOT / "services/brain-api/src"))
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
AUTH_ID = "AION-210-KI-0004"
NEXT_AUTH_ID = "AION-212-KI-0005"
SUCCESSOR_AUTH_ID = "AION-214-KI-0006"
CURRENT_AUTH_ID = "AION-216-KI-0007"
FINAL_AUTH_ID = "AION-218-KI-0008"
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
FINAL_SCOPE = (
    "operator-invoked-allowlisted-public-https-fetch-dns-pinning-integrated-"
    "research-verified-candidate-pilot-operator-review-abstention-core"
)
ENGINE_STATE = "implemented_deterministic_in_memory_assessment_persistent_write_disabled"
SOURCE_FILES = [
    "services/brain-api/src/aion_brain/contracts/knowledge_epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_corroboration.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_contradiction.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_freshness.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_confidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_evidence.py",
]
REQUIRED_EXAMPLES = [
    "examples/knowledge-intelligence/epistemic-assessment-request.json",
    "examples/knowledge-intelligence/epistemic-freshness-policy.json",
    "examples/knowledge-intelligence/evidence-contribution.json",
    "examples/knowledge-intelligence/role-evidence-score.json",
    "examples/knowledge-intelligence/epistemic-scorecard-v1.json",
    "examples/knowledge-intelligence/epistemic-hard-cap-application.json",
    "examples/knowledge-intelligence/claim-epistemic-assessment.json",
    "examples/knowledge-intelligence/epistemic-assessment-batch.json",
    "examples/knowledge-intelligence/epistemic-assessment-query.json",
    "examples/knowledge-intelligence/epistemic-assessment-query-result.json",
    "examples/knowledge-intelligence/epistemic-assessment-integrity-report.json",
    "examples/knowledge-intelligence/epistemic-assessment-fixture-replay.json",
    "examples/knowledge-intelligence/epistemic-incident.json",
    "examples/knowledge-intelligence/epistemic-operator-review.json",
    "examples/knowledge-intelligence/epistemic-assessment-runtime-hold.json",
]
EXPECTED_WEIGHTS = {
    "reference_resolution": Decimal("0.10"),
    "evidence_coverage": Decimal("0.10"),
    "citation_coverage": Decimal("0.10"),
    "provenance_completeness": Decimal("0.10"),
    "source_independence": Decimal("0.25"),
    "source_quality_metadata": Decimal("0.10"),
    "valid_time_applicability": Decimal("0.08"),
    "jurisdiction_applicability": Decimal("0.06"),
    "version_applicability": Decimal("0.06"),
    "freshness": Decimal("0.05"),
}
EXPECTED_FACTORS = {
    "primary_authoritative": Decimal("1.00"),
    "official_standard": Decimal("1.00"),
    "official_government": Decimal("0.90"),
    "peer_reviewed": Decimal("0.85"),
    "vendor_primary": Decimal("0.70"),
    "institutional_primary": Decimal("0.70"),
    "reputable_secondary": Decimal("0.60"),
    "community_unverified": Decimal("0.35"),
    "unknown": Decimal("0.25"),
    "disallowed": Decimal("0.00"),
}
EXPECTED_HARD_CAP_ORDER = [
    "broken_source_registry_or_graph_integrity",
    "applicable_retraction",
    "applicable_supersession_without_current_support",
    "scope_mismatch",
    "insufficient_explicit_scope",
    "unresolved_material_opposition",
    "zero_independent_evidence_groups",
    "one_independent_evidence_group",
    "only_unknown_or_community_unverified_evidence",
    "missing_citation_coverage",
    "incomplete_provenance",
    "stale_evidence",
]


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


for relative in SOURCE_FILES:
    if not (ROOT / relative).is_file():
        raise SystemExit(f"missing AION-211 source file: {relative}")
for relative in REQUIRED_EXAMPLES:
    load_json(relative)

from aion_brain.contracts import knowledge_epistemic_assessment as contracts

if contracts.AUTHORIZATION_TRANSACTION_ID != AUTH_ID:
    raise SystemExit("authorization lineage mismatch")
if contracts.AUTHORIZATION_SCOPE != SCOPE:
    raise SystemExit("authorization scope mismatch")
if contracts.MAXIMUM_PERSISTENT_ASSESSMENT_WRITE_BATCH != 0:
    raise SystemExit("persistent assessment write budget changed")
if dict(contracts.ROLE_SCORE_WEIGHTS) != EXPECTED_WEIGHTS:
    raise SystemExit("role score weights mismatch")
if sum(contracts.ROLE_SCORE_WEIGHTS.values(), Decimal("0.00")) != Decimal("1.00"):
    raise SystemExit("role score weights do not sum to one")
if dict(contracts.SOURCE_QUALITY_METADATA_FACTORS) != EXPECTED_FACTORS:
    raise SystemExit("source quality metadata factors mismatch")
if list(contracts.HARD_CAP_ORDER) != EXPECTED_HARD_CAP_ORDER:
    raise SystemExit("hard cap order mismatch")
policy = contracts.default_scorecard_policy()
if policy.minimum_independent_support_groups != 2 or policy.minimum_independent_opposition_groups != 2:
    raise SystemExit("independence threshold mismatch")
if policy.supported_raw_score_threshold != Decimal("0.550000"):
    raise SystemExit("supported threshold mismatch")
if policy.contradicted_raw_score_threshold != Decimal("0.550000"):
    raise SystemExit("contradicted threshold mismatch")
if policy.mixed_raw_score_threshold != Decimal("0.350000"):
    raise SystemExit("mixed threshold mismatch")
if policy.dominance_margin != Decimal("0.200000"):
    raise SystemExit("dominance margin mismatch")
if policy.abstention_confidence_threshold != Decimal("0.700000"):
    raise SystemExit("abstention threshold mismatch")

program = load_json("docs/knowledge-intelligence/program-ledger.json")
auth = load_json("docs/knowledge-intelligence/authorization-ledger.json")
active = [record for record in auth["records"] if record.get("authorization_active") is True]
if len(active) != 1:
    raise SystemExit("authorization ledger must contain one active record")
record = active[0]
post_aion212 = (ROOT / "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json").exists()

def assert_runtime_disabled(payload: dict) -> None:
    if payload["program_id"] != PROGRAM_ID:
        raise SystemExit("program ID mismatch")
    if payload["epistemic_truth_engine_implemented"] is not True:
        raise SystemExit("engine implementation flag missing")
    if payload["epistemic_truth_engine_state"] != ENGINE_STATE:
        raise SystemExit("engine state mismatch")
    for false_key in (
        "epistemic_truth_engine_runtime_enabled",
        "persistent_assessment_write_enabled",
        "assessment_database_enabled",
        "absolute_truth_oracle_enabled",
        "automatic_claim_acceptance_enabled",
        "automatic_claim_rejection_enabled",
        "knowledge_promotion_enabled",
        "cognitive_belief_mutation_enabled",
        "network_access_enabled",
        "runtime_effect",
    ):
        if payload.get(false_key, False) is not False:
            raise SystemExit(f"runtime boundary flag must remain false: {false_key}")

assert_runtime_disabled(program)

closed_records = [item for item in auth["records"] if item.get("authorization_transaction_id") == AUTH_ID]
if len(closed_records) != 1:
    raise SystemExit("AION-210-KI-0004 authorization record missing")
closed_record = closed_records[0]
assert_runtime_disabled(closed_record)
if closed_record["resource_limits"]["maximum_persistent_assessment_write_batch"] != 0:
    raise SystemExit("AION-210-KI-0004 persistent-write limit mismatch")

if post_aion212:
    post_aion216 = program["program_state"] in {
        "verified_knowledge_memory_authorized_not_implemented",
        "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout",
    }
    post_aion218 = program["program_state"] == "controlled_public_research_pilot_authorized_not_implemented"
    post_aion214 = program["program_state"] in {"tool_verification_fabric_authorized_not_implemented", "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout"}
    if post_aion218:
        expected_auth = FINAL_AUTH_ID
        expected_scope = FINAL_SCOPE
        expected_task = "AION-219"
        expected_closeout = "AION-220"
    elif post_aion216:
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
    if program["authorization_transaction_id"] != expected_auth:
        raise SystemExit("post-AION-212 active authorization mismatch")
    if program["authorization_scope"] != expected_scope:
        raise SystemExit("post-AION-212 active scope mismatch")
    if program["implementation_task"] != expected_task or program["formal_closeout_task"] != expected_closeout:
        raise SystemExit("post-AION-212 task lineage mismatch")
    if record["authorization_transaction_id"] != expected_auth:
        raise SystemExit("active authorization mismatch after closeout")
    if record["authorization_scope"] != expected_scope:
        raise SystemExit("active authorization scope mismatch after closeout")
    if record["implementation_task"] != expected_task or record["formal_closeout_task"] != expected_closeout:
        raise SystemExit("active authorization task lineage mismatch after closeout")
    if closed_record["authorization_active"] is not False or closed_record["authorization_consumed"] is not True:
        raise SystemExit("AION-210-KI-0004 must be closed and consumed after AION-212")
    if closed_record["authorization_expired"] is not True or closed_record["authorization_reusable"] is not False:
        raise SystemExit("AION-210-KI-0004 post-closeout lifecycle mismatch")
else:
    if program["authorization_transaction_id"] != AUTH_ID:
        raise SystemExit("authorization transaction mismatch")
    if program["authorization_scope"] != SCOPE:
        raise SystemExit("authorization scope mismatch")
    if program["implementation_task"] != "AION-211":
        raise SystemExit("implementation task mismatch")
    if program["formal_closeout_task"] != "AION-212":
        raise SystemExit("formal closeout mismatch")
    if record["authorization_transaction_id"] != AUTH_ID:
        raise SystemExit("active authorization must be AION-210-KI-0004 before closeout")
    if record["authorization_scope"] != SCOPE:
        raise SystemExit("active authorization scope mismatch")
    if record["implementation_task"] != "AION-211" or record["formal_closeout_task"] != "AION-212":
        raise SystemExit("active authorization task lineage mismatch")
    if record["authorization_active"] is not True or record["authorization_consumed"] is not False:
        raise SystemExit("AION-210-KI-0004 must remain active and unconsumed")
    if record["authorization_expired"] is not False or record["authorization_reusable"] is not False:
        raise SystemExit("AION-210-KI-0004 lifecycle flags changed")
    if record["resource_limits"]["maximum_persistent_assessment_write_batch"] != 0:
        raise SystemExit("active authorization persistent-write limit mismatch")

scorecard = load_json("examples/knowledge-intelligence/epistemic-scorecard-v1.json")
payload = scorecard["payload"]
if payload["score_weight_sum"] != "1.00":
    raise SystemExit("example score weight sum mismatch")
if payload["hard_cap_order"] != EXPECTED_HARD_CAP_ORDER:
    raise SystemExit("example hard cap order mismatch")
if payload["model_calls_enabled"] or payload["hidden_weights_enabled"] or payload["learned_weights_enabled"]:
    raise SystemExit("scorecard example enables forbidden scoring path")

runtime_hold = load_json("examples/knowledge-intelligence/epistemic-assessment-runtime-hold.json")
hold = runtime_hold["payload"]
if hold["epistemic_truth_engine_runtime_enabled"] or hold["persistent_assessment_write_enabled"]:
    raise SystemExit("runtime hold example is not disabled")
if hold["persistent_write_rejection"]["within_budget"] is not False:
    raise SystemExit("persistent write rejection must fail closed")
PYSCRIPT

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_epistemic_assessment_contracts.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_request.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_source_quality.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_contributions.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_source_independence.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_duplicate_suppression.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_role_ambiguity.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_freshness.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_valid_time.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_jurisdiction.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_versions.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_corrections.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_retractions.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_supersession.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_contradictions.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_scorecard.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_hard_caps.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_status.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_confidence_bands.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_abstention.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_batch.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_queries.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_fixture_replay.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_integrity.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_evidence.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_no_absolute_truth.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_no_automatic_acceptance.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_no_knowledge_promotion.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_no_belief_mutation.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_no_persistent_write.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_no_runtime_registration.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_determinism.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_concurrency.py \
  services/brain-api/tests/test_knowledge_epistemic_assessment_performance.py \
  -q

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-epistemic-truth-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-claim-graph-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-source-registry-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-research-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-closeout-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

echo "knowledge intelligence epistemic assessment PASS"
