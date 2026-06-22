"""Schedule metadata service."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.schedules import ScheduleCreateRequest, ScheduleRecord
from aion_brain.contracts.tasks import TaskLifecycleEvent
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.schedules.repository import ScheduleRepository
from aion_brain.tasks.publisher import TaskLifecyclePublisher


class ScheduleService:
    """Policy-gated schedule metadata service with no worker loop."""

    def __init__(
        self,
        *,
        repository: ScheduleRepository | object,
        policy_adapter: PolicyAdapter,
        publisher: TaskLifecyclePublisher | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._publisher = publisher
        self._telemetry_service = telemetry_service

    def create_schedule(self, request: ScheduleCreateRequest) -> ScheduleRecord:
        """Store schedule metadata only."""
        decision = self._authorize(
            "schedule.create",
            request.schedule_id,
            "medium",
            {"owner_type": request.owner_type, "owner_id": request.owner_id},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        schedule = ScheduleRecord(
            schedule_id=request.schedule_id or f"schedule-{uuid4().hex}",
            owner_type=request.owner_type,
            owner_id=request.owner_id,
            schedule_type=request.schedule_type,
            schedule_expression=request.schedule_expression,
            timezone=request.timezone,
            status="active",
            next_run_at=request.next_run_at,
            last_run_at=None,
            metadata=request.metadata,
            created_at=now,
            updated_at=now,
        )
        saved = self._save_schedule(schedule)
        self._record_event(saved, "schedule_created")
        self._emit_schedule(saved, "schedule_created", 0.4)
        return saved

    def get_schedule(self, schedule_id: str) -> ScheduleRecord | None:
        """Return a schedule by ID."""
        decision = self._authorize("schedule.read", schedule_id, "low", {})
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        get_schedule = getattr(self._repository, "get_schedule", None)
        if callable(get_schedule):
            result = get_schedule(schedule_id)
            if isinstance(result, ScheduleRecord) or result is None:
                return result
        return None

    def list_schedules(
        self,
        owner_type: str | None = None,
        owner_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ScheduleRecord]:
        """List schedule metadata records."""
        decision = self._authorize("schedule.read", None, "low", {})
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        list_schedules = getattr(self._repository, "list_schedules", None)
        if callable(list_schedules):
            result = list_schedules(
                owner_type=owner_type,
                owner_id=owner_id,
                status=status,
                limit=limit,
            )
            if isinstance(result, list):
                return [item for item in result if isinstance(item, ScheduleRecord)]
        return []

    def pause_schedule(self, schedule_id: str) -> ScheduleRecord:
        """Pause schedule metadata."""
        return self._update_schedule_status(schedule_id, "paused")

    def cancel_schedule(self, schedule_id: str) -> ScheduleRecord:
        """Cancel schedule metadata."""
        return self._update_schedule_status(schedule_id, "cancelled")

    def _update_schedule_status(self, schedule_id: str, status: str) -> ScheduleRecord:
        schedule = self.get_schedule(schedule_id)
        if schedule is None:
            raise ValueError("schedule_not_found")
        decision = self._authorize("schedule.update", schedule_id, "medium", {"status": status})
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        updated = schedule.model_copy(update={"status": status, "updated_at": datetime.now(UTC)})
        saved = self._save_schedule(updated)
        self._record_event(saved, "schedule_updated")
        self._emit_schedule(saved, "schedule_updated", 0.5)
        return saved

    def _authorize(
        self,
        action_type: str,
        resource_id: str | None,
        risk_level: str,
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type="schedule",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[],
                security_scope=["workspace:main"],
                context=context,
            )
        )

    def _save_schedule(self, schedule: ScheduleRecord) -> ScheduleRecord:
        save_schedule = getattr(self._repository, "save_schedule", None)
        if callable(save_schedule):
            result = save_schedule(schedule)
            if isinstance(result, ScheduleRecord):
                return result
        return schedule

    def _record_event(self, schedule: ScheduleRecord, event_type: str) -> None:
        event = TaskLifecycleEvent(
            lifecycle_event_id=f"lifecycle-{schedule.schedule_id}-{event_type}-{uuid4().hex}",
            task_id=schedule.owner_id if schedule.owner_type == "task" else None,
            goal_id=schedule.owner_id if schedule.owner_type == "goal" else None,
            trace_id=None,
            event_type=event_type,  # type: ignore[arg-type]
            from_status=None,
            to_status=schedule.status,
            reason=None,
            payload={"schedule_type": schedule.schedule_type},
            created_at=datetime.now(UTC),
        )
        save_event = getattr(self._repository, "save_lifecycle_event", None)
        if callable(save_event):
            save_event(event)
        if self._publisher is not None:
            self._publisher.publish(event)

    def _emit_schedule(self, schedule: ScheduleRecord, event_type: str, intensity: float) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{schedule.schedule_id}-{event_type}",
            trace_id=schedule.owner_id,
            event_type=event_type,  # type: ignore[arg-type]
            node_type="schedule",
            node_id=schedule.schedule_id,
            edge_from=schedule.owner_id,
            edge_to=schedule.schedule_id,
            intensity=intensity,
            payload={"status": schedule.status, "owner_type": schedule.owner_type},
            created_at=datetime.now(UTC),
        )
        emit = getattr(self._telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
