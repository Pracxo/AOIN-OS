"""Version manifest, feature registry, compatibility, and artifact APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.compatibility import (
    CompatibilityMatrix,
    MigrationBaseline,
    ReleaseArtifactManifest,
    SDKCompatibilityReport,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.versioning import FeatureRegistryEntry, VersionManifest
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.versioning.artifacts import ReleaseArtifactService
from aion_brain.versioning.compatibility import CompatibilityMatrixService, SDKCompatibilityService
from aion_brain.versioning.features import FeatureRegistryService
from aion_brain.versioning.manifest import VersionManifestService
from aion_brain.versioning.migrations import MigrationBaselineService

router = APIRouter(prefix="/brain/versioning", tags=["versioning"])


class ManifestCreateRequest(BaseModel):
    """Create version manifest request."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    created_by: str | None = None
    owner_scope: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("owner_scope", "scope"),
    )


class ManifestFreezeRequest(BaseModel):
    """Freeze version manifest request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)
    owner_scope: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("owner_scope", "scope"),
    )


class SeedFeaturesRequest(BaseModel):
    """Seed feature defaults request."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = True
    owner_scope: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("owner_scope", "scope"),
    )


class GenerateCompatibilityRequest(BaseModel):
    """Generate compatibility matrix request."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    owner_scope: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("owner_scope", "scope"),
    )


class GenerateMigrationBaselineRequest(BaseModel):
    """Generate migration baseline request."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(min_length=1)
    owner_scope: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("owner_scope", "scope"),
    )


class GenerateReleaseArtifactsRequest(BaseModel):
    """Generate release artifacts request."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    created_by: str | None = None
    owner_scope: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("owner_scope", "scope"),
    )


def get_version_manifest_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> VersionManifestService:
    """Return version manifest service."""
    return container.version_manifest_service


def get_feature_registry_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> FeatureRegistryService:
    """Return feature registry service."""
    return container.feature_registry_service


def get_compatibility_matrix_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> CompatibilityMatrixService:
    """Return compatibility matrix service."""
    return container.compatibility_matrix_service


def get_migration_baseline_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> MigrationBaselineService:
    """Return migration baseline service."""
    return container.migration_baseline_service


def get_release_artifact_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ReleaseArtifactService:
    """Return release artifact service."""
    return container.release_artifact_service


def get_sdk_compatibility_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> SDKCompatibilityService:
    """Return SDK compatibility service."""
    return container.sdk_compatibility_service


@router.post("/manifests", response_model=VersionManifest)
def create_manifest(
    body: ManifestCreateRequest,
    request: Request,
    service: Annotated[VersionManifestService, Depends(get_version_manifest_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> VersionManifest:
    """Create a version manifest."""
    return service.create_manifest(
        body.version,
        body.created_by or actor_context.actor_id,
        _scope(body.owner_scope, actor_context),
        app=request.app,
    )


@router.get("/manifests/{version}", response_model=VersionManifest)
def get_manifest(
    version: str,
    service: Annotated[VersionManifestService, Depends(get_version_manifest_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> VersionManifest:
    """Return a version manifest."""
    manifest = service.get_manifest(version, _scope(scope, actor_context))
    if manifest is None:
        raise HTTPException(status_code=404, detail="version_manifest_not_found")
    return manifest


@router.get("/manifests", response_model=list[VersionManifest])
def list_manifests(
    service: Annotated[VersionManifestService, Depends(get_version_manifest_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
) -> list[VersionManifest]:
    """List version manifests."""
    return service.list_manifests(_scope(scope, actor_context), status=status)


@router.post("/manifests/{version}/freeze", response_model=VersionManifest)
def freeze_manifest(
    version: str,
    body: ManifestFreezeRequest,
    service: Annotated[VersionManifestService, Depends(get_version_manifest_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> VersionManifest:
    """Freeze a version manifest."""
    return service.freeze_manifest(
        version,
        body.actor_id or actor_context.actor_id,
        body.reason,
        _scope(body.owner_scope, actor_context),
    )


@router.post("/features/seed-defaults")
def seed_feature_defaults(
    body: SeedFeaturesRequest,
    service: Annotated[FeatureRegistryService, Depends(get_feature_registry_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Seed default feature entries."""
    return service.seed_defaults(_scope(body.owner_scope, actor_context), dry_run=body.dry_run)


@router.get("/features", response_model=list[FeatureRegistryEntry])
def list_features(
    service: Annotated[FeatureRegistryService, Depends(get_feature_registry_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    category: str | None = None,
) -> list[FeatureRegistryEntry]:
    """List feature registry entries."""
    return service.list_features(_scope(scope, actor_context), status=status, category=category)


@router.post("/features", response_model=FeatureRegistryEntry)
def create_feature(
    body: FeatureRegistryEntry,
    service: Annotated[FeatureRegistryService, Depends(get_feature_registry_service)],
) -> FeatureRegistryEntry:
    """Create a feature registry entry."""
    return service.create_feature(body)


@router.post("/features/{feature_key}/deprecate", response_model=FeatureRegistryEntry)
def deprecate_feature(
    feature_key: str,
    body: ManifestFreezeRequest,
    service: Annotated[FeatureRegistryService, Depends(get_feature_registry_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> FeatureRegistryEntry:
    """Deprecate a feature entry."""
    return service.deprecate_feature(
        feature_key,
        _scope(body.owner_scope, actor_context),
        actor_id=body.actor_id or actor_context.actor_id,
        reason=body.reason,
    )


@router.post("/compatibility/generate", response_model=CompatibilityMatrix)
def generate_compatibility(
    body: GenerateCompatibilityRequest,
    service: Annotated[CompatibilityMatrixService, Depends(get_compatibility_matrix_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CompatibilityMatrix:
    """Generate compatibility matrix."""
    return service.generate(body.version, _scope(body.owner_scope, actor_context))


@router.get("/compatibility/{version}", response_model=CompatibilityMatrix)
def get_compatibility(
    version: str,
    service: Annotated[CompatibilityMatrixService, Depends(get_compatibility_matrix_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> CompatibilityMatrix:
    """Return compatibility matrix."""
    matrix = service.get(version, _scope(scope, actor_context))
    if matrix is None:
        raise HTTPException(status_code=404, detail="compatibility_matrix_not_found")
    return matrix


@router.post("/migration-baseline/generate", response_model=MigrationBaseline)
def generate_migration_baseline(
    body: GenerateMigrationBaselineRequest,
    service: Annotated[MigrationBaselineService, Depends(get_migration_baseline_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MigrationBaseline:
    """Generate migration baseline."""
    return service.generate(body.schema_version, _scope(body.owner_scope, actor_context))


@router.post("/release-artifacts/generate", response_model=ReleaseArtifactManifest)
def generate_release_artifacts(
    body: GenerateReleaseArtifactsRequest,
    service: Annotated[ReleaseArtifactService, Depends(get_release_artifact_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ReleaseArtifactManifest:
    """Generate release artifact manifest."""
    return service.generate(
        body.version,
        body.created_by or actor_context.actor_id,
        _scope(body.owner_scope, actor_context),
    )


@router.get("/sdk-compatibility", response_model=SDKCompatibilityReport)
def sdk_compatibility(
    service: Annotated[SDKCompatibilityService, Depends(get_sdk_compatibility_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SDKCompatibilityReport:
    """Return SDK/API compatibility report."""
    return service.check(_scope(scope, actor_context))


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value
