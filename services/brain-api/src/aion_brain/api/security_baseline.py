"""Security baseline API."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.security_baseline import (
    HardeningGateRequest,
    HardeningGateRun,
    SecurityControlRecord,
    SecurityScanRequest,
    SecurityScanRun,
    SeedControlsRequest,
    SeedThreatModelsRequest,
    StatusUpdateRequest,
    ThreatModelRecord,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.security_baseline.control_catalog import SecurityControlCatalog
from aion_brain.security_baseline.hardening_gate import HardeningGateService
from aion_brain.security_baseline.repository import SecurityBaselineRepository
from aion_brain.security_baseline.secret_scanner import SecretScanner
from aion_brain.security_baseline.threat_model import ThreatModelService

router = APIRouter(prefix="/brain/security", tags=["security-baseline"])


def get_security_repository(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SecurityBaselineRepository:
    return container.security_baseline_repository


def get_secret_scanner(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SecretScanner:
    return container.secret_scanner


def get_threat_model_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ThreatModelService:
    return container.threat_model_service


def get_control_catalog(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SecurityControlCatalog:
    return container.security_control_catalog


def get_hardening_gate_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> HardeningGateService:
    return container.hardening_gate_service


@router.post("/scans/run", response_model=SecurityScanRun)
def run_security_scan(
    body: SecurityScanRequest,
    scanner: Annotated[SecretScanner, Depends(get_secret_scanner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SecurityScanRun:
    """Run a deterministic local security scan."""
    request = body.model_copy(
        update={
            "created_by": body.created_by or actor_context.actor_id,
            "metadata": {**body.metadata, **_actor_metadata(actor_context)},
        }
    )
    return scanner.scan(request)


@router.get("/scans/{security_scan_id}", response_model=SecurityScanRun)
def get_security_scan(
    security_scan_id: str,
    repository: Annotated[SecurityBaselineRepository, Depends(get_security_repository)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SecurityScanRun:
    """Return one security scan run."""
    _authorize(container, actor_context, "security.scan.read", "security_scan", security_scan_id)
    run = repository.get_scan(security_scan_id)
    if run is None:
        raise HTTPException(status_code=404, detail="security_scan_not_found")
    return run


@router.get("/scans", response_model=list[SecurityScanRun])
def list_security_scans(
    repository: Annotated[SecurityBaselineRepository, Depends(get_security_repository)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scan_type: str | None = None,
    status: str | None = None,
) -> list[SecurityScanRun]:
    """List security scan runs."""
    _authorize(container, actor_context, "security.scan.read", "security_scan", None)
    return repository.list_scans(scan_type=scan_type, status=status)


@router.post("/threat-models/seed-defaults")
def seed_threat_models(
    body: SeedThreatModelsRequest,
    service: Annotated[ThreatModelService, Depends(get_threat_model_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Seed or preview default threat model records."""
    return service.seed_defaults(
        dry_run=body.dry_run,
        owner_scope=body.owner_scope,
        actor_context=_actor_metadata(actor_context),
    )


