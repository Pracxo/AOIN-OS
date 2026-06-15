"""Runtime configuration API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.runtime_config import (
    ConfigProfile,
    ConfigProfileCreateRequest,
    ConfigSnapshot,
    ConfigSnapshotRequest,
    ConfigValidationRequest,
    ConfigValidationRun,
    FeatureFlagOverride,
    FeatureFlagOverrideRequest,
    RuntimeConfigStatus,
    SnapshotCompareRequest,
    StatusUpdateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.runtime_config.feature_flags import FeatureFlagOverrideService
from aion_brain.runtime_config.profiles import ConfigProfileService
from aion_brain.runtime_config.snapshots import ConfigSnapshotService
from aion_brain.runtime_config.status import RuntimeConfigStatusService
from aion_brain.runtime_config.validator import ConfigValidator

router = APIRouter(prefix="/brain/runtime-config", tags=["runtime-config"])


def get_profile_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ConfigProfileService:
    return container.config_profile_service


def get_feature_override_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> FeatureFlagOverrideService:
    return container.feature_flag_override_service


def get_snapshot_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ConfigSnapshotService:
    return container.config_snapshot_service


def get_config_validator(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ConfigValidator:
    return container.config_validator


def get_status_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> RuntimeConfigStatusService:
    return container.runtime_config_status_service


@router.post("/profiles", response_model=ConfigProfile)
def create_profile(
    body: ConfigProfileCreateRequest,
    service: Annotated[ConfigProfileService, Depends(get_profile_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConfigProfile:
    """Create one runtime config profile."""
    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
            "metadata": {**body.metadata, **_actor_metadata(actor_context)},
        }
    )
    return service.create_profile(request)


@router.get("/profiles/{config_profile_id}", response_model=ConfigProfile)
def get_profile(
    config_profile_id: str,
    service: Annotated[ConfigProfileService, Depends(get_profile_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConfigProfile:
    """Return one runtime config profile."""
    profile = service.get_profile(config_profile_id, _scope(scope, actor_context))
    if profile is None:
        raise HTTPException(status_code=404, detail="config_profile_not_found")
    return profile


@router.get("/profiles", response_model=list[ConfigProfile])
def list_profiles(
    service: Annotated[ConfigProfileService, Depends(get_profile_service)],
    status: str | None = None,
    profile_type: str | None = None,
) -> list[ConfigProfile]:
    """List runtime config profiles."""
    return service.list_profiles(status=status, profile_type=profile_type)


@router.post("/profiles/{config_profile_id}/activate", response_model=ConfigProfile)
def activate_profile(
    config_profile_id: str,
    body: StatusUpdateRequest,
    service: Annotated[ConfigProfileService, Depends(get_profile_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConfigProfile:
    """Activate a profile for metadata use."""
    return service.activate_profile(
        config_profile_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


@router.post("/profiles/{config_profile_id}/disable", response_model=ConfigProfile)
def disable_profile(
    config_profile_id: str,
    body: StatusUpdateRequest,
    service: Annotated[ConfigProfileService, Depends(get_profile_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConfigProfile:
    """Disable a profile."""
    return service.disable_profile(
        config_profile_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


@router.post("/feature-overrides", response_model=FeatureFlagOverride)
def create_feature_override(
    body: FeatureFlagOverrideRequest,
    service: Annotated[FeatureFlagOverrideService, Depends(get_feature_override_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> FeatureFlagOverride:
    """Create one feature flag override."""
    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "created_by": body.created_by or actor_context.actor_id,
            "metadata": {**body.metadata, **_actor_metadata(actor_context)},
        }
    )
    return service.create_override(request)


@router.get("/feature-overrides", response_model=list[FeatureFlagOverride])
def list_feature_overrides(
    service: Annotated[FeatureFlagOverrideService, Depends(get_feature_override_service)],
    feature_key: str | None = None,
    status: str | None = None,
) -> list[FeatureFlagOverride]:
    """List feature flag overrides."""
    return service.list_overrides(feature_key=feature_key, status=status)


@router.post("/feature-overrides/{feature_override_id}/disable", response_model=FeatureFlagOverride)
def disable_feature_override(
    feature_override_id: str,
    body: StatusUpdateRequest,
    service: Annotated[FeatureFlagOverrideService, Depends(get_feature_override_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> FeatureFlagOverride:
    """Disable one feature flag override."""
    return service.disable_override(
        feature_override_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


@router.post("/snapshots", response_model=ConfigSnapshot)
def create_snapshot(
    body: ConfigSnapshotRequest,
    service: Annotated[ConfigSnapshotService, Depends(get_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConfigSnapshot:
    """Create a redacted runtime config snapshot."""
    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
            "metadata": {**body.metadata, **_actor_metadata(actor_context)},
        }
    )
    return service.create_snapshot(request)


@router.get("/snapshots/{config_snapshot_id}", response_model=ConfigSnapshot)
def get_snapshot(
    config_snapshot_id: str,
    service: Annotated[ConfigSnapshotService, Depends(get_snapshot_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConfigSnapshot:
    """Return one runtime config snapshot."""
    snapshot = service.get_snapshot(config_snapshot_id, _scope(scope, actor_context))
    if snapshot is None:
        raise HTTPException(status_code=404, detail="config_snapshot_not_found")
    return snapshot


@router.get("/snapshots", response_model=list[ConfigSnapshot])
def list_snapshots(
    service: Annotated[ConfigSnapshotService, Depends(get_snapshot_service)],
    snapshot_type: str | None = None,
    limit: int = 50,
) -> list[ConfigSnapshot]:
    """List runtime config snapshots."""
    return service.list_snapshots(snapshot_type=snapshot_type, limit=limit)


@router.post("/snapshots/compare")
def compare_snapshots(
    body: SnapshotCompareRequest,
    service: Annotated[ConfigSnapshotService, Depends(get_snapshot_service)],
) -> dict[str, object]:
    """Compare two runtime config snapshots."""
    return service.compare(body.snapshot_id_a, body.snapshot_id_b)


@router.post("/validate", response_model=ConfigValidationRun)
def validate_config(
    body: ConfigValidationRequest,
    service: Annotated[ConfigValidator, Depends(get_config_validator)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConfigValidationRun:
    """Validate runtime configuration posture."""
    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
            "metadata": {**body.metadata, **_actor_metadata(actor_context)},
        }
    )
    return service.validate(request)


@router.get("/status", response_model=RuntimeConfigStatus)
def runtime_config_status(
    service: Annotated[RuntimeConfigStatusService, Depends(get_status_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RuntimeConfigStatus:
    """Return runtime config status."""
    return service.status(_scope(scope, actor_context))


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope


def _actor_metadata(actor_context: ActorContext) -> dict[str, object]:
    return {
        "actor_context": {
            "actor_id": actor_context.actor_id,
            "workspace_id": actor_context.workspace_id,
            "security_scope": actor_context.security_scope,
        }
    }
