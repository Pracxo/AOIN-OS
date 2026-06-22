"""Schedule metadata service tests."""

import pytest

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.schedules import ScheduleCreateRequest, ScheduleRecord
from aion_brain.contracts.tasks import TaskLifecycleEvent
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.schedules.service import ScheduleService
from aion_brain.tasks.publisher import NoopTaskLifecyclePublisher


class FakePolicyAdapter:
    """Policy fake for schedule service tests."""

    def __init__(self, *, deny_action: str | None = None) -> None:
        self.deny_action = deny_action
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeScheduleRepository:
    """In-memory schedule repository fake."""

    def __init__(self) -> None:
        self.schedules: dict[str, ScheduleRecord] = {}
        self.events: list[TaskLifecycleEvent] = []

    def save_schedule(self, schedule: ScheduleRecord) -> ScheduleRecord:
        self.schedules[schedule.schedule_id] = schedule
        return schedule

    def get_schedule(self, schedule_id: str) -> ScheduleRecord | None:
        return self.schedules.get(schedule_id)

    def list_schedules(
        self,
        *,
        owner_type: str | None = None,
        owner_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ScheduleRecord]:
        schedules = [
            schedule
            for schedule in self.schedules.values()
            if (owner_type is None or schedule.owner_type == owner_type)
            and (owner_id is None or schedule.owner_id == owner_id)
            and (status is None or schedule.status == status)
        ]
        return schedules[:limit]

    def save_lifecycle_event(self, event: TaskLifecycleEvent) -> TaskLifecycleEvent:
        self.events.append(event)
        return event


class FakeTelemetry:
    """Telemetry fake for schedule service tests."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_schedule_service_stores_metadata_only() -> None:
    """Schedule creation stores metadata and emits lifecycle records."""
    repository = FakeScheduleRepository()
    publisher = NoopTaskLifecyclePublisher(published=False)
    telemetry = FakeTelemetry()
    service = ScheduleService(
        repository=repository,
        policy_adapter=FakePolicyAdapter(),
        publisher=publisher,
        telemetry_service=telemetry,
    )

    schedule = service.create_schedule(
        ScheduleCreateRequest(
            schedule_id="schedule-1",
            owner_type="task",
            owner_id="task-1",
            schedule_type="once",
            schedule_expression="2026-06-07T09:00:00Z",
        )
    )

    assert schedule.status == "active"
    assert repository.schedules["schedule-1"] == schedule
    assert repository.events[0].event_type == "schedule_created"
    assert publisher.events[0].task_id == "task-1"
    assert telemetry.events[0].event_type == "schedule_created"
    assert not hasattr(service, "start")
    assert not hasattr(service, "run_forever")


def test_schedule_service_pause_and_cancel_update_metadata() -> None:
    """Pause and cancel update schedule metadata without running a worker."""
    repository = FakeScheduleRepository()
    service = ScheduleService(repository=repository, policy_adapter=FakePolicyAdapter())
    service.create_schedule(
        ScheduleCreateRequest(
            schedule_id="schedule-1",
            owner_type="goal",
            owner_id="goal-1",
            schedule_type="cron",
            schedule_expression="0 9 * * *",
        )
    )

    paused = service.pause_schedule("schedule-1")
    cancelled = service.cancel_schedule("schedule-1")

    assert paused.status == "paused"
    assert cancelled.status == "cancelled"
    assert [event.event_type for event in repository.events] == [
        "schedule_created",
        "schedule_updated",
        "schedule_updated",
    ]


def test_schedule_service_policy_deny_blocks_create() -> None:
    """Policy denial blocks schedule metadata creation."""
    repository = FakeScheduleRepository()
    service = ScheduleService(
        repository=repository,
        policy_adapter=FakePolicyAdapter(deny_action="schedule.create"),
    )

    with pytest.raises(ValueError, match="policy_denied"):
        service.create_schedule(
            ScheduleCreateRequest(
                schedule_id="schedule-1",
                owner_type="task",
                owner_id="task-1",
                schedule_type="once",
                schedule_expression="2026-06-07T09:00:00Z",
            )
        )

    assert repository.schedules == {}
