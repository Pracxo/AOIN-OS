"""Incident lifecycle service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.incidents import (
    IncidentCreateRequest,
    IncidentQuery,
    IncidentQueryResult,
    IncidentRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.incidents.fingerprint import build_signal_fingerprint
from aion_brain.incidents.redaction import redact_incident_payload, redact_incident_text


class IncidentService:
    """Create and manage incident grouping records without source mutation."""

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

    def with_actor_context(self, actor_context: ActorContext) -> IncidentService:
        return IncidentService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_incident(self, request: IncidentCreateRequest) -> IncidentRecord:
        authorize(
            self._policy_adapter,
            action_type="incident.create",
            resource_type="incident",
            resource_id=request.incident_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level=_risk_for_severity(request.severity),
        )
        summary = redact_incident_text(request.summary)
        metadata = redact_incident_payload(request.metadata)
        correlation_key = request.correlation_key or f"incident:manual:{request.incident_type}"
        fingerprint = request.fingerprint or build_signal_fingerprint(
            "incident",
            request.incident_id or request.title,
            request.incident_type,
            summary,
        )
        now = datetime.now(UTC)
        incident = IncidentRecord(
            incident_id=request.incident_id or f"incident-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status="open",
            incident_type=request.incident_type,
            severity=request.severity,
            title=redact_incident_text(request.title),
            summary=summary,
            owner_scope=request.owner_scope,
            primary_signal_type=request.primary_signal_type,
            primary_signal_id=request.primary_signal_id,
            signal_refs=request.signal_refs,
            alert_refs=request.alert_refs,
            notification_refs=request.notification_refs,
            run_refs=request.run_refs,
            action_refs=request.action_refs,
            model_output_refs=request.model_output_refs,
            prompt_refs=request.prompt_refs,
            grounding_refs=request.grounding_refs,
            security_refs=request.security_refs,
            audit_refs=request.audit_refs,
            scheduler_refs=request.scheduler_refs,
            outcome_refs=request.outcome_refs,
            learning_refs=request.learning_refs,
            blocker_refs=request.blocker_refs,
            related_incident_ids=request.related_incident_ids,
            correlation_key=correlation_key,
            fingerprint=fingerprint,
            confidence=request.confidence,
            metadata={**metadata, "incident_is_grouping": True, "no_remediation": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        stored = _save_incident(self._repository, incident)
        emit_telemetry(
            self._telemetry_service,
            event_type="incident_created",
            node_type="incident",
            node_id=stored.incident_id,
            intensity=_incident_intensity(stored.severity),
            trace_id=stored.trace_id,
            payload={"incident_type": stored.incident_type, "severity": stored.severity},
        )
        return stored

    def get_incident(self, incident_id: str, scope: list[str]) -> IncidentRecord | None:
        authorize(
            self._policy_adapter,
            action_type="incident.read",
            resource_type="incident",
            resource_id=incident_id,
            scope=scope,
            risk_level="low",
        )
        incident = _get_incident(self._repository, incident_id)
        if incident is None or not _scope_matches(incident.owner_scope, scope):
            return None
        return incident

    def query(self, query: IncidentQuery) -> IncidentQueryResult:
        authorize(
            self._policy_adapter,
            action_type="incident.read",
            resource_type="incident",
            resource_id=query.trace_id,
            scope=query.scope,
            trace_id=query.trace_id,
            risk_level="low",
        )
        list_incidents = getattr(self._repository, "list_incidents", None)
        list_signals = getattr(self._repository, "list_signals", None)
        incidents = list_incidents(query) if callable(list_incidents) else []
        signals = []
        if callable(list_signals):
            signals = list_signals(
                scope=query.scope,
                trace_id=query.trace_id,
                source_type=query.source_type,
                source_id=query.source_id,
                correlation_key=query.correlation_key,
                include_deleted=query.include_deleted,
                limit=query.limit,
            )
        return IncidentQueryResult(
            incidents=list(incidents or []),
            signals=list(signals or []),
            total_count=len(incidents or []),
            metadata={"source_mutation": False},
        )

    def acknowledge(self, incident_id: str, actor_id: str | None, reason: str) -> IncidentRecord:
        return self._update_status(incident_id, actor_id, reason, "acknowledged")

    def resolve(self, incident_id: str, actor_id: str | None, reason: str) -> IncidentRecord:
        return self._update_status(incident_id, actor_id, reason, "resolved")

    def dismiss(self, incident_id: str, actor_id: str | None, reason: str) -> IncidentRecord:
        return self._update_status(incident_id, actor_id, reason, "dismissed")

    def archive(self, incident_id: str, actor_id: str | None, reason: str) -> IncidentRecord:
        return self._update_status(incident_id, actor_id, reason, "archived")

    def soft_delete(self, incident_id: str, actor_id: str | None, reason: str) -> bool:
        incident = _require_incident(self._repository, incident_id)
        authorize(
            self._policy_adapter,
            action_type="incident.delete",
            resource_type="incident",
            resource_id=incident_id,
            scope=incident.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason, "source_records_mutated": False},
        )
        deleted = incident.model_copy(
            update={
                "status": "deleted",
                "deleted_at": datetime.now(UTC),
                "metadata": {**incident.metadata, "delete_reason": reason},
            }
        )
        _save_incident(self._repository, deleted)
        return True

    def list_incidents(
        self, scope: list[str], status: str | None = None, limit: int = 100
    ) -> list[IncidentRecord]:
        return self.query(IncidentQuery(scope=scope, status=status, limit=limit)).incidents

    def status(self, scope: list[str] | None = None) -> dict[str, object]:
        query = IncidentQuery(scope=scope or ["workspace:main"], limit=100)
        result = self.query(query)
        open_count = len([item for item in result.incidents if item.status == "open"])
        critical_count = len([item for item in result.incidents if item.severity == "critical"])
        status = "failed" if critical_count else "warning" if open_count else "healthy"
        return {
            "status": status,
            "open_incident_count": open_count,
            "critical_incident_count": critical_count,
        }

    def _update_status(
        self, incident_id: str, actor_id: str | None, reason: str, status: str
    ) -> IncidentRecord:
        incident = _require_incident(self._repository, incident_id)
        authorize(
            self._policy_adapter,
            action_type="incident.update",
            resource_type="incident",
            resource_id=incident_id,
            scope=incident.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason, "source_records_mutated": False},
        )
        now = datetime.now(UTC)
        update: dict[str, object] = {
            "status": status,
            "updated_at": now,
            "metadata": {**incident.metadata, f"{status}_reason": reason},
        }
        if status == "acknowledged":
            update["acknowledged_at"] = now
        if status == "resolved":
            update["resolved_at"] = now
        if status == "archived":
            update["archived_at"] = now
        stored = _save_incident(self._repository, incident.model_copy(update=update))
        if status in {"acknowledged", "resolved"}:
            emit_telemetry(
                self._telemetry_service,
                event_type=f"incident_{status}",
                node_type="incident",
                node_id=stored.incident_id,
                intensity=0.5,
                trace_id=stored.trace_id,
                payload={"status": stored.status, "source_records_mutated": False},
            )
        return stored


def _save_incident(repository: object, incident: IncidentRecord) -> IncidentRecord:
    save = getattr(repository, "save_incident", None)
    stored = save(incident) if callable(save) else incident
    return stored if isinstance(stored, IncidentRecord) else incident


def _get_incident(repository: object, incident_id: str) -> IncidentRecord | None:
    get = getattr(repository, "get_incident", None)
    incident = get(incident_id) if callable(get) else None
    return incident if isinstance(incident, IncidentRecord) else None


def _require_incident(repository: object, incident_id: str) -> IncidentRecord:
    incident = _get_incident(repository, incident_id)
    if incident is None:
        raise ValueError("incident_not_found")
    return incident


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _risk_for_severity(severity: str) -> str:
    return "high" if severity in {"high", "critical"} else "medium"


def _incident_intensity(severity: str) -> float:
    if severity == "critical":
        return 1.0
    if severity == "high":
        return 0.8
    return 0.5


__all__ = ["IncidentService"]
