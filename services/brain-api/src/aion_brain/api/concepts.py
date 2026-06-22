"""Concept registry API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.concepts import (
    ConceptArchiveRequest,
    ConceptCreateRequest,
    ConceptRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/concepts", tags=["concepts"])


@router.post("", response_model=ConceptRecord)
def create_concept(
    body: ConceptCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConceptRecord:
    """Create one concept."""
    try:
        return container.concept_service.create(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("", response_model=list[ConceptRecord])
def list_concepts(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    query: str | None = None,
    concept_type: Annotated[list[str] | None, Query()] = None,
    status: str | None = "active",
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ConceptRecord]:
    """List concepts visible to scope."""
    try:
        return container.concept_service.list_concepts(
            scope=_scope(scope, actor_context),
            query=query,
            concept_types=concept_type,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/{concept_id}", response_model=ConceptRecord)
def get_concept(
    concept_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConceptRecord:
    """Return one concept."""
    try:
        concept = container.concept_service.get(concept_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if concept is None:
        raise HTTPException(status_code=404, detail="concept_not_found")
    return concept


@router.post("/{concept_id}/archive", response_model=ConceptRecord)
def archive_concept(
    concept_id: str,
    body: ConceptArchiveRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConceptRecord:
    """Archive one concept."""
    try:
        return container.concept_service.archive(
            concept_id,
            _scope(scope, actor_context),
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope
