"""Autonomy Governor API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.autonomy.delegation import DelegationService
from aion_brain.autonomy.governor import AutonomyGovernor
from aion_brain.autonomy.repository import AutonomyRepository
from aion_brain.autonomy.run_level import RunLevelService
from aion_brain.config import get_settings
from aion_brain.contracts.autonomy import (
    AutonomyDecision,
    AutonomyDecisionRequest,
    AutonomyProfile,
    AutonomyProfileCreateRequest,
    AutonomyStatus,
    DelegationGrant,
    DelegationGrantRequest,
    RunLevelRecord,
    SetRunLevelRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain/autonomy", tags=["autonomy"])


class DisableProfileRequest(BaseModel):
    """Profile disable request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class EndRunLevelRequest(BaseModel):
    """Run-level end request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class RevokeDelegationRequest(BaseModel):
    """Delegation revoke request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


def get_autonomy_governor(request: Request) -> AutonomyGovernor:
    """Return configured autonomy governor."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "autonomy_governor", None)
    if isinstance(service, AutonomyGovernor):
        return service
    settings = get_settings()
    return get_cached_autonomy_governor(settings.database_url, settings.opa_url)


def get_run_level_service(request: Request) -> RunLevelService:
    """Return configured run-level service."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "run_level_service", None)
    if isinstance(service, RunLevelService):
        return service
    settings = get_settings()
    return get_cached_run_level_service(settings.database_url, settings.opa_url)


