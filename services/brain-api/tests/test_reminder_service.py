"""Reminder service tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.reminders import ReminderCreateRequest
from tests.scheduler_fakes import service_graph


def test_reminder_service_lifecycle() -> None:
    _, _, _, reminders, *_ = service_graph()
    reminder = reminders.create_reminder(
        ReminderCreateRequest(
            reminder_id="reminder-1",
            title="Review",
            message="Review local item.",
            due_at=datetime(2026, 1, 1, tzinfo=UTC),
            owner_scope=["workspace:main"],
        )
    )

    snoozed = reminders.snooze(
        reminder.reminder_id,
        ["workspace:main"],
        datetime.now(UTC) + timedelta(hours=1),
    )
    acknowledged = reminders.acknowledge(reminder.reminder_id, ["workspace:main"])
    dismissed = reminders.dismiss(reminder.reminder_id, ["workspace:main"])

    assert reminder.status == "due"
    assert snoozed.status == "snoozed"
    assert acknowledged.status == "acknowledged"
    assert dismissed.status == "dismissed"
