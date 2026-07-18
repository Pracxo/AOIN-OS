from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest
from pydantic import ValidationError

from aion_brain.contracts.self_improvement import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    ImprovementApprovalBinding,
    ImprovementAuditEvent,
    ImprovementChangeBudget,
    ImprovementGovernanceDecision,
    ImprovementLifecycleState,
    ImprovementProposalRef,
    ImprovementProvenanceRecord,
    ImprovementRiskAssessment,
    ImprovementRollbackPlan,
    utc_now,
)
from aion_brain.self_improvement import (
    SelfImprovementLedger,
    assess_improvement_risk,
    bind_human_approval,
    evaluate_change_budget,
    evaluate_governance,
    protected_path_decision,
    protected_path_decisions,
    redact_evidence_payload,
    require_valid_transition,
    touches_protected_core,
    transition_state,
)
from aion_brain.self_improvement.change_budget import ChangeBudgetLimit

COMMIT_SHA = "a" * 40
DIFF_HASH = "b" * 64


def proposal_ref(*, protected: bool = False) -> ImprovementProposalRef:
    paths = ("services/brain-api/src/aion_brain/self_improvement/approval.py",) if protected else ()
    return ImprovementProposalRef(
        proposal_id="proposal-self-improve-001",
        author_actor_id="actor.author",
        title="Governed self-improvement proposal",
        summary="Evaluate a bounded self-improvement control-plane change.",
        owner_scope=("workspace:main",),
        risk_level="high" if protected else "medium",
        touches_protected_core=protected,
        protected_paths=paths,
        evidence_refs=("evidence-001",),
        created_at=utc_now(),
    )


def lifecycle_state() -> ImprovementLifecycleState:
    return ImprovementLifecycleState(
        lifecycle_state_id="proposal-self-improve-001:approval_pending",
        proposal_id="proposal-self-improve-001",
        state="approval_pending",
        previous_state="sandbox_passed",
        transition_reason="Sandbox evidence is ready for human review.",
        evidence_refs=("evidence-001",),
        created_at=utc_now(),
    )


def rollback_plan() -> ImprovementRollbackPlan:
    return ImprovementRollbackPlan(
        rollback_plan_id="proposal-self-improve-001:rollback",
        proposal_id="proposal-self-improve-001",
        required=True,
        steps=("Revert the approved patch in the temporary worktree.",),
        verification_checks=("Run focused governance tests after rollback.",),
        owner_actor_id="actor.operator",
        estimated_minutes=10,
        created_at=utc_now(),
    )


def test_contract_constants_match_aion166_authorization() -> None:
    assert PROGRAM_ID == "AION-SELF-IMPROVEMENT-001"
    assert AUTHORIZATION_TRANSACTION_ID == "AION-165-SI-0001"
    assert IMPLEMENTATION_TASK == "AION-166"
    assert AUTHORIZATION_SCOPE == "governed-self-improvement-control-plane"


def test_contracts_forbid_extra_fields_and_unknown_lifecycle_values() -> None:
    proposal = proposal_ref()

    extra_payload: dict[str, Any] = {**proposal.model_dump(), "unexpected": True}
    with pytest.raises(ValidationError):
        ImprovementProposalRef(**extra_payload)

    bad_state: Any = "self_rewrite_started"
    with pytest.raises(ValidationError):
        ImprovementLifecycleState(
            lifecycle_state_id="bad-state",
            proposal_id=proposal.proposal_id,
            state=bad_state,
            transition_reason="Unknown states must fail closed.",
            created_at=utc_now(),
        )


def test_lifecycle_transitions_are_explicit() -> None:
    state = transition_state(
        proposal_id="proposal-self-improve-001",
        from_state="observed",
        to_state="hypothesized",
        reason="Observation has a testable hypothesis.",
    )

    assert state.state == "hypothesized"

    with pytest.raises(ValueError, match="invalid_self_improvement_transition"):
        require_valid_transition("observed", "approved")


