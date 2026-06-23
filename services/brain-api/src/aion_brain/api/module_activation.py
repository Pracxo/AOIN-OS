"""Module activation request gate API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.module_activation import (
    ActivationBlocker,
    ActivationGateRun,
    ActivationGateRunRequest,
    ActivationMutationRequest,
    ActivationPlan,
    ActivationPlanCreateRequest,
    ActivationReview,
    ActivationReviewRequest,
    ModuleActivationCreateRequest,
    ModuleActivationQuery,
    ModuleActivationQueryResult,
    ModuleActivationRequest,
    RuntimeRegistrationPreview,
    RuntimeRegistrationPreviewCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["module-activation"])


@router.post("/brain/module-activation/requests", response_model=ModuleActivationRequest)
def create_activation_request(
    body: ModuleActivationCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleActivationRequest:
    """Create a metadata-only future activation request."""
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.module_activation_request_service.with_actor_context(
        actor_context
    ).create_request(request)


@router.get("/brain/module-activation/requests", response_model=list[ModuleActivationRequest])
def list_activation_requests(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    module_slot_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModuleActivationRequest]:
    """List activation request metadata."""
    return container.module_activation_request_service.with_actor_context(
        actor_context
    ).list_requests(
        _scope(scope, actor_context),
        status=status,
        module_slot_id=module_slot_id,
        limit=limit,
    )


@router.post("/brain/module-activation/query", response_model=ModuleActivationQueryResult)
def query_activation_records(
    body: ModuleActivationQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleActivationQueryResult:
    """Query activation gate records."""
    request = body.model_copy(update={"scope": body.scope or actor_context.security_scope})
    return container.module_activation_query_service.query(request)


@router.get(
    "/brain/module-activation/requests/{activation_request_id}",
    response_model=ModuleActivationRequest,
)
def get_activation_request(
    activation_request_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModuleActivationRequest:
    """Return activation request metadata."""
    return container.module_activation_request_service.with_actor_context(
        actor_context
    ).require_request(activation_request_id, _scope(scope, actor_context))


@router.post(
    "/brain/module-activation/requests/{activation_request_id}/archive",
    response_model=ModuleActivationRequest,
)
def archive_activation_request(
    activation_request_id: str,
    body: ActivationMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleActivationRequest:
    """Archive activation request metadata."""
    return container.module_activation_request_service.with_actor_context(
        actor_context
    ).archive_request(
        activation_request_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


@router.delete("/brain/module-activation/requests/{activation_request_id}")
def delete_activation_request(
    activation_request_id: str,
    body: ActivationMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Soft delete activation request metadata."""
    deleted = container.module_activation_request_service.with_actor_context(
        actor_context
    ).soft_delete_request(
        activation_request_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )
    return {"deleted": deleted, "activation_request_id": activation_request_id}


