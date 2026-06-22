"""Execution state machine tests."""

import pytest

from aion_brain.execution.state_machine import (
    can_transition_execution,
    can_transition_step,
    require_valid_execution_transition,
    require_valid_step_transition,
)


def test_execution_state_machine_allows_valid_transitions() -> None:
    """Allowed transitions return true."""
    assert can_transition_execution("pending", "running")
    assert can_transition_execution("running", "completed")
    assert can_transition_step("pending", "running")
    assert can_transition_step("running", "waiting_for_approval")


def test_execution_state_machine_rejects_invalid_transitions() -> None:
    """Invalid transitions raise."""
    assert not can_transition_execution("completed", "running")
    assert not can_transition_step("completed", "running")
    with pytest.raises(ValueError):
        require_valid_execution_transition("completed", "running")
    with pytest.raises(ValueError):
        require_valid_step_transition("completed", "running")
