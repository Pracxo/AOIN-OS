"""AION Brain kernel diagnostics and contract API."""

from datetime import UTC, datetime
from typing import Annotated, Any, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from aion_brain.api_support.error_codes import ERROR_CODE_TAXONOMY
from aion_brain.contracts.api import APIRequestRecord, OpenAPIHygieneReport
from aion_brain.contracts.kernel import (
    ArchitectureBoundaryReport,
    ContractExport,
    KernelAdapterConfig,
    KernelBootRecord,
    KernelSelfTestRequest,
    KernelSelfTestResult,
    KernelServiceRecord,
    KernelStatus,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.policy.enrichment import PolicyInputEnricher

router = APIRouter(prefix="/brain/kernel", tags=["kernel"])
api_router = APIRouter(prefix="/brain/api", tags=["api"])


def get_kernel_container(request: Request) -> KernelContainer:
    """Return the process-wide kernel composition root."""
    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelContainer):
        raise RuntimeError("AION kernel container is not configured")
    return container


@router.get("/status", response_model=KernelStatus)
def kernel_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> KernelStatus:
    """Return assembled kernel status."""
    _authorize(container, actor_context, "kernel.status.read")
    return container.status()


@router.get("/boot/latest", response_model=KernelBootRecord | None)
def latest_boot(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> KernelBootRecord | None:
    """Return the latest kernel boot record."""
    _authorize(container, actor_context, "kernel.boot.read")
    return container.ensure_booted()


@router.get("/services", response_model=list[KernelServiceRecord])
def services(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    status: str | None = None,
    service_type: str | None = None,
) -> list[KernelServiceRecord]:
    """List assembled services."""
    _authorize(container, actor_context, "kernel.services.read")
    return container.service_registry.list_services(status, service_type)


@router.post("/self-test", response_model=KernelSelfTestResult)
def run_self_test(
    body: KernelSelfTestRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> KernelSelfTestResult:
    """Run the deterministic local kernel self-test."""
    _authorize(container, actor_context, "kernel.self_test.run")
    return container.self_test_service.run(body, actor_context)


@router.get("/self-test/latest", response_model=KernelSelfTestResult | None)
def latest_self_test(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> KernelSelfTestResult | None:
    """Return the latest kernel self-test."""
    _authorize(container, actor_context, "kernel.status.read")
    return container.self_test_service.get_latest()


@router.get("/contracts", response_model=ContractExport)
def contracts(
    request: Request,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ContractExport:
    """Export OpenAPI and AION-owned Pydantic contracts."""
    _authorize(container, actor_context, "kernel.contracts.export")
    export = container.contract_export_service.export_contracts(request.app)
    _emit(container, "kernel_contract_exported", "contract", export.export_id, 0.5)
    return export


@router.post("/boundary-check", response_model=ArchitectureBoundaryReport)
def boundary_check(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ArchitectureBoundaryReport:
    """Run the architecture boundary scanner."""
    _authorize(container, actor_context, "kernel.boundary_check.run")
    report = container.boundary_checker.check()
    _emit(
        container,
        "kernel_boundary_check_completed",
        "diagnostic",
        report.report_id,
        0.8 if report.status == "passed" else 1.0,
    )
    return report


@router.get("/adapters", response_model=KernelAdapterConfig)
def adapters(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> KernelAdapterConfig:
    """Return selected kernel adapters."""
    _authorize(container, actor_context, "kernel.status.read")
    return container.adapter_config


@api_router.get("/requests/{request_id}", response_model=APIRequestRecord)
def api_request_record(
    request_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> APIRequestRecord:
    """Return one safe API request audit record."""
    _authorize(container, actor_context, "api.request.read")
    record = container.api_request_audit_service.get_record(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"request_id": request_id})
    return record


@api_router.get("/requests", response_model=list[APIRequestRecord])
def api_request_records(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    trace_id: str | None = None,
    correlation_id: str | None = None,
    limit: int = 50,
) -> list[APIRequestRecord]:
    """List safe API request audit records."""
    _authorize(container, actor_context, "api.request.read")
    return container.api_request_audit_service.list_records(
        trace_id=trace_id,
        correlation_id=correlation_id,
        limit=min(max(limit, 1), container.settings.api_max_page_limit),
    )


@api_router.get("/openapi-hygiene", response_model=OpenAPIHygieneReport)
def openapi_hygiene(
    request: Request,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OpenAPIHygieneReport:
    """Run OpenAPI contract hygiene checks."""
    _authorize(container, actor_context, "api.openapi_hygiene.read")
    report = container.openapi_hygiene_checker.check(request.app.openapi())
    _emit(
        container,
        "api_openapi_hygiene_checked",
        "contract",
        report.report_id,
        0.7 if report.status == "passed" else 1.0,
    )
    return report


@api_router.get("/error-codes", response_model=dict[str, dict[str, Any]])
def error_codes(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, dict[str, Any]]:
    """Return the stable AION API error code taxonomy."""
    _authorize(container, actor_context, "api.error_codes.read")
    return ERROR_CODE_TAXONOMY


def _authorize(container: KernelContainer, actor_context: ActorContext, action_type: str) -> None:
    decision = container.policy_adapter.authorize(
        PolicyInputEnricher().enrich(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=actor_context.trace_id,
                actor_id=actor_context.actor_id,
                workspace_id=actor_context.workspace_id,
                action_type=action_type,
                resource_type="kernel",
                resource_id=None,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=actor_context.security_scope,
                context={},
            ),
            actor_context,
        )
    )
    if not decision.allow:
        raise HTTPException(
            status_code=403,
            detail={"reason": decision.reason, "constraints": decision.constraints},
        )


def _emit(
    container: KernelContainer,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
) -> None:
    emit = getattr(container.telemetry_service, "emit", None)
    if not callable(emit):
        return
    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{node_id}-{event_type}",
                trace_id=node_id,
                event_type=cast(VisualTelemetryEventType, event_type),
                node_type=cast(VisualNodeType, node_type),
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=intensity,
                payload={},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
