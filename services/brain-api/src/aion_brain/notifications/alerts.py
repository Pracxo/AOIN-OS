"""Alert service for local notification routing."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.alerts import AlertCreateRequest, AlertQuery, AlertRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class AlertService:
    """Create and manage generic local alerts."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> AlertService:
        return AlertService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_alert(self, request: AlertCreateRequest) -> AlertRecord:
        authorize(
            self._policy_adapter,
            action_type="alert.create",
            resource_type="alert",
            resource_id=request.alert_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="high" if request.severity in {"high", "critical"} else "medium",
        )
        alert = AlertRecord(
            alert_id=request.alert_id or f"alert-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            alert_type=request.alert_type,
            status="open",
            severity=request.severity,
            title=request.title,
            description=request.description,
            source_type=request.source_type,
            source_id=request.source_id,
            owner_scope=request.owner_scope,
            blocker_refs=request.blocker_refs,
            run_refs=request.run_refs,
            action_refs=request.action_refs,
            evidence_refs=request.evidence_refs,
            audit_refs=request.audit_refs,
            metadata={**request.metadata, "alert_does_not_remediate": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_alert(self._repository, alert)
        emit_telemetry(
            self._telemetry_service,
            event_type="alert_created",
            node_type="alert",
            node_id=stored.alert_id,
            intensity=_intensity(stored.severity),
            trace_id=stored.trace_id,
            payload={"alert_type": stored.alert_type, "severity": stored.severity},
        )
        return stored

    def get_alert(self, alert_id: str, scope: list[str]) -> AlertRecord | None:
        authorize(
            self._policy_adapter,
            action_type="alert.read",
            resource_type="alert",
            resource_id=alert_id,
            scope=scope,
            risk_level="low",
        )
        get = getattr(self._repository, "get_alert", None)
        alert = get(alert_id) if callable(get) else None
        if not isinstance(alert, AlertRecord):
            return None
        return alert if _scope_matches(alert.owner_scope, scope) else None

    def query(self, query: AlertQuery) -> list[AlertRecord]:
        authorize(
            self._policy_adapter,
            action_type="alert.read",
            resource_type="alert",
            resource_id=None,
            scope=query.scope,
            risk_level="low",
        )
        list_alerts = getattr(self._repository, "list_alerts", None)
        if not callable(list_alerts):
            return []
        result = list_alerts(**query.model_dump(mode="python"))
        return [item for item in result if isinstance(item, AlertRecord)]

    def list_alerts(
        self, scope: list[str], status: str | None = None, limit: int = 100
    ) -> list[AlertRecord]:
        return self.query(AlertQuery(scope=scope, status=status, limit=limit))

    def acknowledge(self, alert_id: str, actor_id: str | None, reason: str) -> AlertRecord:
        return self._update(alert_id, actor_id, reason, "acknowledged")

    def resolve(self, alert_id: str, actor_id: str | None, reason: str) -> AlertRecord:
        return self._update(alert_id, actor_id, reason, "resolved")

    def dismiss(self, alert_id: str, actor_id: str | None, reason: str) -> AlertRecord:
        return self._update(alert_id, actor_id, reason, "dismissed")

    def _update(self, alert_id: str, actor_id: str | None, reason: str, status: str) -> AlertRecord:
        alert = _require_alert(self._repository, alert_id)
        authorize(
            self._policy_adapter,
            action_type="alert.update",
            resource_type="alert",
            resource_id=alert_id,
            scope=alert.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason, "status": status},
        )
        now = datetime.now(UTC)
        update: dict[str, object] = {
            "status": status,
            "metadata": {**alert.metadata, f"{status}_reason": reason},
        }
        if status == "acknowledged":
            update["acknowledged_at"] = now
        if status == "resolved":
            update["resolved_at"] = now
        stored = _save_alert(self._repository, alert.model_copy(update=update))
        emit_telemetry(
            self._telemetry_service,
            event_type="alert_resolved" if status == "resolved" else "alert_acknowledged",
            node_type="alert",
            node_id=stored.alert_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"status": stored.status},
        )
        return stored


def _save_alert(repository: object, alert: AlertRecord) -> AlertRecord:
    save = getattr(repository, "save_alert", None)
    stored = save(alert) if callable(save) else alert
    return stored if isinstance(stored, AlertRecord) else alert


def _require_alert(repository: object, alert_id: str) -> AlertRecord:
    get = getattr(repository, "get_alert", None)
    alert = get(alert_id) if callable(get) else None
    if not isinstance(alert, AlertRecord):
        raise ValueError("alert_not_found")
    return alert


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _intensity(severity: str) -> float:
    if severity == "critical":
        return 1.0
    if severity == "high":
        return 0.8
    return 0.5


__all__ = ["AlertService"]
