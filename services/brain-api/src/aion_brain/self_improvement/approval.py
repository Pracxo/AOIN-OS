"""Approval binding helpers for governed self-improvement."""

from __future__ import annotations

from aion_brain.contracts.self_improvement import (
    ImprovementApprovalBinding,
    ImprovementApprovalStatus,
    utc_now,
)


def bind_human_approval(
    *,
    proposal_id: str,
    proposal_author_actor_id: str,
    approver_actor_id: str,
    approval_status: ImprovementApprovalStatus,
    approved_commit_sha: str | None,
    approved_diff_hash: str | None,
    current_commit_sha: str | None,
    current_diff_hash: str | None,
    protected_core_change: bool,
    observed_approver_count: int,
    approval_evidence_refs: tuple[str, ...] = (),
) -> ImprovementApprovalBinding:
    """Bind human approval to the exact commit and diff observed by the approver."""

    return ImprovementApprovalBinding(
        approval_binding_id=f"{proposal_id}:approval:{approver_actor_id}",
        proposal_id=proposal_id,
        approval_status=approval_status,
        proposal_author_actor_id=proposal_author_actor_id,
        approver_actor_id=approver_actor_id,
        approved_commit_sha=approved_commit_sha,
        approved_diff_hash=approved_diff_hash,
        current_commit_sha=current_commit_sha,
        current_diff_hash=current_diff_hash,
        protected_core_change=protected_core_change,
        required_approver_count=2 if protected_core_change else 1,
        observed_approver_count=observed_approver_count,
        approval_evidence_refs=approval_evidence_refs,
        created_at=utc_now(),
    )