def test_evidence_payloads_are_frozen_and_secret_free() -> None:
    assessment = assess_improvement_risk(
        proposal_id="proposal-self-improve-001",
        protected_core_impact=False,
        safety_passed=True,
        benchmark_passed=True,
        quality_score=0.91,
        findings=("No safety finding.",),
        evidence={"benchmarks": [{"name": "unit", "passed": True}]},
    )

    with pytest.raises(TypeError):
        assessment.evidence["new"] = "blocked"
    with pytest.raises(TypeError):
        assessment.evidence["benchmarks"][0]["passed"] = False

    with pytest.raises(ValidationError):
        ImprovementRiskAssessment(
            **assessment.model_copy(update={"evidence": {"token": "sk-test"}}).model_dump()
        )


def test_redaction_helper_removes_obvious_secret_material_before_freezing() -> None:
    redacted = redact_evidence_payload(
        {
            "safe": "kept",
            "api_key": "sk-test",
            "nested": [{"authorization": "Bearer secret"}],
        }
    )

    assert redacted["safe"] == "kept"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"][0]["authorization"] == "[REDACTED]"
    with pytest.raises(TypeError):
        redacted["safe"] = "changed"


def test_approval_binding_requires_exact_commit_diff_and_independent_approver() -> None:
    approval = bind_human_approval(
        proposal_id="proposal-self-improve-001",
        proposal_author_actor_id="actor.author",
        approver_actor_id="actor.reviewer",
        approval_status="approved",
        approved_commit_sha=COMMIT_SHA,
        approved_diff_hash=DIFF_HASH,
        current_commit_sha=COMMIT_SHA,
        current_diff_hash=DIFF_HASH,
        protected_core_change=False,
        observed_approver_count=1,
    )

    assert approval.approval_status == "approved"

    with pytest.raises(ValidationError, match="proposal author cannot approve"):
        bind_human_approval(
            proposal_id="proposal-self-improve-001",
            proposal_author_actor_id="actor.author",
            approver_actor_id="actor.author",
            approval_status="approved",
            approved_commit_sha=COMMIT_SHA,
            approved_diff_hash=DIFF_HASH,
            current_commit_sha=COMMIT_SHA,
            current_diff_hash=DIFF_HASH,
            protected_core_change=False,
            observed_approver_count=1,
        )
    with pytest.raises(ValidationError, match="post-approval code change"):
        bind_human_approval(
            proposal_id="proposal-self-improve-001",
            proposal_author_actor_id="actor.author",
            approver_actor_id="actor.reviewer",
            approval_status="approved",
            approved_commit_sha=COMMIT_SHA,
            approved_diff_hash=DIFF_HASH,
            current_commit_sha="c" * 40,
            current_diff_hash=DIFF_HASH,
            protected_core_change=False,
            observed_approver_count=1,
    )
    with pytest.raises(ValidationError, match="protected-core proposal cannot use single approval"):
        ImprovementApprovalBinding(
            approval_binding_id="proposal-self-improve-001:approval:single",
            proposal_id="proposal-self-improve-001",
            approval_status="pending",
            proposal_author_actor_id="actor.author",
            approver_actor_id="actor.reviewer",
            approved_commit_sha=None,
            approved_diff_hash=None,
            current_commit_sha=None,
            current_diff_hash=None,
            protected_core_change=True,
            required_approver_count=1,
            observed_approver_count=1,
            approval_evidence_refs=(),
            created_at=utc_now(),
        )


