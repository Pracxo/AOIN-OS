"""Workflow lifecycle state machine tests."""

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.workflows import WorkflowRetryPolicy
from aion_brain.workflows.state_machine import (
    calculate_next_retry_at,
    can_transition_workflow_run,
    can_transition_workflow_step,
    require_valid_workflow_run_transition,
)


def test_valid_run_transitions_cover_pause_resume_retry_and_cancel() -> None:
    """Workflow run lifecycle supports durable control transitions."""
    assert can_transition_workflow_run("pending", "running")
    assert can_transition_workflow_run("running", "paused")
    assert can_transition_workflow_run("paused", "running")
    assert can_transition_workflow_run("failed", "retry_scheduled")
    assert can_transition_workflow_run("running", "cancelled")


def test_invalid_run_transition_raises() -> None:
    """Invalid transitions fail deterministically."""
    with pytest.raises(ValueError, match="invalid_workflow_run_transition"):
        require_valid_workflow_run_transition("completed", "running")


def test_valid_step_transitions_cover_terminal_states() -> None:
    """Workflow step lifecycle supports generic outcomes."""
    assert can_transition_workflow_step("pending", "running")
    assert can_transition_workflow_step("running", "completed")
    assert can_transition_workflow_step("running", "blocked_by_policy")
    assert can_transition_workflow_step("running", "waiting_for_approval")


def test_next_retry_uses_bounded_exponential_backoff() -> None:
    """Retry scheduling applies deterministic backoff bounds."""
    now = datetime.now(UTC)
    retry_at = calculate_next_retry_at(
        3,
        WorkflowRetryPolicy(
            max_attempts=5,
            backoff_seconds=10,
            backoff_multiplier=2.0,
            max_backoff_seconds=30,
        ),
        now,
    )

    assert retry_at is not None
    assert (retry_at - now).total_seconds() == 30
