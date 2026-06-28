"""Dry-run action authorization API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.action_authorization import (
    ActionAuthorizationAuditRequest,
    ActionAuthorizationAuditResult,
    DryRunActionAuthorizationDecision,
    DryRunActionAuthorizationRequest,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/action-authorization", tags=["action-authorization"])


@router.post("/authorize", response_model=DryRunActionAuthorizationDecision)
def authorize_dry_run_action(
    body: DryRunActionAuthorizationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DryRunActionAuthorizationDecision:
    """Authorize a dry-run preview or review record. Denials are returned visibly."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id or body.actor_id,
            "workspace_id": body.workspace_id
            or actor_context.workspace_id
            or body.workspace_id,
            "owner_scope": body.owner_scope or _scope(None, actor_context),
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.dry_run_action_authorization_service.authorize(request)


@router.post("/audit", response_model=ActionAuthorizationAuditResult)
def audit_action_authorization(
    body: ActionAuthorizationAuditRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActionAuthorizationAuditResult:
    """Run a dry-run action authorization safety audit."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "action_authorization.audit.run",
        resolved_scope,
        actor_context,
        resource_type="action_authorization_audit",
        risk_level="medium",
        context={"dry_run_only": True, "read_only": True},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.action_authorization_audit_service.audit(request)


@router.get("/status")
def action_authorization_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    """Return dry-run action authorization status flags."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "action_authorization.decision.read",
        resolved_scope,
        actor_context,
        resource_type="action_authorization",
        context={"read_only": True},
    )
    return container.action_authorization_query_service.status(resolved_scope)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _authorize(
    policy_adapter: object,
    action_type: str,
    scope: list[str],
    actor_context: ActorContext,
    *,
    resource_type: str,
    risk_level: str = "low",
    context: dict[str, object] | None = None,
) -> None:
    authorize = getattr(policy_adapter, "authorize", None)
    if not callable(authorize):
        raise AIONPolicyDeniedException("policy_adapter_unavailable")
    decision = authorize(
        PolicyRequest(
            request_id=f"{action_type}-local",
            trace_id=actor_context.trace_id,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=None,
            risk_level=risk_level,
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=scope,
            context={
                "actor_context": actor_context.model_dump(),
                "dry_run_only": True,
                "write_allowed": False,
                "execution_allowed": False,
                "activation_allowed": False,
                "external_calls_allowed": False,
                **(context or {}),
            },
        )
    )
    if not decision.allow:
        raise AIONPolicyDeniedException(decision.reason)


__all__ = ["router"]
