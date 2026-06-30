"""Connector credential architecture and readiness API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.connector_credentials import (
    ConnectorCredentialAuthorizationEntry,
    ConnectorCredentialBoundary,
    ConnectorCredentialLifecycleState,
    ConnectorCredentialReadinessRequest,
    ConnectorCredentialReadinessResult,
    ConnectorSecretRedactionResult,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/connector-credentials", tags=["connector-credentials"])


@router.get("/boundary", response_model=ConnectorCredentialBoundary)
def connector_credential_boundary(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConnectorCredentialBoundary:
    """Return the connector credential architecture boundary."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_credentials.boundary.read",
        resolved_scope,
        actor_context,
        resource_type="connector_credential_boundary",
        context=_safe_context(),
    )
    return container.connector_credential_architecture_service.boundary()


@router.get("/lifecycle", response_model=list[ConnectorCredentialLifecycleState])
def connector_credential_lifecycle(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ConnectorCredentialLifecycleState]:
    """Return future connector credential lifecycle states."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_credentials.lifecycle.read",
        resolved_scope,
        actor_context,
        resource_type="connector_credential_lifecycle",
        context=_safe_context(),
    )
    return container.connector_credential_lifecycle_service.list_states()


@router.get("/authorization", response_model=list[ConnectorCredentialAuthorizationEntry])
def connector_credential_authorization(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ConnectorCredentialAuthorizationEntry]:
    """Return role-aware connector credential authorization entries."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_credentials.authorization.read",
        resolved_scope,
        actor_context,
        resource_type="connector_credential_authorization",
        context=_safe_context(),
    )
    return container.connector_credential_authorization_service.list_entries()


@router.post("/readiness", response_model=ConnectorCredentialReadinessResult)
def connector_credential_readiness(
    body: ConnectorCredentialReadinessRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorCredentialReadinessResult:
    """Evaluate credential readiness without storing or reading material."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_credentials.readiness.preview",
        resolved_scope,
        actor_context,
        resource_type="connector_credential_readiness",
        risk_level="medium",
        context={**_safe_context(), "requested_scopes": body.requested_scopes},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.connector_credential_readiness_service.evaluate(request)


@router.post("/redaction-preview", response_model=ConnectorSecretRedactionResult)
def connector_secret_redaction_preview(
    body: dict[str, Any],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorSecretRedactionResult:
    """Preview redaction without storing the submitted payload."""

    _authorize(
        container.policy_adapter,
        "connector_credentials.redaction.preview",
        _scope(None, actor_context),
        actor_context,
        resource_type="connector_secret_redaction_preview",
        risk_level="medium",
        context=_safe_context(),
    )
    return container.connector_secret_redaction_service.preview(body)


@router.post("/query", response_model=dict[str, Any])
def connector_credential_query(
    body: dict[str, Any],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, Any]:
    """Return connector credential query evidence without material access."""

    requested_scope = body.get("owner_scope")
    resolved_scope = (
        [str(item) for item in requested_scope if str(item).strip()]
        if isinstance(requested_scope, list)
        else _scope(None, actor_context)
    )
    _authorize(
        container.policy_adapter,
        "connector_credentials.status.read",
        resolved_scope,
        actor_context,
        resource_type="connector_credential_query",
        context=_safe_context(),
    )
    return container.connector_credential_query_service.query(body, resolved_scope)


@router.get("/status", response_model=dict[str, Any])
def connector_credential_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    """Return connector credential status with storage disabled."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_credentials.status.read",
        resolved_scope,
        actor_context,
        resource_type="connector_credential_status",
        context=_safe_context(),
    )
    return container.connector_credential_query_service.status(resolved_scope)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _safe_context() -> dict[str, bool]:
    return {
        "read_only": True,
        "design_only": True,
        "credential_storage_enabled": False,
        "token_storage_enabled": False,
        "secret_material_present": False,
        "plaintext_secret_allowed": False,
        "browser_secret_storage_allowed": False,
        "log_secret_allowed": False,
        "external_identity_runtime_enabled": False,
        "connector_runtime_credential_access_enabled": False,
        "connector_runtime_enabled": False,
        "external_calls_enabled": False,
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
