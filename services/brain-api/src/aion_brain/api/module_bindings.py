"""Module slot and capability binding API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.capability_bindings import (
    BindingConflict,
    BindingMutationRequest,
    BindingValidationRequest,
    BindingValidationRun,
    CapabilityBinding,
    CapabilityBindingCreateRequest,
    ModuleBindingQuery,
    ModuleBindingQueryResult,
    ModuleMountPlan,
    MountPlanCreateRequest,
    RouteBindingPreview,
    RoutePreviewCreateRequest,
)
from aion_brain.contracts.module_slots import (
    ModuleSlot,
    ModuleSlotArchiveRequest,
    ModuleSlotCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["module-bindings"])


@router.post("/brain/module-slots", response_model=ModuleSlot)
def create_module_slot(
    body: ModuleSlotCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleSlot:
    """Create inactive module slot metadata."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.module_slot_service.with_actor_context(actor_context).create_slot(request)


@router.get("/brain/module-slots", response_model=list[ModuleSlot])
def list_module_slots(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    slot_type: str | None = None,
    extension_package_id: str | None = None,
    include_deleted: bool = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModuleSlot]:
    """List inactive module slots."""

    return container.module_slot_service.with_actor_context(actor_context).list_slots(
        _scope(scope, actor_context),
        status=status,
        slot_type=slot_type,
        extension_package_id=extension_package_id,
        include_deleted=include_deleted,
        limit=limit,
    )


@router.get("/brain/module-slots/{module_slot_id}", response_model=ModuleSlot)
def get_module_slot(
    module_slot_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModuleSlot:
    """Return inactive module slot metadata."""

    return container.module_slot_service.with_actor_context(actor_context).require_slot(
        module_slot_id,
        _scope(scope, actor_context),
    )


@router.post("/brain/module-slots/{module_slot_id}/archive", response_model=ModuleSlot)
def archive_module_slot(
    module_slot_id: str,
    body: ModuleSlotArchiveRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModuleSlot:
    """Archive inactive module slot metadata."""

    request = body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id})
    return container.module_slot_service.with_actor_context(actor_context).archive_slot(
        module_slot_id,
        _scope(scope, actor_context),
        request,
    )


