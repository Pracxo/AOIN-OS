from __future__ import annotations

import importlib
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from knowledge_verified_memory_test_helpers import FIXED_TIME, fp, sample_candidate
from pydantic import ValidationError

from aion_brain.contracts import governed_learning_memory as glm
from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPO_ROOT / "services" / "brain-api" / "src" / "aion_brain"
GLM_CONTRACT_SOURCE = SOURCE_ROOT / "contracts" / "governed_learning_memory.py"
GLM_PACKAGE_ROOT = SOURCE_ROOT / "governed_learning_memory"

GLM_SOURCE_FILES = (GLM_CONTRACT_SOURCE, *sorted(GLM_PACKAGE_ROOT.glob("*.py")))

PROHIBITED_RUNTIME_TOKENS = (
    "subprocess" + ".",
    "socket" + ".",
    "requests.",
    "httpx" + ".",
    "aiohttp.",
    "urllib" + ".request",
    "sqlite3.",
    "playwright",
    "selenium",
    ".write_text(",
    ".write_bytes(",
    "os.system",
)

PROHIBITED_RUNTIME_COUNTERS = {
    "persistent_knowledge_writes": 0,
    "persistent_verified_knowledge_writes": 0,
    "cognitive_memory_writes": 0,
    "semantic_memory_writes": 0,
    "episodic_memory_writes": 0,
    "procedural_memory_writes": 0,
    "belief_creations": 0,
    "belief_mutations": 0,
    "automatic_promotions": 0,
}


def sample_promotion_request(
    *,
    candidate=None,
    transaction_id: str = "promotion-transaction-001",
    request_kind: glm.PromotionRequestKind = glm.PromotionRequestKind.INITIAL_VERSION,
    targets: tuple[glm.MemoryProjectionTarget, ...] = (glm.MemoryProjectionTarget.SEMANTIC_MEMORY,),
    risk_class: glm.PromotionRiskClass = glm.PromotionRiskClass.LOW,
):
    candidate = candidate or sample_candidate()
    return glm.build_knowledge_promotion_request(
        promotion_request_id=f"promotion-request-{transaction_id}",
        transaction_id=transaction_id,
        request_kind=request_kind,
        candidate_ids=(candidate.candidate_id,),
        candidate_fingerprints=(candidate.candidate_fingerprint,),
        requested_projection_targets=targets,
        risk_class=risk_class,
        owner_scope_fingerprints=(fp(f"scope-{transaction_id}"),),
        requested_at=FIXED_TIME,
        approval_evidence_ids=(f"approval-evidence-{transaction_id}",),
    )


