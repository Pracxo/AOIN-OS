"""Incident signal ingestion service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.incidents import (
    IncidentSignal,
    IncidentSignalCreateRequest,
    IncidentSignalType,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.incidents.fingerprint import build_correlation_key, build_signal_fingerprint
from aion_brain.incidents.redaction import redact_incident_payload, redact_incident_text


class IncidentSignalService:
    """Create and manage normalized incident signals."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> IncidentSignalService:
        return IncidentSignalService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            actor_context=actor_context,
        )

    def create_signal(self, request: IncidentSignalCreateRequest) -> IncidentSignal:
        """Create one redacted incident signal."""

        authorize(
            self._policy_adapter,
            action_type="incident.signal.create",
            resource_type="incident_signal",
            resource_id=request.incident_signal_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=_risk_for_severity(request.severity),
        )
        trace_id = request.trace_id or self._actor_context.trace_id
        summary = redact_incident_text(request.summary)
        metadata = redact_incident_payload(request.metadata)
        correlation_key = build_correlation_key(
            request.source_type,
            request.signal_type,
            trace_id,
            request.source_id,
        )
        fingerprint = build_signal_fingerprint(
            request.source_type,
            request.source_id,
            request.signal_type,
            summary,
        )
        now = datetime.now(UTC)
        signal = IncidentSignal(
            incident_signal_id=request.incident_signal_id or f"incident-signal-{uuid4().hex}",
            incident_id=request.incident_id,
            trace_id=trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            source_type=request.source_type,
            source_id=request.source_id,
            signal_type=request.signal_type,
            severity=request.severity,
            status="new",
            title=redact_incident_text(request.title),
            summary=summary,
            owner_scope=request.owner_scope,
            correlation_key=correlation_key,
            fingerprint=fingerprint,
            refs=request.refs,
            metadata={**metadata, "incident_signal_only": True},
            occurred_at=request.occurred_at or now,
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
        )
        stored = _save_signal(self._repository, signal)
        self._record_audit("incident_signal_created", stored.incident_signal_id)
        self._record_provenance(stored.source_id, stored.incident_signal_id, "creates_signal")
        emit_telemetry(
            self._telemetry_service,
            event_type="incident_signal_created",
            node_type="incident_signal",
            node_id=stored.incident_signal_id,
            intensity=1.0 if stored.severity in {"high", "critical"} else 0.6,
            trace_id=stored.trace_id,
            payload={
                "source_type": stored.source_type,
                "signal_type": stored.signal_type,
                "severity": stored.severity,
            },
        )
        return stored

    def get_signal(self, incident_signal_id: str, scope: list[str]) -> IncidentSignal | None:
        authorize(
            self._policy_adapter,
            action_type="incident.signal.read",
            resource_type="incident_signal",
            resource_id=incident_signal_id,
            scope=scope,
            risk_level="low",
        )
        get = getattr(self._repository, "get_signal", None)
        signal = get(incident_signal_id) if callable(get) else None
        if not isinstance(signal, IncidentSignal):
            return None
        return signal if _scope_matches(signal.owner_scope, scope) else None

    def list_signals(
        self,
        scope: list[str],
        status: str | None = None,
        source_type: str | None = None,
        signal_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[IncidentSignal]:
        authorize(
            self._policy_adapter,
            action_type="incident.signal.read",
            resource_type="incident_signal",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_signals = getattr(self._repository, "list_signals", None)
        if not callable(list_signals):
            return []
        return list(
            list_signals(
                scope=scope,
                status=status,
                source_type=source_type,
                signal_type=signal_type,
                severity=severity,
                limit=limit,
            )
            or []
        )

    def dismiss_signal(
        self, incident_signal_id: str, actor_id: str | None, reason: str
    ) -> IncidentSignal:
        signal = _require_signal(self._repository, incident_signal_id)
        authorize(
            self._policy_adapter,
            action_type="incident.signal.update",
            resource_type="incident_signal",
            resource_id=incident_signal_id,
            scope=signal.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        dismissed = signal.model_copy(
            update={
                "status": "dismissed",
                "dismissed_at": datetime.now(UTC),
                "metadata": {**signal.metadata, "dismiss_reason": reason},
            }
        )
        return _save_signal(self._repository, dismissed)

    def build_from_alert(self, alert_id: str, scope: list[str]) -> IncidentSignal:
        get_alert = getattr(self._repository, "get_alert", None)
        alert = get_alert(alert_id) if callable(get_alert) else None
        if alert is None:
            raise ValueError("alert_not_found")
        return self.create_signal(
            IncidentSignalCreateRequest(
                trace_id=getattr(alert, "trace_id", None),
                actor_id=getattr(alert, "actor_id", None),
                workspace_id=getattr(alert, "workspace_id", None),
                source_type="alert",
                source_id=alert_id,
                signal_type=_signal_type_for_status(getattr(alert, "alert_type", "generic")),
                severity=getattr(alert, "severity", "medium"),
                title=getattr(alert, "title", "Alert signal"),
                summary=getattr(alert, "description", "Alert converted to incident signal."),
                owner_scope=getattr(alert, "owner_scope", scope) or scope,
                refs=[alert_id],
                created_by=getattr(alert, "created_by", None),
            )
        )

    def build_from_notification(self, notification_id: str, scope: list[str]) -> IncidentSignal:
        get_notification = getattr(self._repository, "get_notification", None)
        notification = get_notification(notification_id) if callable(get_notification) else None
        if notification is None:
            raise ValueError("notification_not_found")
        return self.create_signal(
            IncidentSignalCreateRequest(
                trace_id=getattr(notification, "trace_id", None),
                actor_id=getattr(notification, "actor_id", None),
                workspace_id=getattr(notification, "workspace_id", None),
                source_type="notification",
                source_id=notification_id,
                signal_type="generic",
                severity=getattr(notification, "severity", "medium"),
                title=getattr(notification, "title", "Notification signal"),
                summary=getattr(notification, "message", "Notification converted to signal."),
                owner_scope=getattr(notification, "owner_scope", scope) or scope,
                refs=[notification_id],
                created_by=getattr(notification, "created_by", None),
            )
        )

    def _record_audit(self, event_type: str, resource_id: str) -> None:
        record = getattr(self._audit_sink, "record", None)
        if callable(record):
            try:
                record(event_type, resource_id=resource_id)
            except Exception:
                return

    def _record_provenance(self, source_id: str, target_id: str, relation: str) -> None:
        link = getattr(self._provenance_service, "link", None)
        if callable(link):
            try:
                link(source_id, target_id, relation)
            except Exception:
                return


def _save_signal(repository: object, signal: IncidentSignal) -> IncidentSignal:
    save = getattr(repository, "save_signal", None)
    stored = save(signal) if callable(save) else signal
    return stored if isinstance(stored, IncidentSignal) else signal


def _require_signal(repository: object, incident_signal_id: str) -> IncidentSignal:
    get = getattr(repository, "get_signal", None)
    signal = get(incident_signal_id) if callable(get) else None
    if not isinstance(signal, IncidentSignal):
        raise ValueError("incident_signal_not_found")
    return signal


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _risk_for_severity(severity: str) -> str:
    return "high" if severity in {"high", "critical"} else "medium"


def _signal_type_for_status(value: str) -> IncidentSignalType:
    if "timeout" in value:
        return "timed_out"
    if "stalled" in value:
        return "stalled"
    if "failed" in value:
        return "failed"
    if "blocked" in value:
        return "blocked"
    return "generic"


__all__ = ["IncidentSignalService"]
