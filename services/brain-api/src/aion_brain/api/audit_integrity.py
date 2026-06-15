"""Audit integrity and provenance API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.audit_integrity.checkpoints import AuditCheckpointService
from aion_brain.audit_integrity.exporter import AuditExporter
from aion_brain.audit_integrity.ledger import AuditIntegrityLedger
from aion_brain.audit_integrity.provenance import ProvenanceService
from aion_brain.audit_integrity.verifier import AuditVerifier
from aion_brain.contracts.audit_integrity import (
    AuditEntry,
    AuditExportRecord,
    AuditExportRequest,
    AuditIntegrityCheckpoint,
    AuditIntegrityStatus,
    AuditRecordRequest,
    AuditVerificationRequest,
    AuditVerificationRun,
    ProvenanceLink,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["audit-integrity"])


class CheckpointCreateRequest(BaseModel):
    """Create checkpoint request."""

    model_config = ConfigDict(extra="forbid")

    from_sequence: int | None = Field(default=None, ge=1)
    to_sequence: int | None = Field(default=None, ge=1)
    created_by: str | None = None


class ProvenanceDeleteRequest(BaseModel):
    """Soft-delete provenance link request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


def get_audit_ledger(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> AuditIntegrityLedger:
    return container.audit_integrity_ledger


def get_checkpoint_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> AuditCheckpointService:
    return container.audit_checkpoint_service


def get_audit_verifier(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> AuditVerifier:
    return container.audit_verifier


def get_audit_exporter(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> AuditExporter:
    return container.audit_exporter


def get_provenance_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ProvenanceService:
    return container.provenance_service


@router.post("/brain/audit/entries", response_model=AuditEntry)
def record_audit_entry(
    body: AuditRecordRequest,
    ledger: Annotated[AuditIntegrityLedger, Depends(get_audit_ledger)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuditEntry:
    """Append one audit entry."""
    _authorize(container, actor_context, "audit.entry.write", "audit_entry", body.audit_entry_id)
    return ledger.record(
        body.model_copy(
            update={
                "actor_id": body.actor_id or actor_context.actor_id,
                "workspace_id": body.workspace_id or actor_context.workspace_id,
            }
        )
    )


@router.get("/brain/audit/entries", response_model=list[AuditEntry])
def list_audit_entries(
    ledger: Annotated[AuditIntegrityLedger, Depends(get_audit_ledger)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    trace_id: str | None = None,
    resource_type: str | None = None,
    action_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[AuditEntry]:
    """List audit entries."""
    _authorize(container, actor_context, "audit.entry.read", "audit_entry", trace_id)
    return ledger.list_entries(
        trace_id=trace_id,
        resource_type=resource_type,
        action_type=action_type,
        limit=limit,
    )


@router.get("/brain/audit/entries/by-sequence/{sequence_number}", response_model=AuditEntry)
def get_audit_entry_by_sequence(
    sequence_number: int,
    ledger: Annotated[AuditIntegrityLedger, Depends(get_audit_ledger)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuditEntry:
    """Return an audit entry by sequence number."""
    _authorize(container, actor_context, "audit.entry.read", "audit_entry", str(sequence_number))
    entry = ledger.get_by_sequence(sequence_number)
    if entry is None:
        raise HTTPException(status_code=404, detail="audit_entry_not_found")
    return entry


@router.get("/brain/audit/entries/{audit_entry_id}", response_model=AuditEntry)
def get_audit_entry(
    audit_entry_id: str,
    ledger: Annotated[AuditIntegrityLedger, Depends(get_audit_ledger)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuditEntry:
    """Return an audit entry."""
    _authorize(container, actor_context, "audit.entry.read", "audit_entry", audit_entry_id)
    entry = ledger.get_entry(audit_entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="audit_entry_not_found")
    return entry


@router.get("/brain/audit/status", response_model=AuditIntegrityStatus)
def audit_status(
    ledger: Annotated[AuditIntegrityLedger, Depends(get_audit_ledger)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuditIntegrityStatus:
    """Return audit integrity status."""
    _authorize(container, actor_context, "audit.status.read", "audit", None)
    return ledger.status()


@router.post("/brain/audit/checkpoints", response_model=AuditIntegrityCheckpoint)
def create_audit_checkpoint(
    body: CheckpointCreateRequest,
    service: Annotated[AuditCheckpointService, Depends(get_checkpoint_service)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuditIntegrityCheckpoint:
    """Create an audit integrity checkpoint."""
    _authorize(container, actor_context, "audit.checkpoint.create", "audit_checkpoint", None)
    return service.create_checkpoint(
        body.from_sequence,
        body.to_sequence,
        body.created_by or actor_context.actor_id,
    )


@router.get("/brain/audit/checkpoints", response_model=list[AuditIntegrityCheckpoint])
def list_audit_checkpoints(
    service: Annotated[AuditCheckpointService, Depends(get_checkpoint_service)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[AuditIntegrityCheckpoint]:
    """List audit checkpoints."""
    _authorize(container, actor_context, "audit.checkpoint.read", "audit_checkpoint", None)
    return service.list_checkpoints(limit)


@router.post("/brain/audit/verify", response_model=AuditVerificationRun)
def verify_audit(
    body: AuditVerificationRequest,
    verifier: Annotated[AuditVerifier, Depends(get_audit_verifier)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuditVerificationRun:
    """Verify audit integrity."""
    _authorize(container, actor_context, "audit.verify", "audit", body.trace_id, "medium")
    request = body.model_copy(
        update={"created_by": body.created_by or actor_context.actor_id}
    )
    return verifier.verify(request)


@router.get("/brain/audit/verify/{audit_verification_id}", response_model=AuditVerificationRun)
def get_audit_verification(
    audit_verification_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuditVerificationRun:
    """Return one verification run."""
    _authorize(container, actor_context, "audit.verify", "audit", audit_verification_id)
    run = container.audit_integrity_repository.get_verification_run(audit_verification_id)
    if run is None:
        raise HTTPException(status_code=404, detail="audit_verification_not_found")
    return run


@router.post("/brain/audit/export", response_model=AuditExportRecord)
def export_audit(
    body: AuditExportRequest,
    exporter: Annotated[AuditExporter, Depends(get_audit_exporter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AuditExportRecord:
    """Export audit entries locally."""
    return exporter.export(
        body.model_copy(
            update={
                "created_by": body.created_by or actor_context.actor_id,
                "owner_scope": body.owner_scope or actor_context.security_scope,
            }
        )
    )


@router.post("/brain/provenance/links", response_model=ProvenanceLink)
def create_provenance_link(
    body: ProvenanceLink,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
) -> ProvenanceLink:
    """Create one provenance link."""
    return service.create_link(body)


@router.get("/brain/provenance/links", response_model=list[ProvenanceLink])
def list_provenance_links(
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
    source_type: str | None = None,
    source_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    trace_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ProvenanceLink]:
    """List provenance links."""
    return service.list_links(
        source_type=source_type,
        source_id=source_id,
        target_type=target_type,
        target_id=target_id,
        trace_id=trace_id,
        limit=limit,
    )


@router.get("/brain/provenance/traces/{trace_id}", response_model=list[ProvenanceLink])
def trace_provenance(
    trace_id: str,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> list[ProvenanceLink]:
    """Return provenance graph links for a trace."""
    return service.graph_for_trace(trace_id, limit)


@router.delete("/brain/provenance/links/{provenance_link_id}")
def delete_provenance_link(
    provenance_link_id: str,
    body: ProvenanceDeleteRequest,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Soft-delete a provenance link."""
    deleted = service.soft_delete_link(
        provenance_link_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="provenance_link_not_found")
    return {"deleted": True, "provenance_link_id": provenance_link_id}


def _authorize(
    container: KernelContainer,
    actor_context: ActorContext,
    action_type: str,
    resource_type: str,
    resource_id: str | None,
    risk_level: str = "low",
) -> None:
    decision = container.policy_adapter.authorize(
        PolicyRequest(
            request_id=f"{action_type}-{resource_id or 'all'}",
            trace_id=None,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=False,
            requested_permissions=[action_type],
            security_scope=actor_context.security_scope,
            context={"actor_context": actor_context.model_dump(mode="json")},
        )
    )
    if not decision.allow:
        raise HTTPException(status_code=403, detail=decision.reason)
