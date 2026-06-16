"""AION self-model API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.capability_awareness import CapabilityAwarenessRecord
from aion_brain.contracts.confidence import (
    ConfidenceCalibration,
    ConfidenceCalibrationRequest,
    IntrospectionSnapshot,
    IntrospectionSnapshotRequest,
    SelfAssessmentRequest,
    SelfAssessmentRun,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.self_model import (
    LimitationCreateRequest,
    LimitationRecord,
    SelfDescription,
    SelfDescriptionRequest,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/self", tags=["self-model"])


class RefreshCapabilitiesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    dry_run: bool = True


class SeedDefaultsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    dry_run: bool = True


class ResolveLimitationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


@router.get("", response_model=SelfDescription)
def get_self_description(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    include_capabilities: bool = True,
    include_limitations: bool | None = None,
    include_architecture: bool = True,
    include_status: bool = True,
    format: str = "structured",
) -> SelfDescription:
    """Return a factual AION self-description."""
    request = SelfDescriptionRequest(
        scope=_scope(scope, actor_context),
        include_capabilities=include_capabilities,
        include_limitations=(
            include_limitations
            if include_limitations is not None
            else container.settings.self_description_include_limitations_default
        ),
        include_architecture=include_architecture,
        include_status=include_status,
        format=format,  # type: ignore[arg-type]
    )
    try:
        return container.self_description_service.describe(request)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/describe", response_model=SelfDescription)
def describe_self(
    body: SelfDescriptionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SelfDescription:
    try:
        return container.self_description_service.describe(
            body.model_copy(update={"scope": body.scope or actor_context.security_scope})
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/capabilities", response_model=list[CapabilityAwarenessRecord])
def list_capabilities(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    capability_type: str | None = None,
) -> list[CapabilityAwarenessRecord]:
    try:
        return container.capability_awareness_service.list_capabilities(
            _scope(scope, actor_context),
            status=status,
            capability_type=capability_type,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/capabilities/refresh", response_model=list[CapabilityAwarenessRecord])
def refresh_capabilities(
    body: RefreshCapabilitiesRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[CapabilityAwarenessRecord]:
    try:
        return container.capability_awareness_service.refresh(
            body.scope or actor_context.security_scope,
            dry_run=body.dry_run,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/limitations", response_model=LimitationRecord)
def create_limitation(
    body: LimitationCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LimitationRecord:
    try:
        return container.limitation_ledger_service.create_limitation(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/limitations", response_model=list[LimitationRecord])
def list_limitations(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    disclosure_required: bool | None = None,
) -> list[LimitationRecord]:
    try:
        return container.limitation_ledger_service.list_limitations(
            _scope(scope, actor_context),
            status=status,
            category=category,
            severity=severity,
            disclosure_required=disclosure_required,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/limitations/seed-defaults")
def seed_default_limitations(
    body: SeedDefaultsRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    return container.limitation_ledger_service.seed_defaults(
        body.scope or actor_context.security_scope,
        dry_run=body.dry_run,
    )


@router.post("/limitations/{limitation_id}/resolve", response_model=LimitationRecord)
def resolve_limitation(
    limitation_id: str,
    body: ResolveLimitationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LimitationRecord:
    try:
        return container.limitation_ledger_service.resolve_limitation(
            limitation_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/confidence/calibrate", response_model=ConfidenceCalibration)
def calibrate_confidence(
    body: ConfidenceCalibrationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConfidenceCalibration:
    metadata = dict(body.metadata)
    metadata.setdefault("owner_scope", actor_context.security_scope)
    try:
        return container.confidence_calibrator.calibrate(
            body.model_copy(update={"metadata": metadata})
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/confidence", response_model=list[ConfidenceCalibration])
def list_confidence(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    trace_id: str | None = None,
    response_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ConfidenceCalibration]:
    try:
        return container.confidence_calibrator.list_calibrations(
            trace_id=trace_id,
            response_id=response_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/assessment/run", response_model=SelfAssessmentRun)
def run_assessment(
    body: SelfAssessmentRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SelfAssessmentRun:
    try:
        return container.self_assessment_service.run(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "created_by": body.created_by or actor_context.actor_id,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/assessment/{self_assessment_id}", response_model=SelfAssessmentRun)
def get_assessment(
    self_assessment_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SelfAssessmentRun:
    run = container.self_assessment_service.get(self_assessment_id)
    if run is None:
        raise HTTPException(status_code=404, detail="self_assessment_not_found")
    return run


@router.post("/introspection", response_model=IntrospectionSnapshot)
def create_introspection(
    body: IntrospectionSnapshotRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> IntrospectionSnapshot:
    try:
        return container.introspection_snapshot_service.create_snapshot(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/introspection", response_model=list[IntrospectionSnapshot])
def list_introspection(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    snapshot_type: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[IntrospectionSnapshot]:
    try:
        return container.introspection_snapshot_service.list_snapshots(
            _scope(scope, actor_context),
            snapshot_type=snapshot_type,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/introspection/{introspection_snapshot_id}", response_model=IntrospectionSnapshot)
def get_introspection(
    introspection_snapshot_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> IntrospectionSnapshot:
    try:
        snapshot = container.introspection_snapshot_service.get_snapshot(
            introspection_snapshot_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="introspection_snapshot_not_found")
    return snapshot


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]
