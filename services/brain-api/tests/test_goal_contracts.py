"""Goal contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.goals import GoalCreateRequest, GoalRecord


def test_goal_record_validates_status_priority_and_risk() -> None:
    """GoalRecord rejects unknown lifecycle values."""
    with pytest.raises(ValidationError):
        GoalRecord(
            goal_id="goal-1",
            title="Goal",
            description="Goal description",
            status="started",
            priority="normal",
            risk_level="low",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        GoalRecord(
            goal_id="goal-1",
            title="Goal",
            description="Goal description",
            status="proposed",
            priority="now",
            risk_level="low",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        GoalRecord(
            goal_id="goal-1",
            title="Goal",
            description="Goal description",
            status="proposed",
            priority="normal",
            risk_level="domain-risk",
            owner_scope=["workspace:main"],
        )


def test_goal_create_request_rejects_empty_owner_scope() -> None:
    """GoalCreateRequest requires an owner scope."""
    with pytest.raises(ValidationError):
        GoalCreateRequest(
            title="Goal",
            description="Goal description",
            owner_scope=[],
        )
