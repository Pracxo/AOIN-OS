"""Model provider hardening API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.model_provider_hardening import (
    ModelProviderBlocker,
    ModelProviderBlockerDismissRequest,
    ModelProviderProfile,
    ModelProviderProfileCreateRequest,
    ModelProviderProfileSeedRequest,
    ModelProviderReadiness,
    ModelProviderReadinessRequest,
    ModelProviderSimulation,
    ModelProviderSimulationRequest,
    PromptEgressPreview,
    PromptEgressPreviewRequest,
    ProviderHardeningQuery,
    ProviderHardeningQueryResult,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["model-provider-hardening"])


@router.post("/brain/model-providers/profiles", response_model=ModelProviderProfile)
def create_provider_profile(
    body: ModelProviderProfileCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProviderProfile:
    """Create provider-readiness metadata without enabling a provider."""

    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.model_provider_profile_service.create_profile(request)


@router.post("/brain/model-providers/profiles/seed-defaults")
def seed_provider_profiles(
    body: ModelProviderProfileSeedRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Seed or preview safe default provider-hardening profiles."""

    request = body.model_copy(
        update={
            "scope": body.scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.model_provider_profile_service.seed_default_profiles(request)


@router.get("/brain/model-providers/profiles", response_model=list[ModelProviderProfile])
def list_provider_profiles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    provider_key: str | None = None,
    status: str | None = None,
    risk_level: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModelProviderProfile]:
    """List provider profiles."""

    return container.model_provider_profile_service.list_profiles(
        _scope(scope, actor_context),
        provider_key=provider_key,
        status=status,
        risk_level=risk_level,
        limit=limit,
    )


@router.get(
    "/brain/model-providers/profiles/{provider_profile_id}",
    response_model=ModelProviderProfile,
)
def get_provider_profile(
    provider_profile_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModelProviderProfile:
    """Return one provider profile."""

    return container.model_provider_profile_service.get_profile(
        provider_profile_id,
        _scope(scope, actor_context),
    )


@router.post("/brain/model-providers/egress-preview", response_model=PromptEgressPreview)
def create_egress_preview(
    body: PromptEgressPreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PromptEgressPreview:
    """Create a local-only prompt egress preview."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.prompt_egress_guard.preview(request)


@router.post("/brain/model-providers/simulate", response_model=ModelProviderSimulation)
def simulate_provider(
    body: ModelProviderSimulationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProviderSimulation:
    """Run a deterministic dry-run provider simulation."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.model_provider_simulator.simulate(request)


@router.post("/brain/model-providers/readiness", response_model=ModelProviderReadiness)
def assess_provider_readiness(
    body: ModelProviderReadinessRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProviderReadiness:
    """Assess provider readiness without enabling a provider."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.model_provider_readiness_service.assess(request)


@router.get("/brain/model-providers/blockers", response_model=list[ModelProviderBlocker])
def list_provider_blockers(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    provider_key: str | None = None,
    status: str | None = "open",
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModelProviderBlocker]:
    """List provider hardening blockers."""

    return container.model_provider_blocker_service.list_blockers(
        _scope(scope, actor_context),
        provider_key=provider_key,
        status=status,
        severity=severity,
        limit=limit,
    )


@router.post(
    "/brain/model-providers/blockers/{provider_blocker_id}/dismiss",
    response_model=ModelProviderBlocker,
)
def dismiss_provider_blocker(
    provider_blocker_id: str,
    body: ModelProviderBlockerDismissRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModelProviderBlocker:
    """Dismiss a blocker without enabling provider behavior."""

    request = body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id})
    return container.model_provider_blocker_service.dismiss_blocker(
        provider_blocker_id,
        _scope(scope, actor_context),
        request,
    )


@router.post("/brain/model-providers/query", response_model=ProviderHardeningQueryResult)
def query_provider_hardening(
    body: ProviderHardeningQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ProviderHardeningQueryResult:
    """Query provider hardening metadata."""

    request = body.model_copy(update={"scope": body.scope or actor_context.security_scope})
    return container.model_provider_query_service.query(request)


def _scope(value: list[str] | None, actor_context: ActorContext) -> list[str]:
    return value or actor_context.security_scope or ["workspace:main"]


__all__ = ["router"]