def test_safety_and_benchmark_failures_block_governance_even_with_high_quality() -> None:
    proposal = proposal_ref()
    budget = evaluate_change_budget(
        proposal_id=proposal.proposal_id,
        observed_files=1,
        observed_insertions=20,
        observed_deletions=0,
    )
    risk = assess_improvement_risk(
        proposal_id=proposal.proposal_id,
        protected_core_impact=False,
        safety_passed=False,
        benchmark_passed=True,
        quality_score=1.0,
        findings=("Safety gate failed.",),
    )

    decision = evaluate_governance(
        proposal=proposal,
        lifecycle_state=lifecycle_state(),
        risk_assessment=risk,
        change_budget=budget,
    )

    assert decision.status == "blocked"
    assert "safety_failed" in decision.reason_codes
    assert decision.patch_creation_allowed is False
    assert decision.git_mutation_allowed is False
    assert decision.pr_creation_allowed is False
    assert decision.production_runtime_activation_allowed is False

    with pytest.raises(ValidationError, match="benchmark failure blocks approval"):
        ImprovementRiskAssessment(
            risk_assessment_id="proposal-self-improve-001:risk",
            proposal_id=proposal.proposal_id,
            risk_level="medium",
            protected_core_impact=False,
            safety_passed=True,
            benchmark_passed=False,
            quality_score=1.0,
            approval_eligible=True,
            findings=(),
            evidence={},
            created_at=utc_now(),
        )


def test_high_risk_without_rollback_cannot_be_approved() -> None:
    proposal = proposal_ref(protected=True)
    budget = evaluate_change_budget(
        proposal_id=proposal.proposal_id,
        observed_files=1,
        observed_insertions=20,
        observed_deletions=0,
        protected_paths_touched=1,
        limit=ChangeBudgetLimit(max_protected_paths=1),
    )
    risk = assess_improvement_risk(
        proposal_id=proposal.proposal_id,
        protected_core_impact=True,
        safety_passed=True,
        benchmark_passed=True,
        quality_score=0.92,
        requested_risk_level="high",
    )
    approval = bind_human_approval(
        proposal_id=proposal.proposal_id,
        proposal_author_actor_id=proposal.author_actor_id,
        approver_actor_id="actor.reviewer",
        approval_status="approved",
        approved_commit_sha=COMMIT_SHA,
        approved_diff_hash=DIFF_HASH,
        current_commit_sha=COMMIT_SHA,
        current_diff_hash=DIFF_HASH,
        protected_core_change=True,
        observed_approver_count=2,
    )

    decision = evaluate_governance(
        proposal=proposal,
        lifecycle_state=lifecycle_state(),
        risk_assessment=risk,
        change_budget=budget,
        protected_path_decisions=protected_path_decisions(proposal.protected_paths),
        approval_binding=approval,
    )

    assert decision.status == "blocked"
    assert "rollback_plan_missing" in decision.reason_codes
    with pytest.raises(ValidationError, match="missing rollback plan"):
        ImprovementGovernanceDecision(
            **decision.model_copy(
                update={"status": "approved", "reason_codes": ("exact_human_approval_bound",)}
            ).model_dump()
        )


def test_protected_path_classification_requires_dual_approval() -> None:
    decision = protected_path_decision(".github/workflows/aion-ci.yml")

    assert decision.protected is True
    assert decision.required_approver_count == 2
    assert touches_protected_core(("docs/self-improvement/policy/holdout.md",))
    assert not protected_path_decision("docs/self-improvement/readme.md").protected


def test_change_budget_overrun_blocks_approval() -> None:
    proposal = proposal_ref()
    budget = evaluate_change_budget(
        proposal_id=proposal.proposal_id,
        observed_files=21,
        observed_insertions=20,
        observed_deletions=0,
    )
    risk = assess_improvement_risk(
        proposal_id=proposal.proposal_id,
        protected_core_impact=False,
        safety_passed=True,
        benchmark_passed=True,
        quality_score=0.9,
    )
    decision = evaluate_governance(
        proposal=proposal,
        lifecycle_state=lifecycle_state(),
        risk_assessment=risk,
        change_budget=budget,
    )

    assert budget.within_budget is False
    assert decision.status == "blocked"
    assert "change_budget_exceeded" in decision.reason_codes

    with pytest.raises(ValidationError):
        ImprovementChangeBudget(
            **budget.model_copy(update={"within_budget": True}).model_dump()
        )


