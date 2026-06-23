"""Read-only Operator Console API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.operator_console import (
    ConsoleAuditRequest,
    ConsoleAuditResult,
    ConsoleViewModel,
    ConsoleViewModelRequest,
    ConsoleWorkflowMap,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.operator_console.service import (
    ConsoleContractAuditService,
    ConsoleViewModelService,
)

router = APIRouter(prefix="/brain/operator-console", tags=["operator-console"])


def get_console_view_model_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ConsoleViewModelService:
    return container.operator_console_view_model_service


def get_console_audit_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ConsoleContractAuditService:
    return container.operator_console_contract_audit_service


@router.get("/views", response_model=list[dict[str, object]])
def list_console_views(
    service: Annotated[ConsoleViewModelService, Depends(get_console_view_model_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[dict[str, object]]:
    """List read-only console views."""
    try:
        return service.list_views(_scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/view-model", response_model=ConsoleViewModel)
def get_console_view_model(
    body: ConsoleViewModelRequest,
    service: Annotated[ConsoleViewModelService, Depends(get_console_view_model_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConsoleViewModel:
    """Return a redacted read-only console view model."""
    try:
        request = body.model_copy(
            update={
                "trace_id": body.trace_id or actor_context.trace_id,
                "actor_id": body.actor_id or actor_context.actor_id,
                "workspace_id": body.workspace_id or actor_context.workspace_id,
                "owner_scope": body.owner_scope or actor_context.security_scope,
                "created_by": body.created_by or actor_context.actor_id,
            }
        )
        return service.get_view_model(request)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/audit", response_model=ConsoleAuditResult)
def audit_console_contracts(
    body: ConsoleAuditRequest,
    service: Annotated[ConsoleContractAuditService, Depends(get_console_audit_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConsoleAuditResult:
    """Run a local read-only console contract audit."""
    try:
        request = body.model_copy(
            update={
                "trace_id": body.trace_id or actor_context.trace_id,
                "owner_scope": body.owner_scope or actor_context.security_scope,
                "created_by": body.created_by or actor_context.actor_id,
            }
        )
        return service.audit(request)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/workflows", response_model=list[ConsoleWorkflowMap])
def get_console_workflows(
    service: Annotated[ConsoleViewModelService, Depends(get_console_view_model_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ConsoleWorkflowMap]:
    """Return read-only console workflow maps."""
    try:
        return service.get_workflows(_scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/demo-map", response_model=dict[str, object])
def get_console_demo_map(
    service: Annotated[ConsoleViewModelService, Depends(get_console_view_model_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    """Return the local console demo map."""
    try:
        return service.get_demo_map(_scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


__all__ = ["router"]
