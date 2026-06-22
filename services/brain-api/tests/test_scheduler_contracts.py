"""Scheduler contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.scheduler import RecurrenceRule, ScheduleCreateRequest


def test_recurrence_rule_validates_bounds() -> None:
    with pytest.raises(ValidationError):
        RecurrenceRule(frequency="daily", interval=0)
    with pytest.raises(ValidationError):
        RecurrenceRule(frequency="weekly", days_of_week=[7])
    with pytest.raises(ValidationError):
        RecurrenceRule(frequency="monthly", day_of_month=32)


def test_schedule_rejects_direct_execution_payload() -> None:
    with pytest.raises(ValidationError):
        ScheduleCreateRequest(
            name="Unsafe",
            description="Do not execute.",
            schedule_type="generic",
            target_type="generic",
            action_mode="notify_only",
            recurrence=RecurrenceRule(frequency="once"),
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            owner_scope=["workspace:main"],
            target_payload={"execute": True},
        )
