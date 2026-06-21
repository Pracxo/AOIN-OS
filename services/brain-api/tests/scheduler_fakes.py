"""Shared scheduler test fakes."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.scheduler.due_items import DueItemService
from aion_brain.scheduler.policies import SchedulePolicyService
from aion_brain.scheduler.query import SchedulerQueryService
from aion_brain.scheduler.recurrence import RecurrenceEvaluator
from aion_brain.scheduler.reminders import ReminderService
from aion_brain.scheduler.reports import SchedulerReportService
from aion_brain.scheduler.repository import SchedulerRepository
from aion_brain.scheduler.service import ScheduleService
from aion_brain.scheduler.tick import SchedulerTickOrchestrator


class AllowPolicy:
    """Always-allow policy fake."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy(AllowPolicy):
    """Deny one action."""

    def __init__(self, action_type: str) -> None:
        super().__init__()
        self._action_type = action_type

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self._action_type
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=not allow,
            reason="allowed" if allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeTelemetry:
    """Collect telemetry events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeSettings:
    """Scheduler settings fake."""

    scheduler_enabled = True
    scheduler_tick_enabled = True
    scheduler_background_enabled = False
    reminders_enabled = True
    scheduler_create_notifications_default = False
    scheduler_create_action_proposals_default = False
    scheduler_create_operator_items_default = True
    scheduler_max_due_items_per_tick = 1000
    scheduler_default_timezone = "UTC"


def repository() -> SchedulerRepository:
    """Return an in-memory scheduler repository."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return SchedulerRepository(engine=engine)


def service_graph(
    *,
    policy: AllowPolicy | None = None,
    telemetry: FakeTelemetry | None = None,
) -> tuple[
    SchedulerRepository,
    ScheduleService,
    DueItemService,
    ReminderService,
    SchedulerTickOrchestrator,
    SchedulePolicyService,
    SchedulerReportService,
    SchedulerQueryService,
    AllowPolicy,
    FakeTelemetry,
]:
    repo = repository()
    selected_policy = policy or AllowPolicy()
    selected_telemetry = telemetry or FakeTelemetry()
    recurrence = RecurrenceEvaluator()
    due_items = DueItemService(repo, selected_policy, telemetry_service=selected_telemetry)
    reminders = ReminderService(
        repo,
        selected_policy,
        telemetry_service=selected_telemetry,
        settings=FakeSettings(),
    )
    schedules = ScheduleService(
        repo,
        selected_policy,
        recurrence_evaluator=recurrence,
        telemetry_service=selected_telemetry,
        settings=FakeSettings(),
    )
    tick = SchedulerTickOrchestrator(
        repo,
        selected_policy,
        due_item_service=due_items,
        reminder_service=reminders,
        recurrence_evaluator=recurrence,
        telemetry_service=selected_telemetry,
        settings=FakeSettings(),
    )
    policy_service = SchedulePolicyService(repo, selected_policy)
    reports = SchedulerReportService(repo, selected_policy, telemetry_service=selected_telemetry)
    query = SchedulerQueryService(repo)
    return (
        repo,
        schedules,
        due_items,
        reminders,
        tick,
        policy_service,
        reports,
        query,
        selected_policy,
        selected_telemetry,
    )
