"""Grounding Manager API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.citations import (
    CitationCreateRequest,
    CitationRecord,
    GroundingQueryResult,
    ResponseCitationMap,
    UnsupportedStatement,
)
from aion_brain.contracts.grounding import (
    GroundingQuery,
    GroundingSource,
    GroundingSourceCreateRequest,
    GroundingVerificationRequest,
    GroundingVerificationRun,
    SourceCoverageReport,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/grounding", tags=["grounding"])


class MapResponseRequest(BaseModel):
    """Request to map a stored response."""

    model_config = ConfigDict(extra="forbid")

    owner_scope: list[str] = Field(default_factory=list)
    required_source_types: list[str] = Field(default_factory=list)


class MapTextRequest(BaseModel):
    """Request to map arbitrary public text."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    trace_id: str | None = None
    owner_scope: list[str] = Field(default_factory=list)
    sources: list[GroundingSource] = Field(default_factory=list)
    target_type: str = "generic"
    target_id: str | None = None
    required_source_types: list[str] = Field(default_factory=list)


class CoverageRequest(BaseModel):
    """Request to build a source coverage report."""

    model_config = ConfigDict(extra="forbid")

    response_id: str | None = None
    explanation_id: str | None = None
    owner_scope: list[str] = Field(default_factory=list)
    required_source_types: list[str] = Field(default_factory=list)


@router.post("/sources", response_model=GroundingSource)
def create_source(
    body: GroundingSourceCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> GroundingSource:
    """Create one grounding source."""

    try:
        return container.grounding_source_service.with_actor_context(actor_context).create_source(
            body
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/sources/{grounding_source_id}", response_model=GroundingSource)
def get_source(
    grounding_source_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> GroundingSource:
    """Return one grounding source."""

    try:
        source = container.grounding_source_service.with_actor_context(actor_context).get_source(
            grounding_source_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if source is None:
        raise HTTPException(status_code=404, detail="grounding_source_not_found")
    return source


@router.post("/citations", response_model=CitationRecord)
def create_citation(
    body: CitationCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CitationRecord:
    """Create one citation."""

    try:
        return container.citation_service.with_actor_context(actor_context).create_citation(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/citations", response_model=list[CitationRecord])
def list_citations(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    response_id: str | None = None,
    explanation_id: str | None = None,
    source_id: str | None = None,
    limit: int = 100,
) -> list[CitationRecord]:
    """List active citations."""

    try:
        return container.citation_service.with_actor_context(actor_context).list_citations(
            response_id=response_id,
            explanation_id=explanation_id,
            source_id=source_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/map-response/{response_id}", response_model=ResponseCitationMap)
def map_response(
    response_id: str,
    body: MapResponseRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResponseCitationMap:
    """Map a stored response to citations."""

    try:
        return container.citation_mapper.with_actor_context(actor_context).map_response(
            response_id,
            _scope(body.owner_scope, actor_context),
            body.required_source_types,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/map-text", response_model=ResponseCitationMap)
def map_text(
    body: MapTextRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResponseCitationMap:
    """Map arbitrary public text to citations."""

    try:
        return container.citation_mapper.with_actor_context(actor_context).map_text(
            text=body.text,
            trace_id=body.trace_id or actor_context.trace_id,
            owner_scope=_scope(body.owner_scope, actor_context),
            sources=body.sources,
            target_type=body.target_type,
            target_id=body.target_id,
            required_source_types=body.required_source_types,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/verify", response_model=GroundingVerificationRun)
def verify_grounding(
    body: GroundingVerificationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> GroundingVerificationRun:
    """Run grounding verification."""

    scoped = body.model_copy(
        update={
            "owner_scope": _scope(body.owner_scope, actor_context),
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.grounding_verifier.with_actor_context(actor_context).verify(scoped)


@router.get("/verifications/{grounding_verification_id}", response_model=GroundingVerificationRun)
def get_verification(
    grounding_verification_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> GroundingVerificationRun:
    """Return one grounding verification."""

    verification = container.grounding_verifier.get_verification(grounding_verification_id)
    if verification is None:
        raise HTTPException(status_code=404, detail="grounding_verification_not_found")
    return verification


@router.post("/coverage", response_model=SourceCoverageReport)
def coverage(
    body: CoverageRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SourceCoverageReport:
    """Build a source coverage report."""

    try:
        return container.source_coverage_service.with_actor_context(actor_context).report(
            response_id=body.response_id,
            explanation_id=body.explanation_id,
            owner_scope=_scope(body.owner_scope, actor_context),
            required_source_types=body.required_source_types,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/query", response_model=GroundingQueryResult)
def query_grounding(
    body: GroundingQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> GroundingQueryResult:
    """Query grounding and citation records."""

    try:
        return container.grounding_query_service.with_actor_context(actor_context).query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/unsupported", response_model=list[UnsupportedStatement])
def unsupported(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    response_id: str | None = None,
    explanation_id: str | None = None,
    trace_id: str | None = None,
    limit: int = 100,
) -> list[UnsupportedStatement]:
    """List unresolved unsupported statements."""

    list_unsupported = getattr(container.grounding_repository, "list_unsupported", None)
    if not callable(list_unsupported):
        return []
    result = list_unsupported(
        response_id=response_id,
        explanation_id=explanation_id,
        trace_id=trace_id,
        limit=limit,
    )
    return [item for item in result if isinstance(item, UnsupportedStatement)]


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


__all__ = ["router"]
