"""Lifecycle state validation for governed self-improvement."""

from __future__ import annotations

from aion_brain.contracts.self_improvement import (
    ImprovementLifecycleState,
    ImprovementLifecycleValue,
    utc_now,
)

ALLOWED_TRANSITIONS: dict[ImprovementLifecycleValue, set[ImprovementLifecycleValue]] = {
    "observed": {"hypothesized", "archived"},
    "hypothesized": {"test_created", "rejected", "archived"},
    "test_created": {"experiment_ready", "rejected", "archived"},
    "experiment_ready": {"patch_created", "rejected", "archived"},
    "patch_created": {"sandbox_running", "rejected", "archived"},
    "sandbox_running": {"sandbox_passed", "sandbox_failed"},
    "sandbox_passed": {"approval_pending"},
    "sandbox_failed": {"hypothesized", "rejected", "archived"},
    "approval_pending": {"approved", "rejected", "archived"},
    "approved": {"pr_created", "rolled_back"},
    "pr_created": {"merged", "rolled_back"},
    "merged": {"canary", "archived"},
    "canary": {"promoted", "rolled_back"},
    "promoted": {"archived"},
    "rolled_back": {"archived"},
    "rejected": {"archived"},
    "archived": set(),
}


def can_transition(
    from_state: ImprovementLifecycleValue,
    to_state: ImprovementLifecycleValue,
) -> bool:
    """Return whether a governed self-improvement lifecycle transition is allowed."""

    return to_state in ALLOWED_TRANSITIONS[from_state]


def require_valid_transition(
    from_state: ImprovementLifecycleValue,
    to_state: ImprovementLifecycleValue,
) -> None:
    """Raise when a lifecycle transition is not allowed."""

    if not can_transition(from_state, to_state):
        raise ValueError(f"invalid_self_improvement_transition:{from_state}->{to_state}")


def transition_state(
    *,
    proposal_id: str,
    from_state: ImprovementLifecycleValue,
    to_state: ImprovementLifecycleValue,
    reason: str,
    evidence_refs: tuple[str, ...] = (),
) -> ImprovementLifecycleState:
    """Create a validated lifecycle state snapshot."""

    require_valid_transition(from_state, to_state)
    return ImprovementLifecycleState(
        lifecycle_state_id=f"{proposal_id}:{to_state}",
        proposal_id=proposal_id,
        state=to_state,
        previous_state=from_state,
        transition_reason=reason,
        evidence_refs=evidence_refs,
        created_at=utc_now(),
    )

