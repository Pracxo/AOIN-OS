"""Reminder contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.reminders import ReminderRecord


def test_reminder_rejects_empty_scope_and_requires_snooze_time() -> None:
    with pytest.raises(ValidationError):
        ReminderRecord(
            reminder_id="reminder-1",
            reminder_type="generic",
            title="Review",
            message="Review item.",
            due_at=datetime(2026, 1, 1, tzinfo=UTC),
            status="pending",
            owner_scope=[],
        )
    with pytest.raises(ValidationError):
        ReminderRecord(
            reminder_id="reminder-1",
            reminder_type="generic",
            title="Review",
            message="Review item.",
            due_at=datetime(2026, 1, 1, tzinfo=UTC),
            status="snoozed",
            owner_scope=["workspace:main"],
        )