@router.delete("/brain/module-slots/{module_slot_id}")
def delete_module_slot(
    module_slot_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    """Soft-delete inactive module slot metadata."""

    slot = container.module_slot_service.with_actor_context(actor_context).soft_delete_slot(
        module_slot_id,
        _scope(scope, actor_context),
        actor_context.actor_id,
    )
    return {"deleted": True, "module_slot_id": slot.module_slot_id}


@router.post("/brain/capability-bindings", response_model=CapabilityBinding)
def create_capability_binding(
    body: CapabilityBindingCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CapabilityBinding:
    """Create inactive capability binding metadata."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.capability_binding_service.with_actor_context(actor_context).create_binding(
        request
    )


@router.get("/brain/capability-bindings", response_model=list[CapabilityBinding])
def list_capability_bindings(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    module_slot_id: str | None = None,
    status: str | None = None,
    capability_type: str | None = None,
    risk_level: str | None = None,
    extension_package_id: str | None = None,
    include_deleted: bool = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[CapabilityBinding]:
    """List inactive capability bindings."""

    return container.capability_binding_service.with_actor_context(actor_context).list_bindings(
        _scope(scope, actor_context),
        module_slot_id=module_slot_id,
        status=status,
        capability_type=capability_type,
        risk_level=risk_level,
        extension_package_id=extension_package_id,
        include_deleted=include_deleted,
        limit=limit,
    )


@router.get("/brain/capability-bindings/{capability_binding_id}", response_model=CapabilityBinding)
def get_capability_binding(
    capability_binding_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> CapabilityBinding:
    """Return inactive capability binding metadata."""

    return container.capability_binding_service.with_actor_context(actor_context).require_binding(
        capability_binding_id,
        _scope(scope, actor_context),
    )


@router.post(
    "/brain/capability-bindings/{capability_binding_id}/disable",
    response_model=CapabilityBinding,
)
def disable_capability_binding(
    capability_binding_id: str,
    body: BindingMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> CapabilityBinding:
    """Disable inactive capability binding metadata."""

    request = body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id})
    return container.capability_binding_service.with_actor_context(actor_context).disable_binding(
        capability_binding_id, _scope(scope, actor_context), request
    )


@router.post("/brain/module-bindings/validate", response_model=BindingValidationRun)
def validate_module_bindings(
    body: BindingValidationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BindingValidationRun:
    """Validate module slots and capability bindings without activation."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.binding_validator.validate(request)


@router.get(
    "/brain/module-bindings/validations/{binding_validation_id}",
    response_model=BindingValidationRun,
)
def get_binding_validation(
    binding_validation_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BindingValidationRun:
    """Return a binding validation run."""

    run = container.binding_validator.get_validation_run(
        binding_validation_id,
        _scope(scope, actor_context),
    )
    if run is None:
        from aion_brain.api_support.errors import AIONNotFoundException

        raise AIONNotFoundException("binding_validation_not_found")
    return run


@router.get("/brain/module-bindings/conflicts", response_model=list[BindingConflict])
def list_binding_conflicts(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    module_slot_id: str | None = None,
    capability_binding_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[BindingConflict]:
    """List binding conflicts."""

    return container.binding_conflict_service.list_conflicts(
        _scope(scope, actor_context),
        status=status,
        severity=severity,
        module_slot_id=module_slot_id,
        capability_binding_id=capability_binding_id,
        limit=limit,
    )


@router.post(
    "/brain/module-bindings/conflicts/{binding_conflict_id}/dismiss",
    response_model=BindingConflict,
)
def dismiss_binding_conflict(
    binding_conflict_id: str,
    body: BindingMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BindingConflict:
    """Dismiss a binding conflict."""

    request = body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id})
    return container.binding_conflict_service.dismiss_conflict(
        binding_conflict_id,
        _scope(scope, actor_context),
        request,
    )


@router.post("/brain/module-bindings/mount-plans", response_model=ModuleMountPlan)
def create_mount_plan(
    body: MountPlanCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleMountPlan:
    """Create a non-executable module mount plan."""

    request = body.model_copy(
        update={
            "scope": body.scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.module_mount_plan_service.create_plan(request)


@router.get("/brain/module-bindings/mount-plans", response_model=list[ModuleMountPlan])
def list_mount_plans(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    module_slot_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModuleMountPlan]:
    """List non-executable module mount plans."""

    return container.module_mount_plan_service.list_plans(
        _scope(scope, actor_context),
        status=status,
        module_slot_id=module_slot_id,
        limit=limit,
    )


@router.get("/brain/module-bindings/mount-plans/{mount_plan_id}", response_model=ModuleMountPlan)
def get_mount_plan(
    mount_plan_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModuleMountPlan:
    """Return one non-executable module mount plan."""

    return container.module_mount_plan_service.require_plan(
        mount_plan_id,
        _scope(scope, actor_context),
    )


@router.post("/brain/module-bindings/route-previews", response_model=RouteBindingPreview)
def create_route_preview(
    body: RoutePreviewCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RouteBindingPreview:
    """Create a route binding preview without route registration."""

    request = body.model_copy(
        update={
            "scope": body.scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.route_binding_preview_service.create_preview(request)


@router.get("/brain/module-bindings/route-previews", response_model=list[RouteBindingPreview])
def list_route_previews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    module_slot_id: str | None = None,
    capability_binding_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[RouteBindingPreview]:
    """List route binding previews."""

    return container.route_binding_preview_service.list_previews(
        _scope(scope, actor_context),
        module_slot_id=module_slot_id,
        capability_binding_id=capability_binding_id,
        status=status,
        limit=limit,
    )


@router.post("/brain/module-bindings/query", response_model=ModuleBindingQueryResult)
def query_module_bindings(
    body: ModuleBindingQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleBindingQueryResult:
    """Query module binding registry records."""

    request = body.model_copy(update={"scope": body.scope or actor_context.security_scope})
    return container.module_binding_query_service.query(request)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]
