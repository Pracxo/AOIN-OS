"""Read-only local session prototype API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.local_session import (
    LocalSessionAuditRequest,
    LocalSessionAuditResult,
    LocalSessionBoundaryCheck,
    LocalSessionContext,
    LocalSessionPreview,
    LocalSessionPreviewRequest,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["local-session"])


class LocalSessionBoundaryRequest(BaseModel):
    """Request a local session boundary check."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
    created_by: str | None = None


@router.post("/brain/local-session/preview", response_model=LocalSessionPreview)
def preview_local_session(
    body: LocalSessionPreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LocalSessionPreview:
    """Create a synthetic local session preview without authenticating a user."""
    _authorize(
        container.policy_adapter,
        "local_session.preview.create",
        body.owner_scope or actor_context.security_scope,
        actor_context,
        resource_type="local_session_preview",
        risk_level="medium",
        context=_safe_context(),
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id or body.actor_id,
            "workspace_id": body.workspace_id
            or actor_context.workspace_id
            or body.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.local_session_preview_service.create_preview(request)


@router.post("/brain/local-session/context", response_model=LocalSessionContext)
def local_session_context(
    body: LocalSessionPreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LocalSessionContext:
    """Return a role-aware read-only local session context preview."""
    _authorize(
        container.policy_adapter,
        "local_session.context.read",
        body.owner_scope or actor_context.security_scope,
        actor_context,
        resource_type="local_session_context",
        risk_level="medium",
        context=_safe_context(),
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    preview = container.local_session_preview_service.create_preview(request)
    return container.local_session_context_service.build_context(preview)


@router.get("/brain/local-session/status")
def local_session_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    """Return local session status and no-go warnings."""
    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "local_session.status.read",
        resolved_scope,
        actor_context,
        resource_type="local_session_status",
        context=_safe_context(),
    )
    return container.local_session_query_service.status(resolved_scope)


@router.post("/brain/local-session/boundary-check", response_model=LocalSessionBoundaryCheck)
def local_session_boundary_check(
    body: LocalSessionBoundaryRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LocalSessionBoundaryCheck:
    """Run a local session safety boundary check."""
    scope = body.scope or actor_context.security_scope or ["workspace:main"]
    _authorize(
        container.policy_adapter,
        "local_session.boundary.check",
        scope,
        actor_context,
        resource_type="local_session_boundary",
        risk_level="medium",
        context=_safe_context(),
    )
    return container.local_session_boundary_service.check()


@router.post("/brain/local-session/audit", response_model=LocalSessionAuditResult)
def audit_local_session(
    body: LocalSessionAuditRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LocalSessionAuditResult:
    """Run a local session no-go safety audit."""
    _authorize(
        container.policy_adapter,
        "local_session.audit.run",
        body.owner_scope or actor_context.security_scope,
        actor_context,
        resource_type="local_session_audit",
        risk_level="medium",
        context=_safe_context(),
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.local_session_audit_service.audit(request)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _safe_context() -> dict[str, bool]:
    return {
        "dev_only": True,
        "read_only": True,
        "production_session": False,
        "production_auth": False,
        "credentials_present": False,
        "token_issued": False,
        "cookie_issued": False,
        "persistent": False,
        "write_actions_enabled": False,
        "execute_allowed": False,
        "activation_allowed": False,
        "external_calls_allowed": False,
    }


def _authorize(
    policy_adapter: object,
    action_type: str,
    scope: list[str],
    actor_context: ActorContext,
    *,
    resource_type: str,
    risk_level: str = "low",
    context: dict[str, Any] | None = None,
) -> None:
    authorize = getattr(policy_adapter, "authorize", None)
    if not callable(authorize):
        raise AIONPolicyDeniedException("policy_adapter_unavailable")
    decision = authorize(
        PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
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
                **(context or {}),
            },
        )
    )
    if not decision.allow:
        raise AIONPolicyDeniedException(decision.reason)


__all__ = ["router"]
