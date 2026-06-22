"""Scheduler audit integration tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.scheduler import RecurrenceRule, ScheduleCreateRequest
from tests.scheduler_fakes import service_graph


class FakeAudit:
    def __init__(self) -> None:
        self.events: list[object] = []

    def record_event(self, event: object) -> None:
        self.events.append(event)


def test_schedule_creation_records_audit_event_best_effort() -> None:
    _, schedules, *_ = service_graph()
    audit = FakeAudit()
    schedules._audit_sink = audit

    schedules.create_schedule(
        ScheduleCreateRequest(
            schedule_id="schedule-1",
            name="Audit",
            description="Audit local schedule.",
            recurrence=RecurrenceRule(frequency="once"),
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            owner_scope=["workspace:main"],
        )
    )

    assert audit.events
