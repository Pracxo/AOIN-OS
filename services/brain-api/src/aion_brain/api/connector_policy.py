"""Connector policy action catalog API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.connector_policy import (
    ConnectorAuthorizationMatrixEntry,
    ConnectorPolicyAction,
    ConnectorPolicyDryRunRequest,
    ConnectorPolicyDryRunResult,
    ConnectorPolicyTraceabilityRecord,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/connector-policy", tags=["connector-policy"])


@router.get("/catalog", response_model=list[ConnectorPolicyAction])
def connector_policy_catalog(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ConnectorPolicyAction]:
    """Return the connector policy action catalog."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_policy.catalog.read",
        resolved_scope,
        actor_context,
        resource_type="connector_policy_catalog",
        context=_safe_context(),
    )
    return container.connector_policy_catalog_service.list_actions(include_denied=True)


@router.get("/matrix", response_model=list[ConnectorAuthorizationMatrixEntry])
def connector_policy_matrix(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ConnectorAuthorizationMatrixEntry]:
    """Return the connector policy role/action matrix."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_policy.matrix.read",
        resolved_scope,
        actor_context,
        resource_type="connector_authorization_matrix",
        context=_safe_context(),
    )
    return container.connector_authorization_matrix_service.list_entries()


@router.post("/dry-run", response_model=ConnectorPolicyDryRunResult)
def connector_policy_dry_run(
    body: ConnectorPolicyDryRunRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorPolicyDryRunResult:
    """Evaluate a connector policy action without executing it."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_policy.dry_run",
        resolved_scope,
        actor_context,
        resource_type="connector_policy_dry_run",
        risk_level="medium",
        context={**_safe_context(), "requested_action_key": body.requested_action_key},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.connector_policy_dry_run_service.evaluate(request)


@router.post("/traceability/query", response_model=list[ConnectorPolicyTraceabilityRecord])
def connector_policy_traceability_query(
    body: dict[str, Any],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[ConnectorPolicyTraceabilityRecord]:
    """Return connector policy traceability evidence."""

    requested_scope = body.get("owner_scope")
    resolved_scope = (
        [str(item) for item in requested_scope if str(item).strip()]
        if isinstance(requested_scope, list)
        else _scope(None, actor_context)
    )
    _authorize(
        container.policy_adapter,
        "connector_policy.traceability.read",
        resolved_scope,
        actor_context,
        resource_type="connector_policy_traceability",
        context=_safe_context(),
    )
    return container.connector_policy_traceability_service.query(body, resolved_scope)


@router.get("/status", response_model=dict[str, Any])
def connector_policy_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    """Return connector policy status with runtime permissions disabled."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_policy.catalog.read",
        resolved_scope,
        actor_context,
        resource_type="connector_policy_status",
        context=_safe_context(),
    )
    return container.connector_policy_query_service.status(resolved_scope)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _safe_context() -> dict[str, bool]:
    return {
        "read_only": True,
        "dry_run_only": True,
        "connector_runtime_enabled": False,
        "connector_external_calls_enabled": False,
        "connector_credentials_enabled": False,
        "connector_token_storage_enabled": False,
        "connector_activation_enabled": False,
        "connector_route_registration_enabled": False,
        "runtime_allowed": False,
        "external_call_allowed": False,
        "credential_access_allowed": False,
        "token_access_allowed": False,
        "activation_allowed": False,
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