@router.post("/threat-models", response_model=ThreatModelRecord)
def create_threat_model(
    body: ThreatModelRecord,
    service: Annotated[ThreatModelService, Depends(get_threat_model_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ThreatModelRecord:
    """Create one threat model record."""
    return service.create(
        body.model_copy(
            update={
                "created_by": body.created_by or actor_context.actor_id,
                "metadata": {**body.metadata, **_actor_metadata(actor_context)},
            }
        )
    )


@router.get("/threat-models", response_model=list[ThreatModelRecord])
def list_threat_models(
    service: Annotated[ThreatModelService, Depends(get_threat_model_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    status: str | None = None,
    category: str | None = None,
) -> list[ThreatModelRecord]:
    """List threat model records."""
    return service.list(
        status=status,
        category=category,
        owner_scope=actor_context.security_scope,
        actor_context=_actor_metadata(actor_context),
    )


@router.post("/threat-models/{threat_model_id}/status", response_model=ThreatModelRecord)
def update_threat_model_status(
    threat_model_id: str,
    body: StatusUpdateRequest,
    service: Annotated[ThreatModelService, Depends(get_threat_model_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ThreatModelRecord:
    """Update a threat model status."""
    return service.update_status(
        threat_model_id,
        body.status,
        body.actor_id or actor_context.actor_id,
        body.reason,
        owner_scope=actor_context.security_scope,
        actor_context=_actor_metadata(actor_context),
    )


@router.post("/controls/seed-defaults")
def seed_controls(
    body: SeedControlsRequest,
    service: Annotated[SecurityControlCatalog, Depends(get_control_catalog)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Seed or preview default security controls."""
    return service.seed_defaults(dry_run=body.dry_run, actor_context=_actor_metadata(actor_context))


@router.post("/controls", response_model=SecurityControlRecord)
def create_control(
    body: SecurityControlRecord,
    service: Annotated[SecurityControlCatalog, Depends(get_control_catalog)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SecurityControlRecord:
    """Create one security control."""
    return service.create(
        body.model_copy(update={"metadata": {**body.metadata, **_actor_metadata(actor_context)}})
    )


@router.get("/controls", response_model=list[SecurityControlRecord])
def list_controls(
    service: Annotated[SecurityControlCatalog, Depends(get_control_catalog)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    status: str | None = None,
    category: str | None = None,
) -> list[SecurityControlRecord]:
    """List security controls."""
    return service.list(
        status=status,
        category=category,
        actor_context=_actor_metadata(actor_context),
    )


@router.post("/controls/{control_key}/status", response_model=SecurityControlRecord)
def update_control_status(
    control_key: str,
    body: StatusUpdateRequest,
    service: Annotated[SecurityControlCatalog, Depends(get_control_catalog)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SecurityControlRecord:
    """Update a control status."""
    return service.update_status(
        control_key,
        body.status,
        body.actor_id or actor_context.actor_id,
        body.reason,
        actor_context=_actor_metadata(actor_context),
    )


@router.post("/hardening-gate/run", response_model=HardeningGateRun)
def run_hardening_gate(
    body: HardeningGateRequest,
    request: Request,
    service: Annotated[HardeningGateService, Depends(get_hardening_gate_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> HardeningGateRun:
    """Run the local hardening gate."""
    gate_request = body.model_copy(
        update={
            "created_by": body.created_by or actor_context.actor_id,
            "metadata": {**body.metadata, **_actor_metadata(actor_context)},
        }
    )
    return service.run(gate_request, app=request.app)


@router.get("/hardening-gate/{hardening_gate_id}", response_model=HardeningGateRun)
def get_hardening_gate(
    hardening_gate_id: str,
    repository: Annotated[SecurityBaselineRepository, Depends(get_security_repository)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> HardeningGateRun:
    """Return one hardening gate run."""
    _authorize(
        container,
        actor_context,
        "security.hardening.read",
        "hardening_gate",
        hardening_gate_id,
    )
    run = repository.get_hardening_gate(hardening_gate_id)
    if run is None:
        raise HTTPException(status_code=404, detail="hardening_gate_not_found")
    return run


@router.get("/hardening-gate", response_model=list[HardeningGateRun])
def list_hardening_gates(
    repository: Annotated[SecurityBaselineRepository, Depends(get_security_repository)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    version: str | None = None,
    status: str | None = None,
) -> list[HardeningGateRun]:
    """List hardening gate runs."""
    _authorize(container, actor_context, "security.hardening.read", "hardening_gate", None)
    return repository.list_hardening_gates(version=version, status=status)


def _authorize(
    container: KernelContainer,
    actor_context: ActorContext,
    action_type: str,
    resource_type: str,
    resource_id: str | None,
) -> None:
    decision = container.policy_adapter.authorize(
        PolicyInputEnricher().enrich(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=actor_context.trace_id,
                actor_id=actor_context.actor_id,
                workspace_id=actor_context.workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[action_type],
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


def _actor_metadata(actor_context: ActorContext) -> dict[str, object]:
    return {"actor_context": actor_context.model_dump(mode="json")}
