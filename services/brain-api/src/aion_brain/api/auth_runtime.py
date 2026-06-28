"""Disabled production auth runtime API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.auth_runtime import (
    AuthRuntimeAuditRequest,
    AuthRuntimeAuditResult,
    AuthRuntimeStatus,
    MockClaimsPreviewRequest,
    MockClaimsPreviewResult,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/auth-runtime", tags=["auth-runtime"])


@router.get("/status", response_model=AuthRuntimeStatus)
def auth_runtime_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> AuthRuntimeStatus:
    """Return disabled auth-runtime status."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "auth_runtime.status.read",
        resolved_scope,
        actor_context,
        resource_type="auth_runtime_status",
        context=_safe_context(),
    )
    return container.auth_runtime_gate_service.status(resolved_scope)


@router.post("/mock-claims/preview", response_model=MockClaimsPreviewResult)
def mock_claims_preview(
    body: MockClaimsPreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MockClaimsPreviewResult:
    """Preview mock claims without authenticating or creating auth material."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "auth_runtime.mock_claims.preview",
        resolved_scope,
        actor_context,
        resource_type="mock_claims_preview",
        risk_level="medium",
        context={**_safe_context(), "mock_only": True},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.mock_claims_preview_service.preview(request)


@router.post("/audit", response_model=AuthRuntimeAuditResult)
def audit_auth_runtime(
    body: AuthRuntimeAuditRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuthRuntimeAuditResult:
    """Run disabled auth-runtime safety audit."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "auth_runtime.audit.run",
        resolved_scope,
        actor_context,
        resource_type="auth_runtime_audit",
        risk_level="medium",
        context={**_safe_context(), "read_only": True},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.auth_runtime_audit_service.audit(request)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _safe_context() -> dict[str, bool]:
    return {
        "dev_only": True,
        "read_only": True,
        "production_auth": False,
        "production_auth_enabled": False,
        "external_identity_provider_enabled": False,
        "credentials_present": False,
        "auth_credentials_enabled": False,
        "session_present": False,
        "auth_sessions_enabled": False,
        "token_issued": False,
        "cookie_issued": False,
        "persistent": False,
        "write_allowed": False,
        "execute_allowed": False,
        "activation_allowed": False,
        "external_calls_allowed": False,
        "auth_runtime_enabled": False,
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
