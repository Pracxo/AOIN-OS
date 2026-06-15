"""Cognitive cycle lifecycle state machine."""

_RUN_TRANSITIONS = {
    ("pending", "running"),
    ("pending", "failed"),
    ("pending", "blocked_by_policy"),
    ("pending", "waiting_for_approval"),
    ("pending", "cancelled"),
    ("running", "completed"),
    ("running", "failed"),
    ("running", "blocked_by_policy"),
    ("running", "waiting_for_approval"),
    ("running", "cancelled"),
    ("waiting_for_approval", "running"),
    ("waiting_for_approval", "cancelled"),
}

_STEP_TRANSITIONS = {
    ("pending", "running"),
    ("running", "completed"),
    ("running", "skipped"),
    ("running", "failed"),
    ("running", "blocked_by_policy"),
    ("running", "waiting_for_approval"),
}


def can_transition_cycle_run(from_status: str, to_status: str) -> bool:
    """Return whether a cycle run transition is valid."""
    return from_status == to_status or (from_status, to_status) in _RUN_TRANSITIONS


def can_transition_cycle_step(from_status: str, to_status: str) -> bool:
    """Return whether a cycle step transition is valid."""
    return from_status == to_status or (from_status, to_status) in _STEP_TRANSITIONS


def require_valid_cycle_run_transition(from_status: str, to_status: str) -> None:
    """Raise for invalid cycle run transitions."""
    if not can_transition_cycle_run(from_status, to_status):
        raise ValueError(f"invalid_cycle_run_transition:{from_status}->{to_status}")


def require_valid_cycle_step_transition(from_status: str, to_status: str) -> None:
    """Raise for invalid cycle step transitions."""
    if not can_transition_cycle_step(from_status, to_status):
        raise ValueError(f"invalid_cycle_step_transition:{from_status}->{to_status}")
