"""Release package API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.release_package import (
    ReleaseHandoffReport,
    ReleasePackage,
    ReleasePackageRequest,
    ReleasePackageValidation,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.release_package.packager import ReleasePackager

router = APIRouter(prefix="/brain/release-package", tags=["release-package"])


def get_release_packager(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ReleasePackager:
    """Return release packager service."""
    return container.release_packager


@router.post("/create", response_model=ReleasePackage)
def create_release_package(
    body: ReleasePackageRequest,
    request: Request,
    service: Annotated[ReleasePackager, Depends(get_release_packager)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ReleasePackage:
    """Create or dry-run a local release package."""
    body = body.model_copy(
        update={
            "created_by": body.created_by or actor_context.actor_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
        }
    )
    return service.package(body, app=request.app)


@router.get("/{release_package_id}", response_model=ReleasePackage)
def get_release_package(
    release_package_id: str,
    service: Annotated[ReleasePackager, Depends(get_release_packager)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReleasePackage:
    """Return one release package."""
    package = service.get(release_package_id, _scope(scope, actor_context))
    if package is None:
        raise HTTPException(status_code=404, detail="release_package_not_found")
    return package


@router.get("", response_model=list[ReleasePackage])
def list_release_packages(
    service: Annotated[ReleasePackager, Depends(get_release_packager)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    version: str | None = None,
    status: str | None = None,
) -> list[ReleasePackage]:
    """List release packages."""
    return service.list(_scope(scope, actor_context), version=version, status=status)


@router.post("/{release_package_id}/validate", response_model=ReleasePackageValidation)
def validate_release_package(
    release_package_id: str,
    service: Annotated[ReleasePackager, Depends(get_release_packager)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReleasePackageValidation:
    """Return validation for one release package after policy authorization."""
    return service.validate_package(release_package_id, _scope(scope, actor_context))


@router.get("/{release_package_id}/handoff", response_model=ReleaseHandoffReport)
def get_release_handoff(
    release_package_id: str,
    service: Annotated[ReleasePackager, Depends(get_release_packager)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReleaseHandoffReport:
    """Return final local handoff report for a release package."""
    return service.handoff(release_package_id, _scope(scope, actor_context))


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value
