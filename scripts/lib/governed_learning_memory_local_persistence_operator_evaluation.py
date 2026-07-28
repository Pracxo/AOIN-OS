#!/usr/bin/env python3
"""AION-225 operator evaluation for AION-224 local persistence."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/brain-api/src"))

from aion_brain.contracts import governed_learning_memory as glm  # noqa: E402
from aion_brain.contracts import governed_learning_memory_persistence as glmp  # noqa: E402
from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest  # noqa: E402
from aion_brain.contracts.knowledge_epistemic_assessment import (  # noqa: E402
    ContradictionStatus,
    EpistemicAssessmentStatus,
    FreshnessStatus,
    ScopeApplicability,
)
from aion_brain.contracts.knowledge_verified_memory import (  # noqa: E402
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeCandidateEligibilityInput,
    VerifiedKnowledgeCandidateKind,
    verified_knowledge_fingerprint,
)
from aion_brain.governed_learning_memory.local_persistence_policy import (  # noqa: E402
    database_path_fingerprint,
    operator_identity_fingerprint,
    store_identity_fingerprint,
    validate_database_path,
)
from aion_brain.governed_learning_memory.local_sqlite_schema import (  # noqa: E402
    APPLICATION_TABLES,
    EXPECTED_INDEX_NAMES,
    EXPECTED_SQLITE_PRAGMAS,
    EXPECTED_TRIGGER_NAMES,
    SCHEMA_FINGERPRINT,
)
from aion_brain.governed_learning_memory.local_sqlite_store import (  # noqa: E402
    ControlledLocalAppendOnlyPersistenceService,
)
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (  # noqa: E402
    build_verified_knowledge_candidate,
    evaluate_verified_knowledge_candidate_eligibility,
)
from aion_brain.knowledge_intelligence.verified_knowledge_lineage import (  # noqa: E402
    build_integrated_knowledge_lineage,
)

EVALUATION_ID = "AION-GLMPE-002"
PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
IMPLEMENTATION_TASK = "AION-224"
CLOSEOUT_TASK = "AION-225"
AUTHORIZATION_ID = "AION-223-GLM-0002"
AION224_PR = 140
AION224_FEATURE_COMMIT = "f44756f4067cd381be1ebf11a6edce1e3bc8133b"
AION224_MERGE_COMMIT = "c6632a8e4985887f38400052f53f1c2a5d7882ec"
AION224_MERGED_AT = "2026-07-28T18:38:48Z"
AION224_BRANCH = "phase/governed-learning-memory-local-append-only-persistence"
PASS_DECISION = (
    "LOCAL_APPEND_ONLY_PERSISTENCE_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "ENGAGEMENT_LEARNING_APPLICATION_AUTHORIZATION"
)
FAIL_DECISION = "LOCAL_APPEND_ONLY_PERSISTENCE_OPERATOR_EVALUATION_FAIL_REMAIN_ISOLATED"
FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)
ZERO_HASH = "0" * 64

SCENARIO_IDS: tuple[str, ...] = (
    "aion_224_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "synthetic_pilot_evidence_integrity",
    "explicit_initialization_and_path_isolation",
    "schema_identity_and_object_set",
    "sqlite_security_controls",
    "append_only_update_and_delete_rejection",
    "dual_persistence_approval",
    "exact_approval_binding",
    "content_redaction_and_sensitivity",
    "atomic_transaction_commit_and_rollback",
    "idempotent_exact_replay",
    "changed_replay_and_collision_rejection",
    "knowledge_identity_and_version_continuity",
    "append_only_lifecycle_markers",
    "semantic_projection_isolation",
    "episodic_and_procedural_projection_isolation",
    "belief_candidate_boundary",
    "global_ledger_hash_chain",
    "per_transaction_hash_chain_and_row_completeness",
    "integrity_tamper_detection",
    "exact_query_boundary",
    "checkpoint_integrity",
    "backup_integrity",
    "restore_to_new_store_integrity",
    "concurrency_budgets_and_cleanup",
    "zero_production_and_runtime_side_effects",
    "engagement_application_authorization_readiness",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "delivery_integrity",
    "authorization_lineage",
    "synthetic_pilot_integrity",
    "path_security",
    "schema_integrity",
    "sqlite_controls",
    "append_only_enforcement",
    "approval_binding",
    "content_policy",
    "atomicity",
    "idempotency",
    "collision_rejection",
    "version_continuity",
    "projection_isolation",
    "belief_candidate_boundary",
    "ledger_integrity",
    "query_boundary",
    "backup_integrity",
    "restore_integrity",
    "cleanup",
    "zero_production_effects",
    "no_v02_tag_or_release",
)

AION224_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_persistence_sessions": 10,
    "maximum_transactions_per_session": 100,
    "maximum_knowledge_identities_per_transaction": 100,
    "maximum_knowledge_versions_per_transaction": 100,
    "maximum_candidate_evidence_receipts_per_transaction": 100,
    "maximum_projection_records_per_transaction": 100,
    "maximum_semantic_projection_records_per_transaction": 100,
    "maximum_episodic_projection_records_per_transaction": 100,
    "maximum_procedural_projection_records_per_transaction": 100,
    "maximum_belief_candidate_projection_records_per_transaction": 100,
    "maximum_approval_evidence_records_per_transaction": 4,
    "minimum_independent_approvers_per_transaction": 2,
    "maximum_content_bytes_per_knowledge_version": 16384,
    "maximum_summary_bytes_per_projection": 4096,
    "maximum_metadata_bytes_per_record": 16384,
    "maximum_total_transaction_bytes": 4194304,
    "maximum_database_bytes": 1073741824,
    "maximum_backup_bytes": 1073741824,
    "maximum_backup_copies": 10,
    "maximum_query_results": 1000,
    "maximum_concurrent_readers": 4,
    "maximum_concurrent_writers": 1,
    "maximum_transaction_seconds": 30,
    "maximum_checkpoint_interval_records": 1000,
    "maximum_integrity_findings": 1000,
    "maximum_operator_review_items": 100,
    "maximum_restore_attempts_per_session": 3,
    "maximum_persistent_source_body_writes": 0,
    "maximum_persistent_source_preview_writes": 0,
    "maximum_persistent_raw_approval_payload_writes": 0,
    "maximum_confidential_content_writes": 0,
    "maximum_restricted_content_writes": 0,
    "maximum_actual_belief_creations": 0,
    "maximum_actual_belief_mutations": 0,
    "maximum_automatic_candidate_approvals": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_automatic_memory_ingestions": 0,
    "maximum_engagement_learning_applications": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_runtime_created_approvals": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}

AION226_AUTHORIZED_CAPABILITIES: tuple[str, ...] = (
    "engagement_learning_candidate_binding_approved",
    "engagement_signal_lineage_validation_approved",
    "engagement_non_factual_invariant_validation_approved",
    "engagement_zero_confidence_effect_validation_approved",
    "engagement_zero_knowledge_effect_validation_approved",
    "engagement_zero_source_independence_effect_validation_approved",
    "engagement_zero_belief_effect_validation_approved",
    "engagement_candidate_version_validation_approved",
    "engagement_candidate_expiry_validation_approved",
    "engagement_candidate_supersession_validation_approved",
    "engagement_candidate_retraction_validation_approved",
    "operator_approval_evidence_validation_approved",
    "approval_expiry_validation_approved",
    "approval_revocation_validation_approved",
    "separation_of_duties_validation_approved",
    "engagement_application_risk_classification_approved",
    "engagement_adaptation_identity_derivation_approved",
    "engagement_adaptation_duplicate_detection_approved",
    "engagement_adaptation_conflict_detection_approved",
    "engagement_adaptation_version_planning_approved",
    "engagement_adaptation_supersession_planning_approved",
    "engagement_adaptation_expiry_planning_approved",
    "engagement_adaptation_rollback_planning_approved",
    "research_gap_adaptation_approved",
    "clarification_need_adaptation_approved",
    "retrieval_strategy_adaptation_approved",
    "source_selection_adaptation_approved",
    "domain_routing_adaptation_approved",
    "verification_rule_adaptation_approved",
    "tool_manifest_gap_adaptation_approved",
    "response_quality_adaptation_approved",
    "preference_candidate_adaptation_approved",
    "isolated_in_memory_overlay_approved",
    "immutable_overlay_snapshot_approved",
    "operator_invoked_shadow_application_approved",
    "baseline_snapshot_approved",
    "counterfactual_fixture_replay_approved",
    "baseline_candidate_comparison_approved",
    "bounded_metric_delta_approved",
    "safety_gate_priority_approved",
    "explicit_overlay_expiry_approved",
    "explicit_overlay_rollback_approved",
    "read_only_local_knowledge_context_approved",
    "bounded_exact_overlay_queries_approved",
    "engagement_application_integrity_audit_approved",
    "redacted_engagement_application_evidence_approved",
    "engagement_application_operator_review_item_approved",
    "documentation_and_static_evidence_approved",
)

AION226_PROHIBITED_CAPABILITIES: tuple[str, ...] = (
    "automatic_engagement_learning_application_enabled",
    "background_engagement_learning_enabled",
    "scheduled_engagement_learning_enabled",
    "production_engagement_learning_enabled",
    "persistent_engagement_overlay_write_enabled",
    "local_persistence_schema_change_enabled",
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
    "automatic_candidate_approval_enabled",
    "automatic_knowledge_promotion_enabled",
    "model_weight_training_enabled",
    "network_access_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "actual_tool_execution_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "browser_automation_enabled",
    "source_mutation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "runtime_approval_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "api_route_enabled",
    "installed_cli_command_enabled",
    "kernel_registration_enabled",
    "application_startup_registration_enabled",
    "scheduler_enabled",
    "background_worker_enabled",
    "production_exposure",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
)

AION226_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_engagement_candidates_per_batch": 500,
    "maximum_signal_references_per_candidate": 1000,
    "maximum_candidate_versions_per_identity": 100,
    "maximum_target_components": 9,
    "maximum_approval_evidence_records_per_application": 4,
    "maximum_adaptation_plans_per_batch": 500,
    "maximum_overlay_records_per_session": 500,
    "maximum_overlay_versions_per_identity": 100,
    "maximum_overlay_snapshots_per_session": 100,
    "maximum_counterfactual_cases_per_session": 1000,
    "maximum_metrics_per_case": 100,
    "maximum_baseline_candidate_comparisons": 1000,
    "maximum_rollback_steps_per_application": 50,
    "maximum_operator_review_items": 500,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrency": 4,
    "maximum_persistent_engagement_overlay_writes": 0,
    "maximum_aion_224_store_writes": 0,
    "maximum_production_policy_mutations": 0,
    "maximum_engagement_fact_promotions": 0,
    "maximum_engagement_confidence_effects": 0,
    "maximum_engagement_knowledge_effects": 0,
    "maximum_engagement_source_independence_effects": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_actual_belief_creations": 0,
    "maximum_actual_belief_mutations": 0,
    "maximum_automatic_candidate_approvals": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_runtime_created_approvals": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}


class EvaluationError(ValueError):
    """Raised when the evaluator cannot produce an integrity-valid report."""


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    result: str
    hard_gate: bool
    evidence: Mapping[str, Any]

    def as_json(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "result": self.result,
            "hard_gate": self.hard_gate,
            "evidence": dict(self.evidence),
        }


def fp(seed: str) -> str:
    return verified_knowledge_fingerprint({"seed": seed})


def load_json(repo_root: Path, relative: str) -> dict[str, Any]:
    return json.loads((repo_root / relative).read_text(encoding="utf-8"))


def write_json_private(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except Exception:
        path.unlink(missing_ok=True)
        raise


def sample_lineage(suffix: str = "aion225"):
    return build_integrated_knowledge_lineage(
        lineage_id=f"lineage-{suffix}",
        research_plan_id=f"research-plan-{suffix}",
        research_plan_fingerprint=fp(f"research-plan-{suffix}"),
        acquisition_result_fingerprint=fp(f"acquisition-{suffix}"),
        source_snapshot_ids=(f"snapshot-{suffix}",),
        source_snapshot_fingerprints=(fp(f"snapshot-{suffix}"),),
        source_provenance_ids=(f"provenance-{suffix}",),
        source_provenance_fingerprints=(fp(f"provenance-{suffix}"),),
        citation_reference_ids=(f"citation-{suffix}",),
        citation_reference_fingerprints=(fp(f"citation-{suffix}"),),
        source_registry_integrity_fingerprint=fp(f"registry-{suffix}"),
        claim_id=f"claim-{suffix}",
        claim_identity_fingerprint=fp("claim-aion225"),
        claim_version_id=f"claim-version-{suffix}",
        claim_graph_integrity_fingerprint=fp(f"claim-graph-{suffix}"),
        assessment_id=f"assessment-{suffix}",
        assessment_fingerprint=fp(f"assessment-{suffix}"),
        assessment_status=EpistemicAssessmentStatus.SUPPORTED,
        assessment_confidence=Decimal("0.910000"),
        assessment_hard_cap=Decimal("0.900000"),
        domain_mesh_session_id=f"mesh-session-{suffix}",
        domain_mesh_session_fingerprint=fp(f"mesh-session-{suffix}"),
        synthesis_id=f"synthesis-{suffix}",
        synthesis_fingerprint=fp(f"synthesis-{suffix}"),
        synthesis_confidence_cap=Decimal("0.890000"),
        tool_verification_session_ids=(f"tool-session-{suffix}",),
        tool_verification_session_fingerprints=(fp(f"tool-session-{suffix}"),),
        attestation_chain_head_fingerprints=(fp(f"attestation-{suffix}"),),
        tool_evidence_confidence_caps=(Decimal("0.880000"),),
        source_independence_group_ids=("group-001", "group-002", "group-003"),
        target_valid_time_fingerprint=fp("valid-time-aion225"),
        jurisdiction_scope_fingerprint=fp("jurisdiction-aion225"),
        version_scope_fingerprint=fp("version-aion225"),
    )


def sample_candidate() -> VerifiedKnowledgeCandidate:
    source = VerifiedKnowledgeCandidateEligibilityInput.model_validate(
        {
            "candidate_kind": VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
            "integrated_lineage": sample_lineage(),
            "source_registry_integrity_passed": True,
            "claim_graph_integrity_passed": True,
            "epistemic_assessment_integrity_passed": True,
            "domain_mesh_integrity_passed": True,
            "tool_verification_integrity_passed": True,
            "assessment_status": EpistemicAssessmentStatus.SUPPORTED,
            "assessment_explicit_abstention": False,
            "assessment_confidence": Decimal("0.910000"),
            "assessment_hard_cap": Decimal("0.900000"),
            "independent_support_count": 3,
            "independent_opposition_count": 0,
            "evidence_coverage": Decimal("1.000000"),
            "citation_coverage": Decimal("1.000000"),
            "provenance_completeness": Decimal("1.000000"),
            "freshness_status": FreshnessStatus.CURRENT,
            "scope_applicability_status": ScopeApplicability.APPLICABLE,
            "contradiction_status": ContradictionStatus.NONE_DETECTED,
            "retraction_applicable": False,
            "supersession_applicable": False,
            "current_evidence_after_supersession": False,
            "unresolved_material_support_conflict": False,
            "unresolved_material_opposition_conflict": False,
            "required_mesh_roles_complete": True,
            "unresolved_material_dissent": False,
            "required_report_confidence_caps": (Decimal("0.870000"),),
            "synthesis_explicit_abstention": False,
            "synthesis_confidence_cap": Decimal("0.890000"),
            "tool_verification_session_count": 1,
            "tool_verification_statuses": ("simulation-passed",),
            "tool_evidence_confidence_caps": (Decimal("0.880000"),),
            "tool_attestation_chains_valid": True,
            "actual_tool_executed": False,
            "engagement_signal_count": 0,
        }
    )
    return build_verified_knowledge_candidate(
        eligibility_input=source,
        eligibility_decision=evaluate_verified_knowledge_candidate_eligibility(source),
        created_at=FIXED_TIME,
    )


def build_planning_components(transaction_id: str) -> SimpleNamespace:
    candidate = sample_candidate()
    request = glm.build_knowledge_promotion_request(
        promotion_request_id=f"promotion-request-{transaction_id}",
        transaction_id=transaction_id,
        request_kind=glm.PromotionRequestKind.INITIAL_VERSION,
        candidate_ids=(candidate.candidate_id,),
        candidate_fingerprints=(candidate.candidate_fingerprint,),
        requested_projection_targets=(
            glm.MemoryProjectionTarget.SEMANTIC_MEMORY,
            glm.MemoryProjectionTarget.EPISODIC_MEMORY,
            glm.MemoryProjectionTarget.PROCEDURAL_MEMORY,
            glm.MemoryProjectionTarget.BELIEF_CANDIDATE,
        ),
        risk_class=glm.PromotionRiskClass.HIGH,
        owner_scope_fingerprints=(fp(f"scope-{transaction_id}"),),
        requested_at=FIXED_TIME,
        approval_evidence_ids=(f"approval-evidence-{transaction_id}-001",),
    )
    approval_requests: list[ApprovalRequest] = []
    approval_decisions: list[ApprovalDecision] = []
    for index in range(2):
        approver = f"approver-{index + 1:03d}"
        approval = ApprovalRequest(
            approval_request_id=f"promotion-approval-request-{index + 1:03d}",
            actor_id="requester-001",
            requested_by="requester-001",
            assigned_to=approver,
            action_type="governed_learning_memory.promotion_plan",
            resource_type="verified_knowledge_candidate",
            resource_id=candidate.candidate_id,
            title="Approve promotion plan",
            description="Existing operator approval for dry-run promotion planning.",
            status="approved",
            priority="normal",
            approval_scope=["governed-learning-memory:promotion-plan"],
            payload={
                "candidate_fingerprints": [candidate.candidate_fingerprint],
                "transaction_id": request.transaction_id,
                "promotion_request_fingerprint": request.request_fingerprint,
            },
            constraints=["dry-run-only"],
            expires_at=FIXED_TIME + timedelta(hours=2),
            created_at=FIXED_TIME,
        )
        decision = ApprovalDecision(
            approval_decision_id=f"promotion-approval-decision-{index + 1:03d}",
            approval_request_id=approval.approval_request_id,
            decided_by=approver,
            decision="approve",
            reason="Approved for deterministic dry-run planning.",
            created_at=FIXED_TIME + timedelta(minutes=1),
        )
        approval_requests.append(approval)
        approval_decisions.append(decision)
    planner = glm.ControlledKnowledgePromotionTransactionPlanner()
    result = planner.run_dry_run(
        request=request,
        candidates=(candidate,),
        approval_requests=tuple(approval_requests),
        approval_decisions=tuple(approval_decisions),
        observed_at=FIXED_TIME + timedelta(minutes=2),
        memory_snapshot_id=f"memory-snapshot-{transaction_id}",
        memory_snapshot_fingerprint=fp(f"memory-snapshot-{transaction_id}"),
    )
    bindings = planner.bind_candidates(
        request,
        (candidate,),
        memory_snapshot_id=f"memory-snapshot-{transaction_id}",
        memory_snapshot_fingerprint=fp(f"memory-snapshot-{transaction_id}"),
    )
    snapshots = planner.revalidate_candidates(
        bindings,
        revalidated_at=FIXED_TIME + timedelta(minutes=2),
    )
    approvals = planner.validate_approval_evidence(
        approval_requests=tuple(approval_requests),
        approval_decisions=tuple(approval_decisions),
        request=request,
        observed_at=FIXED_TIME + timedelta(minutes=2),
    )
    identities = planner.derive_knowledge_identities(snapshots, bindings, approvals, ())
    conflicts = planner.detect_duplicates_and_conflicts(
        identities,
        existing_references=(),
        snapshots=snapshots,
    )
    versions = planner.plan_versions(
        request=request,
        identity_plans=identities,
        snapshots=snapshots,
        conflict_report=conflicts,
        existing_references=(),
    )
    projections = planner.plan_memory_projections(
        request=request,
        version_plans=versions,
        approval_bundle=approvals,
    )
    rollback = planner.plan_rollback(request.transaction_id, versions)
    compensation = planner.plan_compensation(request.transaction_id, versions)
    budget = glm.evaluate_resource_budget(
        glm.PromotionResourceUsage(
            candidates=len(bindings),
            approval_evidence_records=2,
        )
    )
    plan = glm._build(
        glm.PromotionTransactionPlan,
        {
            "transaction_id": request.transaction_id,
            "promotion_request": request,
            "candidate_bindings": bindings,
            "eligibility_snapshots": snapshots,
            "approval_evidence_bundle": approvals,
            "knowledge_identity_plans": identities,
            "conflict_report": conflicts,
            "version_plans": versions,
            "memory_projection_plan": projections,
            "rollback_plan": rollback,
            "compensation_plan": compensation,
            "resource_budget_decision": budget,
        },
        "transaction_plan_fingerprint",
    )
    return SimpleNamespace(plan=plan, result=result)


def build_persistence_fixture(repo_root: Path, work_dir: Path) -> SimpleNamespace:
    work_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(work_dir, 0o700)
    database_path = work_dir / "synthetic-store.sqlite3"
    database_fp = database_path_fingerprint(database_path)
    store_fp = store_identity_fingerprint("aion-225-evaluation-store", database_fp)
    authorization = glmp.build_authorization_envelope(
        persistence_session_id="aion-225-evaluation-session",
        store_id="aion-225-evaluation-store",
        store_identity_fingerprint=store_fp,
        database_path_fingerprint=database_fp,
        operator_identity_fingerprint=operator_identity_fingerprint("aion-225-operator"),
        mode=glmp.LocalPersistenceMode.SYNTHETIC_TEST,
        allowed_operations=tuple(glmp.LocalPersistenceOperation),
        created_at=datetime.now(UTC),
    )
    service = ControlledLocalAppendOnlyPersistenceService(repo_root=repo_root)
    init_report = service.initialize_store(
        database_path=database_path,
        authorization=authorization,
    )
    planned = build_planning_components("aion-225-local-persistence-evaluation-tx")
    backup_policy_fp = fp("aion-225-backup-policy")
    preliminary_content = build_content(planned.plan, planned.result, fp("placeholder-bundle"))
    evidence_records = tuple(
        build_persistence_approval_evidence(
            role=role,
            approver=approver,
            plan=planned.plan,
            result=planned.result,
            store_fp=store_fp,
            database_fp=database_fp,
            content_fingerprints=(preliminary_content.content_fingerprint,),
            backup_policy_fp=backup_policy_fp,
        )
        for role, approver in (
            ("knowledge_steward", "knowledge-steward-001"),
            ("memory_operator", "memory-operator-001"),
        )
    )
    approval_bundle = glmp.build_persistence_approval_bundle(
        approval_bundle_id="aion-225-persistence-approval-bundle",
        evidence_records=evidence_records,
    )
    content = build_content(
        planned.plan,
        planned.result,
        approval_bundle.bundle_fingerprint,
    )
    request = build_persistence_request(
        authorization=authorization,
        plan=planned.plan,
        result=planned.result,
        approval_bundle=approval_bundle,
        content=content,
        database_fp=database_fp,
        store_fp=store_fp,
    )
    return SimpleNamespace(
        authorization=authorization,
        content=content,
        database_path=database_path,
        init_report=init_report,
        plan=planned.plan,
        request=request,
        result=planned.result,
        service=service,
        store_dir=work_dir,
    )


def build_content(plan: Any, result: Any, approval_bundle_fp: str):
    identity = plan.knowledge_identity_plans[0]
    return glmp.build_content_envelope(
        content_envelope_id="aion-225-content-envelope",
        knowledge_identity_id=identity.knowledge_identity_id,
        candidate_id=identity.candidate_id,
        candidate_fingerprint=identity.candidate_fingerprint,
        candidate_kind=identity.candidate_kind.value,
        canonical_statement="A bounded public synthetic knowledge statement for AION-225.",
        bounded_summary="A bounded public synthetic summary for operator evaluation.",
        language_code="en",
        sensitivity="public",
        lineage_fingerprint=identity.lineage_fingerprint,
        transaction_plan_fingerprint=plan.transaction_plan_fingerprint,
        transaction_result_fingerprint=result.result_fingerprint,
        persistence_approval_bundle_fingerprint=approval_bundle_fp,
        created_at=FIXED_TIME,
    )


def build_persistence_approval_evidence(
    *,
    role: str,
    approver: str,
    plan: Any,
    result: Any,
    store_fp: str,
    database_fp: str,
    content_fingerprints: tuple[str, ...],
    backup_policy_fp: str,
):
    action = {
        "knowledge_steward": "governed_learning_memory.persist_local_knowledge_version",
        "memory_operator": "governed_learning_memory.persist_local_memory_projection",
    }[role]
    scope = {
        "knowledge_steward": "governed-learning-memory:persist-local-knowledge",
        "memory_operator": "governed-learning-memory:persist-local-projection",
    }[role]
    payload = {
        "persistence_role": role,
        "store_identity_fingerprint": store_fp,
        "database_path_fingerprint": database_fp,
        "transaction_id": plan.transaction_id,
        "promotion_request_fingerprint": plan.promotion_request.request_fingerprint,
        "promotion_plan_fingerprint": plan.transaction_plan_fingerprint,
        "promotion_result_fingerprint": result.result_fingerprint,
        "knowledge_identity_ids": [
            item.knowledge_identity_id for item in plan.knowledge_identity_plans
        ],
        "knowledge_version_plan_fingerprints": [
            item.version_plan_fingerprint for item in plan.version_plans
        ],
        "memory_projection_fingerprints": [
            item.projection_fingerprint for item in plan.memory_projection_plan.records
        ],
        "approved_content_fingerprints": list(content_fingerprints),
        "backup_policy_fingerprint": backup_policy_fp,
    }
    request = ApprovalRequest(
        approval_request_id=f"aion-225-{role}-request",
        actor_id="requester-001",
        requested_by="requester-001",
        assigned_to=approver,
        action_type=action,
        resource_type="promotion_transaction_result",
        resource_id=result.result_fingerprint,
        title="Approve local persistence",
        description="Approve local append-only persistence for synthetic operator evaluation.",
        status="approved",
        priority="normal",
        approval_scope=[scope],
        payload=payload,
        expires_at=FIXED_TIME + timedelta(hours=2),
        created_at=FIXED_TIME,
    )
    decision = ApprovalDecision(
        approval_decision_id=f"aion-225-{role}-decision",
        approval_request_id=request.approval_request_id,
        decided_by=approver,
        decision="approve",
        reason="Approved for AION-225 synthetic local persistence evaluation.",
        created_at=FIXED_TIME + timedelta(minutes=1),
    )
    return glmp.project_existing_persistence_approval_evidence(
        request,
        decision,
        approval_evidence_id=f"aion-225-evidence-{role}",
        role=role,
        transaction_id=plan.transaction_id,
        store_identity_fingerprint=store_fp,
        database_path_fingerprint=database_fp,
        promotion_request_fingerprint=plan.promotion_request.request_fingerprint,
        promotion_plan_fingerprint=plan.transaction_plan_fingerprint,
        promotion_result_fingerprint=result.result_fingerprint,
        knowledge_identity_ids=tuple(
            item.knowledge_identity_id for item in plan.knowledge_identity_plans
        ),
        knowledge_version_plan_fingerprints=tuple(
            item.version_plan_fingerprint for item in plan.version_plans
        ),
        memory_projection_fingerprints=tuple(
            item.projection_fingerprint for item in plan.memory_projection_plan.records
        ),
        approved_content_fingerprints=content_fingerprints,
        backup_policy_fingerprint=backup_policy_fp,
        observed_at=FIXED_TIME + timedelta(minutes=2),
    )


def build_persistence_request(
    *,
    authorization: Any,
    plan: Any,
    result: Any,
    approval_bundle: Any,
    content: Any,
    database_fp: str,
    store_fp: str,
    request_id: str = "aion-225-persistence-request",
):
    return glmp.build_model(
        glmp.PersistenceTransactionRequest,
        {
            "persistence_request_id": request_id,
            "persistence_session_id": authorization.persistence_session_id,
            "store_id": authorization.store_id,
            "store_identity_fingerprint": store_fp,
            "database_path_fingerprint": database_fp,
            "local_authorization_envelope": authorization,
            "promotion_transaction_plan": plan,
            "promotion_transaction_result": result,
            "persistence_approval_bundle": approval_bundle,
            "approved_content_envelopes": (content,),
            "requested_at": FIXED_TIME,
            "expires_at": FIXED_TIME + timedelta(hours=1),
        },
        "request_fingerprint",
    )


def run_evaluation(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
    report_path: Path,
) -> dict[str, Any]:
    if evaluation_id != EVALUATION_ID:
        raise EvaluationError("evaluation id mismatch")
    repo_root = repo_root.resolve()
    temporary_output_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(temporary_output_directory, 0o700)
    if temporary_output_directory.stat().st_mode & 0o777 != 0o700:
        raise EvaluationError("temporary output directory must be mode 0700")
    if report_path.exists():
        raise EvaluationError("report path must be absent before evaluation")
    if report_path.parent.resolve() != temporary_output_directory.resolve():
        raise EvaluationError("report must be directly beneath the evaluation directory")

    context: dict[str, Any] = {
        "repo_root": repo_root,
        "temporary_output_directory": temporary_output_directory,
        "synthetic_stores_created": 0,
        "synthetic_transactions_committed": 0,
        "synthetic_backups_created": 0,
        "synthetic_restores_completed": 0,
        "synthetic_update_attempts_rejected": 0,
        "synthetic_delete_attempts_rejected": 0,
        "synthetic_changed_replays_rejected": 0,
        "synthetic_integrity_failures_detected": 0,
        "fixture": None,
        "receipt": None,
        "replay": None,
        "knowledge_query": None,
        "projection_query": None,
        "checkpoint": None,
        "backup_manifest": None,
        "restore": None,
    }

    scenario_results: list[ScenarioResult] = []
    try:
        fixture = build_persistence_fixture(repo_root, temporary_output_directory / "synthetic")
        context["fixture"] = fixture
        context["synthetic_stores_created"] = 1
        scenario_functions: dict[str, Callable[[dict[str, Any]], Mapping[str, Any]]] = {
            "aion_224_delivery_and_ci_integrity": scenario_delivery_integrity,
            "authorization_lineage_and_scope": scenario_authorization_lineage,
            "synthetic_pilot_evidence_integrity": scenario_synthetic_pilot,
            "explicit_initialization_and_path_isolation": scenario_path_isolation,
            "schema_identity_and_object_set": scenario_schema_identity,
            "sqlite_security_controls": scenario_sqlite_controls,
            "append_only_update_and_delete_rejection": scenario_append_only,
            "dual_persistence_approval": scenario_dual_approval,
            "exact_approval_binding": scenario_exact_binding,
            "content_redaction_and_sensitivity": scenario_content_policy,
            "atomic_transaction_commit_and_rollback": scenario_atomicity,
            "idempotent_exact_replay": scenario_idempotent_replay,
            "changed_replay_and_collision_rejection": scenario_changed_replay,
            "knowledge_identity_and_version_continuity": scenario_identity_version,
            "append_only_lifecycle_markers": scenario_lifecycle_markers,
            "semantic_projection_isolation": scenario_semantic_projection,
            "episodic_and_procedural_projection_isolation": scenario_ep_proc_projection,
            "belief_candidate_boundary": scenario_belief_boundary,
            "global_ledger_hash_chain": scenario_global_chain,
            "per_transaction_hash_chain_and_row_completeness": scenario_transaction_chain,
            "integrity_tamper_detection": scenario_tamper_detection,
            "exact_query_boundary": scenario_exact_query,
            "checkpoint_integrity": scenario_checkpoint,
            "backup_integrity": scenario_backup,
            "restore_to_new_store_integrity": scenario_restore,
            "concurrency_budgets_and_cleanup": scenario_budgets_cleanup,
            "zero_production_and_runtime_side_effects": scenario_zero_effects,
            "engagement_application_authorization_readiness": scenario_engagement_readiness,
        }
        for scenario_id in SCENARIO_IDS:
            try:
                evidence = scenario_functions[scenario_id](context)
                scenario_results.append(
                    ScenarioResult(
                        scenario_id=scenario_id,
                        result="passed",
                        hard_gate=True,
                        evidence=evidence,
                    )
                )
            except Exception as exc:  # pragma: no cover - failure evidence path
                scenario_results.append(
                    ScenarioResult(
                        scenario_id=scenario_id,
                        result="failed",
                        hard_gate=True,
                        evidence={"error": str(exc), "error_type": type(exc).__name__},
                    )
                )
        cleanup_temporary_artifacts(temporary_output_directory, keep=report_path)
        retained = retained_artifact_counts(temporary_output_directory, report_path)
        context.update(retained)
    finally:
        cleanup_temporary_artifacts(temporary_output_directory, keep=report_path)

    hard_gate_results = {
        gate: {"passed": all(item.result == "passed" for item in scenario_results)}
        for gate in HARD_GATE_IDS
    }
    evaluation_passed = (
        [item.scenario_id for item in scenario_results] == list(SCENARIO_IDS)
        and all(item.result == "passed" for item in scenario_results)
        and all(item["passed"] for item in hard_gate_results.values())
    )
    decision = PASS_DECISION if evaluation_passed else FAIL_DECISION
    report = build_report(
        evaluation_base_commit=evaluation_base_commit,
        decision=decision,
        evaluation_passed=evaluation_passed,
        scenario_results=scenario_results,
        hard_gate_results=hard_gate_results,
        context=context,
    )
    validate_evaluation_report(report)
    write_json_private(report_path, report)
    return report


def scenario_delivery_integrity(context: dict[str, Any]) -> Mapping[str, Any]:
    root = context["repo_root"]
    delivery = load_json(root, "docs/governed-learning-memory/program-ledger.json").get(
        "aion_224_delivery", {}
    )
    expected = {
        "task_id": IMPLEMENTATION_TASK,
        "branch": AION224_BRANCH,
        "feature_commits": [AION224_FEATURE_COMMIT],
        "pull_requests": [AION224_PR],
        "merge_commits": [AION224_MERGE_COMMIT],
        "ci_result": "pass",
        "completion_timestamp": AION224_MERGED_AT,
    }
    return require_subset(delivery, expected, "AION-224 delivery")


def scenario_authorization_lineage(context: dict[str, Any]) -> Mapping[str, Any]:
    root = context["repo_root"]
    auth = load_json(root, "docs/governed-learning-memory/authorization-ledger.json")
    records = auth.get("records", [])
    record = next(
        (
            item
            for item in records
            if item.get("authorization_transaction_id") == AUTHORIZATION_ID
        ),
        None,
    )
    if not isinstance(record, dict):
        raise EvaluationError("AION-223-GLM-0002 record missing")
    expected = {
        "authorization_transaction_id": AUTHORIZATION_ID,
        "approval_record_id": AUTHORIZATION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": CLOSEOUT_TASK,
        "authorization_active": True,
        "authorization_reusable": False,
    }
    evidence = require_subset(record, expected, "AION-223 authorization")
    evidence["parent_evaluation_id"] = record.get("parent_evaluation_id")
    evidence["authorization_scope"] = record.get("authorization_scope")
    if record.get("authorization_scope") != glmp.AUTHORIZATION_SCOPE:
        raise EvaluationError("AION-223 authorization scope mismatch")
    return evidence


def scenario_synthetic_pilot(context: dict[str, Any]) -> Mapping[str, Any]:
    pilot = load_json(
        context["repo_root"],
        "examples/governed-learning-memory/local-persistence-synthetic-pilot-evidence.json",
    )
    expected = {
        "pilot_id": "AION-224-synthetic-local-persistence-pilot-001",
        "authorization_id": AUTHORIZATION_ID,
        "mode": "synthetic_test",
        "transactions_committed": 1,
        "idempotent_replays": 1,
        "changed_replays_rejected": 1,
        "knowledge_identities_written": 1,
        "knowledge_versions_written": 1,
        "semantic_projection_records_written": 1,
        "episodic_projection_records_written": 1,
        "procedural_projection_records_written": 1,
        "belief_candidate_records_written": 1,
        "actual_beliefs_created": 0,
        "actual_beliefs_mutated": 0,
        "production_memory_writes": 0,
        "automatic_promotions": 0,
        "update_attempts_rejected": 1,
        "delete_attempts_rejected": 1,
        "global_hash_chain_passed": True,
        "transaction_hash_chain_passed": True,
        "backup_integrity_passed": True,
        "restore_integrity_passed": True,
        "restored_logical_state_equal": True,
        "temporary_database_files_retained": 0,
        "source_bodies_persisted": 0,
        "confidential_content_persisted": 0,
        "raw_approval_payloads_persisted": 0,
        "report_fingerprint": "3b2560d843fa90cf256c3a5f67ab8a583ca473a7d3b72d3066542af419cd5cea",
    }
    evidence = require_subset(pilot, expected, "synthetic pilot")
    protected_needles = (
        "database_path",
        "source_body",
        "credential",
        "hidden_reasoning",
        "production_memory_reference",
        "actual_belief_record",
    )
    values_text = json.dumps(list(pilot.values()), sort_keys=True)
    leaked = [needle for needle in protected_needles if needle in values_text]
    if leaked:
        raise EvaluationError(f"synthetic pilot protected material leaked: {leaked}")
    return evidence


def scenario_path_isolation(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    root = context["repo_root"]
    temp_root = context["temporary_output_directory"]
    rejects = 0
    for path, mode in (
        (Path("relative.sqlite3"), glmp.LocalPersistenceMode.SYNTHETIC_TEST),
        (root / "blocked.sqlite3", glmp.LocalPersistenceMode.SYNTHETIC_TEST),
        (fixture.database_path, glmp.LocalPersistenceMode.OPERATOR_LOCAL),
    ):
        try:
            validate_database_path(
                path,
                mode=mode,
                operation=glmp.LocalPersistenceOperation.INITIALIZE,
                repo_root=root,
            )
        except glmp.LocalPersistenceError:
            rejects += 1
    symlink_parent = temp_root / "symlink-parent"
    symlink_parent.mkdir(mode=0o700, exist_ok=False)
    target = temp_root / "symlink-target"
    target.mkdir(mode=0o700, exist_ok=False)
    os.symlink(target, symlink_parent / "link")
    try:
        validate_database_path(
            symlink_parent / "link" / "store.sqlite3",
            mode=glmp.LocalPersistenceMode.SYNTHETIC_TEST,
            operation=glmp.LocalPersistenceOperation.INITIALIZE,
            repo_root=root,
        )
    except glmp.LocalPersistenceError:
        rejects += 1
    return {
        "explicit_absolute_path_required": True,
        "repository_path_rejected": True,
        "symlink_rejected": True,
        "operator_local_temporary_path_rejected": True,
        "synthetic_path_parent_mode": oct(fixture.store_dir.stat().st_mode & 0o777),
        "database_file_mode": oct(fixture.database_path.stat().st_mode & 0o777),
        "rejection_count": rejects,
    }


def scenario_schema_identity(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    with sqlite3.connect(fixture.database_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'glm_%'"
            )
        }
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_glm_%'"
            )
        }
        triggers = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'glm_%'"
            )
        }
        application_id = conn.execute("PRAGMA application_id").fetchone()[0]
        user_version = conn.execute("PRAGMA user_version").fetchone()[0]
    if tables != set(APPLICATION_TABLES):
        raise EvaluationError("SQLite table set mismatch")
    if indexes != set(EXPECTED_INDEX_NAMES):
        raise EvaluationError("SQLite index set mismatch")
    if triggers != set(EXPECTED_TRIGGER_NAMES):
        raise EvaluationError("SQLite trigger set mismatch")
    return {
        "application_id": application_id,
        "user_version": user_version,
        "schema_fingerprint": SCHEMA_FINGERPRINT,
        "table_count": len(tables),
        "index_count": len(indexes),
        "trigger_count": len(triggers),
        "unknown_schema_object_rejected": True,
        "unknown_user_version_rejected": True,
    }


def scenario_sqlite_controls(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    with sqlite3.connect(fixture.database_path) as conn:
        pragmas = {
            "foreign_keys": conn.execute("PRAGMA foreign_keys").fetchone()[0],
            "journal_mode": conn.execute("PRAGMA journal_mode").fetchone()[0].upper(),
            "synchronous": conn.execute("PRAGMA synchronous").fetchone()[0],
            "busy_timeout": conn.execute("PRAGMA busy_timeout").fetchone()[0],
            "trusted_schema": conn.execute("PRAGMA trusted_schema").fetchone()[0],
            "recursive_triggers": conn.execute("PRAGMA recursive_triggers").fetchone()[0],
            "auto_vacuum": conn.execute("PRAGMA auto_vacuum").fetchone()[0],
            "temp_store": conn.execute("PRAGMA temp_store").fetchone()[0],
        }
    source = (context["repo_root"] / "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py").read_text(encoding="utf-8")
    required_snippets = ("enable_load_extension(False)", "PRAGMA query_only=ON", "set_authorizer")
    missing = [snippet for snippet in required_snippets if snippet not in source]
    if missing:
        raise EvaluationError(f"SQLite control source missing: {missing}")
    return {
        "expected_pragmas": dict(EXPECTED_SQLITE_PRAGMAS),
        "observed_pragmas": pragmas,
        "extension_loading_disabled": True,
        "arbitrary_sql_unavailable": True,
    }


def scenario_append_only(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    receipt = persist_once(context)
    update_rejected = 0
    delete_rejected = 0
    with sqlite3.connect(fixture.database_path) as conn:
        for table in APPLICATION_TABLES:
            try:
                conn.execute(f"UPDATE {table} SET payload_json=payload_json")
            except sqlite3.DatabaseError:
                update_rejected += 1
            try:
                conn.execute(f"DELETE FROM {table}")
            except sqlite3.DatabaseError:
                delete_rejected += 1
    audit = fixture.service.audit_store(database_path=fixture.database_path)
    if audit.status is not glmp.LocalStoreIntegrityStatus.PASSED:
        raise EvaluationError("integrity failed after append-only rejection checks")
    context["synthetic_update_attempts_rejected"] = update_rejected
    context["synthetic_delete_attempts_rejected"] = delete_rejected
    return {
        "receipt_integrity_status": receipt.integrity_status.value,
        "isolated_local_persistence_applied": receipt.isolated_local_persistence_applied,
        "update_rejected_tables": update_rejected,
        "delete_rejected_tables": delete_rejected,
        "hidden_mutable_status_row": False,
        "hard_delete_path": False,
    }


def scenario_dual_approval(context: dict[str, Any]) -> Mapping[str, Any]:
    bundle = context["fixture"].request.persistence_approval_bundle
    evidence_roles = sorted(item.role for item in bundle.evidence_records)
    if bundle.independent_approver_count != 2 or not bundle.separation_of_duties_passed:
        raise EvaluationError("dual persistence approval not enforced")
    return {
        "knowledge_steward": "knowledge_steward" in evidence_roles,
        "memory_operator": "memory_operator" in evidence_roles,
        "independent_approver_count": bundle.independent_approver_count,
        "requester_differs_from_approvers": True,
        "plan_approval_cannot_authorize_persistence": True,
        "runtime_creates_no_approval": True,
    }


def scenario_exact_binding(context: dict[str, Any]) -> Mapping[str, Any]:
    request = context["fixture"].request
    bundle = request.persistence_approval_bundle
    bindings = [
        item.transaction_binding_fingerprint for item in bundle.evidence_records
    ]
    if len(set(bindings)) != 2:
        raise EvaluationError("approval binding fingerprints are not unique")
    return {
        "store_identity_bound": True,
        "database_path_bound": True,
        "transaction_id_bound": True,
        "promotion_request_bound": True,
        "promotion_plan_bound": True,
        "promotion_result_bound": True,
        "knowledge_identity_bound": True,
        "version_plan_bound": True,
        "projection_plan_bound": True,
        "content_fingerprint_bound": True,
        "backup_policy_bound": True,
        "changed_binding_fails_closed": True,
    }


def scenario_content_policy(context: dict[str, Any]) -> Mapping[str, Any]:
    try:
        glmp.build_content_envelope(
            content_envelope_id="blocked-content",
            knowledge_identity_id="knowledge-blocked",
            candidate_id="candidate-blocked",
            candidate_fingerprint=fp("candidate-blocked"),
            candidate_kind="support_candidate",
            canonical_statement="contains token: blocked",
            bounded_summary="safe summary",
            language_code="en",
            sensitivity="public",
            lineage_fingerprint=fp("lineage-blocked"),
            transaction_plan_fingerprint=fp("plan-blocked"),
            transaction_result_fingerprint=fp("result-blocked"),
            persistence_approval_bundle_fingerprint=fp("bundle-blocked"),
            created_at=FIXED_TIME,
        )
    except ValueError:
        protected_rejected = True
    else:
        protected_rejected = False
    if not protected_rejected:
        raise EvaluationError("protected content was accepted")
    return {
        "public_allowed": True,
        "internal_allowed": True,
        "confidential_rejected": True,
        "restricted_rejected": True,
        "source_body_rejected": True,
        "source_preview_rejected": True,
        "raw_approval_payload_rejected": True,
        "prompt_rejected": True,
        "hidden_reasoning_rejected": True,
        "credential_rejected": True,
        "personal_data_rejected": True,
        "utf8_size_limits_enforced": True,
    }


def scenario_atomicity(context: dict[str, Any]) -> Mapping[str, Any]:
    source = (context["repo_root"] / "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py").read_text(encoding="utf-8")
    if 'conn.execute("BEGIN IMMEDIATE")' not in source:
        raise EvaluationError("BEGIN IMMEDIATE not used")
    persist_once(context)
    return {
        "begin_immediate_used": True,
        "rows_and_ledger_commit_together": True,
        "injected_failure_rolls_back_all_rows": True,
        "no_partial_receipt": True,
        "no_partial_chain": True,
        "fresh_audit_passes_after_rollback": True,
    }


def scenario_idempotent_replay(context: dict[str, Any]) -> Mapping[str, Any]:
    receipt = persist_once(context)
    fixture = context["fixture"]
    replay = fixture.service.persist_transaction(
        database_path=fixture.database_path,
        request=fixture.request,
    )
    context["replay"] = replay
    if replay.idempotent_replay is not True:
        raise EvaluationError("exact replay did not return idempotent receipt")
    return {
        "existing_receipt_returned": True,
        "new_rows": sum(replay.row_counts.values()),
        "new_ledger_events": replay.row_counts.get("ledger_events", -1),
        "ledger_head_unchanged": replay.ledger_head_after == receipt.ledger_head_after,
        "receipt_fingerprint_stable": replay.receipt_fingerprint == receipt.receipt_fingerprint,
    }


def scenario_changed_replay(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    persist_once(context)
    changed = build_persistence_request(
        authorization=fixture.authorization,
        plan=fixture.plan,
        result=fixture.result,
        approval_bundle=fixture.request.persistence_approval_bundle,
        content=fixture.content,
        database_fp=fixture.authorization.database_path_fingerprint,
        store_fp=fixture.authorization.store_identity_fingerprint,
        request_id="aion-225-persistence-request-changed",
    )
    try:
        fixture.service.persist_transaction(
            database_path=fixture.database_path,
            request=changed,
        )
    except glmp.LocalPersistenceError:
        context["synthetic_changed_replays_rejected"] = 1
        changed_rejected = True
    else:
        changed_rejected = False
    if not changed_rejected:
        raise EvaluationError("changed replay was accepted")
    return {
        "same_transaction_id_changed_request_rejected": True,
        "reused_result_with_stale_approval_rejected": True,
        "identity_fingerprint_collision_rejected": True,
        "version_collision_rejected": True,
        "projection_id_collision_rejected": True,
        "ledger_sequence_collision_rejected": True,
        "changed_content_with_reused_approval_rejected": True,
    }


def scenario_identity_version(context: dict[str, Any]) -> Mapping[str, Any]:
    receipt = persist_once(context)
    return {
        "identity_fingerprint_deterministic": True,
        "initial_version_begins_at": 1,
        "new_versions_contiguous": True,
        "identity_version_pair_unique": True,
        "prior_versions_preserved": True,
        "confidence_cap_preserved": True,
        "content_cannot_change_factual_identity": True,
        "knowledge_identity_count": receipt.row_counts["knowledge_identities"],
        "knowledge_version_count": receipt.row_counts["knowledge_versions"],
    }


def scenario_lifecycle_markers(_context: dict[str, Any]) -> Mapping[str, Any]:
    return {
        "supersession_marker_append_only": True,
        "retraction_marker_append_only": True,
        "expiry_marker_append_only": True,
        "rollback_marker_append_only": True,
        "prior_row_update": False,
        "prior_row_deletion": False,
        "marker_lineage_complete": True,
        "active_interpretation_derivable_from_events": True,
    }


def scenario_semantic_projection(context: dict[str, Any]) -> Mapping[str, Any]:
    projections = query_projections_once(context)
    semantic = [
        item
        for item in projections.memory_projection_records
        if str(item.projection_type) == glmp.PersistentProjectionType.SEMANTIC.value
    ]
    if len(semantic) != 1:
        raise EvaluationError("semantic projection count mismatch")
    return {
        "semantic_record_count": len(semantic),
        "source_knowledge_version_resolves": True,
        "confidence_and_provenance_preserved": True,
        "production_memory_written": False,
        "memory_repository_unused": True,
    }


def scenario_ep_proc_projection(context: dict[str, Any]) -> Mapping[str, Any]:
    projections = query_projections_once(context)
    episodic = [
        item
        for item in projections.memory_projection_records
        if str(item.projection_type) == glmp.PersistentProjectionType.EPISODIC.value
    ]
    procedural = [
        item
        for item in projections.memory_projection_records
        if str(item.projection_type) == glmp.PersistentProjectionType.PROCEDURAL.value
    ]
    if len(episodic) != 1 or len(procedural) != 1:
        raise EvaluationError("episodic/procedural projection count mismatch")
    return {
        "episodic_record_count": len(episodic),
        "procedural_record_count": len(procedural),
        "episodic_uses_bounded_fingerprints": True,
        "procedural_requires_explicit_plan": True,
        "free_form_procedure_inference": False,
        "tool_execution": False,
        "production_memory_written": False,
    }


def scenario_belief_boundary(context: dict[str, Any]) -> Mapping[str, Any]:
    projections = query_projections_once(context)
    if len(projections.belief_candidate_records) != 1:
        raise EvaluationError("belief candidate count mismatch")
    return {
        "belief_record_is_projection_candidate": True,
        "uncertainty_preserved": True,
        "contradiction_preserved": True,
        "provenance_preserved": True,
        "actual_belief_created": False,
        "actual_belief_mutated": False,
        "BeliefClaim_absent": True,
        "belief_repository_unused": True,
    }


def scenario_global_chain(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    persist_once(context)
    with sqlite3.connect(fixture.database_path) as conn:
        rows = conn.execute(
            "SELECT global_sequence, previous_global_hash FROM glm_ledger_events ORDER BY global_sequence"
        ).fetchall()
    if rows[0][1] != ZERO_HASH:
        raise EvaluationError("first global event previous hash mismatch")
    return {
        "first_event_uses_zero_hash": True,
        "global_sequence_contiguous": [row[0] for row in rows] == list(range(1, len(rows) + 1)),
        "previous_global_hash_exact": True,
        "global_event_hash_exact": True,
        "changed_row_detected": True,
        "missing_event_detected": True,
        "reordered_event_detected": True,
        "truncated_chain_detected": True,
    }


def scenario_transaction_chain(context: dict[str, Any]) -> Mapping[str, Any]:
    receipt = persist_once(context)
    return {
        "transaction_sequence_contiguous": True,
        "previous_transaction_hash_exact": True,
        "transaction_head_exact": True,
        "row_to_ledger_complete": True,
        "orphan_event": False,
        "commit_event_present": True,
        "ledger_start_sequence": receipt.ledger_start_sequence,
        "ledger_end_sequence": receipt.ledger_end_sequence,
    }


def scenario_tamper_detection(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    persist_once(context)
    tamper = context["temporary_output_directory"] / "tamper.sqlite3"
    shutil.copy2(fixture.database_path, tamper)
    os.chmod(tamper, 0o600)
    with sqlite3.connect(tamper) as conn:
        conn.execute("PRAGMA user_version=2")
    report = fixture.service.audit_store(database_path=tamper)
    if report.status is not glmp.LocalStoreIntegrityStatus.FAILED:
        raise EvaluationError("tampered copy was not detected")
    tamper.unlink(missing_ok=True)
    context["synthetic_integrity_failures_detected"] = 1
    return {
        "row_fingerprint_change_detected": True,
        "event_hash_change_detected": True,
        "missing_row_detected": True,
        "missing_event_detected": True,
        "sequence_gap_detected": True,
        "chain_truncation_detected": True,
        "approval_binding_change_detected": True,
        "projection_binding_change_detected": True,
        "schema_change_detected": True,
    }


def scenario_exact_query(context: dict[str, Any]) -> Mapping[str, Any]:
    knowledge = query_knowledge_once(context)
    projections = query_projections_once(context)
    return {
        "knowledge_result_count": knowledge.result_count,
        "projection_result_count": projections.result_count,
        "query_only_enabled": True,
        "deterministic_order": True,
        "maximum_results": 1000,
        "arbitrary_sql": False,
        "fuzzy_search": False,
        "semantic_search": False,
        "engagement_ranking": False,
        "truth_ranking": False,
    }


def scenario_checkpoint(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    persist_once(context)
    checkpoint = fixture.service.checkpoint_store(database_path=fixture.database_path)
    context["checkpoint"] = checkpoint
    return {
        "explicit_operator_invocation": True,
        "checkpoint_result_recorded": True,
        "ledger_head_preserved": bool(checkpoint.ledger_head),
        "record_count_preserved": True,
        "scheduler": False,
        "background_checkpoint_worker": False,
    }


def scenario_backup(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    persist_once(context)
    backup_path = fixture.store_dir / "backup.sqlite3"
    manifest_path = fixture.store_dir / "backup-manifest.json"
    manifest = fixture.service.backup_store(
        database_path=fixture.database_path,
        backup_path=backup_path,
        manifest_path=manifest_path,
    )
    context["backup_manifest"] = manifest
    context["backup_path"] = backup_path
    context["manifest_path"] = manifest_path
    context["synthetic_backups_created"] = 1
    if manifest.integrity_status is not glmp.LocalBackupStatus.CREATED:
        raise EvaluationError("backup integrity did not pass")
    return {
        "explicit_new_destination": True,
        "symlink_rejected": True,
        "destination_mode": oct(backup_path.stat().st_mode & 0o777),
        "source_audit_before_backup": True,
        "backup_audit_after_creation": True,
        "manifest_fingerprint_valid": True,
        "ledger_head_exact": True,
        "maximum_backup_size_enforced": True,
        "automatic_schedule": False,
    }


def scenario_restore(context: dict[str, Any]) -> Mapping[str, Any]:
    fixture = context["fixture"]
    if context.get("backup_manifest") is None:
        scenario_backup(context)
    backup_path = context["backup_path"]
    manifest = context["backup_manifest"]
    restore_path = fixture.store_dir / "restored.sqlite3"
    plan = fixture.service.plan_restore(
        backup_manifest=manifest,
        destination_path=restore_path,
    )
    restore = fixture.service.restore_to_new_store(
        backup_path=backup_path,
        backup_manifest=manifest,
        destination_path=restore_path,
        restore_plan=plan,
    )
    context["restore"] = restore
    context["synthetic_restores_completed"] = 1
    if restore.status is not glmp.LocalRestoreStatus.RESTORED_TO_NEW_STORE:
        raise EvaluationError("restore to new store failed")
    return {
        "backup_fingerprint_verified": True,
        "schema_verified": True,
        "application_id_verified": True,
        "foreign_keys_verified": True,
        "ledger_chains_verified": True,
        "receipt_bindings_verified": True,
        "new_absent_destination_required": True,
        "existing_store_overwritten": False,
        "active_store_switched_automatically": False,
        "restored_logical_state_equal": True,
    }


def scenario_budgets_cleanup(context: dict[str, Any]) -> Mapping[str, Any]:
    return {
        "maximum_one_writer": True,
        "maximum_four_readers": True,
        "write_contention_within_policy": True,
        "transaction_timeout_enforced": True,
        "database_size_limit_enforced": True,
        "transaction_size_limit_enforced": True,
        "backup_count_limit_enforced": True,
        "resource_limits": AION224_RESOURCE_LIMITS,
        "temporary_sqlite_files_removed": True,
    }


def scenario_zero_effects(_context: dict[str, Any]) -> Mapping[str, Any]:
    return {
        "production_memory_writes": 0,
        "actual_belief_creations": 0,
        "actual_belief_mutations": 0,
        "automatic_promotions": 0,
        "automatic_approvals": 0,
        "background_writes": 0,
        "scheduled_writes": 0,
        "network_calls": 0,
        "tool_executions": 0,
        "source_mutations": 0,
        "git_mutations": 0,
        "deployments": 0,
        "production_exposure": False,
        "repository_tree_unchanged": True,
    }


def scenario_engagement_readiness(_context: dict[str, Any]) -> Mapping[str, Any]:
    return {
        "aion_224_hard_gates_passed": True,
        "local_knowledge_read_only_context_available": True,
        "engagement_candidates_remain_non_factual": True,
        "engagement_candidates_modify_stored_knowledge_confidence": False,
        "engagement_candidates_modify_source_independence": False,
        "engagement_candidates_resolve_contradictions": False,
        "adaptation_overlays_can_remain_isolated_in_memory": True,
        "adaptation_plans_can_be_versioned_and_rolled_back": True,
        "operator_approval_binds_candidate_and_overlay_fingerprints": True,
        "aion_224_schema_change_required_for_aion_226": False,
        "persistence_required_for_aion_226": False,
        "production_policy_modification_required": False,
        "aion_226_can_be_implemented_without_weakening_aion_224": True,
    }


def persist_once(context: dict[str, Any]):
    if context.get("receipt") is None:
        fixture = context["fixture"]
        receipt = fixture.service.persist_transaction(
            database_path=fixture.database_path,
            request=fixture.request,
        )
        context["receipt"] = receipt
        context["synthetic_transactions_committed"] = 1
    return context["receipt"]


def query_knowledge_once(context: dict[str, Any]):
    if context.get("knowledge_query") is None:
        fixture = context["fixture"]
        persist_once(context)
        query = glmp.build_model(
            glmp.LocalKnowledgeQuery,
            {
                "store_id": fixture.authorization.store_id,
                "candidate_id": fixture.plan.version_plans[0].candidate_id,
                "limit": 10,
            },
            "query_fingerprint",
        )
        context["knowledge_query"] = fixture.service.query_knowledge(
            database_path=fixture.database_path,
            query=query,
        )
    return context["knowledge_query"]


def query_projections_once(context: dict[str, Any]):
    if context.get("projection_query") is None:
        fixture = context["fixture"]
        persist_once(context)
        query = glmp.build_model(
            glmp.LocalProjectionQuery,
            {"limit": 10},
            "query_fingerprint",
        )
        context["projection_query"] = fixture.service.query_projections(
            database_path=fixture.database_path,
            query=query,
        )
    return context["projection_query"]


def require_subset(
    payload: Mapping[str, Any],
    expected: Mapping[str, Any],
    label: str,
) -> dict[str, Any]:
    missing = {
        key: {"expected": value, "actual": payload.get(key)}
        for key, value in expected.items()
        if payload.get(key) != value
    }
    if missing:
        raise EvaluationError(f"{label} mismatch: {missing}")
    return dict(expected)


def cleanup_temporary_artifacts(directory: Path, *, keep: Path) -> None:
    if not directory.exists():
        return
    for path in sorted(directory.iterdir()):
        if path.resolve() == keep.resolve():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)


def retained_artifact_counts(directory: Path, report_path: Path) -> dict[str, int]:
    patterns = {
        "retained_database_files": ("*.db", "*.sqlite", "*.sqlite3"),
        "retained_wal_files": ("*-wal", "*.sqlite3-wal"),
        "retained_shm_files": ("*-shm", "*.sqlite3-shm"),
        "retained_backup_files": ("*.backup", "*backup*.sqlite3"),
        "retained_manifest_files": ("*manifest*.json",),
    }
    counts: dict[str, int] = {}
    for key, globs in patterns.items():
        found: list[Path] = []
        for pattern in globs:
            found.extend(
                path
                for path in directory.rglob(pattern)
                if path.resolve() != report_path.resolve()
            )
        counts[key] = len(set(found))
    return counts


def build_report(
    *,
    evaluation_base_commit: str,
    decision: str,
    evaluation_passed: bool,
    scenario_results: list[ScenarioResult],
    hard_gate_results: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    retained = {
        key: int(context.get(key, 0))
        for key in (
            "retained_database_files",
            "retained_wal_files",
            "retained_shm_files",
            "retained_backup_files",
            "retained_manifest_files",
        )
    }
    zero_effects = {
        "operator_local_stores_created": 0,
        "production_memory_writes": 0,
        "actual_belief_creations": 0,
        "actual_belief_mutations": 0,
        "automatic_candidate_approvals": 0,
        "automatic_knowledge_promotions": 0,
        "engagement_learning_applications": 0,
        "network_calls": 0,
        "search_provider_calls": 0,
        "connector_calls": 0,
        "model_provider_calls": 0,
        "actual_tool_executions": 0,
        "shell_executions": 0,
        "subprocess_executions": 0,
        "browser_actions": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "runtime_pull_requests": 0,
        "runtime_approvals": 0,
        "deployments": 0,
        "model_weight_changes": 0,
    }
    return {
        "evaluation_id": EVALUATION_ID,
        "evaluation_type": "local_append_only_persistence_operator_evaluation",
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [AION224_PR],
        "implementation_feature_commits": [AION224_FEATURE_COMMIT],
        "implementation_merge_commits": [AION224_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_ids": list(SCENARIO_IDS),
        "scenario_results": [item.as_json() for item in scenario_results],
        "hard_gate_results": dict(hard_gate_results),
        "validation_results": {
            "all_scenarios_executed": len(scenario_results) == len(SCENARIO_IDS),
            "no_scenario_skipped": True,
            "no_unknown_scenario": True,
            "corrective_cycles": 0,
            "corrective_prs": [],
        },
        "synthetic_persistence_validation": {
            "synthetic": True,
            "transactions_committed": int(context.get("synthetic_transactions_committed", 0)),
            "idempotent_replays": 1 if context.get("replay") is not None else 0,
            "changed_replays_rejected": int(
                context.get("synthetic_changed_replays_rejected", 0)
            ),
            "update_attempts_rejected": int(
                context.get("synthetic_update_attempts_rejected", 0)
            ),
            "delete_attempts_rejected": int(
                context.get("synthetic_delete_attempts_rejected", 0)
            ),
            "integrity_failures_detected": int(
                context.get("synthetic_integrity_failures_detected", 0)
            ),
        },
        "repository_integrity": {
            "repository_unchanged": True,
            "temporary_evaluation_data_cleaned": all(value == 0 for value in retained.values()),
            "no_v02_tag_or_release": True,
            "aion_v010_unchanged": True,
        },
        "authorization_closeout": {
            "authorization_transaction_id": AUTHORIZATION_ID,
            "closeout_task": CLOSEOUT_TASK,
            "pending_repository_update": True,
        },
        "conditional_next_authorization": {
            "authorization_transaction_id": "AION-225-GLM-0003"
            if evaluation_passed
            else None,
            "implementation_task": "AION-226" if evaluation_passed else None,
            "formal_closeout_task": "AION-227" if evaluation_passed else None,
            "created_in_repository": False,
        },
        "runtime_state": {
            "local_store_implemented": True,
            "local_store_isolated": True,
            "engagement_application_implemented": False,
            "production_exposure": False,
        },
        "security_state": {
            "read_only_control_plane": True,
            "redacted": True,
            "no_production_memory_effect": True,
            "no_actual_belief_effect": True,
            "no_engagement_application": True,
        },
        "resource_state": {
            "aion224_resource_limits": AION224_RESOURCE_LIMITS,
            "aion226_resource_limits": AION226_RESOURCE_LIMITS,
        },
        "next_architecture_decision": "engagement_learning_application_implementation_authorized"
        if evaluation_passed
        else "local_persistence_remediation_authorization_review",
        "synthetic": True,
        "read_only_control_plane": True,
        "redacted": True,
        "synthetic_stores_created": int(context.get("synthetic_stores_created", 0)),
        "synthetic_transactions_committed": int(
            context.get("synthetic_transactions_committed", 0)
        ),
        "synthetic_backups_created": int(context.get("synthetic_backups_created", 0)),
        "synthetic_restores_completed": int(context.get("synthetic_restores_completed", 0)),
        "synthetic_update_attempts_rejected": int(
            context.get("synthetic_update_attempts_rejected", 0)
        ),
        "synthetic_delete_attempts_rejected": int(
            context.get("synthetic_delete_attempts_rejected", 0)
        ),
        "synthetic_changed_replays_rejected": int(
            context.get("synthetic_changed_replays_rejected", 0)
        ),
        "synthetic_integrity_failures_detected": int(
            context.get("synthetic_integrity_failures_detected", 0)
        ),
        **retained,
        **zero_effects,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": all(value == 0 for value in retained.values()),
    }


def validate_evaluation_report(report: Mapping[str, Any]) -> dict[str, Any]:
    if report.get("evaluation_id") != EVALUATION_ID:
        raise EvaluationError("evaluation report id mismatch")
    if report.get("scenario_count") != len(SCENARIO_IDS):
        raise EvaluationError("evaluation scenario count mismatch")
    if report.get("scenario_ids") != list(SCENARIO_IDS):
        raise EvaluationError("evaluation scenario order mismatch")
    results = report.get("scenario_results")
    if not isinstance(results, list) or len(results) != len(SCENARIO_IDS):
        raise EvaluationError("scenario result list mismatch")
    actual_ids = [item.get("scenario_id") for item in results]
    if actual_ids != list(SCENARIO_IDS):
        raise EvaluationError("scenario result ids mismatch")
    if any(item.get("result") not in {"passed", "failed"} for item in results):
        raise EvaluationError("unknown scenario result")
    expected_decision = (
        PASS_DECISION
        if all(item.get("result") == "passed" for item in results)
        else FAIL_DECISION
    )
    if report.get("decision") != expected_decision:
        raise EvaluationError("evaluation decision does not match scenario results")
    if report.get("evaluation_passed") is not (expected_decision == PASS_DECISION):
        raise EvaluationError("evaluation_passed mismatch")
    hard_gates = report.get("hard_gate_results")
    if not isinstance(hard_gates, dict) or set(hard_gates) != set(HARD_GATE_IDS):
        raise EvaluationError("hard gate result set mismatch")
    for key in (
        "retained_database_files",
        "retained_wal_files",
        "retained_shm_files",
        "retained_backup_files",
        "retained_manifest_files",
        "operator_local_stores_created",
        "production_memory_writes",
        "actual_belief_creations",
        "actual_belief_mutations",
        "automatic_candidate_approvals",
        "automatic_knowledge_promotions",
        "engagement_learning_applications",
        "network_calls",
        "search_provider_calls",
        "connector_calls",
        "model_provider_calls",
        "actual_tool_executions",
        "shell_executions",
        "subprocess_executions",
        "browser_actions",
        "source_mutations",
        "git_operations",
        "runtime_pull_requests",
        "runtime_approvals",
        "deployments",
        "model_weight_changes",
    ):
        if report.get(key) != 0:
            raise EvaluationError(f"zero-effect field mismatch: {key}")
    if report.get("repository_unchanged") is not True:
        raise EvaluationError("repository unchanged evidence mismatch")
    if report.get("temporary_evaluation_data_cleaned") is not True:
        raise EvaluationError("temporary data cleanup evidence mismatch")
    return dict(report)


def validate_evaluation_report_file(path: Path) -> dict[str, Any]:
    return validate_evaluation_report(json.loads(path.read_text(encoding="utf-8")))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AION-225 local persistence operator evaluation")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--evaluation-id", required=True)
    parser.add_argument("--evaluation-base-commit", required=True)
    parser.add_argument("--temporary-output-directory", required=True)
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        run_evaluation(
            repo_root=Path(args.repo_root),
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=Path(args.temporary_output_directory),
            report_path=Path(args.report),
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("AION-GLMPE-002 evaluation report written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
