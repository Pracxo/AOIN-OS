"""Connector sandbox design and readiness API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.connector_sandbox import (
    ConnectorSandboxBoundary,
    ConnectorSandboxCapabilityRule,
    ConnectorSandboxReadinessRequest,
    ConnectorSandboxReadinessResult,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/connector-sandbox", tags=["connector-sandbox"])


@router.get("/boundary", response_model=ConnectorSandboxBoundary)
def connector_sandbox_boundary(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConnectorSandboxBoundary:
    """Return the connector sandbox isolation boundary."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_sandbox.boundary.read",
        resolved_scope,
        actor_context,
        resource_type="connector_sandbox_boundary",
        context=_safe_context(),
    )
    return container.connector_isolation_boundary_service.boundary()


@router.get("/capability-rules", response_model=list[ConnectorSandboxCapabilityRule])
def connector_sandbox_capability_rules(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ConnectorSandboxCapabilityRule]:
    """Return connector sandbox capability rules."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_sandbox.capability_rules.read",
        resolved_scope,
        actor_context,
        resource_type="connector_sandbox_capability_rules",
        context=_safe_context(),
    )
    return container.connector_sandbox_capability_rule_service.list_rules(include_denied=True)


@router.post("/readiness", response_model=ConnectorSandboxReadinessResult)
def connector_sandbox_readiness(
    body: ConnectorSandboxReadinessRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorSandboxReadinessResult:
    """Evaluate sandbox readiness without executing sandboxed code."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_sandbox.readiness.preview",
        resolved_scope,
        actor_context,
        resource_type="connector_sandbox_readiness",
        risk_level="medium",
        context={**_safe_context(), "requested_capabilities": body.requested_capabilities},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.connector_sandbox_readiness_service.evaluate(request)


@router.post("/query", response_model=dict[str, Any])
def connector_sandbox_query(
    body: dict[str, Any],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, Any]:
    """Return connector sandbox query evidence without runtime execution."""

    requested_scope = body.get("owner_scope")
    resolved_scope = (
        [str(item) for item in requested_scope if str(item).strip()]
        if isinstance(requested_scope, list)
        else _scope(None, actor_context)
    )
    _authorize(
        container.policy_adapter,
        "connector_sandbox.status.read",
        resolved_scope,
        actor_context,
        resource_type="connector_sandbox_query",
        context=_safe_context(),
    )
    return container.connector_sandbox_query_service.query(body, resolved_scope)


@router.get("/status", response_model=dict[str, Any])
def connector_sandbox_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    """Return connector sandbox status with execution permissions disabled."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_sandbox.status.read",
        resolved_scope,
        actor_context,
        resource_type="connector_sandbox_status",
        context=_safe_context(),
    )
    return container.connector_sandbox_query_service.status(resolved_scope)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _safe_context() -> dict[str, bool]:
    return {
        "read_only": True,
        "design_only": True,
        "sandbox_execution_enabled": False,
        "connector_runtime_enabled": False,
        "runtime_execution_allowed": False,
        "filesystem_access_allowed": False,
        "network_access_allowed": False,
        "credential_access_allowed": False,
        "token_access_allowed": False,
        "process_spawn_allowed": False,
        "dynamic_import_allowed": False,
        "package_install_allowed": False,
        "connector_activation_allowed": False,
        "write_allowed": False,
        "execute_allowed": False,
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
