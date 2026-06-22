"""Guardrail rule and evaluation API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.config import get_settings
from aion_brain.contracts.guardrails import GuardrailDecision, GuardrailRule
from aion_brain.contracts.risk import RiskAssessment
from aion_brain.contracts.scopes import ActorContext
from aion_brain.guardrails.engine import GuardrailEngine
from aion_brain.guardrails.repository import GuardrailRepository
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain/guardrails", tags=["guardrails"])


def get_guardrail_engine() -> GuardrailEngine:
    """Return the configured guardrail engine."""
    settings = get_settings()
    return get_cached_guardrail_engine(
        settings.database_url,
        settings.opa_url,
        settings.guardrails_enabled,
    )


@lru_cache
def get_cached_guardrail_engine(
    database_url: str,
    opa_url: str,
    guardrails_enabled: bool,
) -> GuardrailEngine:
    """Return a cached guardrail engine."""
    settings = get_settings().model_copy(
        update={
            "database_url": database_url,
            "opa_url": opa_url,
            "guardrails_enabled": guardrails_enabled,
        }
    )
    return GuardrailEngine(
        repository=GuardrailRepository(database_url),
        policy_adapter=OPAAdapter(opa_url),
        telemetry_service=None,
        settings=settings,
    )


@router.post("", response_model=GuardrailRule)
def create_guardrail_rule(
    rule: GuardrailRule,
    engine: Annotated[GuardrailEngine, Depends(get_guardrail_engine)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> GuardrailRule:
    """Create or update one generic guardrail rule."""
    enriched = rule.model_copy(update={"created_by": rule.created_by or actor_context.actor_id})
    try:
        return engine.create_rule(enriched)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("", response_model=list[GuardrailRule])
def list_guardrail_rules(
    engine: Annotated[GuardrailEngine, Depends(get_guardrail_engine)],
    status: Annotated[str | None, Query()] = None,
) -> list[GuardrailRule]:
    """List generic guardrail rules."""
    try:
        return engine.list_rules(status=status)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/{guardrail_id}/disable", response_model=GuardrailRule)
def disable_guardrail_rule(
    guardrail_id: str,
    engine: Annotated[GuardrailEngine, Depends(get_guardrail_engine)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> GuardrailRule:
    """Disable one guardrail rule."""
    try:
        return engine.disable_rule(guardrail_id, actor_id=actor_context.actor_id)
    except ValueError as exc:
        status = 404 if str(exc) == "guardrail_rule_not_found" else 403
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/evaluate", response_model=GuardrailDecision)
def evaluate_guardrails(
    risk: RiskAssessment,
    engine: Annotated[GuardrailEngine, Depends(get_guardrail_engine)],
) -> GuardrailDecision:
    """Evaluate generic guardrails for a persisted risk assessment."""
    try:
        return engine.evaluate(risk)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
