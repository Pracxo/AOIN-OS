"""Governance decision service for self-improvement proposals."""

from __future__ import annotations

from aion_brain.contracts.self_improvement import (
    ImprovementApprovalBinding,
    ImprovementChangeBudget,
    ImprovementDecisionStatus,
    ImprovementGovernanceDecision,
    ImprovementLifecycleState,
    ImprovementProposalRef,
    ImprovementProtectedPathDecision,
    ImprovementRiskAssessment,
    ImprovementRollbackPlan,
    utc_now,
)


def evaluate_governance(
    *,
    proposal: ImprovementProposalRef,
    lifecycle_state: ImprovementLifecycleState,
    risk_assessment: ImprovementRiskAssessment,
    change_budget: ImprovementChangeBudget,
    protected_path_decisions: tuple[ImprovementProtectedPathDecision, ...] = (),
    approval_binding: ImprovementApprovalBinding | None = None,
    rollback_plan: ImprovementRollbackPlan | None = None,
) -> ImprovementGovernanceDecision:
    """Evaluate a proposal without enabling patch, Git, PR, or production runtime actions."""

    status, reason_codes = _decision_status(
        risk_assessment=risk_assessment,
        change_budget=change_budget,
        approval_binding=approval_binding,
        rollback_plan=rollback_plan,
    )
    return ImprovementGovernanceDecision(
        governance_decision_id=f"{proposal.proposal_id}:governance",
        proposal=proposal,
        lifecycle_state=lifecycle_state,
        risk_assessment=risk_assessment,
        change_budget=change_budget,
        protected_path_decisions=protected_path_decisions,
        approval_binding=approval_binding,
        rollback_plan=rollback_plan,
        status=status,
        reason_codes=reason_codes,
        patch_creation_allowed=False,
        git_mutation_allowed=False,
        pr_creation_allowed=False,
        production_runtime_activation_allowed=False,
        created_at=utc_now(),
    )


def _decision_status(
    *,
    risk_assessment: ImprovementRiskAssessment,
    change_budget: ImprovementChangeBudget,
    approval_binding: ImprovementApprovalBinding | None,
    rollback_plan: ImprovementRollbackPlan | None,
) -> tuple[ImprovementDecisionStatus, tuple[str, ...]]:
    reason_codes: list[str] = []
    if not risk_assessment.safety_passed:
        reason_codes.append("safety_failed")
    if not risk_assessment.benchmark_passed:
        reason_codes.append("benchmark_failed")
    if not change_budget.within_budget:
        reason_codes.append("change_budget_exceeded")
    if risk_assessment.risk_level in {"high", "critical"} and rollback_plan is None:
        reason_codes.append("rollback_plan_missing")
    if reason_codes:
        return "blocked", tuple(reason_codes)
    if approval_binding is None:
        return "approval_pending", ("human_approval_required",)
    if approval_binding.approval_status != "approved":
        return "approval_pending", ("human_approval_not_approved",)
    return "approved", ("exact_human_approval_bound",)

