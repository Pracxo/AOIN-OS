"""Explicit local workflow scheduler tick."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.schedules import ScheduleRecord
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.workflows import WorkflowRunRequest


class LocalScheduler:
    """Convert due schedule metadata into workflow run requests on explicit ticks."""

    def __init__(
        self,
        *,
        schedule_service: object,
        schedule_repository: object,
        workflow_service: object,
        enabled: bool,
        telemetry_service: object | None = None,
        autonomy_governor: object | None = None,
    ) -> None:
        self._schedule_service = schedule_service
        self._schedule_repository = schedule_repository
        self._workflow_service = workflow_service
        self._enabled = enabled
        self._telemetry_service = telemetry_service
        self._autonomy_governor = autonomy_governor

    def tick(self, now: datetime | None = None) -> dict[str, Any]:
        """Run one deterministic scheduler tick."""
        if not self._enabled:
            return {"status": "skipped", "reason": "workflow_scheduler_disabled", "triggered": 0}
        autonomy = self._autonomy_decision()
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return {
                "status": "blocked_by_autonomy",
                "reason": str(getattr(autonomy, "reason", "autonomy_denied")),
                "triggered": 0,
            }
        current = now or datetime.now(UTC)
        list_schedules = getattr(self._schedule_service, "list_schedules", None)
        if not callable(list_schedules):
            return {"status": "failed", "reason": "schedule_service_unavailable", "triggered": 0}
        schedules = list_schedules(status="active", limit=100)
        triggered = 0
        skipped = 0
        errors: list[dict[str, Any]] = []
        for schedule in schedules:
            if not isinstance(schedule, ScheduleRecord) or not _due(schedule, current):
                continue
            if schedule.owner_type == "workflow":
                try:
                    run_workflow = getattr(self._workflow_service, "run_workflow", None)
                    if not callable(run_workflow):
                        raise RuntimeError("workflow_service_unavailable")
                    run_workflow(
                        WorkflowRunRequest(
                            workflow_id=schedule.owner_id,
                            mode="dry_run",
                            input={"schedule_id": schedule.schedule_id},
                            metadata={
                                "scheduled": True,
                                "security_scope": _scope_from_schedule(schedule),
                            },
                        )
                    )
                    triggered += 1
                    self._update_schedule(schedule, current)
                except Exception as exc:
                    errors.append({"schedule_id": schedule.schedule_id, "reason": str(exc)})
            elif schedule.owner_type == "task":
                skipped += 1
                self._update_schedule(schedule, current)
            else:
                skipped += 1
        self._emit(
            "workflow_scheduler_tick",
            "scheduler",
            "local-scheduler",
            0.5,
            {"triggered": triggered},
        )
        return {"status": "completed", "triggered": triggered, "skipped": skipped, "errors": errors}

    def _autonomy_decision(self) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    actor_id="aion-system",
                    workspace_id=None,
                    requested_mode="dry_run",
                    action_type="workflow.scheduler.tick",
                    resource_type="scheduler",
                    resource_id="local-scheduler",
                    risk_level="medium",
                    approval_present=False,
                    context={"security_scope": ["workspace:main"]},
                    metadata={"scheduler": "local"},
                )
            ),
        )

    def _update_schedule(self, schedule: ScheduleRecord, now: datetime) -> None:
        save_schedule = getattr(self._schedule_repository, "save_schedule", None)
        if not callable(save_schedule):
            return
        updates: dict[str, Any] = {"last_run_at": now, "updated_at": now}
        if schedule.schedule_type == "once":
            updates["next_run_at"] = None
            updates["status"] = "paused"
        elif schedule.schedule_type == "interval":
            updates["next_run_at"] = now + timedelta(seconds=_interval_seconds(schedule))
        save_schedule(schedule.model_copy(update=updates))

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{node_id}-{event_type}",
            trace_id=node_id,
            event_type=event_type,  # type: ignore[arg-type]
            node_type=node_type,  # type: ignore[arg-type]
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=intensity,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        emit = getattr(self._telemetry_service, "emit", None)
        if callable(emit):
            emit(event)


def _due(schedule: ScheduleRecord, now: datetime) -> bool:
    return schedule.next_run_at is not None and schedule.next_run_at <= now


def _interval_seconds(schedule: ScheduleRecord) -> int:
    try:
        return max(1, int(schedule.schedule_expression))
    except ValueError:
        return max(1, int(schedule.metadata.get("interval_seconds", 60)))


def _scope_from_schedule(schedule: ScheduleRecord) -> list[str]:
    value = schedule.metadata.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return ["workspace:main"]
