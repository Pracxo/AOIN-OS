"""Scheduler notification integration tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.scheduler import (
    RecurrenceRule,
    ScheduleCreateRequest,
    SchedulerTickRequest,
)
from tests.scheduler_fakes import FakeSettings, service_graph


class FakeNotificationRouter:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def publish(self, request: object) -> object:
        self.requests.append(request)
        return request


def test_scheduler_tick_can_publish_local_notifications() -> None:
    _, schedules, _, _, tick, *_ = service_graph()
    router = FakeNotificationRouter()
    tick._notification_router = router
    tick._settings = FakeSettings()
    schedules.create_schedule(
        ScheduleCreateRequest(
            schedule_id="schedule-1",
            name="Notify",
            description="Notify locally.",
            schedule_type="notification",
            target_type="notification",
            action_mode="notify_only",
            recurrence=RecurrenceRule(frequency="once"),
            start_at=datetime(2026, 1, 1, 9, tzinfo=UTC),
            owner_scope=["workspace:main"],
        )
    )

    run = tick.run_tick(
        SchedulerTickRequest(
            scope=["workspace:main"],
            mode="controlled",
            window_start=datetime(2026, 1, 1, 8, tzinfo=UTC),
            window_end=datetime(2026, 1, 1, 10, tzinfo=UTC),
            create_notifications=True,
        )
    )

    assert run.notifications_created == 1
    assert len(router.requests) == 1
