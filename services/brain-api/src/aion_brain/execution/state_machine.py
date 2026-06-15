"""Execution state transition rules."""

EXECUTION_TRANSITIONS = {
    ("pending", "running"),
    ("running", "completed"),
    ("running", "blocked_by_policy"),
    ("running", "waiting_for_approval"),
    ("running", "failed"),
    ("running", "cancelled"),
    ("waiting_for_approval", "running"),
    ("waiting_for_approval", "cancelled"),
}

STEP_TRANSITIONS = {
    ("pending", "running"),
    ("running", "completed"),
    ("running", "blocked_by_policy"),
    ("running", "waiting_for_approval"),
    ("running", "skipped"),
    ("running", "failed"),
    ("waiting_for_approval", "running"),
    ("waiting_for_approval", "skipped"),
}


def can_transition_execution(from_status: str, to_status: str) -> bool:
    """Return whether an execution status transition is valid."""
    return (from_status, to_status) in EXECUTION_TRANSITIONS


def can_transition_step(from_status: str, to_status: str) -> bool:
    """Return whether a step status transition is valid."""
    return (from_status, to_status) in STEP_TRANSITIONS


def require_valid_execution_transition(from_status: str, to_status: str) -> None:
    """Raise when an execution transition is invalid."""
    if not can_transition_execution(from_status, to_status):
        raise ValueError(f"Invalid execution transition: {from_status} -> {to_status}")


def require_valid_step_transition(from_status: str, to_status: str) -> None:
    """Raise when a step transition is invalid."""
    if not can_transition_step(from_status, to_status):
        raise ValueError(f"Invalid step transition: {from_status} -> {to_status}")