@router.post(
    "/brain/module-activation/requests/{activation_request_id}/gate",
    response_model=ActivationGateRun,
)
def run_activation_gate(
    activation_request_id: str,
    body: ActivationGateRunRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActivationGateRun:
    """Run activation gate checks without activation."""
    return container.activation_gate_service.run_gate(
        activation_request_id,
        body.scope or actor_context.security_scope,
        mode=body.mode,
        created_by=body.created_by or actor_context.actor_id,
    )


@router.get(
    "/brain/module-activation/requests/{activation_request_id}/gate-runs",
    response_model=list[ActivationGateRun],
)
def list_activation_gate_runs(
    activation_request_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ActivationGateRun]:
    """List gate runs for one activation request."""
    return container.activation_gate_service.list_gate_runs(
        _scope(scope, actor_context),
        activation_request_id=activation_request_id,
        status=status,
        limit=limit,
    )


@router.get("/brain/module-activation/blockers", response_model=list[ActivationBlocker])
def list_activation_blockers(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    activation_request_id: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ActivationBlocker]:
    """List activation blockers."""
    return container.activation_blocker_service.list_blockers(
        _scope(scope, actor_context),
        activation_request_id=activation_request_id,
        status=status,
        severity=severity,
        limit=limit,
    )


@router.post(
    "/brain/module-activation/blockers/{activation_blocker_id}/dismiss",
    response_model=ActivationBlocker,
)
def dismiss_activation_blocker(
    activation_blocker_id: str,
    body: ActivationMutationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActivationBlocker:
    """Dismiss a blocker record without activating anything."""
    return container.activation_blocker_service.dismiss_blocker(
        activation_blocker_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


@router.post("/brain/module-activation/reviews", response_model=ActivationReview)
def create_activation_review(
    body: ActivationReviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ActivationReview:
    """Record an activation review without changing runtime behavior."""
    request = body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "reviewer_id": body.reviewer_id or actor_context.actor_id,
        }
    )
    return container.activation_review_service.review(request, _scope(scope, actor_context))


@router.get("/brain/module-activation/reviews", response_model=list[ActivationReview])
def list_activation_reviews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    activation_request_id: str | None = None,
    decision: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ActivationReview]:
    """List activation reviews."""
    return container.activation_review_service.list_reviews(
        _scope(scope, actor_context),
        activation_request_id=activation_request_id,
        decision=decision,
        limit=limit,
    )


@router.post(
    "/brain/module-activation/requests/{activation_request_id}/plans",
    response_model=ActivationPlan,
)
def create_activation_plan(
    activation_request_id: str,
    body: ActivationPlanCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActivationPlan:
    """Create a non-executable activation plan."""
    return container.activation_plan_service.create_plan(
        activation_request_id,
        body.scope or actor_context.security_scope,
        created_by=body.created_by or actor_context.actor_id,
    )


@router.get("/brain/module-activation/plans", response_model=list[ActivationPlan])
def list_activation_plans(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    module_slot_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ActivationPlan]:
    """List non-executable activation plans."""
    return container.activation_plan_service.list_plans(
        _scope(scope, actor_context),
        status=status,
        module_slot_id=module_slot_id,
        limit=limit,
    )


@router.get("/brain/module-activation/plans/{activation_plan_id}", response_model=ActivationPlan)
def get_activation_plan(
    activation_plan_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ActivationPlan:
    """Return one non-executable activation plan."""
    return container.activation_plan_service.get_plan(
        activation_plan_id,
        _scope(scope, actor_context),
    )


@router.post(
    "/brain/module-activation/requests/{activation_request_id}/runtime-registration-preview",
    response_model=RuntimeRegistrationPreview,
)
def create_runtime_registration_preview(
    activation_request_id: str,
    body: RuntimeRegistrationPreviewCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RuntimeRegistrationPreview:
    """Create a runtime registration preview without runtime mutation."""
    return container.runtime_registration_preview_service.create_preview(
        activation_request_id,
        body.scope or actor_context.security_scope,
        created_by=body.created_by or actor_context.actor_id,
    )


@router.get(
    "/brain/module-activation/runtime-registration-previews",
    response_model=list[RuntimeRegistrationPreview],
)
def list_runtime_registration_previews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    activation_request_id: str | None = None,
    module_slot_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[RuntimeRegistrationPreview]:
    """List runtime registration previews."""
    return container.runtime_registration_preview_service.list_previews(
        _scope(scope, actor_context),
        activation_request_id=activation_request_id,
        module_slot_id=module_slot_id,
        status=status,
        limit=limit,
    )


@router.get(
    "/brain/module-activation/runtime-registration-previews/{registration_preview_id}",
    response_model=RuntimeRegistrationPreview,
)
def get_runtime_registration_preview(
    registration_preview_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RuntimeRegistrationPreview:
    """Return one runtime registration preview."""
    return container.runtime_registration_preview_service.get_preview(
        registration_preview_id,
        _scope(scope, actor_context),
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


__all__ = ["router"]
