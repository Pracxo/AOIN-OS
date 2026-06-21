"""Due item service tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.scheduler import RecurrenceRule, ScheduleCreateRequest
from tests.scheduler_fakes import service_graph


def test_due_item_service_is_idempotent() -> None:
    _, schedules, due_items, *_ = service_graph()
    schedule = schedules.create_schedule(
        ScheduleCreateRequest(
            schedule_id="schedule-1",
            name="Due",
            description="Due item.",
            recurrence=RecurrenceRule(frequency="once"),
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            owner_scope=["workspace:main"],
        )
    )

    first = due_items.create_due_item(schedule, schedule.start_at, "tick-1")
    second = due_items.create_due_item(schedule, schedule.start_at, "tick-1")

    assert first.due_item_id == second.due_item_id
    assert due_items.list_due_items(["workspace:main"], status="due") == [first]
