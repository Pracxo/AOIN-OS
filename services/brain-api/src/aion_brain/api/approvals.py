"""Approval control plane API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.approvals.repository import ApprovalRepository
from aion_brain.approvals.service import ApprovalService
from aion_brain.config import get_settings
from aion_brain.contracts.approvals import (
    ApprovalCreateRequest,
    ApprovalDecision,
    ApprovalDecisionRequest,
    ApprovalInboxQuery,
    ApprovalRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.guardrails.engine import GuardrailEngine
from aion_brain.guardrails.repository import GuardrailRepository
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.risk.engine import RiskEngine
from aion_brain.risk.repository import RiskRepository

router = APIRouter(prefix="/brain/approvals", tags=["approvals"])


def get_approval_service() -> ApprovalService:
    """Return the configured approval service."""
    settings = get_settings()
    return get_cached_approval_service(
        settings.database_url,
        settings.opa_url,
        settings.risk_engine_enabled,
        settings.guardrails_enabled,
        settings.approvals_enabled,
        settings.approval_default_expiry_hours,
        settings.high_risk_requires_approval,
        settings.critical_risk_blocks_by_default,
    )


@lru_cache
def get_cached_approval_service(
    database_url: str,
    opa_url: str,
    risk_engine_enabled: bool,
    guardrails_enabled: bool,
    approvals_enabled: bool,
    approval_default_expiry_hours: int,
    high_risk_requires_approval: bool,
    critical_risk_blocks_by_default: bool,
) -> ApprovalService:
    """Return a cached approval service."""
    settings = get_settings().model_copy(
        update={
            "database_url": database_url,
            "opa_url": opa_url,
            "risk_engine_enabled": risk_engine_enabled,
            "guardrails_enabled": guardrails_enabled,
            "approvals_enabled": approvals_enabled,
            "approval_default_expiry_hours": approval_default_expiry_hours,
            "high_risk_requires_approval": high_risk_requires_approval,
            "critical_risk_blocks_by_default": critical_risk_blocks_by_default,
        }
    )
    policy = OPAAdapter(opa_url)
    risk = RiskEngine(
        repository=RiskRepository(database_url),
        policy_adapter=policy,
        telemetry_service=None,
        settings=settings,
    )
    guardrail = GuardrailEngine(
        repository=GuardrailRepository(database_url),
        policy_adapter=policy,
        telemetry_service=None,
        settings=settings,
    )
    return ApprovalService(
        repository=ApprovalRepository(database_url),
        risk_engine=risk,
        guardrail_engine=guardrail,
        policy_adapter=policy,
        telemetry_service=None,
        settings=settings,
    )


@router.post("", response_model=ApprovalRequest)
def create_approval_request(
    request: ApprovalCreateRequest,
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ApprovalRequest:
    """Create a pending approval request."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "requested_by": request.requested_by or actor_context.actor_id,
            "approval_scope": request.approval_scope or actor_context.security_scope,
        }
    )
    try:
        return service.create_request(enriched)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("", response_model=list[ApprovalRequest])
def list_approval_requests(
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: Annotated[str | None, Query()] = "pending",
    priority: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ApprovalRequest]:
    """List approval inbox records."""
    query = ApprovalInboxQuery(
        scope=scope or actor_context.security_scope or ["workspace:main"],
        actor_id=actor_context.actor_id,
        workspace_id=actor_context.workspace_id,
        status=status,  # type: ignore[arg-type]
        priority=priority,  # type: ignore[arg-type]
        limit=limit,
    )
    try:
        return service.list_pending(query)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{approval_request_id}", response_model=ApprovalRequest)
def get_approval_request(
    approval_request_id: str,
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ApprovalRequest:
    """Return one approval request."""
    try:
        approval = service.get_request(
            approval_request_id,
            scope or actor_context.security_scope or ["workspace:main"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if approval is None:
        raise HTTPException(status_code=404, detail="approval_request_not_found")
    return approval


@router.post("/{approval_request_id}/decide", response_model=ApprovalDecision)
def decide_approval_request(
    approval_request_id: str,
    request: ApprovalDecisionRequest,
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ApprovalDecision:
    """Approve, deny, or cancel one approval request."""
    enriched = request.model_copy(
        update={
            "approval_request_id": approval_request_id,
            "decided_by": request.decided_by or actor_context.actor_id,
        }
    )
    try:
        return service.decide(enriched)
    except ValueError as exc:
        status = 404 if str(exc) == "approval_request_not_found" else 403
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{approval_request_id}/cancel", response_model=ApprovalRequest)
def cancel_approval_request(
    approval_request_id: str,
    service: Annotated[ApprovalService, Depends(get_approval_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    reason: str = "cancelled",
) -> ApprovalRequest:
    """Cancel one approval request."""
    try:
        return service.cancel(
            approval_request_id,
            actor_id=actor_context.actor_id,
            reason=reason,
        )
    except ValueError as exc:
        status = 404 if str(exc) == "approval_request_not_found" else 403
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.post("/{approval_request_id}/expire", response_model=ApprovalRequest)
def expire_approval_request(
    approval_request_id: str,
    service: Annotated[ApprovalService, Depends(get_approval_service)],
) -> ApprovalRequest:
    """Expire one approval request."""
    try:
        return service.expire(approval_request_id)
    except ValueError as exc:
        status = 404 if str(exc) == "approval_request_not_found" else 403
        raise HTTPException(status_code=status, detail=str(exc)) from exc
