"""Local backup and restore-preview API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.backups.exporter import BackupExporter
from aion_brain.backups.restore_preview import RestorePreviewService
from aion_brain.backups.restore_service import RestoreService
from aion_brain.backups.validator import BackupValidator
from aion_brain.contracts.backups import (
    BackupJob,
    BackupRequest,
    BackupValidationReport,
    RestoreJob,
    RestorePreview,
    RestorePreviewRequest,
    RestoreRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["backups"])


class BackupPathValidationRequest(BaseModel):
    """Path-based backup validation request."""

    model_config = ConfigDict(extra="forbid")

    backup_path: str = Field(min_length=1)
    scope: list[str] = Field(default_factory=list)


def get_backup_exporter(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> BackupExporter:
    """Return the configured backup exporter."""
    return container.backup_exporter


def get_restore_preview_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> RestorePreviewService:
    """Return the configured restore preview service."""
    return container.restore_preview_service


def get_restore_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> RestoreService:
    """Return the configured restore service."""
    return container.restore_service


def get_backup_validator(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> BackupValidator:
    """Return the configured backup validator."""
    return container.backup_validator


@router.post("/brain/backups/export", response_model=BackupJob)
def export_backup(
    body: BackupRequest,
    service: Annotated[BackupExporter, Depends(get_backup_exporter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BackupJob:
    """Create a dry-run or write-mode local backup."""
    return service.export(_backup_request(body, actor_context))


@router.get("/brain/backups", response_model=list[BackupJob])
def list_backups(
    service: Annotated[BackupExporter, Depends(get_backup_exporter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    workspace_id: str | None = None,
    status: str | None = None,
) -> list[BackupJob]:
    """List local backup jobs."""
    return service.list_jobs(
        _scope(scope, actor_context),
        workspace_id=workspace_id,
        status=status,
    )


@router.get("/brain/backups/{backup_job_id}", response_model=BackupJob)
def get_backup(
    backup_job_id: str,
    service: Annotated[BackupExporter, Depends(get_backup_exporter)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BackupJob:
    """Return one local backup job."""
    job = service.get_job(backup_job_id, _scope(scope, actor_context))
    if job is None:
        raise HTTPException(status_code=404, detail="backup_job_not_found")
    return job


@router.post("/brain/backups/{backup_job_id}/validate", response_model=BackupValidationReport)
def validate_backup(
    backup_job_id: str,
    service: Annotated[BackupValidator, Depends(get_backup_validator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BackupValidationReport:
    """Validate a stored backup job."""
    return service.validate_backup_job(backup_job_id, _scope(scope, actor_context))


@router.post("/brain/backups/validate-path", response_model=BackupValidationReport)
def validate_backup_path(
    body: BackupPathValidationRequest,
    service: Annotated[BackupValidator, Depends(get_backup_validator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BackupValidationReport:
    """Validate a local backup path."""
    return service.validate_backup_path(
        body.backup_path,
        body.scope or actor_context.security_scope,
    )


@router.post("/brain/restore/preview", response_model=RestorePreview)
def preview_restore(
    body: RestorePreviewRequest,
    service: Annotated[RestorePreviewService, Depends(get_restore_preview_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RestorePreview:
    """Preview a local backup restore."""
    return service.preview(_preview_request(body, actor_context))


@router.get("/brain/restore/previews/{restore_preview_id}", response_model=RestorePreview)
def get_restore_preview(
    restore_preview_id: str,
    service: Annotated[RestorePreviewService, Depends(get_restore_preview_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RestorePreview:
    """Return one restore preview."""
    preview = service.get_preview(restore_preview_id, _scope(scope, actor_context))
    if preview is None:
        raise HTTPException(status_code=404, detail="restore_preview_not_found")
    return preview


@router.post("/brain/restore/apply", response_model=RestoreJob)
def apply_restore(
    body: RestoreRequest,
    service: Annotated[RestoreService, Depends(get_restore_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RestoreJob:
    """Dry-run or guarded apply for a restore preview."""
    return service.restore(_restore_request(body, actor_context))


def _backup_request(body: BackupRequest, actor_context: ActorContext) -> BackupRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )


def _preview_request(
    body: RestorePreviewRequest,
    actor_context: ActorContext,
) -> RestorePreviewRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )


def _restore_request(body: RestoreRequest, actor_context: ActorContext) -> RestoreRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value
