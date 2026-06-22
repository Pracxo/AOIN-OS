"""Task contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.tasks import CognitiveTask


def test_cognitive_task_validates_task_type() -> None:
    """CognitiveTask accepts generic task types."""
    task = CognitiveTask(
        task_id="task-1",
        title="Task",
        description="Task description",
        task_type="generic",
        status="proposed",
        priority="normal",
        risk_level="low",
        owner_scope=["workspace:main"],
    )

    assert task.task_type == "generic"


def test_cognitive_task_rejects_domain_specific_task_type() -> None:
    """Domain-specific task types are not valid Brain core contracts."""
    with pytest.raises(ValidationError):
        CognitiveTask(
            task_id="task-1",
            title="Task",
            description="Task description",
            task_type="finance.trade",
            status="proposed",
            priority="normal",
            risk_level="low",
            owner_scope=["workspace:main"],
        )
