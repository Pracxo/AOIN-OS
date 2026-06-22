"""Workflow lifecycle state machine."""

from datetime import datetime, timedelta

from aion_brain.contracts.workflows import WorkflowRetryPolicy

_RUN_TRANSITIONS = {
    ("pending", "running"),
    ("running", "completed"),
    ("running", "failed"),
    ("running", "waiting_for_approval"),
    ("running", "paused"),
    ("running", "blocked_by_policy"),
    ("running", "retry_scheduled"),
    ("running", "cancelled"),
    ("paused", "running"),
    ("paused", "cancelled"),
    ("waiting_for_approval", "running"),
    ("waiting_for_approval", "cancelled"),
    ("retry_scheduled", "running"),
    ("retry_scheduled", "cancelled"),
    ("failed", "retry_scheduled"),
    ("failed", "cancelled"),
}

_STEP_TRANSITIONS = {
    ("pending", "running"),
    ("running", "completed"),
    ("running", "failed"),
    ("running", "skipped"),
    ("running", "blocked_by_policy"),
    ("running", "waiting_for_approval"),
    ("waiting_for_approval", "running"),
    ("failed", "running"),
}


def can_transition_workflow_run(from_status: str, to_status: str) -> bool:
    """Return whether a workflow run transition is valid."""
    return (from_status, to_status) in _RUN_TRANSITIONS or from_status == to_status


def can_transition_workflow_step(from_status: str, to_status: str) -> bool:
    """Return whether a workflow step transition is valid."""
    return (from_status, to_status) in _STEP_TRANSITIONS or from_status == to_status


def require_valid_workflow_run_transition(from_status: str, to_status: str) -> None:
    """Raise when a workflow run transition is invalid."""
    if not can_transition_workflow_run(from_status, to_status):
        raise ValueError(f"invalid_workflow_run_transition:{from_status}->{to_status}")


def require_valid_workflow_step_transition(from_status: str, to_status: str) -> None:
    """Raise when a workflow step transition is invalid."""
    if not can_transition_workflow_step(from_status, to_status):
        raise ValueError(f"invalid_workflow_step_transition:{from_status}->{to_status}")


def calculate_next_retry_at(
    retry_count: int,
    retry_policy: WorkflowRetryPolicy,
    now: datetime,
) -> datetime | None:
    """Calculate the next retry timestamp for the next attempt."""
    if retry_count >= retry_policy.max_attempts:
        return None
    delay = retry_policy.backoff_seconds * (
        retry_policy.backoff_multiplier ** max(0, retry_count - 1)
    )
    bounded_delay = min(int(delay), retry_policy.max_backoff_seconds)
    return now + timedelta(seconds=bounded_delay)
