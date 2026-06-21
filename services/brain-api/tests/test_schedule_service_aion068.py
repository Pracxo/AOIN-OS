"""AION-068 schedule service tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.scheduler import RecurrenceRule, ScheduleCreateRequest
from tests.scheduler_fakes import DenyPolicy, service_graph


def test_schedule_service_creates_and_reads_schedule() -> None:
    _, schedules, *_ = service_graph()
    schedule = schedules.create_schedule(_request())

    assert schedule.status == "active"
    assert schedule.next_due_at == datetime(2026, 1, 1, 9, tzinfo=UTC)
    assert schedules.get_schedule(schedule.schedule_id, ["workspace:main"]) == schedule


def test_schedule_service_pause_resume_disable_delete() -> None:
    _, schedules, *_ = service_graph()
    schedule = schedules.create_schedule(_request())

    assert schedules.pause_schedule(schedule.schedule_id, ["workspace:main"]).status == "paused"
    assert schedules.resume_schedule(schedule.schedule_id, ["workspace:main"]).status == "active"
    assert schedules.disable_schedule(schedule.schedule_id, ["workspace:main"]).status == "disabled"
    assert schedules.delete_schedule(schedule.schedule_id, ["workspace:main"]) is True


def test_policy_deny_blocks_schedule_create() -> None:
    _, schedules, *_ = service_graph(policy=DenyPolicy("scheduler.schedule.create"))

    with pytest.raises(PermissionError):
        schedules.create_schedule(_request())


def _request() -> ScheduleCreateRequest:
    return ScheduleCreateRequest(
        schedule_id="schedule-1",
        name="Review local due item",
        description="Create local records only.",
        schedule_type="reminder",
        target_type="reminder",
        action_mode="notify_only",
        recurrence=RecurrenceRule(frequency="once"),
        start_at=datetime(2026, 1, 1, 9, tzinfo=UTC),
        owner_scope=["workspace:main"],
    )
