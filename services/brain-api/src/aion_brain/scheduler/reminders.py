"""Reminder queue service for the local scheduler."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.reminders import ReminderCreateRequest, ReminderRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.scheduler.policy_context import scheduler_policy_context


class ReminderService:
    """Create and manage local reminders."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ReminderService:
        return ReminderService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_reminder(
        self,
        request: ReminderCreateRequest,
        *,
        authorize_request: bool = True,
        persist: bool = True,
    ) -> ReminderRecord:
        if self._settings is not None and not bool(
            getattr(self._settings, "reminders_enabled", True)
        ):
            raise RuntimeError("reminders_disabled")
        if authorize_request:
            authorize(
                self._policy_adapter,
                action_type="scheduler.reminder.create",
                resource_type="reminder",
                resource_id=request.reminder_id,
                scope=request.owner_scope,
                trace_id=request.trace_id or self._actor_context.trace_id,
                actor_id=request.actor_id or self._actor_context.actor_id,
                workspace_id=request.workspace_id or self._actor_context.workspace_id,
                risk_level="medium",
                context=scheduler_policy_context(
                    "scheduler.reminder.create",
                    request.owner_scope,
                    actor_context=self._actor_context,
                ),
            )
        now = datetime.now(UTC)
        reminder = ReminderRecord(
            reminder_id=request.reminder_id or f"reminder-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            schedule_id=request.schedule_id,
            due_item_id=request.due_item_id,
            reminder_type=request.reminder_type,
            title=request.title,
            message=request.message,
            due_at=request.due_at,
            status="due" if request.due_at <= now else "pending",
            owner_scope=request.owner_scope,
            refs=request.refs,
            metadata={**request.metadata, "local_only": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
        )
        if not persist:
            return reminder
        stored = _save_reminder(self._repository, reminder)
        self._emit(stored, "reminder_created", 0.65)
        return stored

    def list_reminders(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        due_before: datetime | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ReminderRecord]:
        authorize(
            self._policy_adapter,
            action_type="scheduler.reminder.read",
            resource_type="reminder",
            resource_id=None,
            scope=scope,
            risk_level="low",
            context=scheduler_policy_context(
                "scheduler.reminder.read",
                scope,
                actor_context=self._actor_context,
            ),
        )
        list_reminders = getattr(self._repository, "list_reminders", None)
        if not callable(list_reminders):
            return []
        result = list_reminders(
            scope=scope,
            status=status,
            due_before=due_before,
            include_deleted=include_deleted,
            limit=limit,
        )
        return [item for item in result if isinstance(item, ReminderRecord)]

    def acknowledge(self, reminder_id: str, scope: list[str]) -> ReminderRecord:
        return self._update(reminder_id, scope, "acknowledged", "reminder_acknowledged")

    def dismiss(self, reminder_id: str, scope: list[str]) -> ReminderRecord:
        return self._update(reminder_id, scope, "dismissed", "reminder_dismissed")

    def snooze(self, reminder_id: str, scope: list[str], snoozed_until: datetime) -> ReminderRecord:
        reminder = self._require_reminder(reminder_id, scope)
        authorize(
            self._policy_adapter,
            action_type="scheduler.reminder.update",
            resource_type="reminder",
            resource_id=reminder_id,
            scope=scope,
            risk_level="low",
            context=scheduler_policy_context(
                "scheduler.reminder.update",
                scope,
                actor_context=self._actor_context,
            ),
        )
        stored = _save_reminder(
            self._repository,
            reminder.model_copy(
                update={
                    "status": "snoozed",
                    "snooze_count": reminder.snooze_count + 1,
                    "snoozed_until": snoozed_until,
                }
            ),
        )
        self._emit(stored, "reminder_snoozed", 0.45)
        return stored

    def _update(
        self, reminder_id: str, scope: list[str], status: str, event_type: str
    ) -> ReminderRecord:
        reminder = self._require_reminder(reminder_id, scope)
        authorize(
            self._policy_adapter,
            action_type="scheduler.reminder.update",
            resource_type="reminder",
            resource_id=reminder_id,
            scope=scope,
            risk_level="low",
            context=scheduler_policy_context(
                "scheduler.reminder.update",
                scope,
                actor_context=self._actor_context,
            ),
        )
        now = datetime.now(UTC)
        updates: dict[str, object] = {"status": status}
        if status == "acknowledged":
            updates["acknowledged_at"] = now
        if status == "dismissed":
            updates["dismissed_at"] = now
        stored = _save_reminder(self._repository, reminder.model_copy(update=updates))
        self._emit(stored, event_type, 0.4)
        return stored

    def _require_reminder(self, reminder_id: str, scope: list[str]) -> ReminderRecord:
        get = getattr(self._repository, "get_reminder", None)
        reminder = get(reminder_id) if callable(get) else None
        if not isinstance(reminder, ReminderRecord) or not set(reminder.owner_scope) & set(scope):
            raise ValueError("reminder_not_found")
        return reminder

    def _emit(self, reminder: ReminderRecord, event_type: str, intensity: float) -> None:
        emit_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="reminder",
            node_id=reminder.reminder_id,
            intensity=intensity,
            trace_id=reminder.trace_id,
            edge_from=reminder.schedule_id,
            edge_to=reminder.reminder_id,
            payload={"owner_scope": reminder.owner_scope, "status": reminder.status},
        )


def _save_reminder(repository: object, reminder: ReminderRecord) -> ReminderRecord:
    save = getattr(repository, "save_reminder", None)
    stored = save(reminder) if callable(save) else reminder
    return stored if isinstance(stored, ReminderRecord) else reminder
