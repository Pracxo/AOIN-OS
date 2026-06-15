"""Risk assessment API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion_brain.api.approvals import get_approval_service
from aion_brain.config import get_settings
from aion_brain.contracts.guardrails import (
    RiskGuardrailEvaluation,
    RiskGuardrailEvaluationRequest,
)
from aion_brain.contracts.risk import RiskAssessment, RiskAssessmentRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.risk.engine import RiskEngine
from aion_brain.risk.repository import RiskRepository

router = APIRouter(prefix="/brain/risk", tags=["risk"])


def get_risk_engine() -> RiskEngine:
    """Return the configured risk engine."""
    settings = get_settings()
    return get_cached_risk_engine(
        settings.database_url,
        settings.opa_url,
        settings.risk_engine_enabled,
        settings.high_risk_requires_approval,
        settings.critical_risk_blocks_by_default,
    )


@lru_cache
def get_cached_risk_engine(
    database_url: str,
    opa_url: str,
    risk_engine_enabled: bool,
    high_risk_requires_approval: bool,
    critical_risk_blocks_by_default: bool,
) -> RiskEngine:
    """Return a cached risk engine."""
    settings = get_settings().model_copy(
        update={
            "database_url": database_url,
            "opa_url": opa_url,
            "risk_engine_enabled": risk_engine_enabled,
            "high_risk_requires_approval": high_risk_requires_approval,
            "critical_risk_blocks_by_default": critical_risk_blocks_by_default,
        }
    )
    return RiskEngine(
        repository=RiskRepository(database_url),
        policy_adapter=OPAAdapter(opa_url),
        telemetry_service=None,
        settings=settings,
    )


@router.post("/assess", response_model=RiskAssessment)
def assess_risk(
    request: RiskAssessmentRequest,
    engine: Annotated[RiskEngine, Depends(get_risk_engine)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RiskAssessment:
    """Assess generic risk for one Brain action."""
    enriched = _enrich_request(request, actor_context)
    try:
        return engine.assess(enriched)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/evaluate", response_model=RiskGuardrailEvaluation)
def evaluate_risk_guardrails(
    request: RiskGuardrailEvaluationRequest,
    service: Annotated[object, Depends(get_approval_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RiskGuardrailEvaluation:
    """Assess risk, evaluate guardrails, and maybe create approval."""
    enriched = request.model_copy(update={"risk": _enrich_request(request.risk, actor_context)})
    evaluate = getattr(service, "evaluate_and_maybe_request", None)
    if not callable(evaluate):
        raise HTTPException(status_code=503, detail="approval_service_unavailable")
    try:
        result = evaluate(enriched)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if isinstance(result, RiskGuardrailEvaluation):
        return result
    raise HTTPException(status_code=500, detail="invalid_evaluation_response")


def _enrich_request(
    request: RiskAssessmentRequest,
    actor_context: ActorContext,
) -> RiskAssessmentRequest:
    scope = request.context.get("security_scope")
    return request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "trace_id": request.trace_id or actor_context.trace_id,
            "context": {
                **request.context,
                "security_scope": scope
                if isinstance(scope, list)
                else actor_context.security_scope,
                "actor_context": actor_context.model_dump(mode="json"),
            },
        }
    )
