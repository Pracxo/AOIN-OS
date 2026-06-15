"""AION Model Gateway API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from aion_brain.contracts.model_gateway import (
    ModelBudgetRecord,
    ModelGatewayRequest,
    ModelGatewayResponse,
    ModelProfile,
    ModelProvider,
    ModelProviderHealth,
    ModelUsageRecord,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.policy.enrichment import PolicyInputEnricher

router = APIRouter(prefix="/brain", tags=["model-gateway"])


class DisableRequest(BaseModel):
    """Disable request body."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


def get_kernel_container(request: Request) -> KernelContainer:
    """Return the process-wide kernel container."""
    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelContainer):
        raise RuntimeError("AION kernel container is not configured")
    return container


@router.post("/model-providers", response_model=ModelProvider)
def register_provider(
    provider: ModelProvider,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProvider:
    """Register a model provider contract."""
    try:
        return container.model_provider_registry.register_provider(provider, actor_context)
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc


@router.get("/model-providers", response_model=list[ModelProvider])
def list_providers(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    status: str | None = None,
) -> list[ModelProvider]:
    """List model providers."""
    try:
        return container.model_provider_registry.list_providers(status, actor_context)
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc


@router.get("/model-providers/{provider_id}", response_model=ModelProvider)
def get_provider(
    provider_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProvider:
    """Return one model provider."""
    try:
        provider = container.model_provider_registry.get_provider(provider_id, actor_context)
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc
    if provider is None:
        raise HTTPException(status_code=404, detail="model_provider_not_found")
    return provider


@router.post("/model-providers/{provider_id}/disable", response_model=ModelProvider)
def disable_provider(
    provider_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProvider:
    """Disable a model provider."""
    try:
        return container.model_provider_registry.disable_provider(
            provider_id,
            body.reason,
            actor_context,
        )
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="model_provider_not_found") from exc


@router.post("/model-providers/{provider_id}/health-check", response_model=ModelProviderHealth)
def provider_health_check(
    provider_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProviderHealth:
    """Run a local provider health check."""
    try:
        return container.model_provider_registry.health_check(provider_id, actor_context)
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc


@router.post("/model-profiles", response_model=ModelProfile)
def register_profile(
    profile: ModelProfile,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProfile:
    """Register a model profile contract."""
    try:
        return container.model_profile_registry.register_profile(profile, actor_context)
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc


@router.get("/model-profiles", response_model=list[ModelProfile])
def list_profiles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    provider_id: str | None = None,
    mode: str | None = None,
    status: str | None = None,
) -> list[ModelProfile]:
    """List model profiles."""
    try:
        return container.model_profile_registry.list_profiles(
            provider_id,
            mode,
            status,
            actor_context,
        )
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc


@router.get("/model-profiles/{model_profile_id}", response_model=ModelProfile)
def get_profile(
    model_profile_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProfile:
    """Return one model profile."""
    try:
        profile = container.model_profile_registry.get_profile(model_profile_id, actor_context)
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc
    if profile is None:
        raise HTTPException(status_code=404, detail="model_profile_not_found")
    return profile


@router.post("/model-profiles/{model_profile_id}/disable", response_model=ModelProfile)
def disable_profile(
    model_profile_id: str,
    body: DisableRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelProfile:
    """Disable a model profile."""
    try:
        return container.model_profile_registry.disable_profile(
            model_profile_id,
            body.reason,
            actor_context,
        )
    except PermissionError as exc:
        raise _forbidden(str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="model_profile_not_found") from exc


@router.post("/model-gateway/complete", response_model=ModelGatewayResponse)
def complete(
    body: ModelGatewayRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelGatewayResponse:
    """Complete a prompt through the model gateway."""
    enriched = _enrich_gateway_request(body, actor_context)
    return container.model_gateway_service.complete(enriched)


@router.get("/model-usage", response_model=list[ModelUsageRecord])
def list_usage(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    trace_id: str | None = None,
    reasoning_id: str | None = None,
    provider_id: str | None = None,
    workspace_id: str | None = None,
    limit: int = 100,
) -> list[ModelUsageRecord]:
    """List model usage records."""
    _authorize(container, actor_context, "model.usage.read", "model_usage")
    return container.model_usage_ledger.list_usage(
        trace_id=trace_id,
        reasoning_id=reasoning_id,
        provider_id=provider_id,
        workspace_id=workspace_id,
        limit=limit,
    )


@router.post("/model-budgets", response_model=ModelBudgetRecord)
def create_budget(
    budget: ModelBudgetRecord,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModelBudgetRecord:
    """Create or replace a local model budget record."""
    _authorize(container, actor_context, "model.budget.create", "model_budget")
    return container.model_gateway_repository.save_budget(budget)


@router.get("/model-budgets", response_model=list[ModelBudgetRecord])
def list_budgets(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    workspace_id: str | None = None,
    actor_id: str | None = None,
    status: str | None = None,
) -> list[ModelBudgetRecord]:
    """List model budget records."""
    _authorize(container, actor_context, "model.budget.read", "model_budget")
    return container.model_gateway_repository.list_budgets(
        workspace_id=workspace_id,
        actor_id=actor_id,
        status=status,
    )


def _enrich_gateway_request(
    request: ModelGatewayRequest,
    actor_context: ActorContext,
) -> ModelGatewayRequest:
    metadata = {
        **request.metadata,
        "roles": actor_context.roles,
        "permissions": actor_context.permissions,
        "dev_mode": actor_context.dev_mode,
    }
    return request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "scope": request.scope or actor_context.security_scope,
            "metadata": metadata,
        }
    )


def _authorize(
    container: KernelContainer,
    actor_context: ActorContext,
    action_type: str,
    resource_type: str,
) -> None:
    decision = container.policy_adapter.authorize(
        PolicyInputEnricher().enrich(
            PolicyRequest(
                request_id=f"{action_type}-{resource_type}",
                trace_id=actor_context.trace_id,
                actor_id=actor_context.actor_id,
                workspace_id=actor_context.workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=None,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=actor_context.security_scope or ["workspace:main"],
                context={},
            ),
            actor_context,
        )
    )
    if not decision.allow:
        raise _forbidden(decision.reason)


def _forbidden(reason: str) -> HTTPException:
    return HTTPException(status_code=403, detail={"reason": reason})
