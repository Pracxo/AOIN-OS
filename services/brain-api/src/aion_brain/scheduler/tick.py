"""Explicit local tick orchestrator for AION Scheduler."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aion_brain.contracts.action_proposals import ActionProposalCreateRequest
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.contracts.reminders import ReminderCreateRequest, ReminderRecord
from aion_brain.contracts.scheduler import (
    ScheduleDueItem,
    ScheduleRecord,
    SchedulerTickRequest,
    SchedulerTickRun,
    SchedulerTickStatus,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.scheduler.due_items import DueItemService
from aion_brain.scheduler.policy_context import scheduler_policy_context
from aion_brain.scheduler.recurrence import RecurrenceEvaluator
from aion_brain.scheduler.reminders import ReminderService


class SchedulerTickOrchestrator:
    """Run one deterministic scheduler tick when explicitly called."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        due_item_service: DueItemService,
        reminder_service: ReminderService,
        recurrence_evaluator: RecurrenceEvaluator | None = None,
        notification_router: object | None = None,
        action_proposal_service: object | None = None,
        operator_repository: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._due_items = due_item_service
        self._reminders = reminder_service
        self._recurrence = recurrence_evaluator or RecurrenceEvaluator()
        self._notification_router = notification_router
        self._action_proposal_service = action_proposal_service
        self._operator_repository = operator_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings

    def run_tick(self, request: SchedulerTickRequest) -> SchedulerTickRun:
        """Run one local scheduler tick. This does not execute scheduled targets."""

        if self._settings is not None and not bool(
            getattr(self._settings, "scheduler_tick_enabled", True)
        ):
            raise RuntimeError("scheduler_tick_disabled")
        decision = authorize(
            self._policy_adapter,
            action_type="scheduler.tick",
            resource_type="scheduler_tick",
            resource_id=request.tick_run_id,
            scope=request.scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level="medium" if request.mode == "controlled" else "low",
            context=scheduler_policy_context(
                "scheduler.tick",
                request.scope,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                extra={"mode": request.mode, "no_target_execution": True},
            ),
        )
        tick_at = _utc(request.tick_at or datetime.now(UTC))
        window_end = _utc(request.window_end or tick_at)
        window_start = _utc(request.window_start or (window_end - timedelta(minutes=1)))
        tick_run_id = request.tick_run_id or f"scheduler-tick-{uuid4().hex}"
        emit_telemetry(
            self._telemetry_service,
            event_type="scheduler_tick_started",
            node_type="scheduler_tick",
            node_id=tick_run_id,
            intensity=0.5,
            trace_id=request.trace_id,
            payload={"owner_scope": request.scope, "mode": request.mode},
        )
        schedules = self._eligible_schedules(request, window_end)
        due_items: list[ScheduleDueItem] = []
        reminders: list[ReminderRecord] = []
        errors: list[str] = []
        missed_count = 0
        max_due_items = request.max_due_items or int(
            getattr(self._settings, "scheduler_max_due_items_per_tick", 1000)
        )
        persist = request.mode == "controlled"
        for schedule in schedules:
            try:
                due_times = self._due_times(schedule, request, window_start, window_end)
                for due_at in due_times:
                    if len(due_items) >= max_due_items:
                        break
                    missed = due_at < window_start
                    if missed:
                        missed_count += 1
                        emit_telemetry(
                            self._telemetry_service,
                            event_type="schedule_missed_detected",
                            node_type="due_item",
                            node_id=schedule.schedule_id,
                            intensity=0.8,
                            trace_id=schedule.trace_id,
                            payload={
                                "owner_scope": schedule.owner_scope,
                                "due_at": due_at.isoformat(),
                            },
                        )
                    due_item = self._due_items.create_due_item(
                        schedule,
                        due_at,
                        tick_run_id,
                        missed=missed,
                        persist=persist,
                    )
                    due_items.append(due_item)
                    reminder = self._maybe_create_reminder(schedule, due_item, persist=persist)
                    if reminder is not None:
                        reminders.append(reminder)
                    if persist:
                        self._update_schedule_after_due(schedule, due_at, tick_run_id)
            except Exception as exc:
                errors.append(f"{schedule.schedule_id}:{exc.__class__.__name__}")
        notifications_created = (
            self._publish_notifications(due_items, reminders, request) if persist else 0
        )
        action_proposals_created = (
            self._create_action_proposals(due_items, request) if persist else 0
        )
        operator_items_created = self._create_operator_items(due_items, request) if persist else 0
        status: SchedulerTickStatus = (
            "dry_run" if request.mode == "dry_run" else ("warning" if errors else "completed")
        )
        tick_run = SchedulerTickRun(
            tick_run_id=tick_run_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.scope,
            mode=request.mode,
            status=status,
            tick_at=tick_at,
            window_start=window_start,
            window_end=window_end,
            schedules_checked=len(schedules),
            due_items_created=len(due_items),
            reminders_created=len(reminders),
            notifications_created=notifications_created,
            action_proposals_created=action_proposals_created,
            operator_items_created=operator_items_created,
            schedules_missed=missed_count,
            due_items=due_items,
            reminders=reminders,
            policy_decision_ids=[decision.decision_id],
            result={"no_target_execution": True},
            errors=errors,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        stored = _save_tick_run(self._repository, tick_run) if persist else tick_run
        emit_telemetry(
            self._telemetry_service,
            event_type="scheduler_tick_completed",
            node_type="scheduler_tick",
            node_id=stored.tick_run_id,
            intensity=0.8 if not errors else 0.95,
            trace_id=stored.trace_id,
            payload={"owner_scope": stored.owner_scope, "status": stored.status},
        )
        _best_effort_call(
            self._audit_sink,
            "record_event",
            {"event_type": "scheduler_tick_completed", "tick_run_id": stored.tick_run_id},
        )
        _best_effort_call(
            self._provenance_service,
            "record_link",
            stored.tick_run_id,
            stored.tick_run_id,
            "scheduler_tick_created",
        )
        return stored

    def get_tick_run(self, tick_run_id: str, scope: list[str]) -> SchedulerTickRun | None:
        authorize(
            self._policy_adapter,
            action_type="scheduler.report.read",
            resource_type="scheduler_tick",
            resource_id=tick_run_id,
            scope=scope,
            risk_level="low",
            context=scheduler_policy_context("scheduler.report.read", scope),
        )
        get = getattr(self._repository, "get_tick_run", None)
        tick_run = get(tick_run_id) if callable(get) else None
        if isinstance(tick_run, SchedulerTickRun) and set(tick_run.owner_scope) & set(scope):
            return tick_run
        return None

    def _eligible_schedules(
        self, request: SchedulerTickRequest, window_end: datetime
    ) -> list[ScheduleRecord]:
        list_schedules = getattr(self._repository, "list_schedules", None)
        if not callable(list_schedules):
            return []
        schedules = list_schedules(
            scope=request.scope,
            status="active",
            due_before=window_end,
            limit=request.max_due_items
            or int(getattr(self._settings, "scheduler_max_due_items_per_tick", 1000)),
        )
        result = [item for item in schedules if isinstance(item, ScheduleRecord)]
        if request.schedule_ids:
            allowed = set(request.schedule_ids)
            result = [item for item in result if item.schedule_id in allowed]
        return result

    def _due_times(
        self,
        schedule: ScheduleRecord,
        request: SchedulerTickRequest,
        window_start: datetime,
        window_end: datetime,
    ) -> list[datetime]:
        if schedule.recurrence.frequency == "manual":
            if request.force_manual and (
                not request.schedule_ids or schedule.schedule_id in set(request.schedule_ids)
            ):
                return [window_end]
            return []
        start = schedule.next_due_at or schedule.start_at
        due_times = self._recurrence.due_between(
            schedule.recurrence,
            schedule.start_at,
            min(window_start, start),
            window_end,
            end_at=schedule.end_at,
            max_items=request.max_due_items or 1000,
        )
        return [
            item
            for item in due_times
            if schedule.last_due_at is None or item > schedule.last_due_at
        ]

    def _maybe_create_reminder(
        self,
        schedule: ScheduleRecord,
        due_item: ScheduleDueItem,
        *,
        persist: bool,
    ) -> ReminderRecord | None:
        if schedule.target_type not in {"reminder", "notification", "operator_action", "generic"}:
            return None
        return self._reminders.create_reminder(
            ReminderCreateRequest(
                trace_id=due_item.trace_id,
                actor_id=due_item.actor_id,
                workspace_id=due_item.workspace_id,
                schedule_id=schedule.schedule_id,
                due_item_id=due_item.due_item_id,
                reminder_type="schedule",
                title=f"Schedule due: {schedule.name}",
                message=schedule.description,
                due_at=due_item.due_at,
                owner_scope=due_item.owner_scope,
                refs=[due_item.due_item_id],
                metadata={"schedule_type": schedule.schedule_type, "local_only": True},
                created_by=schedule.created_by,
            ),
            authorize_request=False,
            persist=persist,
        )

    def _update_schedule_after_due(
        self, schedule: ScheduleRecord, due_at: datetime, tick_run_id: str
    ) -> None:
        next_due = self._recurrence.next_due(
            schedule.recurrence,
            due_at,
            schedule.start_at,
            schedule.end_at,
        )
        status = (
            "completed"
            if schedule.recurrence.frequency == "once" and next_due is None
            else schedule.status
        )
        save = getattr(self._repository, "save_schedule", None)
        if callable(save):
            save(
                schedule.model_copy(
                    update={
                        "last_due_at": due_at,
                        "next_due_at": next_due,
                        "last_tick_run_id": tick_run_id,
                        "status": status,
                        "updated_at": datetime.now(UTC),
                    }
                )
            )

    def _publish_notifications(
        self,
        due_items: list[ScheduleDueItem],
        reminders: list[ReminderRecord],
        request: SchedulerTickRequest,
    ) -> int:
        enabled = request.create_notifications
        if enabled is None:
            enabled = bool(getattr(self._settings, "scheduler_create_notifications_default", True))
        publish = getattr(self._notification_router, "publish", None)
        if not enabled or not callable(publish):
            return 0
        count = 0
        for reminder in reminders:
            try:
                publish(
                    NotificationPublishRequest(
                        trace_id=reminder.trace_id,
                        actor_id=reminder.actor_id,
                        workspace_id=reminder.workspace_id,
                        topic_key="scheduler.reminder",
                        severity="info",
                        title=reminder.title,
                        message=reminder.message,
                        source_type="reminder",
                        source_id=reminder.reminder_id,
                        owner_scope=reminder.owner_scope,
                        refs=[*(reminder.refs), *(item.due_item_id for item in due_items)],
                        metadata={"local_only": True, "no_external_delivery": True},
                    )
                )
                count += 1
            except Exception:
                continue
        return count

    def _create_action_proposals(
        self, due_items: list[ScheduleDueItem], request: SchedulerTickRequest
    ) -> int:
        enabled = request.create_action_proposals
        if enabled is None:
            enabled = bool(
                getattr(self._settings, "scheduler_create_action_proposals_default", False)
            )
        create = getattr(self._action_proposal_service, "create_proposal", None)
        if not enabled or not callable(create):
            return 0
        count = 0
        for due_item in due_items:
            if due_item.action_mode != "propose_only":
                continue
            try:
                create(
                    ActionProposalCreateRequest(
                        trace_id=due_item.trace_id,
                        actor_id=due_item.actor_id,
                        workspace_id=due_item.workspace_id,
                        source_type="scheduler",
                        source_id=due_item.due_item_id,
                        proposal_type="generic",
                        title="Scheduled action proposal",
                        description="A local schedule created an action proposal for review.",
                        action_type="scheduler.proposed_action",
                        target_type=due_item.target_type,
                        owner_scope=due_item.owner_scope,
                        proposed_payload=due_item.target_payload,
                        risk_level="medium",
                        metadata={"no_execution": True},
                    )
                )
                count += 1
            except Exception:
                continue
        return count

    def _create_operator_items(
        self, due_items: list[ScheduleDueItem], request: SchedulerTickRequest
    ) -> int:
        enabled = request.create_operator_items
        if enabled is None:
            enabled = bool(getattr(self._settings, "scheduler_create_operator_items_default", True))
        save = getattr(self._operator_repository, "save_action_item", None)
        if not enabled or not callable(save):
            return 0
        from aion_brain.contracts.operator import OperatorActionItem

        count = 0
        for due_item in due_items:
            if due_item.action_mode not in {"operator_item_only", "notify_only", "manual"}:
                continue
            try:
                save(
                    OperatorActionItem(
                        action_item_id=f"operator-scheduler-{due_item.due_item_id}",
                        trace_id=due_item.trace_id,
                        source_type="due_item",
                        source_id=due_item.due_item_id,
                        category="scheduler",
                        severity="medium",
                        status="open",
                        title="Scheduled due item requires review.",
                        description="A local scheduler due item is ready for operator review.",
                        recommended_action="review_scheduler_due_item",
                        runbook_ref="docs/temporal-scheduler.md",
                        owner_scope=due_item.owner_scope,
                        metadata={"schedule_id": due_item.schedule_id},
                        created_at=datetime.now(UTC),
                    )
                )
                count += 1
            except Exception:
                continue
        return count


def _save_tick_run(repository: object, tick_run: SchedulerTickRun) -> SchedulerTickRun:
    save = getattr(repository, "save_tick_run", None)
    stored = save(tick_run) if callable(save) else tick_run
    return stored if isinstance(stored, SchedulerTickRun) else tick_run


def _best_effort_call(target: object | None, method_name: str, *args: object) -> None:
    method = getattr(target, method_name, None)
    if not callable(method):
        return
    try:
        method(*args)
    except Exception:
        return


def _utc(value: datetime) -> datetime:
    return value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)
