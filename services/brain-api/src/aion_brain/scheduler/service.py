"""Policy-gated local schedule service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aion_brain.contracts.scheduler import ScheduleCreateRequest, ScheduleRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.scheduler.policy_context import scheduler_policy_context
from aion_brain.scheduler.recurrence import RecurrenceEvaluator


class ScheduleService:
    """Create and mutate local schedules without executing target actions."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        recurrence_evaluator: RecurrenceEvaluator | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._recurrence = recurrence_evaluator or RecurrenceEvaluator()
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ScheduleService:
        return ScheduleService(
            self._repository,
            self._policy_adapter,
            recurrence_evaluator=self._recurrence,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_schedule(self, request: ScheduleCreateRequest) -> ScheduleRecord:
        if self._settings is not None and not bool(
            getattr(self._settings, "scheduler_enabled", True)
        ):
            raise RuntimeError("scheduler_disabled")
        authorize(
            self._policy_adapter,
            action_type="scheduler.schedule.create",
            resource_type="schedule",
            resource_id=request.schedule_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
            context=scheduler_policy_context(
                "scheduler.schedule.create",
                request.owner_scope,
                actor_context=self._actor_context,
            ),
        )
        now = datetime.now(UTC)
        next_due_at = self._recurrence.next_due(
            request.recurrence,
            request.start_at - timedelta(microseconds=1),
            request.start_at,
            request.end_at,
        )
        schedule = ScheduleRecord(
            schedule_id=request.schedule_id or f"schedule-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            name=request.name,
            description=request.description,
            schedule_type=request.schedule_type,
            target_type=request.target_type,
            action_mode=request.action_mode,
            recurrence=request.recurrence,
            start_at=request.start_at,
            end_at=request.end_at,
            timezone=request.timezone,
            status="active",
            next_due_at=next_due_at,
            owner_scope=request.owner_scope,
            target_payload=request.target_payload,
            metadata={**request.metadata, "no_target_execution": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        stored = _save_schedule(self._repository, schedule)
        self._record_side_effects(stored, "schedule_created")
        return stored

    def get_schedule(self, schedule_id: str, scope: list[str]) -> ScheduleRecord | None:
        authorize(
            self._policy_adapter,
            action_type="scheduler.schedule.read",
            resource_type="schedule",
            resource_id=schedule_id,
            scope=scope,
            risk_level="low",
            context=scheduler_policy_context(
                "scheduler.schedule.read",
                scope,
                actor_context=self._actor_context,
            ),
        )
        get_schedule = getattr(self._repository, "get_schedule", None)
        schedule = get_schedule(schedule_id) if callable(get_schedule) else None
        if isinstance(schedule, ScheduleRecord) and _scope_matches(schedule.owner_scope, scope):
            return schedule
        return None

    def list_schedules(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        schedule_type: str | None = None,
        limit: int = 100,
    ) -> list[ScheduleRecord]:
        authorize(
            self._policy_adapter,
            action_type="scheduler.schedule.read",
            resource_type="schedule",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_schedules = getattr(self._repository, "list_schedules", None)
        if not callable(list_schedules):
            return []
        result = list_schedules(
            scope=scope,
            status=status,
            schedule_type=schedule_type,
            limit=limit,
        )
        return [item for item in result if isinstance(item, ScheduleRecord)]

    def pause_schedule(self, schedule_id: str, scope: list[str]) -> ScheduleRecord:
        return self._update_status(schedule_id, scope, "paused", "schedule_paused")

    def resume_schedule(self, schedule_id: str, scope: list[str]) -> ScheduleRecord:
        schedule = self._require_schedule(schedule_id, scope)
        now = datetime.now(UTC)
        next_due_at = self._recurrence.next_due(
            schedule.recurrence,
            now,
            schedule.start_at,
            schedule.end_at,
        )
        updated = schedule.model_copy(
            update={
                "status": "active",
                "next_due_at": next_due_at,
                "paused_at": None,
                "updated_at": now,
            }
        )
        stored = _save_schedule(self._repository, updated)
        self._record_side_effects(stored, "schedule_resumed")
        return stored

    def disable_schedule(self, schedule_id: str, scope: list[str]) -> ScheduleRecord:
        return self._update_status(schedule_id, scope, "disabled", "schedule_disabled")

    def delete_schedule(self, schedule_id: str, scope: list[str]) -> bool:
        schedule = self._require_schedule(schedule_id, scope)
        authorize(
            self._policy_adapter,
            action_type="scheduler.schedule.delete",
            resource_type="schedule",
            resource_id=schedule_id,
            scope=scope,
            risk_level="medium",
            context=scheduler_policy_context(
                "scheduler.schedule.delete",
                scope,
                actor_context=self._actor_context,
            ),
        )
        now = datetime.now(UTC)
        _save_schedule(
            self._repository,
            schedule.model_copy(update={"status": "deleted", "deleted_at": now, "updated_at": now}),
        )
        return True

    def _update_status(
        self,
        schedule_id: str,
        scope: list[str],
        status: str,
        event_type: str,
    ) -> ScheduleRecord:
        schedule = self._require_schedule(schedule_id, scope)
        authorize(
            self._policy_adapter,
            action_type="scheduler.schedule.update",
            resource_type="schedule",
            resource_id=schedule_id,
            scope=scope,
            risk_level="medium",
            context=scheduler_policy_context(
                "scheduler.schedule.update",
                scope,
                actor_context=self._actor_context,
                extra={"status": status},
            ),
        )
        now = datetime.now(UTC)
        updates: dict[str, object] = {"status": status, "updated_at": now}
        if status == "paused":
            updates["paused_at"] = now
        if status == "disabled":
            updates["disabled_at"] = now
        stored = _save_schedule(self._repository, schedule.model_copy(update=updates))
        self._record_side_effects(stored, event_type)
        return stored

    def _require_schedule(self, schedule_id: str, scope: list[str]) -> ScheduleRecord:
        schedule = self.get_schedule(schedule_id, scope)
        if schedule is None:
            raise ValueError("schedule_not_found")
        return schedule

    def _record_side_effects(self, schedule: ScheduleRecord, event_type: str) -> None:
        emit_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="schedule",
            node_id=schedule.schedule_id,
            intensity=0.6,
            trace_id=schedule.trace_id,
            payload={
                "owner_scope": schedule.owner_scope,
                "schedule_type": schedule.schedule_type,
                "target_type": schedule.target_type,
                "no_target_execution": True,
            },
        )
        _best_effort_call(
            self._audit_sink,
            "record_event",
            {"event_type": event_type, "schedule_id": schedule.schedule_id},
        )
        _best_effort_call(
            self._provenance_service,
            "record_link",
            schedule.schedule_id,
            schedule.schedule_id,
            "scheduled_by",
        )


def _save_schedule(repository: object, schedule: ScheduleRecord) -> ScheduleRecord:
    save = getattr(repository, "save_schedule", None)
    stored = save(schedule) if callable(save) else schedule
    return stored if isinstance(stored, ScheduleRecord) else schedule


def _scope_matches(item_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(item_scope) & set(requested_scope))


def _best_effort_call(target: object | None, method_name: str, *args: object) -> None:
    method = getattr(target, method_name, None)
    if not callable(method):
        return
    try:
        method(*args)
    except Exception:
        return
