"""Approval request state machine."""

from aion_brain.contracts.approvals import ApprovalStatus

_ALLOWED_TRANSITIONS: dict[ApprovalStatus, set[ApprovalStatus]] = {
    "pending": {"approved", "denied", "expired", "cancelled"},
    "approved": set(),
    "denied": set(),
    "expired": set(),
    "cancelled": set(),
}


def can_transition_approval(from_status: ApprovalStatus, to_status: ApprovalStatus) -> bool:
    """Return whether an approval request may transition."""
    return to_status in _ALLOWED_TRANSITIONS[from_status]


def require_valid_approval_transition(
    from_status: ApprovalStatus,
    to_status: ApprovalStatus,
) -> None:
    """Raise when an approval transition is invalid."""
    if not can_transition_approval(from_status, to_status):
        raise ValueError(f"invalid_approval_transition:{from_status}->{to_status}")
