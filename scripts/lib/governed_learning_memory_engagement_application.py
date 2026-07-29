"""AION-226 engagement-learning shadow application validation helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
AUTHORIZATION_ID = "AION-225-GLM-0003"
NEXT_AUTHORIZATION_ID = "AION-227-GLM-0004"
PROGRAM_STATE = (
    "governed_learning_memory_engagement_application_implemented_shadow_only_"
    "pending_closeout"
)
POST_CLOSEOUT_PROGRAM_STATE = (
    "governed_learning_memory_controlled_local_continual_learning_pilot_"
    "authorized_not_implemented"
)
AION228_IMPLEMENTED_PROGRAM_STATE = (
    "governed_learning_memory_controlled_local_continual_learning_pilot_"
    "implemented_completed_pending_final_closeout"
)
APPLICATION_STATE = (
    "implemented_deterministic_operator_approved_non_factual_in_memory_shadow_only_"
    "pending_closeout"
)
POST_CLOSEOUT_APPLICATION_STATE = (
    "implemented_deterministic_operator_approved_non_factual_in_memory_shadow_only"
)
RUNTIME_STATE = (
    "engagement_learning_application_implemented_in_memory_shadow_only_pending_closeout"
)
POST_CLOSEOUT_RUNTIME_STATE = (
    "engagement_learning_application_implemented_in_memory_shadow_only"
)

AION226_SOURCE_SCOPE: tuple[str, ...] = (
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
AION226_SUPPORT_SCOPE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py",
    "scripts/governed-learning-memory-engagement-shadow-run.py",
)
PROHIBITED_SOURCE_PATHS: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_database.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_background_worker.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_scheduler.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_production_adapter.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_policy_writer.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_memory_writer.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_belief_writer.py",
    "services/brain-api/src/aion_brain/api/governed_engagement_learning.py",
)
DOC_PATHS: tuple[str, ...] = (
    "docs/governed-learning-memory/engagement-application-implementation.md",
    "docs/governed-learning-memory/engagement-application-contracts.md",
    "docs/governed-learning-memory/engagement-candidate-binding-implementation.md",
    "docs/governed-learning-memory/engagement-lifecycle-validation.md",
    "docs/governed-learning-memory/engagement-risk-implementation.md",
    "docs/governed-learning-memory/engagement-approval-implementation.md",
    "docs/governed-learning-memory/engagement-adaptation-identity-implementation.md",
    "docs/governed-learning-memory/engagement-conflict-implementation.md",
    "docs/governed-learning-memory/engagement-versioning-implementation.md",
    "docs/governed-learning-memory/engagement-target-policy-implementation.md",
    "docs/governed-learning-memory/engagement-overlay-implementation.md",
    "docs/governed-learning-memory/engagement-baseline-implementation.md",
    "docs/governed-learning-memory/engagement-shadow-session.md",
    "docs/governed-learning-memory/engagement-counterfactual-implementation.md",
    "docs/governed-learning-memory/engagement-metric-implementation.md",
    "docs/governed-learning-memory/engagement-rollback-implementation.md",
    "docs/governed-learning-memory/engagement-integrity-implementation.md",
    "docs/governed-learning-memory/engagement-security-review.md",
    "docs/governed-learning-memory/engagement-operator-runbook.md",
    "docs/governed-learning-memory/engagement-shadow-synthetic-pilot.md",
    "docs/governed-learning-memory/aion-226-checklist.md",
    "docs/adr/0190-operator-approved-non-factual-engagement-learning-shadow-application.md",
)
RELEASE_DOC_PATHS: tuple[str, ...] = (
    "docs/release/governed-learning-memory-engagement-application-implementation.md",
    "docs/release/governed-learning-memory-engagement-application-security-evidence.md",
    "docs/release/governed-learning-memory-engagement-shadow-synthetic-pilot.md",
    "docs/release/governed-learning-memory-engagement-application-runtime-hold.md",
    "docs/release/governed-learning-memory-engagement-application-no-go.md",
    "docs/release/governed-learning-memory-engagement-application-checklist.md",
    "docs/release/governed-learning-memory-engagement-application-evidence-matrix.md",
)
PILOT_EVIDENCE_PATH = (
    "examples/governed-learning-memory/engagement-shadow-synthetic-pilot-evidence.json"
)
STATIC_EVIDENCE_PATHS: tuple[str, ...] = (
    "operator-console-static/demo-data/governed-learning-memory-engagement-authorization.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-candidate-binding.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-lifecycle-evidence.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-risk-assessment.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-approval-bundle.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-adaptation-identity.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-conflict-report.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-version-plan.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-target-policy.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-baseline-snapshot.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-overlay-record.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-overlay-snapshot.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-counterfactual-result.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-metric-delta.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-rollback-plan.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-application-plan.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-application-result.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-integrity-report.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-synthetic-pilot.json",
    "operator-console-static/demo-data/governed-learning-memory-engagement-runtime-boundary.json",
)

TRUE_FLAGS: tuple[str, ...] = (
    "engagement_learning_application_authorized",
    "engagement_learning_application_implemented",
    "operator_invoked_engagement_shadow_application_authorized",
    "operator_invoked_engagement_shadow_application_available",
    "engagement_candidate_binding_available",
    "engagement_signal_lineage_validation_available",
    "engagement_risk_classification_available",
    "engagement_approval_evidence_validation_available",
    "engagement_separation_of_duties_available",
    "engagement_adaptation_identity_available",
    "engagement_duplicate_detection_available",
    "engagement_conflict_detection_available",
    "engagement_adaptation_versioning_available",
    "engagement_overlay_planning_available",
    "engagement_overlay_snapshot_available",
    "engagement_baseline_snapshot_available",
    "engagement_counterfactual_evaluation_available",
    "engagement_metric_delta_available",
    "engagement_expiry_available",
    "engagement_rollback_available",
    "engagement_integrity_audit_available",
    "engagement_exact_query_available",
    "synthetic_engagement_shadow_pilot_completed",
)
FALSE_FLAGS: tuple[str, ...] = (
    "automatic_engagement_learning_application_enabled",
    "background_engagement_learning_enabled",
    "scheduled_engagement_learning_enabled",
    "production_engagement_learning_enabled",
    "persistent_engagement_overlay_write_enabled",
    "aion_224_store_write_enabled",
    "production_policy_mutation_enabled",
    "production_retrieval_policy_mutation_enabled",
    "production_source_selection_mutation_enabled",
    "production_domain_routing_mutation_enabled",
    "production_verification_rule_mutation_enabled",
    "production_tool_manifest_mutation_enabled",
    "production_response_policy_mutation_enabled",
    "automatic_preference_application_enabled",
    "engagement_signal_as_fact_enabled",
    "engagement_factual_effect_enabled",
    "engagement_confidence_effect_enabled",
    "engagement_knowledge_effect_enabled",
    "engagement_source_independence_effect_enabled",
    "engagement_citation_coverage_effect_enabled",
    "engagement_provenance_effect_enabled",
    "engagement_contradiction_resolution_effect_enabled",
    "engagement_freshness_effect_enabled",
    "cognitive_memory_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "model_weight_training_enabled",
    "network_access_enabled",
    "production_exposure",
    "runtime_enabled",
    "runtime_effect",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
)
PROHIBITED_IMPORT_RE = re.compile(
    r"^\s*(import|from)\s+"
    r"(subprocess|socket|requests|httpx|aiohttp|urllib[.]request|sqlite3|git|github|selenium|playwright)"
    r"(\s|\.|$)",
    re.MULTILINE,
)
PROHIBITED_DEPENDENCY_RE = re.compile(
    r"ApprovalService|ApprovalRepository|MemoryRepository|BeliefRepository|"
    r"ControlledLocalAppendOnlyPersistenceService|production_adapter"
)


class EngagementApplicationCheckError(ValueError):
    """Raised when AION-226 validation fails."""


def load_json(relative: str, root: Path = REPO_ROOT) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise EngagementApplicationCheckError(message)


def require_file(relative: str, root: Path = REPO_ROOT) -> None:
    if not (root / relative).is_file():
        fail(f"required file missing: {relative}")


def require_absent(relative: str, root: Path = REPO_ROOT) -> None:
    if (root / relative).exists():
        fail(f"prohibited file exists: {relative}")


def require_true(payload: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if payload.get(key) is not True:
            fail(f"{label} expected true: {key}")


def require_false(payload: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if payload.get(key) is not False:
            fail(f"{label} expected false: {key}")


def validate_source_scope(root: Path = REPO_ROOT) -> None:
    for relative in (*AION226_SOURCE_SCOPE, *AION226_SUPPORT_SCOPE):
        require_file(relative, root)
    for relative in PROHIBITED_SOURCE_PATHS:
        require_absent(relative, root)
    for relative in AION226_SOURCE_SCOPE:
        text = (root / relative).read_text(encoding="utf-8")
        if PROHIBITED_IMPORT_RE.search(text):
            fail(f"prohibited runtime import in {relative}")
        if PROHIBITED_DEPENDENCY_RE.search(text):
            fail(f"prohibited mutation dependency in {relative}")
    if not (root / "scripts/governed-learning-memory-engagement-shadow-run.py").stat().st_mode & 0o111:
        fail("engagement shadow runner must be executable")


def _validate_aion225_delivery(payload: Mapping[str, Any]) -> None:
    delivery = payload.get("aion_225_delivery")
    if not isinstance(delivery, Mapping):
        fail("AION-225 delivery missing")
    expected = {
        "task_id": "AION-225",
        "branch": "phase/governed-learning-memory-local-persistence-evaluation-engagement-authorization",
        "harness_commit": "1ec76b82a4506919ea6c7a57b67fe10ebfba2612",
        "closeout_commit": "8c3c9fe06d1f3304255ab7c13ad4ba2b86cb63ad",
        "pull_requests": [141],
        "merge_commits": ["00b6f4cc4e604a2dd1af1ae255422bb7dde4a1f9"],
        "ci_result": "pass",
        "completion_timestamp": "2026-07-29T06:28:57Z",
        "evaluation_id": "AION-GLMPE-002",
        "evaluation_decision": (
            "LOCAL_APPEND_ONLY_PERSISTENCE_OPERATOR_EVALUATION_PASS_RECOMMEND_"
            "ENGAGEMENT_LEARNING_APPLICATION_AUTHORIZATION"
        ),
    }
    for key, value in expected.items():
        if delivery.get(key) != value:
            fail(f"AION-225 delivery mismatch: {key}")
    if delivery.get("feature_commits") != [
        "1ec76b82a4506919ea6c7a57b67fe10ebfba2612",
        "8c3c9fe06d1f3304255ab7c13ad4ba2b86cb63ad",
    ]:
        fail("AION-225 feature commit reconciliation mismatch")


def validate_implementation_state(root: Path = REPO_ROOT) -> None:
    for relative in (
        "docs/governed-learning-memory/program-ledger.json",
        "docs/governed-learning-memory/authorization-ledger.json",
    ):
        payload = load_json(relative, root)
        if payload.get("program_id") != PROGRAM_ID:
            fail(f"{relative} program id mismatch")
        program_state = payload.get("program_state")
        if program_state not in {
            PROGRAM_STATE,
            POST_CLOSEOUT_PROGRAM_STATE,
            AION228_IMPLEMENTED_PROGRAM_STATE,
        }:
            fail(f"{relative} program state mismatch")
        if program_state == PROGRAM_STATE:
            if payload.get("engagement_learning_application_state") != APPLICATION_STATE:
                fail(f"{relative} engagement state mismatch")
            if payload.get("active_glm_implementation_authorization_count") != 1:
                fail(f"{relative} active authorization count mismatch")
            if payload.get("active_glm_implementation_authorization") != AUTHORIZATION_ID:
                fail(f"{relative} active authorization mismatch")
            if payload.get("active_glm_implementation_task") != "AION-226":
                fail(f"{relative} implementation task mismatch")
            if payload.get("formal_closeout_task") != "AION-227":
                fail(f"{relative} formal closeout mismatch")
        else:
            if (
                payload.get("engagement_learning_application_state")
                != POST_CLOSEOUT_APPLICATION_STATE
            ):
                fail(f"{relative} post-closeout engagement state mismatch")
            if payload.get("active_glm_implementation_authorization_count") != 1:
                fail(f"{relative} post-closeout active authorization count mismatch")
            if payload.get("active_glm_implementation_authorization") != NEXT_AUTHORIZATION_ID:
                fail(f"{relative} post-closeout active authorization mismatch")
            if payload.get("active_glm_implementation_task") != "AION-228":
                fail(f"{relative} post-closeout implementation task mismatch")
            if payload.get("formal_closeout_task") != "AION-229":
                fail(f"{relative} post-closeout formal closeout mismatch")
            if payload.get("engagement_application_operator_evaluation_passed") is not True:
                fail(f"{relative} AION-227 evaluation pass projection mismatch")
            if payload.get("controlled_local_continual_learning_pilot_authorized") is not True:
                fail(f"{relative} continual-learning authorization projection mismatch")
            expected_implemented = program_state == AION228_IMPLEMENTED_PROGRAM_STATE
            if (
                payload.get("controlled_local_continual_learning_pilot_implemented")
                is not expected_implemented
            ):
                fail(f"{relative} continual-learning implementation projection mismatch")
            if expected_implemented:
                if payload.get("operator_invoked_continual_learning_pilot_available") is not True:
                    fail(f"{relative} AION-228 operator availability mismatch")
                if payload.get("deterministic_continual_learning_simulation_available") is not True:
                    fail(f"{relative} AION-228 deterministic simulation mismatch")
                if payload.get("controlled_live_pilot_completed") is not True:
                    fail(f"{relative} AION-228 live pilot completion mismatch")
                if payload.get("controlled_live_pilot_cycle_count") != 3:
                    fail(f"{relative} AION-228 live pilot cycle count mismatch")
            closeouts = payload.get("authorization_closeout_records")
            if not isinstance(closeouts, list) or not any(
                item.get("authorization_transaction_id") == AUTHORIZATION_ID
                and item.get("authorization_active") is False
                and item.get("authorization_consumed") is True
                and item.get("authorization_expired") is True
                and item.get("authorization_reusable") is False
                and item.get("authorization_closed_by_task") == "AION-227"
                for item in closeouts
                if isinstance(item, Mapping)
            ):
                fail(f"{relative} AION-225 closeout record mismatch")
        if payload.get("final_planned_glm_closeout_task") != "AION-229":
            fail(f"{relative} final planned closeout mismatch")
        require_true(payload, TRUE_FLAGS, relative)
        require_false(payload, FALSE_FLAGS, relative)
        _validate_aion225_delivery(payload)
        delivery = payload.get("aion_226_delivery")
        if not isinstance(delivery, Mapping):
            fail(f"{relative} AION-226 delivery missing")
        if program_state == PROGRAM_STATE:
            if delivery.get("authorization_state") != (
                "implementation_complete_pending_AION-227_closeout"
            ):
                fail(f"{relative} AION-226 delivery authorization state mismatch")
            if delivery.get("runtime_state") != RUNTIME_STATE:
                fail(f"{relative} AION-226 delivery runtime state mismatch")
            if delivery.get("ci_result") != "pending" or delivery.get("completion_timestamp") is not None:
                fail(f"{relative} AION-226 delivery must remain pending before PR merge")
        else:
            if delivery.get("authorization_state") != "consumed_by_AION-226_closed_by_AION-227":
                fail(f"{relative} post-closeout AION-226 authorization state mismatch")
            if delivery.get("runtime_state") != POST_CLOSEOUT_RUNTIME_STATE:
                fail(f"{relative} post-closeout AION-226 runtime state mismatch")
            if delivery.get("ci_result") != "pass":
                fail(f"{relative} post-closeout AION-226 CI mismatch")
            if delivery.get("pull_requests") != [142, 143]:
                fail(f"{relative} post-closeout AION-226 PR reconciliation mismatch")


def validate_docs_and_examples(root: Path = REPO_ROOT) -> None:
    for relative in (*DOC_PATHS, *RELEASE_DOC_PATHS, *STATIC_EVIDENCE_PATHS):
        require_file(relative, root)
    if "0190-operator-approved-non-factual-engagement-learning-shadow-application.md" not in (
        root / "docs/adr/README.md"
    ).read_text(encoding="utf-8"):
        fail("ADR 0190 missing from ADR index")


def validate_pilot_evidence(root: Path = REPO_ROOT) -> dict[str, Any]:
    report = load_json(PILOT_EVIDENCE_PATH, root)
    expected_values: dict[str, Any] = {
        "authorization_id": AUTHORIZATION_ID,
        "mode": "deterministic_simulation",
        "candidate_count": 9,
        "candidate_kind_count": 9,
        "low_risk_application_count": 4,
        "elevated_risk_application_count": 5,
        "adaptation_identity_count": 9,
        "overlay_record_count": 9,
        "overlay_snapshot_count": 1,
        "counterfactual_case_count": 9,
        "comparison_count": 9,
        "exact_replays": 1,
        "changed_replays_rejected": 1,
        "duplicate_no_ops": 1,
        "material_conflicts_abstained": 1,
        "expired_overlays": 9,
        "rolled_back_overlays": 9,
        "active_overlay_records_after_close": 0,
        "persistent_overlay_writes": 0,
        "aion_224_store_writes": 0,
        "production_policy_mutations": 0,
        "engagement_fact_promotions": 0,
        "engagement_confidence_effects": 0,
        "engagement_knowledge_effects": 0,
        "engagement_source_independence_effects": 0,
        "cognitive_memory_writes": 0,
        "actual_belief_creations": 0,
        "actual_belief_mutations": 0,
        "model_weight_changes": 0,
        "network_calls": 0,
        "integrity_passed": True,
        "temporary_files_retained": 0,
        "redacted": True,
        "runtime_effect": False,
    }
    for key, value in expected_values.items():
        if report.get(key) != value:
            fail(f"pilot evidence mismatch: {key}")
    if report.get("approval_evidence_count") != 14:
        fail("pilot approval evidence count mismatch")
    if sorted(report.get("candidate_kinds", [])) != [
        "clarification_need",
        "domain_routing",
        "preference_candidate",
        "research_gap",
        "response_quality",
        "retrieval_strategy",
        "source_selection",
        "tool_manifest_gap",
        "verification_rule",
    ]:
        fail("pilot candidate kind coverage mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", str(report.get("report_fingerprint", ""))):
        fail("pilot report fingerprint mismatch")
    return report


def validate_runtime_boundary(root: Path = REPO_ROOT) -> None:
    validate_implementation_state(root)
    report = validate_pilot_evidence(root)
    if report["active_overlay_records_after_close"] != 0:
        fail("active overlay records after close must remain zero")


def validate_implementation(root: Path = REPO_ROOT) -> None:
    validate_source_scope(root)
    validate_implementation_state(root)
    validate_docs_and_examples(root)
    validate_pilot_evidence(root)


def main() -> int:
    try:
        validate_implementation()
    except EngagementApplicationCheckError as exc:
        print(f"ERROR: {exc}")
        return 1
    print("governed learning memory engagement application validator PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