def sample_approval_pair(
    request,
    candidate,
    *,
    request_id: str = "approval-request-001",
    requester: str = "requester-001",
    approver: str = "approver-001",
    status: str = "approved",
    decision: str = "approve",
    expires_delta: timedelta = timedelta(hours=2),
):
    approval = ApprovalRequest(
        approval_request_id=request_id,
        actor_id=requester,
        requested_by=requester,
        assigned_to=approver,
        action_type="governed_learning_memory.promotion_plan",
        resource_type="verified_knowledge_candidate",
        resource_id=candidate.candidate_id,
        title="Approve promotion plan",
        description="Existing operator approval for dry-run promotion planning.",
        status=status,
        priority="normal",
        approval_scope=["governed-learning-memory:promotion-plan"],
        payload={
            "candidate_fingerprints": [candidate.candidate_fingerprint],
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


def sample_transaction_context(
    *,
    transaction_id: str = "promotion-transaction-001",
    request_kind: glm.PromotionRequestKind = glm.PromotionRequestKind.INITIAL_VERSION,
    targets: tuple[glm.MemoryProjectionTarget, ...] = (glm.MemoryProjectionTarget.SEMANTIC_MEMORY,),
    risk_class: glm.PromotionRiskClass = glm.PromotionRiskClass.LOW,
    approval_pairs: int = 1,
):
    candidate = sample_candidate()
    request = sample_promotion_request(
        candidate=candidate,
        transaction_id=transaction_id,
        request_kind=request_kind,
        targets=targets,
        risk_class=risk_class,
    )
    approvals: list[ApprovalRequest] = []
    decisions: list[ApprovalDecision] = []
    for index in range(approval_pairs):
        approval, decision = sample_approval_pair(
            request,
            candidate,
            request_id=f"approval-request-{index + 1:03d}",
            approver=f"approver-{index + 1:03d}",
        )
        approvals.append(approval)
        decisions.append(decision)
    planner = glm.ControlledKnowledgePromotionTransactionPlanner()
    result = planner.run_dry_run(
        request=request,
        candidates=(candidate,),
        approval_requests=tuple(approvals),
        approval_decisions=tuple(decisions),
        observed_at=FIXED_TIME + timedelta(minutes=2),
        memory_snapshot_id=f"memory-snapshot-{transaction_id}",
        memory_snapshot_fingerprint=fp(f"memory-snapshot-{transaction_id}"),
    )
    record = glm.build_journal_record(
        journal_record_id=f"journal-record-{transaction_id}",
        result=result,
        recorded_at=FIXED_TIME + timedelta(minutes=3),
    )
    journal = glm.InMemoryPromotionTransactionJournal().with_transaction(record)
    return SimpleNamespace(
        candidate=candidate,
        request=request,
        approvals=tuple(approvals),
        decisions=tuple(decisions),
        planner=planner,
        result=result,
        record=record,
        journal=journal,
    )


def source_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in GLM_SOURCE_FILES)


def sample_planning_components(
    *,
    transaction_id: str = "promotion-transaction-components",
    request_kind: glm.PromotionRequestKind = glm.PromotionRequestKind.INITIAL_VERSION,
    targets: tuple[glm.MemoryProjectionTarget, ...] = (glm.MemoryProjectionTarget.SEMANTIC_MEMORY,),
    risk_class: glm.PromotionRiskClass = glm.PromotionRiskClass.LOW,
    approval_pairs: int = 1,
    existing_references: tuple[glm.ExistingKnowledgeVersionReference, ...] = (),
):
    context = sample_transaction_context(
        transaction_id=transaction_id,
        request_kind=request_kind,
        targets=targets,
        risk_class=risk_class,
        approval_pairs=approval_pairs,
    )
    bindings = context.planner.bind_candidates(
        context.request,
        (context.candidate,),
        memory_snapshot_id=f"memory-snapshot-{transaction_id}",
        memory_snapshot_fingerprint=fp(f"memory-snapshot-{transaction_id}"),
    )
    snapshots = context.planner.revalidate_candidates(
        bindings,
        revalidated_at=FIXED_TIME + timedelta(minutes=2),
    )
    approvals = context.planner.validate_approval_evidence(
        approval_requests=context.approvals,
        approval_decisions=context.decisions,
        request=context.request,
        observed_at=FIXED_TIME + timedelta(minutes=2),
    )
    identities = context.planner.derive_knowledge_identities(
        snapshots,
        bindings,
        approvals,
        existing_references,
    )
    conflicts = context.planner.detect_duplicates_and_conflicts(
        identities,
        existing_references=existing_references,
        snapshots=snapshots,
    )
    versions = context.planner.plan_versions(
        request=context.request,
        identity_plans=identities,
        snapshots=snapshots,
        conflict_report=conflicts,
        existing_references=existing_references,
    )
    projections = context.planner.plan_memory_projections(
        request=context.request,
        version_plans=versions,
        approval_bundle=approvals,
    )
    rollback = context.planner.plan_rollback(context.request.transaction_id, versions)
    compensation = context.planner.plan_compensation(context.request.transaction_id, versions)
    return SimpleNamespace(
        context=context,
        bindings=bindings,
        snapshots=snapshots,
        approvals=approvals,
        identities=identities,
        conflicts=conflicts,
        versions=versions,
        projections=projections,
        rollback=rollback,
        compensation=compensation,
    )


def sample_existing_reference(
    identity_plan,
    *,
    version_number: int = 1,
    candidate_fingerprint: str | None = None,
    lineage_fingerprint: str | None = None,
):
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
        knowledge_version_fingerprint=fp(f"knowledge-version-{version_number}"),
        lifecycle_status="active",
        effective_from=FIXED_TIME,
    )


def test_governed_learning_memory_contracts_execute_dry_run_only():
    context = sample_transaction_context()

    assert context.result.status is glm.PromotionTransactionStatus.DRY_RUN_PASSED
    assert context.result.ready_for_future_persistence_review is True
    assert context.result.future_persistence_authorized is False
    assert context.result.runtime_effect is False
    assert context.result.result_fingerprint
    for field, expected in PROHIBITED_RUNTIME_COUNTERS.items():
        assert getattr(context.result, field) == expected


def test_governed_learning_memory_modules_import_without_runtime_registration():
    modules = [
        "aion_brain.governed_learning_memory",
        "aion_brain.governed_learning_memory.promotion_requests",
        "aion_brain.governed_learning_memory.approval_evidence",
        "aion_brain.governed_learning_memory.eligibility_revalidation",
        "aion_brain.governed_learning_memory.knowledge_identity",
        "aion_brain.governed_learning_memory.version_planning",
        "aion_brain.governed_learning_memory.memory_projection",
        "aion_brain.governed_learning_memory.promotion_transactions",
        "aion_brain.governed_learning_memory.rollback",
        "aion_brain.governed_learning_memory.integrity",
        "aion_brain.governed_learning_memory.evidence",
    ]

    for module in modules:
        assert importlib.import_module(module)


def test_governed_learning_memory_rejects_fingerprint_tampering():
    context = sample_transaction_context()

    with pytest.raises(ValidationError):
        glm.KnowledgePromotionRequest.model_validate(
            context.request.model_copy(
                update={"request_fingerprint": fp("tampered")},
            ).model_dump(mode="python")
        )
