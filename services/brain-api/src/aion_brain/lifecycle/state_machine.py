"""Deterministic lifecycle state machine."""

_GOAL_TRANSITIONS = {
    ("proposed", "active"),
    ("proposed", "cancelled"),
    ("active", "paused"),
    ("active", "completed"),
    ("active", "cancelled"),
    ("active", "failed"),
    ("paused", "active"),
    ("paused", "cancelled"),
    ("failed", "active"),
}

_TASK_TRANSITIONS = {
    ("proposed", "queued"),
    ("proposed", "cancelled"),
    ("queued", "running"),
    ("queued", "cancelled"),
    ("running", "completed"),
    ("running", "waiting_for_approval"),
    ("running", "blocked_by_policy"),
    ("running", "failed"),
    ("running", "cancelled"),
    ("waiting_for_approval", "queued"),
    ("waiting_for_approval", "cancelled"),
    ("blocked_by_policy", "queued"),
    ("blocked_by_policy", "cancelled"),
    ("failed", "queued"),
}


def can_transition_goal(from_status: str, to_status: str) -> bool:
    """Return whether a goal transition is valid."""
    return (from_status, to_status) in _GOAL_TRANSITIONS


def can_transition_task(from_status: str, to_status: str) -> bool:
    """Return whether a task transition is valid."""
    return (from_status, to_status) in _TASK_TRANSITIONS


def require_valid_goal_transition(from_status: str, to_status: str) -> None:
    """Raise when a goal transition is invalid."""
    if not can_transition_goal(from_status, to_status):
        raise ValueError(f"Invalid goal transition: {from_status} -> {to_status}")


def require_valid_task_transition(from_status: str, to_status: str) -> None:
    """Raise when a task transition is invalid."""
    if not can_transition_task(from_status, to_status):
        raise ValueError(f"Invalid task transition: {from_status} -> {to_status}")
