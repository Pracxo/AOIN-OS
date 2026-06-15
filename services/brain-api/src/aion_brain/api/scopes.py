"""Scope resolution API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from aion_brain.api.dependencies import get_scope_resolver
from aion_brain.contracts.scopes import ActorContext, ScopeResolution, ScopeResolutionRequest
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.scopes.resolver import ScopeResolver

router = APIRouter(prefix="/brain/scopes", tags=["scopes"])


@router.post("/resolve", response_model=ScopeResolution)
def resolve_scope(
    request: ScopeResolutionRequest,
    resolver: Annotated[ScopeResolver, Depends(get_scope_resolver)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ScopeResolution:
    """Resolve actor scopes and permissions."""
    return resolver.resolve(request, actor_context)
