"""Deterministic incident correlation engine."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from aion_brain.contracts.incidents import (
    IncidentCorrelationRequest,
    IncidentCorrelationRun,
    IncidentCreateRequest,
    IncidentRecord,
    IncidentSignal,
    IncidentType,
)
from aion_brain.contracts.root_cause import IncidentSeverity
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.incidents.service import IncidentService

_SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


class IncidentCorrelationEngine:
    """Group incident signals without mutating source systems."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        incident_service: IncidentService | None = None,
        autonomy_governor: object | None = None,
        notification_router: object | None = None,
        operator_repository: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._incident_service = incident_service
        self._autonomy_governor = autonomy_governor
        self._notification_router = notification_router
        self._operator_repository = operator_repository
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> IncidentCorrelationEngine:
        return IncidentCorrelationEngine(
            self._repository,
            self._policy_adapter,
            incident_service=self._incident_service,
            autonomy_governor=self._autonomy_governor,
            notification_router=self._notification_router,
            operator_repository=self._operator_repository,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def correlate(self, request: IncidentCorrelationRequest) -> IncidentCorrelationRun:
        """Run deterministic local correlation."""

        authorize(
            self._policy_adapter,
            action_type="incident.correlate",
            resource_type="incident_correlation",
            resource_id=request.correlation_run_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium" if request.mode == "dry_run" else "high",
            context={"mode": request.mode, "source_records_mutated": False},
        )
        if request.mode == "controlled":
            self._authorize_autonomy(request)
        run_id = request.correlation_run_id or f"incident-correlation-run-{uuid4().hex}"
        trace_id = request.trace_id or self._actor_context.trace_id
        now = datetime.now(UTC)
        emit_telemetry(
            self._telemetry_service,
            event_type="incident_correlation_started",
            node_type="correlation_run",
            node_id=run_id,
            intensity=0.6,
            trace_id=trace_id,
            payload={"mode": request.mode},
        )
        window_end = request.window_end or now
        default_minutes = int(
            getattr(self._settings, "incident_correlation_default_window_minutes", 60)
        )
        window_start = request.window_start or (window_end - timedelta(minutes=default_minutes))
        signals = self._load_signals(request, window_start, window_end)
        groups = _group_signals(signals)
        incidents: list[IncidentRecord] = []
        signals_linked = 0
        incidents_created = 0
        if request.mode == "controlled" and request.create_incidents:
            service = self._incident_service or IncidentService(
                self._repository,
                self._policy_adapter,
                telemetry_service=self._telemetry_service,
                actor_context=self._actor_context,
            )
            for group in groups.values():
                incident = service.create_incident(_incident_request_from_group(group, request))
                incidents.append(incident)
                incidents_created += 1
                for signal in group:
                    link = getattr(self._repository, "link_signal", None)
                    if callable(link):
                        link(signal.incident_signal_id, incident.incident_id)
                        signals_linked += 1
        elif request.mode == "dry_run":
            incidents = [_preview_incident(group, request) for group in groups.values()]
        run = IncidentCorrelationRun(
            correlation_run_id=run_id,
            trace_id=trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status="dry_run" if request.mode == "dry_run" else "completed",
            mode=request.mode,
            owner_scope=request.owner_scope,
            window_start=window_start,
            window_end=window_end,
            rules_applied=request.rule_ids,
            signals_seen=len(signals),
            signals_linked=signals_linked,
            incidents_created=incidents_created,
            incidents_updated=0,
            incidents_unchanged=0 if incidents_created else len(groups),
            incidents=incidents,
            warnings=[],
            failures=[],
            result={
                "group_count": len(groups),
                "source_records_mutated": False,
                "remediation_executed": False,
            },
            metadata={**request.metadata, "incident_owned_records_only": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            completed_at=datetime.now(UTC),
        )
        stored = _save_run(self._repository, run)
        emit_telemetry(
            self._telemetry_service,
            event_type="incident_correlation_completed",
            node_type="correlation_run",
            node_id=stored.correlation_run_id,
            intensity=0.8 if stored.status in {"completed", "dry_run"} else 1.0,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "signals_seen": stored.signals_seen},
        )
        return stored

    def get_correlation_run(self, correlation_run_id: str) -> IncidentCorrelationRun | None:
        get = getattr(self._repository, "get_correlation_run", None)
        run = get(correlation_run_id) if callable(get) else None
        return run if isinstance(run, IncidentCorrelationRun) else None

    def _authorize_autonomy(self, request: IncidentCorrelationRequest) -> None:
        authorize_call = getattr(self._autonomy_governor, "authorize", None)
        if not callable(authorize_call):
            return
        decision = authorize_call(
            action_type="incident.correlate",
            owner_scope=request.owner_scope,
            mode=request.mode,
        )
        if getattr(decision, "allow", True) is False:
            raise PermissionError("blocked_by_autonomy")

    def _load_signals(
        self,
        request: IncidentCorrelationRequest,
        window_start: datetime,
        window_end: datetime,
    ) -> list[IncidentSignal]:
        list_signals = getattr(self._repository, "list_signals", None)
        if not callable(list_signals):
            return []
        max_signals = int(getattr(self._settings, "incident_max_signals_per_run", 1000))
        signals = list(
            list_signals(
                scope=request.owner_scope,
                since=window_start,
                until=window_end,
                limit=max_signals,
            )
            or []
        )
        if request.source_types:
            signals = [signal for signal in signals if signal.source_type in request.source_types]
        if request.signal_types:
            signals = [signal for signal in signals if signal.signal_type in request.signal_types]
        return signals[:max_signals]


def _group_signals(signals: list[IncidentSignal]) -> dict[str, list[IncidentSignal]]:
    groups: dict[str, list[IncidentSignal]] = defaultdict(list)
    for signal in signals:
        key = signal.correlation_key or signal.trace_id or signal.fingerprint
        groups[key].append(signal)
    return dict(groups)


def _incident_request_from_group(
    signals: list[IncidentSignal], request: IncidentCorrelationRequest
) -> IncidentCreateRequest:
    primary = _highest_severity_signal(signals)
    source_refs = _refs_by_source(signals)
    return IncidentCreateRequest(
        trace_id=primary.trace_id or request.trace_id,
        actor_id=primary.actor_id or request.actor_id,
        workspace_id=primary.workspace_id or request.workspace_id,
        incident_type=_incident_type_for(primary),
        severity=_max_severity(signals),
        title=f"Correlated {primary.signal_type} incident",
        summary=f"{len(signals)} local signal(s) grouped by deterministic correlation.",
        owner_scope=primary.owner_scope,
        primary_signal_type=primary.signal_type,
        primary_signal_id=primary.incident_signal_id,
        signal_refs=[signal.incident_signal_id for signal in signals],
        alert_refs=source_refs["alert"],
        notification_refs=source_refs["notification"],
        run_refs=source_refs["run_supervision"],
        action_refs=source_refs["action_proposal"],
        model_output_refs=source_refs["model_output"],
        prompt_refs=source_refs["prompt_boundary"],
        grounding_refs=source_refs["grounding"],
        security_refs=source_refs["security"],
        audit_refs=source_refs["audit"],
        scheduler_refs=source_refs["scheduler"],
        outcome_refs=source_refs["outcome"],
        learning_refs=source_refs["learning"],
        correlation_key=primary.correlation_key,
        fingerprint=primary.fingerprint,
        confidence=min(1.0, 0.45 + 0.1 * len(signals)),
        metadata={"source_records_mutated": False, "correlation_mode": request.mode},
        created_by=request.created_by,
    )


def _preview_incident(
    signals: list[IncidentSignal], request: IncidentCorrelationRequest
) -> IncidentRecord:
    incident_request = _incident_request_from_group(signals, request)
    primary_id = incident_request.primary_signal_id or uuid4().hex
    return IncidentRecord(
        incident_id=f"incident-preview-{primary_id}",
        trace_id=incident_request.trace_id,
        actor_id=incident_request.actor_id,
        workspace_id=incident_request.workspace_id,
        status="open",
        incident_type=incident_request.incident_type,
        severity=incident_request.severity,
        title=incident_request.title,
        summary=incident_request.summary,
        owner_scope=incident_request.owner_scope,
        primary_signal_type=incident_request.primary_signal_type,
        primary_signal_id=incident_request.primary_signal_id,
        signal_refs=incident_request.signal_refs,
        alert_refs=incident_request.alert_refs,
        notification_refs=incident_request.notification_refs,
        run_refs=incident_request.run_refs,
        action_refs=incident_request.action_refs,
        model_output_refs=incident_request.model_output_refs,
        prompt_refs=incident_request.prompt_refs,
        grounding_refs=incident_request.grounding_refs,
        security_refs=incident_request.security_refs,
        audit_refs=incident_request.audit_refs,
        scheduler_refs=incident_request.scheduler_refs,
        outcome_refs=incident_request.outcome_refs,
        learning_refs=incident_request.learning_refs,
        blocker_refs=[],
        correlation_key=incident_request.correlation_key or "incident:preview",
        fingerprint=incident_request.fingerprint or f"preview-{primary_id}",
        confidence=incident_request.confidence,
        metadata={
            **incident_request.metadata,
            "dry_run_preview": True,
            "incident_is_grouping": True,
        },
        created_by=incident_request.created_by,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _refs_by_source(signals: list[IncidentSignal]) -> dict[str, list[str]]:
    refs: dict[str, list[str]] = defaultdict(list)
    for signal in signals:
        refs[signal.source_type].append(signal.source_id)
    return defaultdict(list, refs)


def _highest_severity_signal(signals: list[IncidentSignal]) -> IncidentSignal:
    return max(signals, key=lambda signal: _SEVERITY_RANK[signal.severity])


def _max_severity(signals: list[IncidentSignal]) -> IncidentSeverity:
    return _highest_severity_signal(signals).severity


def _incident_type_for(signal: IncidentSignal) -> IncidentType:
    if signal.source_type == "prompt_boundary":
        return "prompt_injection"
    if signal.source_type == "grounding":
        return "grounding"
    if signal.source_type == "model_output":
        return "model_output"
    if signal.source_type == "run_supervision":
        return "run_failure"
    if signal.source_type == "scheduler":
        return "scheduler_miss"
    if signal.source_type == "resilience":
        return "resilience_degradation"
    if signal.source_type == "security":
        return "security_failure"
    if signal.source_type == "audit":
        return "audit_integrity"
    if signal.source_type in {"release", "freeze"}:
        return "release_failure"
    if signal.source_type == "backup":
        return "backup_failure"
    if signal.source_type == "learning":
        return "learning_signal"
    if signal.signal_type in {"unsafe", "high_risk"}:
        return "safety"
    return "operational"


def _save_run(repository: object, run: IncidentCorrelationRun) -> IncidentCorrelationRun:
    save = getattr(repository, "save_correlation_run", None)
    stored = save(run) if callable(save) else run
    return stored if isinstance(stored, IncidentCorrelationRun) else run


__all__ = ["IncidentCorrelationEngine"]
