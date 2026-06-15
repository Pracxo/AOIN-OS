"""Small helper for side-effect boundaries that need central approvals."""

from dataclasses import dataclass, field
from typing import Any

from aion_brain.contracts.guardrails import (
    RiskGuardrailEvaluation,
    RiskGuardrailEvaluationRequest,
)
from aion_brain.contracts.risk import RiskAssessmentRequest, RiskLevel


@dataclass(frozen=True)
class ApprovalGateResult:
    """Normalized result from the risk/guardrail/approval control plane."""

    final_decision: str
    reason: str
    approval_request_id: str | None = None
    constraints: list[str] = field(default_factory=list)


def evaluate_approval_gate(
    approval_service: object | None,
    *,
    trace_id: str | None,
    actor_id: str | None,
    workspace_id: str | None,
    action_type: str,
    resource_type: str,
    resource_id: str | None,
    requested_risk_level: str,
    security_scope: list[str],
    payload: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ApprovalGateResult | None:
    """Evaluate the central control plane when a service is configured."""
    evaluate = getattr(approval_service, "evaluate_and_maybe_request", None)
    if not callable(evaluate):
        return None
    risk_context = {
        "security_scope": security_scope,
        **(context or {}),
    }
    risk_metadata = {
        "security_scope": security_scope,
        **(metadata or {}),
    }
    try:
        result = evaluate(
            RiskGuardrailEvaluationRequest(
                risk=RiskAssessmentRequest(
                    trace_id=trace_id,
                    actor_id=actor_id,
                    workspace_id=workspace_id,
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    requested_risk_level=_risk_level(requested_risk_level),
                    payload=payload or {},
                    context=risk_context,
                    metadata=risk_metadata,
                )
            )
        )
    except Exception:
        return ApprovalGateResult(
            final_decision="require_approval",
            reason="approval_control_plane_unavailable",
            constraints=["fail_closed"],
        )
    if not isinstance(result, RiskGuardrailEvaluation):
        return ApprovalGateResult(
            final_decision="require_approval",
            reason="approval_control_plane_invalid_response",
            constraints=["fail_closed"],
        )
    approval_id = (
        result.approval_request.approval_request_id if result.approval_request else None
    )
    constraints = [
        *result.risk_assessment.constraints,
        *result.guardrail_decision.constraints,
    ]
    return ApprovalGateResult(
        final_decision=result.final_decision,
        reason=result.reason,
        approval_request_id=approval_id,
        constraints=constraints,
    )


def _risk_level(value: str) -> RiskLevel:
    if value in {"low", "medium", "high", "critical"}:
        return value  # type: ignore[return-value]
    return "medium"
