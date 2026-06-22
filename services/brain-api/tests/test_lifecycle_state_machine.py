"""Lifecycle state machine tests."""

import pytest

from aion_brain.lifecycle.state_machine import (
    can_transition_goal,
    can_transition_task,
    require_valid_goal_transition,
    require_valid_task_transition,
)


def test_goal_lifecycle_allows_valid_transitions() -> None:
    """Goal lifecycle allows configured transitions."""
    assert can_transition_goal("proposed", "active") is True
    assert can_transition_goal("active", "completed") is True
    require_valid_goal_transition("paused", "active")


def test_goal_lifecycle_rejects_invalid_transitions() -> None:
    """Goal lifecycle rejects invalid transitions."""
    assert can_transition_goal("completed", "active") is False
    with pytest.raises(ValueError):
        require_valid_goal_transition("completed", "active")


def test_task_lifecycle_allows_valid_transitions() -> None:
    """Task lifecycle allows configured transitions."""
    assert can_transition_task("proposed", "queued") is True
    assert can_transition_task("queued", "running") is True
    require_valid_task_transition("running", "completed")


def test_task_lifecycle_rejects_invalid_transitions() -> None:
    """Task lifecycle rejects invalid transitions."""
    assert can_transition_task("completed", "running") is False
    with pytest.raises(ValueError):
        require_valid_task_transition("completed", "running")
