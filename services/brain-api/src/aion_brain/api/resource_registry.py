"""Global Resource Registry API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.resource_references import (
    BrokenReference,
    OrphanedResource,
    ResourceReferenceCreateRequest,
    ResourceReferenceLink,
)
from aion_brain.contracts.resource_registry import (
    ReferenceValidationRequest,
    ReferenceValidationRun,
    RegistryRebuildRequest,
    RegistryRebuildRun,
    RegistrySnapshot,
    RegistrySnapshotType,
    ResourceIndexRecord,
    ResourceIndexUpsertRequest,
    ResourceRegistryQuery,
    ResourceRegistryQueryResult,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/registry", tags=["resource-registry"])


class MutationReasonRequest(BaseModel):
    """Reason-bearing registry mutation request."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1)


class SnapshotCreateRequest(BaseModel):
    """Manual registry snapshot request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    snapshot_type: RegistrySnapshotType = "manual"
    trace_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


@router.post("/resources", response_model=ResourceIndexRecord)
def upsert_resource(
    body: ResourceIndexUpsertRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResourceIndexRecord:
    try:
        return container.resource_registry_service.with_actor_context(actor_context).upsert(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/resources/by-uri", response_model=ResourceIndexRecord)
def get_resource_by_uri(
    resource_uri: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ResourceIndexRecord:
    try:
        record = container.resource_registry_service.with_actor_context(actor_context).get_by_uri(
            resource_uri, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="resource_not_found")
    return record


@router.get("/resources/{resource_type}/{resource_id}", response_model=ResourceIndexRecord)
def get_resource(
    resource_type: str,
    resource_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ResourceIndexRecord:
    try:
        record = container.resource_registry_service.with_actor_context(
            actor_context
        ).get_by_type_id(resource_type, resource_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="resource_not_found")
    return record


@router.post("/query", response_model=ResourceRegistryQueryResult)
def query_registry(
    body: ResourceRegistryQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResourceRegistryQueryResult:
    try:
        return container.registry_query_service.with_actor_context(actor_context).query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/links", response_model=ResourceReferenceLink)
def create_link(
    body: ResourceReferenceCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ResourceReferenceLink:
    try:
        return container.resource_link_service.with_actor_context(actor_context).create_link(
            body,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/links", response_model=list[ResourceReferenceLink])
def list_links(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    source_uri: str | None = None,
    target_uri: str | None = None,
    relation_type: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ResourceReferenceLink]:
    try:
        return container.resource_link_service.with_actor_context(actor_context).list_links(
            _scope(scope, actor_context),
            source_uri=source_uri,
            target_uri=target_uri,
            relation_type=relation_type,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/backlinks", response_model=list[dict[str, object]])
def list_backlinks(
    resource_uri: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[dict[str, object]]:
    try:
        return container.backlink_service.with_actor_context(actor_context).list_backlinks(
            resource_uri,
            _scope(scope, actor_context),
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/validate", response_model=ReferenceValidationRun)
def validate_references(
    body: ReferenceValidationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ReferenceValidationRun:
    try:
        return container.reference_validator.with_actor_context(actor_context).validate(
            _validation_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/validation-runs/{validation_run_id}", response_model=ReferenceValidationRun)
def get_validation_run(
    validation_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReferenceValidationRun:
    try:
        run = container.reference_validator.with_actor_context(actor_context).get_run(
            validation_run_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if run is None:
        raise HTTPException(status_code=404, detail="validation_run_not_found")
    return run


@router.get("/broken-references", response_model=list[BrokenReference])
def list_broken_references(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    validation_run_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[BrokenReference]:
    try:
        return container.reference_validator.with_actor_context(
            actor_context
        ).list_broken_references(
            _scope(scope, actor_context),
            status=status,
            severity=severity,
            validation_run_id=validation_run_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/broken-references/{broken_reference_id}/dismiss", response_model=BrokenReference)
def dismiss_broken_reference(
    broken_reference_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BrokenReference:
    try:
        return container.reference_validator.with_actor_context(
            actor_context
        ).dismiss_broken_reference(broken_reference_id, _scope(scope, actor_context), body.reason)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/orphaned-resources", response_model=list[OrphanedResource])
def list_orphaned_resources(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    validation_run_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[OrphanedResource]:
    try:
        return container.reference_validator.with_actor_context(
            actor_context
        ).list_orphaned_resources(
            _scope(scope, actor_context),
            status=status,
            severity=severity,
            validation_run_id=validation_run_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/orphaned-resources/{orphaned_resource_id}/dismiss", response_model=OrphanedResource)
def dismiss_orphaned_resource(
    orphaned_resource_id: str,
    body: MutationReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> OrphanedResource:
    try:
        return container.reference_validator.with_actor_context(
            actor_context
        ).dismiss_orphaned_resource(orphaned_resource_id, _scope(scope, actor_context), body.reason)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rebuild", response_model=RegistryRebuildRun)
def rebuild_registry(
    body: RegistryRebuildRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RegistryRebuildRun:
    try:
        return container.registry_rebuilder.with_actor_context(actor_context).rebuild(
            _rebuild_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/rebuild-runs/{rebuild_run_id}", response_model=RegistryRebuildRun)
def get_rebuild_run(
    rebuild_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RegistryRebuildRun:
    try:
        run = container.registry_rebuilder.with_actor_context(actor_context).get_run(
            rebuild_run_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if run is None:
        raise HTTPException(status_code=404, detail="rebuild_run_not_found")
    return run


@router.post("/snapshots", response_model=RegistrySnapshot)
def create_snapshot(
    body: SnapshotCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RegistrySnapshot:
    try:
        return container.registry_snapshot_service.with_actor_context(
            actor_context
        ).create_snapshot(
            _scope(body.scope, actor_context),
            snapshot_type=body.snapshot_type,
            trace_id=body.trace_id,
            metadata=body.metadata,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/snapshots/{registry_snapshot_id}", response_model=RegistrySnapshot)
def get_snapshot(
    registry_snapshot_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RegistrySnapshot:
    try:
        snapshot = container.registry_snapshot_service.with_actor_context(
            actor_context
        ).get_snapshot(registry_snapshot_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="registry_snapshot_not_found")
    return snapshot


@router.get("/snapshots", response_model=list[RegistrySnapshot])
def list_snapshots(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    snapshot_type: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[RegistrySnapshot]:
    try:
        return container.registry_snapshot_service.with_actor_context(actor_context).list_snapshots(
            _scope(scope, actor_context),
            snapshot_type=snapshot_type,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


def _validation_with_context(
    body: ReferenceValidationRequest,
    actor_context: ActorContext,
) -> ReferenceValidationRequest:
    return body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
        }
    )


def _rebuild_with_context(
    body: RegistryRebuildRequest,
    actor_context: ActorContext,
) -> RegistryRebuildRequest:
    return body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
        }
    )
