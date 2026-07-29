"""AION-225 engagement-application authorization validators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.governed_learning_memory_local_persistence_operator_evaluation import (
    AION226_AUTHORIZED_CAPABILITIES,
    AION226_PROHIBITED_CAPABILITIES,
    AION226_RESOURCE_LIMITS,
    PASS_DECISION,
    validate_evaluation_report_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
AION223_AUTHORIZATION_ID = "AION-223-GLM-0002"
AION225_AUTHORIZATION_ID = "AION-225-GLM-0003"
AION224_FEATURE_COMMIT = "f44756f4067cd381be1ebf11a6edce1e3bc8133b"
AION224_MERGE_COMMIT = "c6632a8e4985887f38400052f53f1c2a5d7882ec"
AION224_PR = 140
ENGAGEMENT_AUTHORIZATION_SCOPE = (
    "engagement-learning-candidate-non-factual-validation-operator-approval-"
    "risk-routing-bounded-adaptation-versioning-isolated-in-memory-shadow-overlay-"
    "counterfactual-evaluation-rollback-expiry-audit-core"
)
AION226_SOURCE_SCOPE = (
    "services/brain-api/src/aion_brain/contracts/governed_engagement_learning.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_candidate_binding.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_application_approval.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_adaptation_identity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_adaptation_planning.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_overlay.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_shadow_application.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_counterfactual_evaluation.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_rollback.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_integrity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_evidence.py",
)


class EngagementAuthorizationError(ValueError):
    """Raised when AION-225 authorization evidence is inconsistent."""


def load_json(relative: str, root: Path = REPO_ROOT) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise EngagementAuthorizationError(message)


def record_by_id(records: list[Mapping[str, Any]], authorization_id: str) -> Mapping[str, Any]:
    for record in records:
        if record.get("authorization_transaction_id") == authorization_id:
            return record
    fail(f"authorization record missing: {authorization_id}")


def require_false(payload: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if payload.get(key) is not False:
            fail(f"{label} expected false: {key}")


def require_true(payload: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if payload.get(key) is not True:
            fail(f"{label} expected true: {key}")


def validate_local_persistence_operator_evaluation(root: Path = REPO_ROOT) -> dict[str, Any]:
    report = validate_evaluation_report_file(
        root / "examples/governed-learning-memory/local-persistence-operator-evaluation-report.json"
    )
    if report["decision"] != PASS_DECISION or report["evaluation_passed"] is not True:
        fail("AION-225 evaluation must be exact PASS")
    if report["scenario_count"] != 28:
        fail("AION-225 scenario count mismatch")
    if not all(item["result"] == "passed" for item in report["scenario_results"]):
        fail("AION-225 scenario result mismatch")
    return report


def validate_authorization_ledgers(root: Path = REPO_ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    program = load_json("docs/governed-learning-memory/program-ledger.json", root)
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json", root)
    for label, payload in (("program", program), ("authorization", auth)):
        if payload.get("program_id") != PROGRAM_ID:
            fail(f"{label} program id mismatch")
        expected = {
            "program_state": "governed_learning_memory_engagement_application_authorized_not_implemented",
            "active_glm_implementation_authorization_count": 1,
            "active_glm_implementation_authorization": AION225_AUTHORIZATION_ID,
            "active_glm_implementation_task": "AION-226",
            "formal_closeout_task": "AION-227",
            "local_persistence_operator_evaluation_passed": True,
            "local_persistence_operator_evaluation_id": "AION-GLMPE-002",
            "local_persistence_operator_evaluation_decision": PASS_DECISION,
            "engagement_learning_application_authorized": True,
            "engagement_learning_application_implemented": False,
            "operator_invoked_engagement_shadow_application_authorized": True,
            "operator_invoked_engagement_shadow_application_available": False,
            "automatic_engagement_learning_application_enabled": False,
            "persistent_engagement_overlay_write_enabled": False,
            "production_policy_mutation_enabled": False,
            "engagement_signal_as_fact_enabled": False,
            "engagement_confidence_effect_enabled": False,
            "engagement_knowledge_effect_enabled": False,
            "cognitive_memory_write_enabled": False,
            "actual_belief_creation_enabled": False,
            "actual_belief_mutation_enabled": False,
            "network_access_enabled": False,
            "production_exposure": False,
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                fail(f"{label} {key} mismatch")
    if auth.get("active_authorizations") != [AION225_AUTHORIZATION_ID]:
        fail("active authorization list mismatch")
    records = auth.get("records")
    if not isinstance(records, list):
        fail("authorization records missing")
    parent = record_by_id(records, AION223_AUTHORIZATION_ID)
    child = record_by_id(records, AION225_AUTHORIZATION_ID)
    if (
        parent.get("authorization_active") is not False
        or parent.get("authorization_consumed") is not True
        or parent.get("authorization_consumed_by_task") != "AION-224"
        or parent.get("authorization_consumed_by_prs") != [AION224_PR]
        or parent.get("authorization_consumed_by_feature_commits") != [AION224_FEATURE_COMMIT]
        or parent.get("authorization_consumed_by_merge_commits") != [AION224_MERGE_COMMIT]
        or parent.get("authorization_expired") is not True
        or parent.get("authorization_reusable") is not False
        or parent.get("authorization_closed_by_task") != "AION-225"
    ):
        fail("AION-223-GLM-0002 closeout mismatch")
    expected_child = {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AION225_AUTHORIZATION_ID,
        "approval_record_id": AION225_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": AION223_AUTHORIZATION_ID,
        "parent_evaluation_id": "AION-GLMPE-002",
        "parent_evaluation_decision": PASS_DECISION,
        "parent_closeout_task": "AION-225",
        "parent_implementation_task": "AION-224",
        "parent_implementation_prs": [AION224_PR],
        "parent_implementation_feature_commits": [AION224_FEATURE_COMMIT],
        "parent_implementation_merge_commits": [AION224_MERGE_COMMIT],
        "candidate_id": "operator-approved-engagement-learning-shadow-application-core",
        "workstream": "governed-learning-memory-engagement-application",
        "implementation_task": "AION-226",
        "formal_closeout_task": "AION-227",
        "authorization_scope": ENGAGEMENT_AUTHORIZATION_SCOPE,
    }
    for key, value in expected_child.items():
        if child.get(key) != value:
            fail(f"AION-225-GLM-0003 {key} mismatch")
    require_true(
        child,
        (
            "authorization_transaction_approved",
            "explicit_approval_record_approval",
            "implementation_authorization_approved",
            "implementation_go_status",
            "authorization_active",
        ),
        "AION-225 authorization",
    )
    require_false(
        child,
        (
            "implementation_no_go_status",
            "authorization_consumed",
            "authorization_expired",
            "authorization_reusable",
        ),
        "AION-225 authorization",
    )
    if child.get("authorized_capabilities") != {
        key: True for key in AION226_AUTHORIZED_CAPABILITIES
    }:
        fail("authorized AION-226 capabilities mismatch")
    if child.get("prohibited_capabilities") != {
        key: False for key in AION226_PROHIBITED_CAPABILITIES
    }:
        fail("prohibited AION-226 capabilities mismatch")
    if child.get("resource_limits") != AION226_RESOURCE_LIMITS:
        fail("AION-226 resource limit mismatch")
    return program, auth


def validate_no_aion226_source(root: Path = REPO_ROOT) -> None:
    for rel in AION226_SOURCE_SCOPE:
        if (root / rel).exists():
            fail(f"AION-226 source exists during AION-225: {rel}")


def validate_engagement_examples(root: Path = REPO_ROOT) -> None:
    auth = load_json("examples/governed-learning-memory/engagement-application-authorization.json", root)
    if auth.get("authorization_transaction_id") != AION225_AUTHORIZATION_ID:
        fail("engagement authorization example mismatch")
    result = load_json("examples/governed-learning-memory/engagement-application-result.json", root)
    require_true(result, ("candidate_is_non_factual", "operator_review_required"), "engagement result")
    require_false(
        result,
        (
            "factual_effect",
            "confidence_effect",
            "knowledge_effect",
            "source_independence_effect",
            "cognitive_memory_effect",
            "belief_effect",
            "model_weight_effect",
            "production_policy_effect",
            "persistent_write_applied",
            "runtime_effect",
        ),
        "engagement result",
    )


def validate_engagement_application_authorization(root: Path = REPO_ROOT) -> None:
    validate_local_persistence_operator_evaluation(root)
    validate_authorization_ledgers(root)
    validate_no_aion226_source(root)
    validate_engagement_examples(root)


def main() -> int:
    try:
        validate_engagement_application_authorization()
    except EngagementAuthorizationError as exc:
        print(f"ERROR: {exc}")
        return 1
    print("governed learning memory engagement application authorization validator PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
