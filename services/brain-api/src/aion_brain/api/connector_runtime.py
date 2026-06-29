"""Disabled external connector runtime API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.connector_runtime import (
    ConnectorEgressPreviewRequest,
    ConnectorEgressPreviewResult,
    ConnectorIngressPreviewRequest,
    ConnectorIngressPreviewResult,
    ConnectorRuntimeAuditRequest,
    ConnectorRuntimeAuditResult,
    ConnectorRuntimeStatus,
    MockConnectorManifest,
    MockConnectorManifestValidationResult,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/connector-runtime", tags=["connector-runtime"])


@router.get("/status", response_model=ConnectorRuntimeStatus)
def connector_runtime_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConnectorRuntimeStatus:
    """Return disabled external connector runtime status."""

    resolved_scope = _scope(scope, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_runtime.status.read",
        resolved_scope,
        actor_context,
        resource_type="connector_runtime_status",
        context=_safe_context(),
    )
    return container.connector_runtime_gate_service.status(resolved_scope)


@router.post("/mock-manifest/validate", response_model=MockConnectorManifestValidationResult)
def validate_mock_connector_manifest(
    body: MockConnectorManifest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MockConnectorManifestValidationResult:
    """Validate a mock-only connector manifest without registering a connector."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_runtime.mock_manifest.validate",
        resolved_scope,
        actor_context,
        resource_type="mock_connector_manifest",
        risk_level="medium",
        context={**_safe_context(), "mock_only": True},
    )
    manifest = body.model_copy(update={"owner_scope": resolved_scope})
    return container.mock_connector_manifest_service.validate(manifest)


@router.post("/egress-preview", response_model=ConnectorEgressPreviewResult)
def connector_egress_preview(
    body: ConnectorEgressPreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorEgressPreviewResult:
    """Preview blocked connector egress without making external calls."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_runtime.egress.preview",
        resolved_scope,
        actor_context,
        resource_type="connector_egress_preview",
        risk_level="medium",
        context={**_safe_context(), "egress_allowed": False},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.connector_egress_preview_service.preview(request)


@router.post("/ingress-preview", response_model=ConnectorIngressPreviewResult)
def connector_ingress_preview(
    body: ConnectorIngressPreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorIngressPreviewResult:
    """Preview untrusted connector ingress normalization without trusting data."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_runtime.ingress.preview",
        resolved_scope,
        actor_context,
        resource_type="connector_ingress_preview",
        risk_level="medium",
        context={**_safe_context(), "trusted": False},
    )
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": resolved_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.connector_ingress_preview_service.preview(request)


@router.post("/audit", response_model=ConnectorRuntimeAuditResult)
def audit_connector_runtime(
    body: ConnectorRuntimeAuditRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConnectorRuntimeAuditResult:
    """Run a disabled external connector runtime safety audit."""

    resolved_scope = body.owner_scope or _scope(None, actor_context)
    _authorize(
        container.policy_adapter,
        "connector_runtime.audit.run",
        resolved_scope,
        actor_context,
        resource_type="connector_runtime_audit",
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
    return container.connector_runtime_audit_service.audit(request)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _safe_context() -> dict[str, bool]:
    return {
        "read_only": True,
        "mock_only": True,
        "connector_runtime_enabled": False,
        "connector_external_calls_enabled": False,
        "connector_credentials_enabled": False,
        "connector_token_storage_enabled": False,
        "connector_activation_enabled": False,
        "connector_route_registration_enabled": False,
        "egress_allowed": False,
        "external_call_allowed": False,
        "credentials_present": False,
        "trusted": False,
        "write_allowed": False,
        "execute_allowed": False,
        "activation_allowed": False,
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
