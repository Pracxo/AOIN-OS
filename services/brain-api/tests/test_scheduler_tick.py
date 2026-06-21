"""Scheduler tick tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.scheduler import (
    RecurrenceRule,
    ScheduleCreateRequest,
    SchedulerTickRequest,
)
from tests.scheduler_fakes import service_graph


def test_tick_dry_run_creates_no_persistent_due_items() -> None:
    _, schedules, due_items, _, tick, *_ = service_graph()
    schedules.create_schedule(_request())

    run = tick.run_tick(
        SchedulerTickRequest(
            scope=["workspace:main"],
            mode="dry_run",
            window_start=datetime(2026, 1, 1, 8, tzinfo=UTC),
            window_end=datetime(2026, 1, 1, 10, tzinfo=UTC),
        )
    )

    assert run.status == "dry_run"
    assert run.due_items_created == 1
    assert due_items.list_due_items(["workspace:main"]) == []


def test_tick_controlled_persists_due_item_and_reminder() -> None:
    repo, schedules, due_items, reminders, tick, *_ = service_graph()
    schedules.create_schedule(_request())

    run = tick.run_tick(
        SchedulerTickRequest(
            scope=["workspace:main"],
            mode="controlled",
            window_start=datetime(2026, 1, 1, 8, tzinfo=UTC),
            window_end=datetime(2026, 1, 1, 10, tzinfo=UTC),
        )
    )

    assert run.status == "completed"
    assert len(due_items.list_due_items(["workspace:main"])) == 1
    assert len(reminders.list_reminders(["workspace:main"])) == 1
    assert repo.get_tick_run(run.tick_run_id) is not None


def _request() -> ScheduleCreateRequest:
    return ScheduleCreateRequest(
        schedule_id="schedule-1",
        name="Due",
        description="Due item.",
        schedule_type="reminder",
        target_type="reminder",
        action_mode="notify_only",
        recurrence=RecurrenceRule(frequency="once"),
        start_at=datetime(2026, 1, 1, 9, tzinfo=UTC),
        owner_scope=["workspace:main"],
    )
