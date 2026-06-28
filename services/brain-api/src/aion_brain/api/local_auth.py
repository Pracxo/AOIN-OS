"""Dev-only local auth contract and simulation API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.local_auth import (
    ConsoleRoleFilterRequest,
    ConsoleRoleFilterResult,
    DevIdentitySimulationRequest,
    LocalAuthAuditRequest,
    LocalAuthAuditResult,
    LocalAuthContext,
    RoleAccessAudit,
    RolePermission,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["local-auth"])


@router.get("/brain/local-auth/roles", response_model=list[RolePermission])
def list_local_auth_roles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[RolePermission]:
    """Return dev-only local role permissions."""
    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "local_auth.roles.read",
        resolved_scope,
        actor_context,
        resource_type="local_auth_role",
    )
    return container.local_role_service.default_permissions()


@router.post("/brain/local-auth/simulate", response_model=LocalAuthContext)
def simulate_local_identity(
    body: DevIdentitySimulationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LocalAuthContext:
    """Create a synthetic local auth context without authenticating a user."""
    _authorize(
        container.policy_adapter,
        "local_auth.identity.simulate",
        body.owner_scope or actor_context.security_scope,
        actor_context,
        resource_type="local_auth_context",
        risk_level="medium",
        context={"dev_only": True, "production_auth": False},
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
    return container.dev_identity_simulator.simulate(request)


@router.post("/brain/local-auth/filter-console", response_model=ConsoleRoleFilterResult)
def filter_console_view_model(
    body: ConsoleRoleFilterRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConsoleRoleFilterResult:
    """Filter a console view model by synthetic local role."""
    _authorize(
        container.policy_adapter,
        "local_auth.console.filter",
        body.auth_context.owner_scope or actor_context.security_scope,
        actor_context,
        resource_type="operator_console_view",
        risk_level="medium",
        context={"read_only": True, "role_filtering": True},
    )
    request = body.model_copy(update={"trace_id": body.trace_id or actor_context.trace_id})
    return container.console_role_filter.filter(request)


@router.get("/brain/local-auth/role-matrix")
def role_permission_matrix(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    """Return the read-only local role permission proof matrix."""
    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "local_auth.role_matrix.read",
        resolved_scope,
        actor_context,
        resource_type="local_auth_role_matrix",
        context={"read_only": True},
    )
    return container.role_permission_matrix_service.build_permission_matrix()


@router.post("/brain/local-auth/role-access-audit", response_model=RoleAccessAudit)
def audit_role_access(
    body: LocalAuthAuditRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RoleAccessAudit:
    """Audit role-aware console view filtering decisions."""
    _authorize(
        container.policy_adapter,
        "local_auth.role_matrix.audit",
        body.owner_scope or actor_context.security_scope,
        actor_context,
        resource_type="local_auth_role_matrix",
        risk_level="medium",
        context={"read_only": True, "role_access_audit": True},
    )
    return container.role_access_audit_service.audit(
        trace_id=body.trace_id or actor_context.trace_id,
    )


@router.post("/brain/local-auth/audit", response_model=LocalAuthAuditResult)
def audit_local_auth(
    body: LocalAuthAuditRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LocalAuthAuditResult:
    """Run a local auth no-go safety audit."""
    _authorize(
        container.policy_adapter,
        "local_auth.audit.run",
        body.owner_scope or actor_context.security_scope,
        actor_context,
        resource_type="local_auth_audit",
        risk_level="medium",
        context={"no_production_auth": True},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.local_auth_audit_service.audit(request)


@router.get("/brain/local-auth/status")
def local_auth_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    """Return local auth status and no-go warnings."""
    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "local_auth.status.read",
        resolved_scope,
        actor_context,
        resource_type="local_auth_status",
    )
    return container.local_auth_query_service.status(resolved_scope)


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
                "dev_only": True,
                **(context or {}),
            },
        )
    )
    if not decision.allow:
        raise AIONPolicyDeniedException(decision.reason)


__all__ = ["router"]
