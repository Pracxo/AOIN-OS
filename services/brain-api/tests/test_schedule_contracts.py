"""Schedule contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.schedules import ScheduleRecord


def test_schedule_record_validates_owner_type_and_schedule_type() -> None:
    """ScheduleRecord validates owner and schedule vocabularies."""
    with pytest.raises(ValidationError):
        ScheduleRecord(
            schedule_id="schedule-1",
            owner_type="module",
            owner_id="task-1",
            schedule_type="once",
            schedule_expression="2026-06-07T09:00:00Z",
            timezone="UTC",
            status="active",
        )
    with pytest.raises(ValidationError):
        ScheduleRecord(
            schedule_id="schedule-1",
            owner_type="task",
            owner_id="task-1",
            schedule_type="magic",
            schedule_expression="2026-06-07T09:00:00Z",
            timezone="UTC",
            status="active",
        )