def get_delegation_service(request: Request) -> DelegationService:
    """Return configured delegation service."""
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "delegation_service", None)
    if isinstance(service, DelegationService):
        return service
    settings = get_settings()
    return get_cached_delegation_service(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_repository(database_url: str) -> AutonomyRepository:
    """Return cached autonomy repository."""
    return AutonomyRepository(database_url)


@lru_cache
def get_cached_run_level_service(database_url: str, opa_url: str) -> RunLevelService:
    """Return cached run-level service."""
    return RunLevelService(get_cached_repository(database_url), OPAAdapter(opa_url))


@lru_cache
def get_cached_delegation_service(database_url: str, opa_url: str) -> DelegationService:
    """Return cached delegation service."""
    return DelegationService(get_cached_repository(database_url), OPAAdapter(opa_url))


@lru_cache
def get_cached_autonomy_governor(database_url: str, opa_url: str) -> AutonomyGovernor:
    """Return cached autonomy governor."""
    settings = get_settings()
    repository = get_cached_repository(database_url)
    policy_adapter = OPAAdapter(opa_url)
    delegation = DelegationService(repository, policy_adapter)
    run_level = RunLevelService(repository, policy_adapter)
    return AutonomyGovernor(
        repository,
        policy_adapter,
        delegation_service=delegation,
        run_level_service=run_level,
        settings=settings,
    )


@router.post("/profiles", response_model=AutonomyProfile)
def create_profile(
    request: AutonomyProfileCreateRequest,
    service: Annotated[AutonomyGovernor, Depends(get_autonomy_governor)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AutonomyProfile:
    """Create an autonomy profile."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
            "created_by": request.created_by or actor_context.actor_id,
        }
    )
    try:
        return service.create_profile(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/profiles", response_model=list[AutonomyProfile])
def list_profiles(
    service: Annotated[AutonomyGovernor, Depends(get_autonomy_governor)],
    actor_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> list[AutonomyProfile]:
    """List autonomy profiles."""
    try:
        return service.list_profiles(actor_id, workspace_id, status)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/profiles/{autonomy_profile_id}", response_model=AutonomyProfile)
def get_profile(
    autonomy_profile_id: str,
    service: Annotated[AutonomyGovernor, Depends(get_autonomy_governor)],
) -> AutonomyProfile:
    """Return one autonomy profile."""
    profile = service.get_profile(autonomy_profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="autonomy_profile_not_found")
    return profile


@router.post("/profiles/{autonomy_profile_id}/disable", response_model=AutonomyProfile)
def disable_profile(
    autonomy_profile_id: str,
    request: DisableProfileRequest,
    service: Annotated[AutonomyGovernor, Depends(get_autonomy_governor)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AutonomyProfile:
    """Disable one autonomy profile."""
    try:
        return service.disable_profile(
            autonomy_profile_id,
            request.actor_id or actor_context.actor_id,
            request.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/run-levels", response_model=RunLevelRecord)
def set_run_level(
    request: SetRunLevelRequest,
    service: Annotated[RunLevelService, Depends(get_run_level_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RunLevelRecord:
    """Set an active run level."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "set_by": request.set_by or actor_context.actor_id,
        }
    )
    try:
        return service.set_run_level(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/run-levels/active", response_model=RunLevelRecord | None)
def get_active_run_level(
    service: Annotated[RunLevelService, Depends(get_run_level_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    actor_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
) -> RunLevelRecord | None:
    """Return active run level."""
    return service.get_active_run_level(
        actor_id or actor_context.actor_id,
        workspace_id or actor_context.workspace_id,
    )


@router.get("/run-levels", response_model=list[RunLevelRecord])
def list_run_levels(
    service: Annotated[RunLevelService, Depends(get_run_level_service)],
    actor_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> list[RunLevelRecord]:
    """List run levels."""
    return service.list_run_levels(actor_id, workspace_id, status)


@router.post("/run-levels/{run_level_id}/end", response_model=RunLevelRecord)
def end_run_level(
    run_level_id: str,
    request: EndRunLevelRequest,
    service: Annotated[RunLevelService, Depends(get_run_level_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RunLevelRecord:
    """End one run level."""
    try:
        return service.end_run_level(
            run_level_id,
            request.actor_id or actor_context.actor_id,
            request.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/delegations", response_model=DelegationGrant)
def create_delegation(
    request: DelegationGrantRequest,
    service: Annotated[DelegationService, Depends(get_delegation_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DelegationGrant:
    """Create a delegation grant."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "delegated_by": request.delegated_by or actor_context.actor_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return service.create_grant(enriched)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/delegations/{delegation_id}", response_model=DelegationGrant)
def get_delegation(
    delegation_id: str,
    service: Annotated[DelegationService, Depends(get_delegation_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> DelegationGrant:
    """Return one delegation."""
    grant = service.get_grant(delegation_id, scope or actor_context.security_scope)
    if grant is None:
        raise HTTPException(status_code=404, detail="delegation_not_found")
    return grant


@router.get("/delegations", response_model=list[DelegationGrant])
def list_delegations(
    service: Annotated[DelegationService, Depends(get_delegation_service)],
    actor_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> list[DelegationGrant]:
    """List delegations."""
    return service.list_grants(actor_id, workspace_id, status)


@router.post("/delegations/{delegation_id}/revoke", response_model=DelegationGrant)
def revoke_delegation(
    delegation_id: str,
    request: RevokeDelegationRequest,
    service: Annotated[DelegationService, Depends(get_delegation_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DelegationGrant:
    """Revoke one delegation."""
    try:
        return service.revoke_grant(
            delegation_id,
            request.actor_id or actor_context.actor_id,
            request.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/decide", response_model=AutonomyDecision)
def decide_autonomy(
    request: AutonomyDecisionRequest,
    service: Annotated[AutonomyGovernor, Depends(get_autonomy_governor)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> AutonomyDecision:
    """Resolve one autonomy decision."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "context": {
                **request.context,
                "security_scope": request.context.get(
                    "security_scope",
                    actor_context.security_scope,
                ),
            },
        }
    )
    return service.decide(enriched)


@router.get("/status", response_model=AutonomyStatus)
def autonomy_status(
    service: Annotated[AutonomyGovernor, Depends(get_autonomy_governor)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    actor_id: Annotated[str | None, Query()] = None,
    workspace_id: Annotated[str | None, Query()] = None,
    scope: Annotated[list[str] | None, Query()] = None,
) -> AutonomyStatus:
    """Return autonomy status."""
    try:
        return service.status(
            actor_id or actor_context.actor_id,
            workspace_id or actor_context.workspace_id,
            scope or actor_context.security_scope,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
