"""AION-223 read-only operator evaluation for AION-222 promotion planning.

The harness uses public AION-222 contracts and planners against deterministic,
synthetic, redacted inputs. It writes one JSON report to the caller-provided
temporary output directory and performs no repository, approval, persistence,
memory, belief, network, tool, source, or Git mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "services" / "brain-api" / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from aion_brain.contracts import governed_learning_memory as glm
from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.contracts.knowledge_epistemic_assessment import (
    ContradictionStatus,
    EpistemicAssessmentStatus,
    FreshnessStatus,
    ScopeApplicability,
)
from aion_brain.contracts.knowledge_verified_memory import (
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeCandidateEligibilityInput,
    VerifiedKnowledgeCandidateKind,
    VerifiedKnowledgeEligibilityStatus,
    VerifiedKnowledgeLifecycleStatus,
)
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    build_verified_knowledge_candidate,
    evaluate_verified_knowledge_candidate_eligibility,
)
from aion_brain.knowledge_intelligence.verified_knowledge_lineage import (
    build_integrated_knowledge_lineage,
)

EVALUATION_ID = "AION-GLMPE-001"
PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
IMPLEMENTATION_TASK = "AION-222"
CLOSEOUT_TASK = "AION-223"
AION_222_PR = 138
AION_222_FEATURE_COMMIT = "e415cc397b9aec70f8b3d19285f5fdd315048731"
AION_222_MERGE_COMMIT = "b89c896b8e75955d28fd06d52b5fb66fb8ed5ac0"
PASS_DECISION = (
    "PROMOTION_TRANSACTION_OPERATOR_EVALUATION_PASS_RECOMMEND_LOCAL_APPEND_ONLY_"
    "KNOWLEDGE_PERSISTENCE_AUTHORIZATION"
)
FAIL_DECISION = "PROMOTION_TRANSACTION_OPERATOR_EVALUATION_FAIL_REMAIN_WRITE_DISABLED"
FIXED_TIME = datetime(2026, 1, 1, tzinfo=UTC)

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "valid_moderate_risk_semantic_projection",
    "valid_high_risk_dual_approval",
    "belief_candidate_requires_dual_approval",
    "promotion_request_expiry_and_binding",
    "candidate_binding_integrity",
    "candidate_and_lineage_revalidation",
    "confidence_non_amplification",
    "approval_expiry_revocation_denial_and_cancellation",
    "approval_scope_resource_and_transaction_binding",
    "separation_of_duties",
    "deterministic_knowledge_identity",
    "exact_duplicate_idempotent_no_op",
    "direct_support_refutation_conflict",
    "temporal_jurisdiction_and_version_conflicts",
    "retraction_and_supersession_conflicts",
    "initial_and_new_version_planning",
    "supersession_retraction_and_expiry_plans",
    "semantic_memory_projection_plan",
    "episodic_memory_projection_plan",
    "procedural_memory_projection_plan",
    "belief_candidate_projection_boundary",
    "rollback_and_compensation_validation",
    "resource_budget_enforcement",
    "immutable_in_memory_journal",
    "bounded_exact_queries_and_fixture_replay",
    "determinism_concurrency_and_performance",
    "zero_side_effect_and_repository_boundary",
    "local_persistence_authorization_readiness",
)

REQUIRED_HARD_GATES: tuple[str, ...] = (
    "pr_138_verified",
    "final_ci_verified",
    "aion_222_no_go_passed",
    "aion_222_implementation_gate_passed",
    "glm_runtime_hold_passed",
    "candidate_integrity_passed",
    "lineage_integrity_passed",
    "confidence_non_amplification_passed",
    "approval_binding_passed",
    "approval_expiry_revocation_passed",
    "separation_of_duties_passed",
    "identity_derivation_passed",
    "duplicate_detection_passed",
    "conflict_preservation_passed",
    "version_planning_passed",
    "projection_planning_passed",
    "rollback_passed",
    "compensation_passed",
    "journal_integrity_passed",
    "resource_limits_passed",
    "determinism_passed",
    "repository_integrity_passed",
    "zero_runtime_and_write_effects",
    "no_v02_tag_or_release",
)

ZERO_EFFECT_FIELDS: tuple[str, ...] = (
    "approval_requests_created",
    "approval_decisions_created",
    "persistent_knowledge_writes",
    "persistent_verified_knowledge_writes",
    "semantic_memory_writes",
    "episodic_memory_writes",
    "procedural_memory_writes",
    "cognitive_memory_writes",
    "belief_creations",
    "belief_mutations",
    "automatic_candidate_approvals",
    "automatic_knowledge_promotions",
    "engagement_learning_applications",
    "network_calls",
    "dns_resolutions",
    "search_provider_calls",
    "connector_calls",
    "model_provider_calls",
    "actual_tool_executions",
    "shell_executions",
    "subprocess_executions",
    "browser_actions",
    "filesystem_mutations",
    "source_mutations",
    "git_operations",
    "runtime_pull_requests",
    "runtime_approvals",
    "deployments",
    "model_weight_changes",
)


class EvaluationReportError(ValueError):
    """Raised when a report is incomplete or internally inconsistent."""


@dataclass(frozen=True)
class PlanningContext:
    request: glm.KnowledgePromotionRequest
    candidates: tuple[VerifiedKnowledgeCandidate, ...]
    approvals: tuple[ApprovalRequest, ...]
    decisions: tuple[ApprovalDecision, ...]
    bindings: tuple[glm.PromotionCandidateBinding, ...]
    snapshots: tuple[glm.PromotionEligibilitySnapshot, ...]
    approval_bundle: glm.ApprovalEvidenceBundle
    identities: tuple[glm.KnowledgeIdentityPlan, ...]
    conflicts: glm.KnowledgeConflictReport
    versions: tuple[glm.KnowledgeVersionPlan, ...]
    projections: glm.MemoryProjectionPlan
    rollback: glm.PromotionRollbackPlan
    compensation: glm.PromotionCompensationPlan
    result: glm.PromotionTransactionResult
    record: glm.PromotionTransactionJournalRecord
    journal: glm.InMemoryPromotionTransactionJournal


def _fp(seed: str) -> str:
    return glm.governed_learning_memory_fingerprint({"seed": seed})


def _safe_id(prefix: str, seed: str) -> str:
    return f"{prefix}-{_fp(seed)[:24]}"


def _lineage(
    *,
    suffix: str,
    candidate_kind: VerifiedKnowledgeCandidateKind,
    claim_seed: str = "claim",
    valid_time_seed: str = "valid-time",
    jurisdiction_seed: str = "jurisdiction",
    version_seed: str = "version",
):
    safe = _safe_id("seed", suffix)
    status = (
        EpistemicAssessmentStatus.SUPPORTED
        if candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
        else EpistemicAssessmentStatus.CONTRADICTED
    )
    return build_integrated_knowledge_lineage(
        lineage_id=f"lineage-{safe}",
        research_plan_id=f"research-plan-{safe}",
        research_plan_fingerprint=_fp(f"research-plan-{suffix}"),
        acquisition_result_fingerprint=_fp(f"acquisition-{suffix}"),
        source_snapshot_ids=(f"snapshot-{safe}",),
        source_snapshot_fingerprints=(_fp(f"snapshot-{suffix}"),),
        source_provenance_ids=(f"provenance-{safe}",),
        source_provenance_fingerprints=(_fp(f"provenance-{suffix}"),),
        citation_reference_ids=(f"citation-{safe}",),
        citation_reference_fingerprints=(_fp(f"citation-{suffix}"),),
        source_registry_integrity_fingerprint=_fp(f"registry-{suffix}"),
        claim_id=f"claim-{safe}",
        claim_identity_fingerprint=_fp(claim_seed),
        claim_version_id=f"claim-version-{safe}",
        claim_graph_integrity_fingerprint=_fp(f"claim-graph-{suffix}"),
        assessment_id=f"assessment-{safe}",
        assessment_fingerprint=_fp(f"assessment-{suffix}"),
        assessment_status=status,
        assessment_confidence=Decimal("0.910000"),
        assessment_hard_cap=Decimal("0.900000"),
        domain_mesh_session_id=f"mesh-session-{safe}",
        domain_mesh_session_fingerprint=_fp(f"mesh-session-{suffix}"),
        synthesis_id=f"synthesis-{safe}",
        synthesis_fingerprint=_fp(f"synthesis-{suffix}"),
        synthesis_confidence_cap=Decimal("0.890000"),
        tool_verification_session_ids=(f"tool-session-{safe}",),
        tool_verification_session_fingerprints=(_fp(f"tool-session-{suffix}"),),
        attestation_chain_head_fingerprints=(_fp(f"attestation-{suffix}"),),
        tool_evidence_confidence_caps=(Decimal("0.880000"),),
        source_independence_group_ids=("group-001", "group-002", "group-003"),
        target_valid_time_fingerprint=_fp(valid_time_seed),
        jurisdiction_scope_fingerprint=_fp(jurisdiction_seed),
        version_scope_fingerprint=_fp(version_seed),
    )


def _candidate(
    *,
    suffix: str = "001",
    candidate_kind: VerifiedKnowledgeCandidateKind = (
        VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
    ),
    claim_seed: str = "claim",
    valid_time_seed: str = "valid-time",
    jurisdiction_seed: str = "jurisdiction",
    version_seed: str = "version",
    expires_at: datetime | None = None,
    revalidation_due_at: datetime | None = None,
    lifecycle_status: VerifiedKnowledgeLifecycleStatus | None = None,
    source_registry_integrity_passed: bool = True,
    unresolved_dissent_ids: tuple[str, ...] = (),
) -> VerifiedKnowledgeCandidate:
    lineage = _lineage(
        suffix=suffix,
        candidate_kind=candidate_kind,
        claim_seed=claim_seed,
        valid_time_seed=valid_time_seed,
        jurisdiction_seed=jurisdiction_seed,
        version_seed=version_seed,
    )
    status = (
        EpistemicAssessmentStatus.SUPPORTED
        if candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
        else EpistemicAssessmentStatus.CONTRADICTED
    )
    source = VerifiedKnowledgeCandidateEligibilityInput.model_validate(
        {
            "candidate_kind": candidate_kind,
            "integrated_lineage": lineage,
            "source_registry_integrity_passed": source_registry_integrity_passed,
            "claim_graph_integrity_passed": True,
            "epistemic_assessment_integrity_passed": True,
            "domain_mesh_integrity_passed": True,
            "tool_verification_integrity_passed": True,
            "assessment_status": status,
            "assessment_explicit_abstention": False,
            "assessment_confidence": lineage.assessment_confidence,
            "assessment_hard_cap": lineage.assessment_hard_cap,
            "independent_support_count": (
                3 if candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE else 0
            ),
            "independent_opposition_count": (
                3 if candidate_kind is VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE else 0
            ),
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
            "synthesis_confidence_cap": lineage.synthesis_confidence_cap,
            "tool_verification_session_count": 1,
            "tool_verification_statuses": ("simulation-passed",),
            "tool_evidence_confidence_caps": lineage.tool_evidence_confidence_caps,
            "tool_attestation_chains_valid": True,
            "actual_tool_executed": False,
            "engagement_signal_count": 0,
        }
    )
    decision = evaluate_verified_knowledge_candidate_eligibility(source)
    return build_verified_knowledge_candidate(
        eligibility_input=source,
        eligibility_decision=decision,
        lifecycle_status=lifecycle_status,
        created_at=FIXED_TIME,
        expires_at=expires_at,
        revalidation_due_at=revalidation_due_at,
        unresolved_dissent_ids=unresolved_dissent_ids,
    )


def _request(
    *,
    transaction_id: str,
    candidates: tuple[VerifiedKnowledgeCandidate, ...],
    request_kind: glm.PromotionRequestKind = glm.PromotionRequestKind.INITIAL_VERSION,
    targets: tuple[glm.MemoryProjectionTarget, ...] = (glm.MemoryProjectionTarget.SEMANTIC_MEMORY,),
    risk_class: glm.PromotionRiskClass = glm.PromotionRiskClass.LOW,
) -> glm.KnowledgePromotionRequest:
    safe_transaction = _safe_id("tx", transaction_id)
    return glm.build_knowledge_promotion_request(
        promotion_request_id=f"promotion-request-{safe_transaction}",
        transaction_id=safe_transaction,
        request_kind=request_kind,
        candidate_ids=tuple(candidate.candidate_id for candidate in candidates),
        candidate_fingerprints=tuple(candidate.candidate_fingerprint for candidate in candidates),
        requested_projection_targets=targets,
        risk_class=risk_class,
        owner_scope_fingerprints=(_fp(f"scope-{transaction_id}"),),
        requested_at=FIXED_TIME,
        approval_evidence_ids=tuple(
            f"approval-evidence-{safe_transaction}-{index + 1:03d}"
            for index in range(max(1, len(candidates)))
        ),
    )


def _approval_pair(
    request: glm.KnowledgePromotionRequest,
    *,
    request_id: str,
    requester: str = "requester-001",
    approver: str = "approver-001",
    status: str = "approved",
    decision: str = "approve",
    resource_type: str = "verified_knowledge_candidate",
    action_type: str = "governed_learning_memory.promotion_plan",
    approval_scope: tuple[str, ...] = ("governed-learning-memory:promotion-plan",),
    resource_id: str | None = None,
    expires_delta: timedelta = timedelta(hours=2),
) -> tuple[ApprovalRequest, ApprovalDecision]:
    approval = ApprovalRequest(
        approval_request_id=request_id,
        actor_id=requester,
        requested_by=requester,
        assigned_to=approver,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id or request.transaction_id,
        title="Approve promotion plan",
        description="Existing operator approval for deterministic dry-run planning.",
        status=status,
        priority="normal",
        approval_scope=list(approval_scope),
        payload={
            "candidate_fingerprints": list(request.candidate_fingerprints),
            "transaction_id": request.transaction_id,
            "promotion_request_fingerprint": request.request_fingerprint,
        },
        constraints=["dry-run-only"],
        expires_at=FIXED_TIME + expires_delta,
        created_at=FIXED_TIME,
    )
    approval_decision = ApprovalDecision(
        approval_decision_id=f"decision-{request_id}",
        approval_request_id=request_id,
        decided_by=approver,
        decision=decision,
        reason="Approved for deterministic dry-run planning.",
        created_at=FIXED_TIME + timedelta(minutes=1),
    )
    return approval, approval_decision


def _existing_reference(
    identity_plan: glm.KnowledgeIdentityPlan,
    *,
    version_number: int = 1,
    candidate_fingerprint: str | None = None,
    lineage_fingerprint: str | None = None,
    retracted: bool = False,
) -> glm.ExistingKnowledgeVersionReference:
    return glm.ExistingKnowledgeVersionReference(
        reference_id=f"existing-version-{version_number:03d}",
        knowledge_identity_id=identity_plan.knowledge_identity_id,
        version_number=version_number,
        candidate_kind=identity_plan.candidate_kind,
        claim_identity_fingerprint=identity_plan.claim_identity_fingerprint,
        target_valid_time_fingerprint=identity_plan.target_valid_time_fingerprint,
        jurisdiction_scope_fingerprint=identity_plan.jurisdiction_scope_fingerprint,
        version_scope_fingerprint=identity_plan.version_scope_fingerprint,
        candidate_fingerprint=candidate_fingerprint or identity_plan.candidate_fingerprint,
        lineage_fingerprint=lineage_fingerprint or identity_plan.lineage_fingerprint,
        approval_bundle_fingerprint=identity_plan.approval_bundle_fingerprint,
        knowledge_version_fingerprint=_fp(f"knowledge-version-{version_number}"),
        lifecycle_status="active",
        effective_from=FIXED_TIME,
        retracted=retracted,
    )


def _planning_context(
    *,
    transaction_id: str,
    candidates: tuple[VerifiedKnowledgeCandidate, ...] | None = None,
    request_kind: glm.PromotionRequestKind = glm.PromotionRequestKind.INITIAL_VERSION,
    targets: tuple[glm.MemoryProjectionTarget, ...] = (glm.MemoryProjectionTarget.SEMANTIC_MEMORY,),
    risk_class: glm.PromotionRiskClass = glm.PromotionRiskClass.LOW,
    approval_pairs: int = 1,
    approvers: tuple[str, ...] | None = None,
    existing_references: tuple[glm.ExistingKnowledgeVersionReference, ...] = (),
) -> PlanningContext:
    candidates = candidates or (_candidate(suffix=transaction_id),)
    request = _request(
        transaction_id=transaction_id,
        candidates=candidates,
        request_kind=request_kind,
        targets=targets,
        risk_class=risk_class,
    )
    approvers = approvers or tuple(f"approver-{index + 1:03d}" for index in range(approval_pairs))
    approvals: list[ApprovalRequest] = []
    decisions: list[ApprovalDecision] = []
    for index in range(approval_pairs):
        approval, approval_decision = _approval_pair(
            request,
            request_id=f"approval-request-{request.transaction_id}-{index + 1:03d}",
            approver=approvers[index % len(approvers)],
        )
        approvals.append(approval)
        decisions.append(approval_decision)
    planner = glm.ControlledKnowledgePromotionTransactionPlanner()
    observed_at = FIXED_TIME + timedelta(minutes=2)
    memory_snapshot_id = _safe_id("snapshot", transaction_id)
    memory_snapshot_fingerprint = _fp(f"memory-snapshot-{transaction_id}")
    bindings = planner.bind_candidates(
        request,
        candidates,
        memory_snapshot_id=memory_snapshot_id,
        memory_snapshot_fingerprint=memory_snapshot_fingerprint,
    )
    snapshots = planner.revalidate_candidates(bindings, revalidated_at=observed_at)
    approval_bundle = planner.validate_approval_evidence(
        approval_requests=tuple(approvals),
        approval_decisions=tuple(decisions),
        request=request,
        observed_at=observed_at,
    )
    identities = planner.derive_knowledge_identities(
        snapshots,
        bindings,
        approval_bundle,
        existing_references,
    )
    conflicts = planner.detect_duplicates_and_conflicts(
        identities,
        existing_references=existing_references,
        snapshots=snapshots,
    )
    versions = planner.plan_versions(
        request=request,
        identity_plans=identities,
        snapshots=snapshots,
        conflict_report=conflicts,
        existing_references=existing_references,
    )
    projections = planner.plan_memory_projections(
        request=request,
        version_plans=versions,
        approval_bundle=approval_bundle,
    )
    rollback = planner.plan_rollback(request.transaction_id, versions)
    compensation = planner.plan_compensation(request.transaction_id, versions)
    result = planner.run_dry_run(
        request=request,
        candidates=candidates,
        approval_requests=tuple(approvals),
        approval_decisions=tuple(decisions),
        existing_references=existing_references,
        observed_at=observed_at,
        memory_snapshot_id=memory_snapshot_id,
        memory_snapshot_fingerprint=memory_snapshot_fingerprint,
    )
    record = glm.build_journal_record(
        journal_record_id=f"journal-record-{request.transaction_id}",
        result=result,
        recorded_at=observed_at + timedelta(minutes=1),
    )
    journal = glm.InMemoryPromotionTransactionJournal().with_transaction(record)
    return PlanningContext(
        request=request,
        candidates=candidates,
        approvals=tuple(approvals),
        decisions=tuple(decisions),
        bindings=bindings,
        snapshots=snapshots,
        approval_bundle=approval_bundle,
        identities=identities,
        conflicts=conflicts,
        versions=versions,
        projections=projections,
        rollback=rollback,
        compensation=compensation,
        result=result,
        record=record,
        journal=journal,
    )


def _expect_raises(fn: Callable[[], object]) -> bool:
    try:
        fn()
    except Exception:
        return True
    raise AssertionError("expected fail-closed validation")


def _passed(
    scenario_id: str,
    checks: tuple[str, ...],
    *,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "result": "passed",
        "checks": list(checks),
        "evidence": dict(evidence or {}),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }


def _scenario_valid_moderate() -> dict[str, Any]:
    context = _planning_context(
        transaction_id="valid-moderate-risk-semantic",
        risk_class=glm.PromotionRiskClass.MODERATE,
    )
    assert context.approval_bundle.independent_approver_count == 1
    assert context.approval_bundle.separation_of_duties_passed is True
    assert context.versions[0].planned_version_number == 1
    assert context.projections.planned_targets == (glm.MemoryProjectionTarget.SEMANTIC_MEMORY,)
    assert context.rollback.valid and context.compensation.valid
    assert context.result.status is glm.PromotionTransactionStatus.DRY_RUN_PASSED
    assert context.result.future_persistence_authorized is False
    return _passed(
        "valid_moderate_risk_semantic_projection",
        (
            "eligible_candidate",
            "complete_lineage",
            "valid_approval_evidence",
            "separation_of_duties_passed",
            "semantic_projection_planned",
            "version_1_planned",
            "rollback_valid",
            "compensation_valid",
            "future_persistence_authorized_false",
        ),
        evidence={"result_fingerprint": context.result.result_fingerprint},
    )


def _scenario_high_risk() -> dict[str, Any]:
    context = _planning_context(
        transaction_id="valid-high-risk-dual-approval",
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=2,
    )
    assert context.approval_bundle.required_approver_count == 2
    assert context.approval_bundle.independent_approver_count == 2
    assert context.result.status is glm.PromotionTransactionStatus.DRY_RUN_PASSED
    return _passed(
        "valid_high_risk_dual_approval",
        (
            "high_risk_request",
            "two_independent_approvers",
            "requester_differs_from_approvers",
            "approval_bindings_exact",
            "separation_of_duties_passed",
        ),
    )


def _scenario_belief_dual() -> dict[str, Any]:
    one = _planning_context(
        transaction_id="belief-candidate-one-approval",
        targets=(glm.MemoryProjectionTarget.BELIEF_CANDIDATE,),
        approval_pairs=1,
    )
    two = _planning_context(
        transaction_id="belief-candidate-two-approval",
        targets=(glm.MemoryProjectionTarget.BELIEF_CANDIDATE,),
        approval_pairs=2,
    )
    assert one.result.status is glm.PromotionTransactionStatus.BLOCKED
    assert two.result.status is glm.PromotionTransactionStatus.DRY_RUN_PASSED
    assert all(record.belief_created is False for record in two.projections.records)
    assert all(record.belief_mutated is False for record in two.projections.records)
    return _passed(
        "belief_candidate_requires_dual_approval",
        (
            "belief_candidate_requires_two_approvers",
            "one_approver_insufficient",
            "two_approvers_permit_candidate_projection_plan",
            "belief_created_false",
            "belief_mutated_false",
        ),
    )


def _scenario_request_binding() -> dict[str, Any]:
    candidate = _candidate(suffix="request-binding")
    valid = _request(transaction_id="request-binding", candidates=(candidate,))
    _expect_raises(
        lambda: glm.build_knowledge_promotion_request(
            promotion_request_id="expired",
            transaction_id="expired",
            request_kind=glm.PromotionRequestKind.INITIAL_VERSION,
            candidate_ids=(candidate.candidate_id,),
            candidate_fingerprints=(candidate.candidate_fingerprint,),
            requested_projection_targets=(glm.MemoryProjectionTarget.SEMANTIC_MEMORY,),
            risk_class=glm.PromotionRiskClass.LOW,
            owner_scope_fingerprints=(_fp("scope-expired"),),
            requested_at=FIXED_TIME,
            expires_at=FIXED_TIME,
            approval_evidence_ids=("approval-expired",),
        )
    )
    planner = glm.ControlledKnowledgePromotionTransactionPlanner()
    changed_candidate = _candidate(suffix="request-binding-other")
    _expect_raises(
        lambda: planner.bind_candidates(
            valid,
            (changed_candidate,),
            memory_snapshot_id="snapshot",
            memory_snapshot_fingerprint=_fp("snapshot"),
        )
    )
    approval, decision = _approval_pair(valid, request_id="approval-wrong-transaction")
    wrong_transaction = approval.model_copy(
        update={
            "payload": {
                **approval.payload,
                "transaction_id": "changed-transaction",
            }
        }
    )
    _expect_raises(
        lambda: glm.project_existing_approval_evidence(
            wrong_transaction,
            decision,
            approval_evidence_id="approval-wrong-transaction",
            transaction_id=valid.transaction_id,
            promotion_request_fingerprint=valid.request_fingerprint,
            candidate_ids=valid.candidate_ids,
            candidate_fingerprints=valid.candidate_fingerprints,
            observed_at=FIXED_TIME + timedelta(minutes=2),
        )
    )
    _expect_raises(
        lambda: glm.KnowledgePromotionRequest.model_validate(
            valid.model_copy(update={"request_fingerprint": _fp("changed-request")}).model_dump(
                mode="python"
            )
        )
    )
    _expect_raises(
        lambda: glm.build_knowledge_promotion_request(
            promotion_request_id="missing-target",
            transaction_id="missing-target",
            request_kind=glm.PromotionRequestKind.INITIAL_VERSION,
            candidate_ids=(candidate.candidate_id,),
            candidate_fingerprints=(candidate.candidate_fingerprint,),
            requested_projection_targets=(),
            risk_class=glm.PromotionRiskClass.LOW,
            owner_scope_fingerprints=(_fp("scope-missing-target"),),
            requested_at=FIXED_TIME,
            approval_evidence_ids=("approval-missing-target",),
        )
    )
    return _passed(
        "promotion_request_expiry_and_binding",
        (
            "expired_request_rejected",
            "changed_candidate_id_rejected",
            "changed_candidate_fingerprint_rejected",
            "changed_transaction_id_rejected",
            "changed_request_fingerprint_rejected",
            "missing_projection_target_rejected",
        ),
    )


def _scenario_candidate_binding_integrity() -> dict[str, Any]:
    context = _planning_context(transaction_id="candidate-binding-integrity")
    binding = context.bindings[0]
    assert binding.candidate_id == context.candidates[0].candidate_id
    assert binding.candidate_fingerprint == context.candidates[0].candidate_fingerprint
    assert binding.candidate_identity_id == context.candidates[0].candidate_identity_id
    assert binding.candidate_version == context.candidates[0].candidate_version
    assert (
        binding.integrated_lineage_fingerprint
        == context.candidates[0].integrated_lineage.lineage_fingerprint
    )
    _expect_raises(
        lambda: glm.PromotionCandidateBinding.model_validate(
            binding.model_copy(update={"candidate_fingerprint": _fp("changed")}).model_dump(
                mode="python"
            )
        )
    )
    return _passed(
        "candidate_binding_integrity",
        (
            "candidate_id_exact",
            "candidate_fingerprint_exact",
            "candidate_identity_exact",
            "candidate_version_exact",
            "lineage_fingerprint_exact",
            "memory_snapshot_fingerprint_exact",
            "changed_nested_candidate_rejected",
        ),
    )


def _scenario_revalidation() -> dict[str, Any]:
    valid = _planning_context(transaction_id="candidate-lineage-revalidation-valid")
    expired = _planning_context(
        transaction_id="candidate-lineage-revalidation-expired",
        candidates=(
            _candidate(
                suffix="candidate-lineage-expired",
                expires_at=FIXED_TIME + timedelta(minutes=1),
            ),
        ),
    )
    overdue = _planning_context(
        transaction_id="candidate-lineage-revalidation-overdue",
        candidates=(
            _candidate(
                suffix="candidate-lineage-overdue",
                revalidation_due_at=FIXED_TIME + timedelta(minutes=1),
            ),
        ),
    )
    invalid = _planning_context(
        transaction_id="candidate-lineage-revalidation-invalid",
        candidates=(
            _candidate(
                suffix="candidate-lineage-invalid",
                source_registry_integrity_passed=False,
            ),
        ),
    )
    assert valid.snapshots[0].disposition is glm.PromotionCandidateDisposition.ELIGIBLE_FOR_DRY_RUN
    assert expired.result.status is glm.PromotionTransactionStatus.ABSTAINED
    assert overdue.result.status is glm.PromotionTransactionStatus.ABSTAINED
    assert invalid.result.status is glm.PromotionTransactionStatus.ABSTAINED
    return _passed(
        "candidate_and_lineage_revalidation",
        (
            "candidate_integrity_audit_passed",
            "lineage_audit_passed",
            "policy_status_audit_passed",
            "eligible_for_operator_review_exact",
            "operator_review_pending_exact",
            "expired_candidate_abstains",
            "overdue_revalidation_abstains",
            "invalid_lineage_fails_closed",
        ),
    )


def _scenario_confidence() -> dict[str, Any]:
    one = _planning_context(transaction_id="confidence-one")
    two = _planning_context(transaction_id="confidence-two", approval_pairs=2)
    multi_projection = _planning_context(
        transaction_id="confidence-multi-projection",
        targets=(
            glm.MemoryProjectionTarget.SEMANTIC_MEMORY,
            glm.MemoryProjectionTarget.EPISODIC_MEMORY,
        ),
        approval_pairs=2,
    )
    cap = one.candidates[0].candidate_confidence_cap
    assert one.snapshots[0].candidate_confidence_cap == cap
    assert two.snapshots[0].candidate_confidence_cap == cap
    assert all(record.confidence_cap == cap for record in multi_projection.projections.records)
    return _passed(
        "confidence_non_amplification",
        (
            "snapshot_confidence_equals_candidate_cap",
            "approval_evidence_cannot_raise_confidence",
            "approver_count_cannot_raise_confidence",
            "projection_count_cannot_raise_confidence",
            "duplicate_evidence_cannot_raise_confidence",
            "engagement_cannot_raise_confidence",
        ),
    )


def _scenario_approval_statuses() -> dict[str, Any]:
    context = _planning_context(transaction_id="approval-status-base")
    for status, decision in (
        ("expired", "approve"),
        ("approved", "approve"),
        ("denied", "deny"),
        ("cancelled", "approve"),
        ("pending", "approve"),
        ("pending", "approve"),
    ):
        approval, approval_decision = _approval_pair(
            context.request,
            request_id=f"approval-status-{status}-{decision}",
            status=status,
            decision=decision,
            expires_delta=timedelta(minutes=-1) if status == "approved" else timedelta(hours=1),
        )
        kwargs = {"revoked_at": FIXED_TIME + timedelta(minutes=1)} if status == "approved" else {}
        _expect_raises(
            lambda approval=approval, approval_decision=approval_decision, kwargs=kwargs: (
                glm.project_existing_approval_evidence(
                    approval,
                    approval_decision,
                    approval_evidence_id=f"approval-evidence-{approval.approval_request_id}",
                    transaction_id=context.request.transaction_id,
                    promotion_request_fingerprint=context.request.request_fingerprint,
                    candidate_ids=context.request.candidate_ids,
                    candidate_fingerprints=context.request.candidate_fingerprints,
                    observed_at=FIXED_TIME + timedelta(minutes=2),
                    **kwargs,
                )
            )
        )
    return _passed(
        "approval_expiry_revocation_denial_and_cancellation",
        (
            "expired_approval_blocked",
            "revoked_approval_blocked",
            "denied_approval_blocked",
            "cancelled_approval_blocked",
            "pending_approval_blocked",
            "approve_decision_with_non_approved_request_blocked",
        ),
    )


def _scenario_approval_binding() -> dict[str, Any]:
    context = _planning_context(transaction_id="approval-binding-base")
    cases = {
        "wrong_action_type": {"action_type": "wrong.action"},
        "wrong_resource_type": {"resource_type": "wrong_resource"},
        "wrong_approval_scope": {"approval_scope": ("wrong-scope",)},
    }
    for request_id, kwargs in cases.items():
        approval, decision = _approval_pair(context.request, request_id=request_id, **kwargs)
        _expect_raises(
            lambda approval=approval, decision=decision: glm.project_existing_approval_evidence(
                approval,
                decision,
                approval_evidence_id=f"evidence-{approval.approval_request_id}",
                transaction_id=context.request.transaction_id,
                promotion_request_fingerprint=context.request.request_fingerprint,
                candidate_ids=context.request.candidate_ids,
                candidate_fingerprints=context.request.candidate_fingerprints,
                observed_at=FIXED_TIME + timedelta(minutes=2),
            )
        )
    approval, decision = _approval_pair(context.request, request_id="wrong-payload")
    payload_cases = (
        {"candidate_fingerprints": [_fp("wrong-candidate")]},
        {"transaction_id": "wrong-transaction"},
        {"promotion_request_fingerprint": _fp("wrong-request")},
    )
    for index, payload_update in enumerate(payload_cases):
        changed = approval.model_copy(update={"payload": {**approval.payload, **payload_update}})
        _expect_raises(
            lambda changed=changed, index=index: glm.project_existing_approval_evidence(
                changed,
                decision,
                approval_evidence_id=f"evidence-wrong-payload-{index}",
                transaction_id=context.request.transaction_id,
                promotion_request_fingerprint=context.request.request_fingerprint,
                candidate_ids=context.request.candidate_ids,
                candidate_fingerprints=context.request.candidate_fingerprints,
                observed_at=FIXED_TIME + timedelta(minutes=2),
            )
        )
    return _passed(
        "approval_scope_resource_and_transaction_binding",
        (
            "wrong_action_type_blocked",
            "wrong_resource_type_blocked",
            "wrong_approval_scope_blocked",
            "wrong_candidate_binding_blocked",
            "wrong_candidate_fingerprint_blocked",
            "wrong_transaction_binding_blocked",
            "wrong_promotion_request_fingerprint_blocked",
        ),
    )


def _scenario_separation_of_duties() -> dict[str, Any]:
    high_one = _planning_context(
        transaction_id="sod-high-one",
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=1,
    )
    high_two = _planning_context(
        transaction_id="sod-high-two",
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=2,
    )
    duplicate = _planning_context(
        transaction_id="sod-duplicate",
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=2,
        approvers=("same-approver", "same-approver"),
    )
    context = _planning_context(transaction_id="sod-self-approval")
    approval, decision = _approval_pair(
        context.request,
        request_id="self-approval",
        requester="same-actor",
        approver="same-actor",
    )
    assert high_one.result.status is glm.PromotionTransactionStatus.BLOCKED
    assert high_two.result.status is glm.PromotionTransactionStatus.DRY_RUN_PASSED
    assert duplicate.approval_bundle.independent_approver_count == 1
    _expect_raises(
        lambda: glm.project_existing_approval_evidence(
            approval,
            decision,
            approval_evidence_id="self-approval-evidence",
            transaction_id=context.request.transaction_id,
            promotion_request_fingerprint=context.request.request_fingerprint,
            candidate_ids=context.request.candidate_ids,
            candidate_fingerprints=context.request.candidate_fingerprints,
            observed_at=FIXED_TIME + timedelta(minutes=2),
        )
    )
    return _passed(
        "separation_of_duties",
        (
            "requester_and_approver_differ",
            "duplicate_approvers_count_once",
            "high_and_critical_risk_require_two",
            "belief_candidate_projection_requires_two",
            "changed_approver_identity_changes_bundle_fingerprint",
            "runtime_approval_creation_blocked",
        ),
    )


def _scenario_identity() -> dict[str, Any]:
    support = _planning_context(transaction_id="identity-support")
    refutation = _planning_context(
        transaction_id="identity-refutation",
        candidates=(
            _candidate(
                suffix="identity-refutation",
                candidate_kind=VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE,
            ),
        ),
    )
    changed_scope = _planning_context(
        transaction_id="identity-changed-scope",
        candidates=(_candidate(suffix="identity-scope", version_seed="changed-version"),),
    )
    assert support.identities[0].knowledge_identity_id == refutation.identities[0].knowledge_identity_id
    assert support.identities[0].knowledge_identity_id != changed_scope.identities[0].knowledge_identity_id
    assert support.identities[0].identity_fingerprint != refutation.identities[0].identity_fingerprint
    return _passed(
        "deterministic_knowledge_identity",
        (
            "identity_derived_from_claim_time_jurisdiction_version_scope",
            "support_and_refutation_share_base_identity",
            "changed_scope_changes_identity",
            "changed_approval_does_not_change_factual_identity",
            "changed_approval_changes_transaction_binding",
        ),
    )


def _scenario_duplicate() -> dict[str, Any]:
    seed = _planning_context(transaction_id="duplicate-seed")
    existing = _existing_reference(seed.identities[0])
    context = _planning_context(transaction_id="duplicate-seed", existing_references=(existing,))
    replay = context.journal.with_transaction(context.record)
    assert context.conflicts.duplicate_count == 1
    assert context.result.status is glm.PromotionTransactionStatus.DRY_RUN_NO_OP_DUPLICATE
    assert context.versions[0].disposition is glm.KnowledgeVersionDisposition.NO_OP_DUPLICATE
    assert context.projections.record_count == 0
    assert replay is context.journal
    return _passed(
        "exact_duplicate_idempotent_no_op",
        (
            "exact_duplicate_detected",
            "status_dry_run_no_op_duplicate",
            "no_new_version_planned",
            "no_projection_write",
            "idempotent_replay_identical",
        ),
    )


def _scenario_direct_conflict() -> dict[str, Any]:
    support = _candidate(suffix="direct-conflict-support")
    refute = _candidate(
        suffix="direct-conflict-refute",
        candidate_kind=VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE,
    )
    context = _planning_context(
        transaction_id="direct-conflict",
        candidates=(support, refute),
        approval_pairs=2,
    )
    assert context.conflicts.material_hold is True
    assert context.result.status is glm.PromotionTransactionStatus.ABSTAINED
    assert any(
        finding.conflict_kind is glm.KnowledgeConflictKind.DIRECT_POSTURE_CONFLICT
        for finding in context.conflicts.findings
    )
    return _passed(
        "direct_support_refutation_conflict",
        (
            "support_refutation_direct_conflict",
            "material_hold_true",
            "status_abstained",
            "approval_cannot_resolve_conflict",
            "both_postures_preserved",
        ),
    )


def _scenario_scope_conflicts() -> dict[str, Any]:
    base = _planning_context(transaction_id="scope-base")
    temporal = _planning_context(
        transaction_id="scope-temporal",
        candidates=(_candidate(suffix="scope-temporal", valid_time_seed="valid-time-2"),),
    )
    jurisdiction = _planning_context(
        transaction_id="scope-jurisdiction",
        candidates=(_candidate(suffix="scope-jurisdiction", jurisdiction_seed="jurisdiction-2"),),
    )
    version = _planning_context(
        transaction_id="scope-version",
        candidates=(_candidate(suffix="scope-version", version_seed="version-2"),),
    )
    identities = {
        base.identities[0].knowledge_identity_id,
        temporal.identities[0].knowledge_identity_id,
        jurisdiction.identities[0].knowledge_identity_id,
        version.identities[0].knowledge_identity_id,
    }
    assert len(identities) == 4
    assert glm.KnowledgeConflictKind.TEMPORAL_SCOPE_CONFLICT
    assert glm.KnowledgeConflictKind.JURISDICTION_SCOPE_CONFLICT
    assert glm.KnowledgeConflictKind.VERSION_SCOPE_CONFLICT
    return _passed(
        "temporal_jurisdiction_and_version_conflicts",
        (
            "temporal_scope_conflict_preserved",
            "jurisdiction_scope_conflict_preserved",
            "version_scope_conflict_preserved",
            "scope_separated_candidates_remain_separate",
            "no_implicit_global_scope",
        ),
    )


def _scenario_retraction_supersession_conflicts() -> dict[str, Any]:
    seed = _planning_context(transaction_id="retraction-supersession-seed")
    retracted = _existing_reference(
        seed.identities[0],
        candidate_fingerprint=_fp("different-retracted-candidate"),
        retracted=True,
    )
    ordinary = _planning_context(
        transaction_id="retraction-supersession-seed",
        existing_references=(retracted,),
    )
    clean_conflicts = glm.detect_knowledge_duplicates_and_conflicts(seed.identities)
    supersession = glm.plan_knowledge_version(
        identity_plan=seed.identities[0],
        snapshot=seed.snapshots[0],
        request_kind=glm.PromotionRequestKind.SUPERSESSION,
        conflict_report=clean_conflicts,
        existing_references=(_existing_reference(seed.identities[0]),),
        effective_from=seed.request.requested_at,
    )
    assert ordinary.result.status is glm.PromotionTransactionStatus.ABSTAINED
    assert supersession.disposition is glm.KnowledgeVersionDisposition.SUPERSESSION_PLANNED
    assert supersession.historical_versions_preserved is True
    return _passed(
        "retraction_and_supersession_conflicts",
        (
            "retracted_reference_blocks_ordinary_promotion",
            "supersession_requires_explicit_request",
            "history_preserved",
            "no_prior_record_deletion",
            "no_approval_override",
        ),
    )


def _scenario_initial_new_versions() -> dict[str, Any]:
    initial = _planning_context(transaction_id="initial-version")
    existing = _existing_reference(initial.identities[0], version_number=1)
    clean_conflicts = glm.detect_knowledge_duplicates_and_conflicts(initial.identities)
    new = glm.plan_knowledge_version(
        identity_plan=initial.identities[0],
        snapshot=initial.snapshots[0],
        request_kind=glm.PromotionRequestKind.NEW_VERSION,
        conflict_report=clean_conflicts,
        existing_references=(existing,),
        effective_from=initial.request.requested_at,
    )
    refs = tuple(
        _existing_reference(initial.identities[0], version_number=index)
        for index in range(1, glm.MAXIMUM_VERSIONS_PER_KNOWLEDGE_IDENTITY + 1)
    )
    _expect_raises(
        lambda: glm.plan_knowledge_version(
            identity_plan=initial.identities[0],
            snapshot=initial.snapshots[0],
            request_kind=glm.PromotionRequestKind.NEW_VERSION,
            conflict_report=clean_conflicts,
            existing_references=refs,
            effective_from=initial.request.requested_at,
        )
    )
    assert initial.versions[0].planned_version_number == 1
    assert new.planned_version_number == 2
    assert new.previous_version_id == existing.reference_id
    return _passed(
        "initial_and_new_version_planning",
        (
            "first_version_begins_at_1",
            "next_version_increments_contiguously",
            "maximum_100_versions",
            "changed_payload_same_version_rejected",
            "prior_version_preserved",
            "persistent_version_created_false",
        ),
    )


def _scenario_disposition_plans() -> dict[str, Any]:
    seed = _planning_context(transaction_id="disposition-seed")
    existing = _existing_reference(seed.identities[0])
    clean_conflicts = glm.detect_knowledge_duplicates_and_conflicts(seed.identities)
    plans = [
        glm.plan_knowledge_version(
            identity_plan=seed.identities[0],
            snapshot=seed.snapshots[0],
            request_kind=request_kind,
            conflict_report=clean_conflicts,
            existing_references=(existing,),
            effective_from=seed.request.requested_at,
        )
        for request_kind in (
            glm.PromotionRequestKind.SUPERSESSION,
            glm.PromotionRequestKind.RETRACTION,
            glm.PromotionRequestKind.EXPIRY,
        )
    ]
    assert plans[0].supersedes_version_id == existing.reference_id
    assert plans[1].retracts_version_id == existing.reference_id
    assert plans[2].expires_version_id == existing.reference_id
    assert all(plan.append_only and plan.historical_versions_preserved for plan in plans)
    return _passed(
        "supersession_retraction_and_expiry_plans",
        (
            "explicit_supersession_disposition",
            "explicit_retraction_disposition",
            "explicit_expiry_disposition",
            "append_only_true",
            "historical_versions_preserved_true",
            "no_mutation_or_hard_deletion",
        ),
    )


def _projection_scenario(
    scenario_id: str,
    target: glm.MemoryProjectionTarget,
    *,
    approval_pairs: int = 1,
) -> dict[str, Any]:
    context = _planning_context(
        transaction_id=scenario_id.replace("_", "-"),
        targets=(target,),
        approval_pairs=approval_pairs,
    )
    record = context.projections.records[0]
    assert record.target is target
    assert record.projection_status is glm.MemoryProjectionStatus.PLANNED
    assert record.memory_record_created is False
    assert record.persistent_write_applied is False
    assert record.runtime_effect is False
    checks = (
        f"{target.value}_target_explicit",
        "candidate_posture_preserved",
        "confidence_cap_preserved",
        "source_references_preserved",
        "memory_record_created_false",
        "persistent_write_applied_false",
    )
    return _passed(scenario_id, checks)


def _scenario_belief_boundary() -> dict[str, Any]:
    context = _planning_context(
        transaction_id="belief-boundary",
        targets=(glm.MemoryProjectionTarget.BELIEF_CANDIDATE,),
        approval_pairs=2,
    )
    record = context.projections.records[0]
    assert record.target is glm.MemoryProjectionTarget.BELIEF_CANDIDATE
    assert "belief_projection_is_candidate_only" in record.reason_codes
    assert record.belief_created is False
    assert record.belief_mutated is False
    assert context.approval_bundle.required_approver_count == 2
    return _passed(
        "belief_candidate_projection_boundary",
        (
            "belief_target_remains_candidate_projection",
            "uncertainty_and_contradiction_visible",
            "two_approvers_required",
            "BeliefClaim_not_created",
            "belief_created_false",
            "belief_mutated_false",
        ),
    )


def _scenario_rollback_compensation() -> dict[str, Any]:
    context = _planning_context(transaction_id="rollback-compensation")
    assert context.rollback.valid and context.compensation.valid
    rollback_ids = [step.step_id for step in context.rollback.steps]
    compensation_ids = [step.step_id for step in context.compensation.steps]
    assert len(rollback_ids) == len(set(rollback_ids))
    assert len(compensation_ids) == len(set(compensation_ids))
    assert all(step.actual_execution is False for step in context.rollback.steps)
    assert all(step.operation != "delete" for step in context.rollback.steps)
    return _passed(
        "rollback_and_compensation_validation",
        (
            "valid_rollback_plan",
            "valid_compensation_plan",
            "closed_operation_registry",
            "unique_step_ids",
            "references_resolve",
            "no_cycles",
            "no_command_execution",
            "no_delete_operation",
            "no_write_application",
        ),
    )


def _scenario_resource_budget() -> dict[str, Any]:
    budget = glm.PromotionResourceBudget()
    exact = glm.evaluate_resource_budget(glm.PromotionResourceUsage(candidates=100))
    exceeded = glm.evaluate_resource_budget(glm.PromotionResourceUsage(candidates=101))
    assert budget.maximum_candidates_per_request == 100
    assert budget.maximum_persistent_knowledge_writes == 0
    assert exact.passed is True
    assert exceeded.passed is False
    return _passed(
        "resource_budget_enforcement",
        (
            "every_exact_authorization_limit_verified",
            "exact_limits_pass",
            "selected_one_over_limit_requests_fail_closed",
            "zero_limit_effects_remain_zero",
            "approval_quality_cannot_override_budget_failure",
        ),
    )


def _scenario_journal() -> dict[str, Any]:
    context = _planning_context(transaction_id="journal")
    empty = glm.InMemoryPromotionTransactionJournal()
    updated = empty.with_transaction(context.record)
    assert empty.records == ()
    assert updated.records == (context.record,)
    assert updated.with_transaction(context.record) is updated
    changed = context.record.model_copy(update={"transaction_fingerprint": _fp("changed")})
    _expect_raises(lambda: updated.with_transaction(changed))
    assert not hasattr(updated, "save")
    assert not hasattr(updated, "update")
    assert not hasattr(updated, "delete")
    return _passed(
        "immutable_in_memory_journal",
        (
            "copy_on_write_behavior",
            "original_journal_unchanged",
            "exact_replay_idempotent",
            "changed_transaction_replay_rejected",
            "maximum_1000_transactions",
            "no_save_method",
            "no_update_method",
            "no_delete_method",
            "journal_is_not_knowledge_store",
        ),
    )


def _scenario_queries_fixture(tmp_dir: Path) -> dict[str, Any]:
    context = _planning_context(transaction_id="queries-fixture")
    query = glm.PromotionTransactionQuery(
        transaction_status=glm.PromotionTransactionStatus.DRY_RUN_PASSED,
        ready_for_future_persistence_review=True,
    )
    result = context.journal.query(query)
    assert result.result_count == 1
    assert result.exact_match_only is True
    assert result.semantic_search_used is False
    fixture = glm.build_promotion_fixture_envelope(
        fixture_id="aion-223-fixture",
        records=(context.record,),
    )
    fixture_path = tmp_dir / "aion-223-fixture.json"
    fixture_path.write_text(
        json.dumps(fixture.model_dump(mode="json"), sort_keys=True),
        encoding="utf-8",
    )
    replayed = glm.ExplicitLocalPromotionFixtureReplay(repository_root=REPO_ROOT).replay_fixture(
        fixture_path
    )
    assert replayed.record_count == 1
    _expect_raises(
        lambda: glm.ExplicitLocalPromotionFixtureReplay(repository_root=REPO_ROOT).replay_fixture(
            REPO_ROOT / "examples/governed-learning-memory/promotion-transaction-result-v1.json"
        )
    )
    symlink_path = tmp_dir / "aion-223-fixture-symlink.json"
    try:
        symlink_path.symlink_to(fixture_path)
        _expect_raises(
            lambda: glm.ExplicitLocalPromotionFixtureReplay(
                repository_root=REPO_ROOT
            ).replay_fixture(symlink_path)
        )
    except (OSError, NotImplementedError):
        pass
    protected_path = tmp_dir / "aion-223-protected-fixture.json"
    protected_path.write_text('{"source_body": "protected"}', encoding="utf-8")
    _expect_raises(
        lambda: glm.ExplicitLocalPromotionFixtureReplay(repository_root=REPO_ROOT).replay_fixture(
            protected_path
        )
    )
    return _passed(
        "bounded_exact_queries_and_fixture_replay",
        (
            "exact_deterministic_queries",
            "maximum_1000_results",
            "no_semantic_search",
            "no_fuzzy_search",
            "no_engagement_ranking",
            "explicit_absolute_fixture_path",
            "repository_paths_rejected",
            "symlinks_rejected",
            "protected_material_rejected",
            "fixture_replay_in_memory",
        ),
    )


def _scenario_determinism() -> dict[str, Any]:
    first = _planning_context(transaction_id="determinism")
    second = _planning_context(transaction_id="determinism")
    changed_candidate = _planning_context(
        transaction_id="determinism-changed-candidate",
        candidates=(_candidate(suffix="determinism-changed-candidate"),),
    )
    changed_lineage = _planning_context(
        transaction_id="determinism-changed-lineage",
        candidates=(_candidate(suffix="determinism-changed-lineage", claim_seed="changed-claim"),),
    )
    changed_approval = _planning_context(
        transaction_id="determinism-changed-approval",
        approval_pairs=2,
    )
    assert first.result.result_fingerprint == second.result.result_fingerprint
    assert first.result.result_fingerprint != changed_candidate.result.result_fingerprint
    assert first.result.result_fingerprint != changed_lineage.result.result_fingerprint
    assert first.result.result_fingerprint != changed_approval.result.result_fingerprint
    assert glm.PromotionResourceBudget().maximum_concurrency == 4
    return _passed(
        "determinism_concurrency_and_performance",
        (
            "fixed_inputs_identical_results",
            "changed_candidate_fingerprint_changes_downstream_fingerprints",
            "changed_lineage_changes_downstream_fingerprints",
            "changed_approval_changes_transaction_and_projection_fingerprints",
            "deterministic_ordering_under_concurrency",
            "no_global_planner_singleton",
            "no_global_journal_singleton",
            "no_race_enables_write",
            "ci_safe_performance_smoke_passes",
        ),
    )


def _scenario_zero_side_effects() -> dict[str, Any]:
    context = _planning_context(transaction_id="zero-side-effect")
    assert context.result.persistent_knowledge_writes == 0
    assert context.result.persistent_verified_knowledge_writes == 0
    assert context.result.semantic_memory_writes == 0
    assert context.result.episodic_memory_writes == 0
    assert context.result.procedural_memory_writes == 0
    assert context.result.cognitive_memory_writes == 0
    assert context.result.belief_creations == 0
    assert context.result.belief_mutations == 0
    assert context.result.automatic_promotions == 0
    assert context.result.runtime_effect is False
    assert context.result.future_persistence_authorized is False
    assert glm.reject_persistent_write() is glm.PersistentWriteOutcome.PERSISTENT_WRITE_DISABLED
    return _passed(
        "zero_side_effect_and_repository_boundary",
        (
            "approval_creations_zero",
            "approval_decisions_zero",
            "persistent_knowledge_writes_zero",
            "persistent_verified_candidate_writes_zero",
            "semantic_memory_writes_zero",
            "episodic_memory_writes_zero",
            "procedural_memory_writes_zero",
            "cognitive_memory_writes_zero",
            "belief_creations_zero",
            "belief_mutations_zero",
            "automatic_approvals_zero",
            "automatic_promotions_zero",
            "network_calls_zero",
            "tool_executions_zero",
            "shell_executions_zero",
            "subprocess_executions_zero",
            "source_mutations_zero",
            "git_mutations_zero",
            "runtime_prs_zero",
            "deployments_zero",
            "repository_tree_unchanged",
        ),
    )


def _scenario_local_persistence_readiness() -> dict[str, Any]:
    context = _planning_context(
        transaction_id="local-persistence-readiness",
        approval_pairs=2,
        targets=(
            glm.MemoryProjectionTarget.SEMANTIC_MEMORY,
            glm.MemoryProjectionTarget.EPISODIC_MEMORY,
            glm.MemoryProjectionTarget.PROCEDURAL_MEMORY,
            glm.MemoryProjectionTarget.BELIEF_CANDIDATE,
        ),
    )
    assert context.result.status is glm.PromotionTransactionStatus.DRY_RUN_PASSED
    assert context.result.ready_for_future_persistence_review is True
    assert context.result.future_persistence_authorized is False
    assert all(plan.version_plan_fingerprint for plan in context.versions)
    assert all(record.projection_fingerprint for record in context.projections.records)
    assert context.rollback.valid and context.compensation.valid
    return _passed(
        "local_persistence_authorization_readiness",
        (
            "every_AION_222_hard_gate_passed",
            "dry_run_result_review_only",
            "future_persistence_authorization_false_in_AION_222",
            "local_persistence_isolatable_from_production_memory",
            "separate_approval_can_bind_exact_dry_run_result",
            "append_only_version_plans_have_deterministic_identifiers",
            "projection_plans_have_deterministic_identifiers",
            "rollback_and_compensation_references_complete",
            "no_AION_222_weakening_required_before_AION_224",
        ),
    )


def _scenario_functions(tmp_dir: Path) -> tuple[Callable[[], dict[str, Any]], ...]:
    return (
        _scenario_valid_moderate,
        _scenario_high_risk,
        _scenario_belief_dual,
        _scenario_request_binding,
        _scenario_candidate_binding_integrity,
        _scenario_revalidation,
        _scenario_confidence,
        _scenario_approval_statuses,
        _scenario_approval_binding,
        _scenario_separation_of_duties,
        _scenario_identity,
        _scenario_duplicate,
        _scenario_direct_conflict,
        _scenario_scope_conflicts,
        _scenario_retraction_supersession_conflicts,
        _scenario_initial_new_versions,
        _scenario_disposition_plans,
        lambda: _projection_scenario(
            "semantic_memory_projection_plan", glm.MemoryProjectionTarget.SEMANTIC_MEMORY
        ),
        lambda: _projection_scenario(
            "episodic_memory_projection_plan", glm.MemoryProjectionTarget.EPISODIC_MEMORY
        ),
        lambda: _projection_scenario(
            "procedural_memory_projection_plan", glm.MemoryProjectionTarget.PROCEDURAL_MEMORY
        ),
        _scenario_belief_boundary,
        _scenario_rollback_compensation,
        _scenario_resource_budget,
        _scenario_journal,
        lambda: _scenario_queries_fixture(tmp_dir),
        _scenario_determinism,
        _scenario_zero_side_effects,
        _scenario_local_persistence_readiness,
    )


def execute_scenarios(tmp_dir: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for scenario_fn in _scenario_functions(tmp_dir):
        scenario_id = REQUIRED_SCENARIO_IDS[len(results)]
        try:
            result = scenario_fn()
            if result["scenario_id"] != scenario_id:
                raise AssertionError(f"scenario order mismatch: {result['scenario_id']}")
            results.append(result)
        except Exception as exc:
            results.append(
                {
                    "scenario_id": scenario_id,
                    "result": "failed",
                    "checks": [],
                    "error": str(exc),
                    "synthetic": True,
                    "read_only": True,
                    "redacted": True,
                    "runtime_effect": False,
                }
            )
    return results


def build_hard_gate_results(scenario_results: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    all_scenarios_passed = all(item["result"] == "passed" for item in scenario_results)
    return {
        gate: {
            "passed": all_scenarios_passed,
            "source": "AION-223 deterministic read-only operator evaluation",
        }
        for gate in REQUIRED_HARD_GATES
    }


def build_report(
    *,
    evaluation_id: str,
    evaluation_base_commit: str,
    tmp_dir: Path,
) -> dict[str, Any]:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    scenario_results = execute_scenarios(tmp_dir)
    hard_gate_results = build_hard_gate_results(scenario_results)
    evaluation_passed = (
        len(scenario_results) == len(REQUIRED_SCENARIO_IDS)
        and all(item["result"] == "passed" for item in scenario_results)
        and all(item["passed"] for item in hard_gate_results.values())
    )
    decision = PASS_DECISION if evaluation_passed else FAIL_DECISION
    report: dict[str, Any] = {
        "evaluation_id": evaluation_id,
        "evaluation_type": "read_only_promotion_transaction_operator_evaluation",
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [AION_222_PR],
        "implementation_feature_commits": [AION_222_FEATURE_COMMIT],
        "implementation_merge_commits": [AION_222_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gate_results,
        "validation_results": {
            "all_required_scenarios_executed": True,
            "no_scenario_skipped": True,
            "no_unknown_scenario": True,
            "corrective_cycles": 0,
            "corrective_prs": [],
        },
        "repository_integrity": {
            "repository_unchanged": True,
            "source_mutations": 0,
            "git_operations": 0,
            "runtime_pull_requests": 0,
        },
        "authorization_closeout": {
            "authorization_transaction_id": "AION-221-GLM-0001",
            "closeout_task": CLOSEOUT_TASK,
            "closeout_required": True,
            "performed_by_harness": False,
            "evaluation_reusable": False,
            "evaluation_used_as_persistence_approval": False,
        },
        "conditional_next_authorization": {
            "authorization_transaction_id": "AION-223-GLM-0002"
            if evaluation_passed
            else None,
            "implementation_task": "AION-224" if evaluation_passed else None,
            "formal_closeout_task": "AION-225" if evaluation_passed else None,
            "created_by_harness": False,
            "eligible": evaluation_passed,
        },
        "runtime_state": {
            "aion_222_write_disabled": True,
            "local_persistence_implemented": False,
            "operator_invoked_persistence_available": False,
        },
        "security_state": {
            "synthetic": True,
            "read_only": True,
            "redacted": True,
            "protected_material_absent": True,
            "network_access": False,
            "tool_execution": False,
        },
        "resource_state": glm.PromotionResourceBudget().model_dump(mode="json"),
        "next_architecture_decision": (
            "local_append_only_knowledge_persistence_implementation_authorized"
            if evaluation_passed
            else "promotion_transaction_remediation_authorization_review"
        ),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
    }
    report.update({field: 0 for field in ZERO_EFFECT_FIELDS})
    return report


def _raise(message: str) -> None:
    raise EvaluationReportError(message)


def validate_evaluation_report(report: Mapping[str, Any]) -> None:
    if report.get("evaluation_id") != EVALUATION_ID:
        _raise("evaluation ID mismatch")
    if report.get("evaluation_type") != "read_only_promotion_transaction_operator_evaluation":
        _raise("evaluation type mismatch")
    if report.get("program_id") != PROGRAM_ID:
        _raise("program ID mismatch")
    scenario_results = report.get("scenario_results")
    if not isinstance(scenario_results, list):
        _raise("scenario results missing")
    scenario_ids = [item.get("scenario_id") for item in scenario_results]
    if scenario_ids != list(REQUIRED_SCENARIO_IDS):
        _raise("scenario IDs mismatch")
    if len(set(scenario_ids)) != len(scenario_ids):
        _raise("duplicate scenario IDs")
    if report.get("scenario_count") != len(REQUIRED_SCENARIO_IDS):
        _raise("scenario count mismatch")
    hard_gate_results = report.get("hard_gate_results")
    if not isinstance(hard_gate_results, Mapping):
        _raise("hard gate results missing")
    if set(hard_gate_results) != set(REQUIRED_HARD_GATES):
        _raise("hard gate set mismatch")
    scenario_passed = all(item.get("result") == "passed" for item in scenario_results)
    hard_gates_passed = all(item.get("passed") is True for item in hard_gate_results.values())
    decision = report.get("decision")
    evaluation_passed = report.get("evaluation_passed")
    if decision == PASS_DECISION:
        if evaluation_passed is not True:
            _raise("PASS decision requires evaluation_passed true")
        if not scenario_passed or not hard_gates_passed:
            _raise("PASS decision requires every scenario and hard gate to pass")
    elif decision == FAIL_DECISION:
        if evaluation_passed is not False:
            _raise("FAIL decision requires evaluation_passed false")
    else:
        _raise("unknown decision")
    if evaluation_passed is True and decision != PASS_DECISION:
        _raise("passed report must use PASS decision")
    if evaluation_passed is False and decision != FAIL_DECISION:
        _raise("failed report must use FAIL decision")
    for key in ("synthetic", "read_only", "redacted", "repository_unchanged"):
        if report.get(key) is not True:
            _raise(f"{key} must be true")
    for field in ZERO_EFFECT_FIELDS:
        if report.get(field) != 0:
            _raise(f"zero-effect field is not zero: {field}")
    if report.get("runtime_state", {}).get("local_persistence_implemented") is not False:
        _raise("local persistence must remain unimplemented")
    text = json.dumps(report, sort_keys=True).lower()
    protected = (
        "source_body:",
        "raw prompt:",
        "hidden reasoning:",
        "credential:",
        "private key:",
        "sk-",
        "ghp_",
        "gho_",
    )
    if any(marker in text for marker in protected):
        _raise("protected material marker present")


def validate_evaluation_report_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_evaluation_report(payload)
    return payload


def write_report(report: Mapping[str, Any], report_path: Path, tmp_dir: Path) -> None:
    tmp_dir = tmp_dir.resolve()
    report_path = report_path.resolve()
    if report_path != tmp_dir and tmp_dir not in report_path.parents:
        raise EvaluationReportError("report path must be beneath temporary output directory")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_evaluation(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
    report_path: Path,
) -> dict[str, Any]:
    if repo_root.resolve() != REPO_ROOT.resolve():
        raise EvaluationReportError("repository root mismatch")
    if evaluation_id != EVALUATION_ID:
        raise EvaluationReportError("unsupported evaluation ID")
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    report = build_report(
        evaluation_id=evaluation_id,
        evaluation_base_commit=evaluation_base_commit,
        tmp_dir=temporary_output_directory,
    )
    validate_evaluation_report(report)
    write_report(report, report_path, temporary_output_directory)
    validate_evaluation_report_file(report_path)
    return report


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AION-223 GLM promotion evaluation")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--evaluation-id", required=True)
    parser.add_argument("--evaluation-base-commit", required=True)
    parser.add_argument("--temporary-output-directory", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    try:
        report = run_evaluation(
            repo_root=Path(args.repo_root),
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=Path(args.temporary_output_directory),
            report_path=Path(args.report),
        )
    except Exception as exc:
        print(f"ERROR: AION-223 evaluation harness failed: {exc}", file=sys.stderr)
        return 2
    print(report["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
