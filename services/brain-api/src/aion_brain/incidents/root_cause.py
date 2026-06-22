"""Root cause candidate service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.root_cause import (
    RootCauseCandidate,
    RootCauseCandidateRequest,
    RootCauseCandidateType,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class RootCauseCandidateService:
    """Generate and manage deterministic root cause hypotheses."""

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

    def with_actor_context(self, actor_context: ActorContext) -> RootCauseCandidateService:
        return RootCauseCandidateService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def generate_for_incident(
        self, incident_id: str, scope: list[str], created_by: str | None = None
    ) -> list[RootCauseCandidate]:
        authorize(
            self._policy_adapter,
            action_type="incident.root_cause.create",
            resource_type="root_cause_candidate",
            resource_id=incident_id,
            scope=scope,
            actor_id=created_by or self._actor_context.actor_id,
            risk_level="medium",
        )
        incident = _get_incident(self._repository, incident_id)
        if incident is None:
            raise ValueError("incident_not_found")
        signals = _signals_for_incident(self._repository, incident_id, scope)
        requests = [_candidate_request(incident_id, signal, created_by) for signal in signals]
        if not requests:
            requests = [
                RootCauseCandidateRequest(
                    incident_id=incident_id,
                    trace_id=getattr(incident, "trace_id", None),
                    candidate_type="unknown",
                    title="Unknown root cause candidate",
                    hypothesis=(
                        "Available local signals are insufficient for a stronger hypothesis."
                    ),
                    severity=getattr(incident, "severity", "medium"),
                    confidence=0.3,
                    supporting_refs=[incident_id],
                    missing_evidence=["additional_local_signal_context"],
                    recommended_checks=["review_source_alerts"],
                    metadata={"candidate_not_truth": True},
                    created_by=created_by,
                )
            ]
        return [self.create_candidate(request) for request in requests]

    def create_candidate(self, request: RootCauseCandidateRequest) -> RootCauseCandidate:
        incident = _get_incident(self._repository, request.incident_id)
        scope = getattr(incident, "owner_scope", ["workspace:main"])
        authorize(
            self._policy_adapter,
            action_type="incident.root_cause.create",
            resource_type="root_cause_candidate",
            resource_id=request.root_cause_candidate_id,
            scope=scope,
            actor_id=request.created_by or self._actor_context.actor_id,
            risk_level="medium",
        )
        now = datetime.now(UTC)
        candidate = RootCauseCandidate(
            root_cause_candidate_id=request.root_cause_candidate_id
            or f"root-cause-candidate-{uuid4().hex}",
            incident_id=request.incident_id,
            trace_id=request.trace_id or getattr(incident, "trace_id", None),
            status="proposed",
            candidate_type=request.candidate_type,
            severity=request.severity,
            title=request.title,
            hypothesis=request.hypothesis,
            confidence=request.confidence,
            supporting_refs=request.supporting_refs,
            opposing_refs=request.opposing_refs,
            missing_evidence=request.missing_evidence,
            recommended_checks=request.recommended_checks,
            metadata={**request.metadata, "candidate_not_truth": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
            updated_at=now,
        )
        stored = _save_candidate(self._repository, candidate)
        emit_telemetry(
            self._telemetry_service,
            event_type="root_cause_candidate_created",
            node_type="root_cause",
            node_id=stored.root_cause_candidate_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={"candidate_type": stored.candidate_type, "candidate_not_truth": True},
        )
        return stored

    def list_candidates(
        self,
        incident_id: str | None = None,
        status: str | None = None,
        candidate_type: str | None = None,
        limit: int = 100,
    ) -> list[RootCauseCandidate]:
        list_candidates = getattr(self._repository, "list_root_causes", None)
        if not callable(list_candidates):
            return []
        return list(
            list_candidates(
                incident_id=incident_id,
                status=status,
                candidate_type=candidate_type,
                limit=limit,
            )
            or []
        )

    def confirm_candidate(
        self, root_cause_candidate_id: str, actor_id: str | None, reason: str
    ) -> RootCauseCandidate:
        return self._update(root_cause_candidate_id, actor_id, reason, "confirmed")

    def dismiss_candidate(
        self, root_cause_candidate_id: str, actor_id: str | None, reason: str
    ) -> RootCauseCandidate:
        return self._update(root_cause_candidate_id, actor_id, reason, "dismissed")

    def _update(
        self,
        root_cause_candidate_id: str,
        actor_id: str | None,
        reason: str,
        status: str,
    ) -> RootCauseCandidate:
        candidate = _require_candidate(self._repository, root_cause_candidate_id)
        incident = _get_incident(self._repository, candidate.incident_id)
        authorize(
            self._policy_adapter,
            action_type="incident.root_cause.update",
            resource_type="root_cause_candidate",
            resource_id=root_cause_candidate_id,
            scope=getattr(incident, "owner_scope", ["workspace:main"]),
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason, "candidate_not_truth": True},
        )
        now = datetime.now(UTC)
        update: dict[str, object] = {
            "status": status,
            "updated_at": now,
            "metadata": {**candidate.metadata, f"{status}_reason": reason},
        }
        if status == "confirmed":
            update["confirmed_at"] = now
        if status == "dismissed":
            update["dismissed_at"] = now
        stored = _save_candidate(self._repository, candidate.model_copy(update=update))
        if status == "confirmed":
            emit_telemetry(
                self._telemetry_service,
                event_type="root_cause_candidate_confirmed",
                node_type="root_cause",
                node_id=stored.root_cause_candidate_id,
                intensity=stored.confidence,
                trace_id=stored.trace_id,
                payload={"candidate_not_truth": True},
            )
        return stored


def _candidate_request(
    incident_id: str, signal: object, created_by: str | None
) -> RootCauseCandidateRequest:
    candidate_type = _candidate_type_for(signal)
    return RootCauseCandidateRequest(
        incident_id=incident_id,
        trace_id=getattr(signal, "trace_id", None),
        candidate_type=candidate_type,
        title=f"{candidate_type.replace('_', ' ').title()} candidate",
        hypothesis=(
            f"Local signal {getattr(signal, 'incident_signal_id', '')} suggests {candidate_type}."
        ),
        severity=getattr(signal, "severity", "medium"),
        confidence=0.65 if getattr(signal, "severity", "") in {"high", "critical"} else 0.5,
        supporting_refs=[getattr(signal, "incident_signal_id", "")],
        missing_evidence=["operator_review"],
        recommended_checks=_recommended_checks(candidate_type),
        metadata={"candidate_not_truth": True},
        created_by=created_by,
    )


def _candidate_type_for(signal: object) -> RootCauseCandidateType:
    source_type = str(getattr(signal, "source_type", "generic"))
    signal_type = str(getattr(signal, "signal_type", "generic"))
    summary = f"{getattr(signal, 'title', '')} {getattr(signal, 'summary', '')}".lower()
    if source_type == "prompt_boundary":
        return "prompt_injection"
    if source_type == "model_output" or signal_type == "unsafe":
        return "unsafe_model_output"
    if source_type == "grounding" or signal_type == "unsupported":
        return "insufficient_grounding"
    if source_type == "audit":
        return "audit_integrity_issue"
    if source_type == "scheduler" or signal_type == "missed":
        return "schedule_missed"
    if signal_type == "timed_out":
        return "timeout"
    if signal_type == "stalled" or "stalled" in summary:
        return "run_stalled"
    if source_type == "resilience" or signal_type == "degraded":
        return "dependency_unavailable"
    if "policy" in summary:
        return "policy_constraint"
    if "autonomy" in summary:
        return "autonomy_constraint"
    if signal_type == "pending_approval" or "approval" in summary:
        return "approval_missing"
    if "capability" in summary:
        return "capability_unavailable"
    if source_type == "outcome":
        return "failed_outcome"
    return "unknown"


def _recommended_checks(candidate_type: str) -> list[str]:
    mapping = {
        "timeout": ["inspect_run_supervision"],
        "run_stalled": ["inspect_run_supervision"],
        "dependency_unavailable": ["run_operator_readiness"],
        "policy_constraint": ["review_policy_decision"],
        "autonomy_constraint": ["review_policy_decision"],
        "approval_missing": ["request_approval"],
        "prompt_injection": ["review_source_alerts"],
        "unsafe_model_output": ["review_source_alerts"],
        "insufficient_grounding": ["run_grounding_verification"],
        "audit_integrity_issue": ["run_audit_verification"],
        "schedule_missed": ["inspect_run_supervision"],
        "failed_outcome": ["review_source_alerts"],
    }
    return mapping.get(candidate_type, ["review_source_alerts"])


def _signals_for_incident(repository: object, incident_id: str, scope: list[str]) -> list[object]:
    list_signals = getattr(repository, "list_signals", None)
    if not callable(list_signals):
        return []
    return [
        signal
        for signal in list(list_signals(scope=scope, limit=100) or [])
        if getattr(signal, "incident_id", None) == incident_id
        or getattr(signal, "incident_signal_id", None)
        in getattr(_get_incident(repository, incident_id), "signal_refs", [])
    ]


def _get_incident(repository: object, incident_id: str) -> object | None:
    get = getattr(repository, "get_incident", None)
    return get(incident_id) if callable(get) else None


def _save_candidate(repository: object, candidate: RootCauseCandidate) -> RootCauseCandidate:
    save = getattr(repository, "save_root_cause", None)
    stored = save(candidate) if callable(save) else candidate
    return stored if isinstance(stored, RootCauseCandidate) else candidate


def _require_candidate(repository: object, candidate_id: str) -> RootCauseCandidate:
    get = getattr(repository, "get_root_cause", None)
    candidate = get(candidate_id) if callable(get) else None
    if not isinstance(candidate, RootCauseCandidate):
        raise ValueError("root_cause_candidate_not_found")
    return candidate


__all__ = ["RootCauseCandidateService"]
