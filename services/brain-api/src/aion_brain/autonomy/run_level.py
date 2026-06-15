"""Run-level control service."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.autonomy.repository import AutonomyRepository
from aion_brain.contracts.autonomy import AutonomyLifecycleEvent, RunLevelRecord, SetRunLevelRequest
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter


class RunLevelService:
    """Manage active AION operating run levels."""

    def __init__(
        self,
        repository: AutonomyRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def set_run_level(self, request: SetRunLevelRequest) -> RunLevelRecord:
        """Set one run level and end any matching active run level."""
        self._authorize(
            "autonomy.run_level.set",
            request.actor_id,
            request.workspace_id,
            ["workspace:main"],
            {"run_level": request.run_level, "reason": request.reason},
        )
        now = datetime.now(UTC)
        current = self.get_active_run_level(request.actor_id, request.workspace_id)
        if current is not None:
            ended = current.model_copy(
                update={"status": "ended", "ended_at": now, "reason": "replaced_by_new_run_level"}
            )
            self._repository.save_run_level(ended)
            self._record_event("run_level_ended", run_level=ended)
        record = RunLevelRecord(
            run_level_id=request.run_level_id or f"run-level-{uuid4().hex}",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            active_profile_id=request.active_profile_id,
            run_level=request.run_level,
            status="active",
            reason=request.reason,
            constraints=request.constraints,
            metadata=request.metadata,
            set_by=request.set_by,
            created_at=now,
            expires_at=request.expires_at,
            ended_at=None,
        )
        saved = self._repository.save_run_level(record)
        self._record_event("run_level_set", run_level=saved)
        return saved

    def get_active_run_level(
        self,
        actor_id: str | None,
        workspace_id: str | None,
    ) -> RunLevelRecord | None:
        """Return the active non-expired run level."""
        self._authorize(
            "autonomy.run_level.read",
            actor_id,
            workspace_id,
            ["workspace:main"],
            {},
            risk_level="low",
        )
        return self._repository.get_active_run_level(actor_id=actor_id, workspace_id=workspace_id)

    def list_run_levels(
        self,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[RunLevelRecord]:
        """List run levels."""
        self._authorize(
            "autonomy.run_level.read",
            actor_id,
            workspace_id,
            ["workspace:main"],
            {"status": status},
            risk_level="low",
        )
        return self._repository.list_run_levels(
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
        )

    def end_run_level(
        self,
        run_level_id: str,
        actor_id: str | None,
        reason: str,
    ) -> RunLevelRecord:
        """End one active run level."""
        record = self._repository.get_run_level(run_level_id)
        if record is None:
            raise ValueError("run_level_not_found")
        self._authorize(
            "autonomy.run_level.end",
            actor_id,
            record.workspace_id,
            ["workspace:main"],
            {"reason": reason},
        )
        updated = record.model_copy(
            update={"status": "ended", "reason": reason, "ended_at": datetime.now(UTC)}
        )
        saved = self._repository.save_run_level(updated)
        self._record_event("run_level_ended", run_level=saved)
        return saved

    def expire_old_run_levels(
        self,
        now: datetime | None = None,
        limit: int = 100,
    ) -> list[RunLevelRecord]:
        """Expire old active run levels."""
        current = now or datetime.now(UTC)
        expired: list[RunLevelRecord] = []
        for record in self._repository.list_run_levels(status="active")[:limit]:
            if record.expires_at is not None and _aware(record.expires_at) <= current:
                saved = self._repository.save_run_level(
                    record.model_copy(update={"status": "expired", "ended_at": current})
                )
                expired.append(saved)
                self._record_event("run_level_ended", run_level=saved)
        return expired

    def _authorize(
        self,
        action_type: str,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        context: dict[str, object],
        *,
        risk_level: str = "medium",
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="run_level",
                resource_id=None,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _record_event(self, event_type: str, *, run_level: RunLevelRecord) -> None:
        event = AutonomyLifecycleEvent(
            autonomy_event_id=f"autonomy-event-{uuid4().hex}",
            run_level_id=run_level.run_level_id,
            trace_id=None,
            event_type=event_type,  # type: ignore[arg-type]
            actor_id=run_level.actor_id,
            workspace_id=run_level.workspace_id,
            payload={"run_level": run_level.run_level, "status": run_level.status},
            created_at=datetime.now(UTC),
        )
        self._repository.save_lifecycle_event(event)
        _emit(
            self._telemetry_service,
            event_type,
            "run_level",
            run_level.run_level_id,
            0.7,
            event.payload,
        )


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    payload: dict[str, object],
) -> None:
    if telemetry_service is None:
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
    try:
        emit = getattr(telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
            return
        save = getattr(telemetry_service, "save_visual_telemetry", None)
        if callable(save):
            save(event.trace_id, [event])
    except Exception:
        return


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
