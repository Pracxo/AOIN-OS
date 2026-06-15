"""Cognitive cycle state-machine tests."""

import pytest

from aion_brain.cycles.state_machine import (
    can_transition_cycle_run,
    can_transition_cycle_step,
    require_valid_cycle_run_transition,
    require_valid_cycle_step_transition,
)


def test_cycle_run_transitions_match_contract() -> None:
    """Cycle run status transitions are explicit."""
    assert can_transition_cycle_run("pending", "running")
    assert can_transition_cycle_run("pending", "blocked_by_policy")
    assert can_transition_cycle_run("running", "completed")
    assert can_transition_cycle_run("running", "waiting_for_approval")
    assert not can_transition_cycle_run("completed", "running")


def test_cycle_step_transitions_match_contract() -> None:
    """Cycle step status transitions are explicit."""
    assert can_transition_cycle_step("pending", "running")
    assert can_transition_cycle_step("running", "completed")
    assert can_transition_cycle_step("running", "blocked_by_policy")
    assert not can_transition_cycle_step("completed", "running")


def test_invalid_cycle_transitions_raise() -> None:
    """Invalid transitions fail fast."""
    with pytest.raises(ValueError):
        require_valid_cycle_run_transition("completed", "running")
    with pytest.raises(ValueError):
        require_valid_cycle_step_transition("completed", "pending")

