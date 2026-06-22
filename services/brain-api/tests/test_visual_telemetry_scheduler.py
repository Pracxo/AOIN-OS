"""Scheduler visual telemetry tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.scheduler import RecurrenceRule, ScheduleCreateRequest
from tests.scheduler_fakes import service_graph


def test_scheduler_emits_visual_telemetry() -> None:
    _, schedules, *_, telemetry = service_graph()

    schedules.create_schedule(
        ScheduleCreateRequest(
            schedule_id="schedule-1",
            name="Telemetry",
            description="Emit telemetry.",
            recurrence=RecurrenceRule(frequency="once"),
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            owner_scope=["workspace:main"],
        )
    )

    assert any(
        getattr(event, "event_type", None) == "schedule_created" for event in telemetry.events
    )
