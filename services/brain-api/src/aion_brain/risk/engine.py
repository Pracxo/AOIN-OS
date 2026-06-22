"""Deterministic generic risk engine."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.risk import RiskAssessment, RiskAssessmentRequest, RiskLevel
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.risk.repository import RiskRepository

BASE_RISK_SCORE: dict[RiskLevel, float] = {
    "low": 0.20,
    "medium": 0.45,
    "high": 0.75,
    "critical": 0.95,
}

RISK_FACTORS: dict[str, float] = {
    "external_effect_possible": 0.15,
    "writes_memory": 0.10,
    "deletes_data": 0.20,
    "invokes_capability": 0.15,
    "uses_external_model": 0.10,
    "uses_mcp": 0.15,
    "controlled_execution": 0.15,
    "affects_skill_activation": 0.15,
    "approval_present": -0.10,
    "dry_run": -0.20,
}


class RiskEngine:
    """Compute and persist deterministic risk for generic Brain actions."""

    def __init__(
        self,
        *,
        repository: RiskRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        settings: Settings,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._audit_sink = audit_sink

    def assess(self, request: RiskAssessmentRequest) -> RiskAssessment:
        """Assess, authorize, persist, and emit risk for one generic action."""
        decision = self._authorize(request)
        if not decision.allow and not decision.approval_required:
            assessment = _assessment(
                request,
                risk_score=1.0,
                factors=[{"factor": "policy_denied", "weight": 1.0}],
                computed_risk_level="critical",
                decision="block",
                constraints=[decision.reason, *decision.constraints],
            )
            return self._save_and_emit(assessment)
        if not self._settings.risk_engine_enabled:
            assessment = _assessment(
                request,
                risk_score=BASE_RISK_SCORE[request.requested_risk_level],
                factors=[{"factor": "risk_engine_disabled", "weight": 0.0}],
                computed_risk_level=request.requested_risk_level,
                decision="allow",
                constraints=["risk_engine_disabled"],
            )
            return self._save_and_emit(assessment)

        score, factors = calculate_risk_score(request)
        computed = computed_risk_level(score)
        risk_decision = risk_decision_for_level(
            computed,
            high_requires_approval=self._settings.high_risk_requires_approval,
            critical_blocks_by_default=self._settings.critical_risk_blocks_by_default,
        )
        constraints = []
        if risk_decision == "require_approval":
            constraints.append("approval_required")
        if risk_decision == "block":
            constraints.append("critical_risk_blocked")
        if decision.approval_required and risk_decision == "allow":
            risk_decision = "require_approval"
            constraints.append("policy_approval_required")

        assessment = _assessment(
            request,
            risk_score=score,
            factors=factors,
            computed_risk_level=computed,
            decision=risk_decision,
            constraints=constraints,
        )
        return self._save_and_emit(assessment)

    def get_assessment(self, risk_assessment_id: str) -> RiskAssessment | None:
        """Return one persisted assessment."""
        return self._repository.get_assessment(risk_assessment_id)

    def _authorize(self, request: RiskAssessmentRequest) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"risk.assess-{request.risk_assessment_id or uuid4().hex}",
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="risk.assess",
                resource_type="risk_assessment",
                resource_id=request.risk_assessment_id,
                risk_level="low",
                approval_present=bool(request.context.get("approval_present")),
                requested_permissions=[],
                security_scope=_scope(request),
                context={
                    "action_type": request.action_type,
                    "resource_type": request.resource_type,
                    **request.context,
                },
            )
        )

    def _save_and_emit(self, assessment: RiskAssessment) -> RiskAssessment:
        saved = self._repository.save_assessment(assessment)
        self._emit(saved)
        record_audit_event(
            self._audit_sink,
            action_type="risk.assess",
            resource_type=assessment.resource_type,
            resource_id=assessment.resource_id or assessment.risk_assessment_id,
            event_type="risk_assessed",
            outcome="blocked" if assessment.decision == "block" else "completed",
            source_component="risk_engine",
            trace_id=assessment.trace_id,
            actor_id=assessment.actor_id,
            workspace_id=assessment.workspace_id,
            risk_level=assessment.computed_risk_level,
            risk_assessment_id=assessment.risk_assessment_id,
            payload={
                "action_type": assessment.action_type,
                "decision": assessment.decision,
                "computed_risk_level": assessment.computed_risk_level,
                "risk_score": assessment.risk_score,
            },
        )
        return saved

    def _emit(self, assessment: RiskAssessment) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{assessment.risk_assessment_id}-risk-assessed",
            trace_id=assessment.trace_id or assessment.risk_assessment_id,
            event_type="risk_assessed",
            node_type="risk",
            node_id=assessment.risk_assessment_id,
            edge_from=assessment.resource_id,
            edge_to=assessment.risk_assessment_id,
            intensity=assessment.risk_score,
            payload={
                "action_type": assessment.action_type,
                "resource_type": assessment.resource_type,
                "computed_risk_level": assessment.computed_risk_level,
                "decision": assessment.decision,
                "owner_scope": _scope_from_assessment(assessment),
            },
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def calculate_risk_score(
    request: RiskAssessmentRequest,
) -> tuple[float, list[dict[str, Any]]]:
    """Return a deterministic score and contributing factors."""
    score = BASE_RISK_SCORE[request.requested_risk_level]
    factors: list[dict[str, Any]] = [
        {
            "factor": "requested_risk_level",
            "value": request.requested_risk_level,
            "weight": score,
        }
    ]
    for key, weight in RISK_FACTORS.items():
        if bool(request.context.get(key)):
            score += weight
            factors.append({"factor": key, "weight": weight})
    return clamp_score(score), factors


def clamp_score(value: float) -> float:
    """Clamp a risk score to 0..1."""
    return max(0.0, min(1.0, value))


def computed_risk_level(score: float) -> RiskLevel:
    """Map a numeric score to a generic risk level."""
    if score < 0.30:
        return "low"
    if score < 0.60:
        return "medium"
    if score < 0.85:
        return "high"
    return "critical"


def risk_decision_for_level(
    risk_level: RiskLevel,
    *,
    high_requires_approval: bool,
    critical_blocks_by_default: bool,
) -> str:
    """Return the default action decision for a computed risk level."""
    if risk_level in {"low", "medium"}:
        return "allow"
    if risk_level == "high":
        return "require_approval" if high_requires_approval else "allow"
    return "block" if critical_blocks_by_default else "require_approval"


def _assessment(
    request: RiskAssessmentRequest,
    *,
    risk_score: float,
    factors: list[dict[str, Any]],
    computed_risk_level: RiskLevel,
    decision: str,
    constraints: list[str],
) -> RiskAssessment:
    return RiskAssessment(
        risk_assessment_id=request.risk_assessment_id or f"risk-{uuid4().hex}",
        trace_id=request.trace_id,
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        action_type=request.action_type,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        requested_risk_level=request.requested_risk_level,
        computed_risk_level=computed_risk_level,
        risk_score=clamp_score(risk_score),
        factors=factors,
        constraints=constraints,
        decision=cast(Any, decision),
        metadata=request.metadata,
        created_at=datetime.now(UTC),
    )


def _scope(request: RiskAssessmentRequest) -> list[str]:
    value = request.context.get("security_scope") or request.metadata.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    if request.workspace_id:
        return [f"workspace:{request.workspace_id}"]
    return ["workspace:main"]


def _scope_from_assessment(assessment: RiskAssessment) -> list[str]:
    value = assessment.metadata.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    if assessment.workspace_id:
        return [f"workspace:{assessment.workspace_id}"]
    return ["workspace:main"]
