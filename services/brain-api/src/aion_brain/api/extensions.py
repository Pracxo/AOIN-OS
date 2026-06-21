"""Extension Registry API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.extension_compatibility import (
    ExtensionCompatibilityRequest,
    ExtensionCompatibilityRun,
)
from aion_brain.contracts.extensions import (
    ExtensionArchiveRequest,
    ExtensionCapabilityDeclaration,
    ExtensionDependencyDeclaration,
    ExtensionInstallPlan,
    ExtensionInstallPlanCreateRequest,
    ExtensionIntakeRequest,
    ExtensionIntakeRun,
    ExtensionManifest,
    ExtensionPackage,
    ExtensionQuery,
    ExtensionQueryResult,
    ExtensionReview,
    ExtensionReviewRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.extensions.policy import authorize_extension_action
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/extensions", tags=["extensions"])


@router.post("/manifests/validate")
def validate_manifest(
    body: ExtensionManifest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, Any]:
    """Validate a manifest without persisting or loading code."""

    try:
        authorize_extension_action(
            container.policy_adapter,
            "extension.manifest.validate",
            actor_context.security_scope,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            trace_id=actor_context.trace_id,
            resource_type="extension_manifest",
            risk_level="low",
            context={"extension_key": body.extension_key},
        )
        return container.extension_manifest_validator.validate(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/intake", response_model=ExtensionIntakeRun)
def intake_manifest(
    body: ExtensionIntakeRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExtensionIntakeRun:
    """Run dry-run or controlled metadata intake."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.extension_intake_service.intake(request)


@router.get("/intake-runs/{extension_intake_id}", response_model=ExtensionIntakeRun)
def get_intake_run(
    extension_intake_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExtensionIntakeRun:
    run = container.extension_intake_service.get_intake_run(
        extension_intake_id,
        _scope(scope, actor_context),
    )
    if run is None:
        raise HTTPException(status_code=404, detail="extension_intake_run_not_found")
    return run


@router.get("/packages/{extension_package_id}", response_model=ExtensionPackage)
def get_package(
    extension_package_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExtensionPackage:
    package = container.extension_package_service.with_actor_context(actor_context).get_package(
        extension_package_id, _scope(scope, actor_context)
    )
    if package is None:
        raise HTTPException(status_code=404, detail="extension_package_not_found")
    return package


@router.post("/query", response_model=ExtensionQueryResult)
def query_extensions(
    body: ExtensionQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExtensionQueryResult:
    request = body.model_copy(update={"scope": body.scope or actor_context.security_scope})
    return container.extension_query_service.query(request)


@router.post("/packages/{extension_package_id}/archive", response_model=ExtensionPackage)
def archive_package(
    extension_package_id: str,
    body: ExtensionArchiveRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExtensionPackage:
    return container.extension_package_service.with_actor_context(actor_context).archive(
        extension_package_id,
        _scope(scope, actor_context),
        body,
    )


@router.delete("/packages/{extension_package_id}")
def delete_package(
    extension_package_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    package = container.extension_package_service.with_actor_context(actor_context).soft_delete(
        extension_package_id,
        _scope(scope, actor_context),
        actor_context.actor_id,
    )
    return {"deleted": True, "extension_package_id": package.extension_package_id}


@router.get(
    "/packages/{extension_package_id}/capabilities",
    response_model=list[ExtensionCapabilityDeclaration],
)
def list_capability_declarations(
    extension_package_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ExtensionCapabilityDeclaration]:
    return container.extension_capability_service.list_for_package(
        extension_package_id,
        _scope(scope, actor_context),
    )


@router.get(
    "/packages/{extension_package_id}/dependencies",
    response_model=list[ExtensionDependencyDeclaration],
)
def list_dependency_declarations(
    extension_package_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[ExtensionDependencyDeclaration]:
    return container.extension_dependency_service.list_for_package(
        extension_package_id,
        _scope(scope, actor_context),
    )


@router.post("/compatibility/check", response_model=ExtensionCompatibilityRun)
def check_compatibility(
    body: ExtensionCompatibilityRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExtensionCompatibilityRun:
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.extension_compatibility_gate.check(request)


@router.get("/compatibility/{extension_compatibility_id}", response_model=ExtensionCompatibilityRun)
def get_compatibility(
    extension_compatibility_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExtensionCompatibilityRun:
    run = container.extension_compatibility_gate.get(
        extension_compatibility_id,
        _scope(scope, actor_context),
    )
    if run is None:
        raise HTTPException(status_code=404, detail="extension_compatibility_not_found")
    return run


@router.post("/packages/{extension_package_id}/review", response_model=ExtensionReview)
def review_package(
    extension_package_id: str,
    body: ExtensionReviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExtensionReview:
    request = body.model_copy(
        update={
            "extension_package_id": extension_package_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
        }
    )
    try:
        return container.extension_review_service.review(request, _scope(scope, actor_context))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/reviews", response_model=list[ExtensionReview])
def list_reviews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    extension_package_id: str | None = None,
    decision: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ExtensionReview]:
    return container.extension_review_service.list_reviews(
        _scope(scope, actor_context),
        extension_package_id=extension_package_id,
        decision=decision,
        limit=limit,
    )


@router.post("/packages/{extension_package_id}/install-plan", response_model=ExtensionInstallPlan)
def create_install_plan(
    extension_package_id: str,
    body: ExtensionInstallPlanCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExtensionInstallPlan:
    package = container.extension_package_service.with_actor_context(actor_context).require_package(
        extension_package_id, body.scope or actor_context.security_scope
    )
    return container.extension_install_plan_service.create_plan(
        package,
        scope=body.scope or actor_context.security_scope,
        created_by=body.created_by or actor_context.actor_id,
    )


@router.get("/install-plans/{install_plan_id}", response_model=ExtensionInstallPlan)
def get_install_plan(
    install_plan_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExtensionInstallPlan:
    return container.extension_install_plan_service.require_plan(
        install_plan_id,
        _scope(scope, actor_context),
    )


@router.get("/install-plans", response_model=list[ExtensionInstallPlan])
def list_install_plans(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    extension_package_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ExtensionInstallPlan]:
    return container.extension_install_plan_service.list_plans(
        _scope(scope, actor_context),
        status=status,
        extension_package_id=extension_package_id,
        limit=limit,
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]