def test_successful_governance_still_does_not_enable_mutating_runtime_actions() -> None:
    proposal = proposal_ref(protected=True)
    budget = evaluate_change_budget(
        proposal_id=proposal.proposal_id,
        observed_files=1,
        observed_insertions=20,
        observed_deletions=0,
        protected_paths_touched=1,
        limit=ChangeBudgetLimit(max_protected_paths=1),
    )
    risk = assess_improvement_risk(
        proposal_id=proposal.proposal_id,
        protected_core_impact=True,
        safety_passed=True,
        benchmark_passed=True,
        quality_score=0.95,
        requested_risk_level="high",
    )
    approval = bind_human_approval(
        proposal_id=proposal.proposal_id,
        proposal_author_actor_id=proposal.author_actor_id,
        approver_actor_id="actor.reviewer",
        approval_status="approved",
        approved_commit_sha=COMMIT_SHA,
        approved_diff_hash=DIFF_HASH,
        current_commit_sha=COMMIT_SHA,
        current_diff_hash=DIFF_HASH,
        protected_core_change=True,
        observed_approver_count=2,
    )
    decision = evaluate_governance(
        proposal=proposal,
        lifecycle_state=lifecycle_state(),
        risk_assessment=risk,
        change_budget=budget,
        protected_path_decisions=protected_path_decisions(proposal.protected_paths),
        approval_binding=approval,
        rollback_plan=rollback_plan(),
    )

    assert decision.status == "approved"
    assert decision.patch_creation_allowed is False
    assert decision.git_mutation_allowed is False
    assert decision.pr_creation_allowed is False
    assert decision.production_runtime_activation_allowed is False

    with pytest.raises(ValidationError, match="Git mutation is not authorized"):
        ImprovementGovernanceDecision(
            **decision.model_copy(update={"git_mutation_allowed": True}).model_dump()
        )


def test_audit_and_provenance_records_reject_unredacted_sensitive_payloads() -> None:
    event = ImprovementAuditEvent(
        audit_event_id="audit-001",
        proposal_id="proposal-self-improve-001",
        event_type="evidence_recorded",
        actor_id="actor.reviewer",
        redacted_summary="Evidence recorded without sensitive material.",
        evidence={"result": {"passed": True}},
        metadata={"scope": "test"},
        created_at=utc_now(),
    )
    provenance = ImprovementProvenanceRecord(
        provenance_record_id="provenance-001",
        proposal_id="proposal-self-improve-001",
        source_refs=("pytest:self_improvement",),
        redacted_summary="Synthetic evidence was produced by local tests.",
        input_evidence={"fixture": "local"},
        output_evidence={"passed": True},
        created_at=utc_now(),
    )

    assert event.evidence["result"]["passed"] is True
    assert provenance.output_evidence["passed"] is True
    with pytest.raises(TypeError):
        provenance.output_evidence["passed"] = False
    with pytest.raises(ValidationError):
        ImprovementAuditEvent(
            **event.model_copy(update={"metadata": {"private_key": "secret"}}).model_dump()
        )


def test_ledger_records_events_concurrently_without_mutating_evidence() -> None:
    ledger = SelfImprovementLedger()
    proposal = proposal_ref()
    ledger.record_proposal(proposal)

    def append(index: int) -> None:
        ledger.append_event(
            ImprovementAuditEvent(
                audit_event_id=f"audit-{index:03d}",
                proposal_id=proposal.proposal_id,
                event_type="evidence_recorded",
                actor_id=f"actor.{index}",
                redacted_summary=f"Concurrent event {index}",
                evidence={"index": index},
                metadata={},
                created_at=utc_now(),
            )
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(append, range(40)))

    events = ledger.list_events(proposal.proposal_id)

    assert len(events) == 40
    assert ledger.get_proposal(proposal.proposal_id) == proposal
    with pytest.raises(AttributeError):
        events.append(events[0])  # type: ignore[attr-defined]
