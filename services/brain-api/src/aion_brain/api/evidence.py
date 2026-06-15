"""Evidence Vault API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from aion_brain.audit.repository import AuditRepository
from aion_brain.config import get_settings
from aion_brain.contracts.evidence import (
    EvidenceChunk,
    EvidenceIngestRequest,
    EvidenceIngestResponse,
    EvidenceLink,
    EvidenceRecord,
    EvidenceSearchRequest,
    EvidenceSearchResult,
    GroundingRequest,
    GroundingResponse,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.evidence.grounding import GroundingService
from aion_brain.evidence.repository import EvidenceRepository
from aion_brain.evidence.service import EvidencePolicyDenied, EvidenceService
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.storage.local_store import LocalObjectStore

router = APIRouter(prefix="/brain/evidence", tags=["evidence"])


class EvidenceDeleteResponse(BaseModel):
    """Evidence delete response."""

    model_config = ConfigDict(extra="forbid")

    deleted: bool
    evidence_id: str


def get_evidence_repository() -> EvidenceRepository:
    """Create the configured evidence repository."""
    settings = get_settings()
    return get_cached_evidence_repository(settings.database_url)


@lru_cache
def get_cached_evidence_repository(database_url: str) -> EvidenceRepository:
    """Return a cached evidence repository."""
    return EvidenceRepository(database_url)


def get_evidence_service() -> EvidenceService:
    """Create the configured evidence service."""
    settings = get_settings()
    return get_cached_evidence_service(
        settings.database_url,
        settings.opa_url,
        settings.local_object_root,
    )


@lru_cache
def get_cached_evidence_service(
    database_url: str,
    opa_url: str,
    local_object_root: str,
) -> EvidenceService:
    """Return a cached evidence service."""
    return EvidenceService(
        evidence_repository=get_cached_evidence_repository(database_url),
        policy_adapter=OPAAdapter(opa_url),
        telemetry_service=AuditRepository(database_url),
        object_store=LocalObjectStore(local_object_root),
    )


def get_grounding_service() -> GroundingService:
    """Create the configured grounding service."""
    settings = get_settings()
    evidence_service = get_cached_evidence_service(
        settings.database_url,
        settings.opa_url,
        settings.local_object_root,
    )
    return GroundingService(
        evidence_service=evidence_service,
        grounding_repository=get_cached_evidence_repository(settings.database_url),
        policy_adapter=OPAAdapter(settings.opa_url),
        telemetry_service=AuditRepository(settings.database_url),
    )


@router.post("", response_model=EvidenceIngestResponse)
def ingest_evidence(
    request: EvidenceIngestRequest,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EvidenceIngestResponse:
    """Ingest text evidence or metadata-only content references."""
    try:
        return service.with_actor_context(actor_context).ingest(request)
    except EvidencePolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/{evidence_id}", response_model=EvidenceRecord)
def get_evidence(
    evidence_id: str,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EvidenceRecord:
    """Return an evidence record."""
    try:
        evidence = service.with_actor_context(actor_context).get_evidence(
            evidence_id,
            _scope_or_actor_scope(scope, actor_context),
        )
    except EvidencePolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if evidence is None:
        raise HTTPException(status_code=404, detail="evidence_not_found")
    return evidence


@router.get("/{evidence_id}/chunks", response_model=list[EvidenceChunk])
def get_evidence_chunks(
    evidence_id: str,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[EvidenceChunk]:
    """Return evidence chunks."""
    try:
        return service.with_actor_context(actor_context).get_chunks(
            evidence_id,
            _scope_or_actor_scope(scope, actor_context),
        )
    except EvidencePolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/search", response_model=list[EvidenceSearchResult])
def search_evidence(
    request: EvidenceSearchRequest,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[EvidenceSearchResult]:
    """Search evidence deterministically."""
    scoped_request = request.model_copy(
        update={"scope": request.scope or actor_context.security_scope}
    )
    try:
        return service.with_actor_context(actor_context).search(scoped_request)
    except EvidencePolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/links", response_model=EvidenceLink)
def link_evidence(
    link: EvidenceLink,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EvidenceLink:
    """Create an evidence link."""
    try:
        return service.with_actor_context(actor_context).link(link)
    except EvidencePolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{evidence_id}/links", response_model=list[EvidenceLink])
def list_evidence_links(
    evidence_id: str,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[EvidenceLink]:
    """List evidence links."""
    try:
        return service.with_actor_context(actor_context).list_links(
            evidence_id,
            _scope_or_actor_scope(scope, actor_context),
        )
    except EvidencePolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/ground", response_model=GroundingResponse)
def ground_evidence(
    request: GroundingRequest,
    service: Annotated[GroundingService, Depends(get_grounding_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> GroundingResponse:
    """Create deterministic grounding claims."""
    scoped_request = request.model_copy(
        update={"scope": request.scope or actor_context.security_scope}
    )
    try:
        return service.with_actor_context(actor_context).ground(scoped_request)
    except EvidencePolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.delete("/{evidence_id}", response_model=EvidenceDeleteResponse)
def delete_evidence(
    evidence_id: str,
    service: Annotated[EvidenceService, Depends(get_evidence_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> EvidenceDeleteResponse:
    """Soft-delete evidence."""
    try:
        deleted = service.with_actor_context(actor_context).soft_delete(
            evidence_id,
            _scope_or_actor_scope(scope, actor_context),
        )
    except EvidencePolicyDenied as exc:
        raise _policy_denied(exc) from exc
    return EvidenceDeleteResponse(deleted=deleted, evidence_id=evidence_id)


def _scope_or_actor_scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope


def _policy_denied(exc: EvidencePolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "reason": exc.decision.reason,
            "decision_id": exc.decision.decision_id,
            "constraints": exc.decision.constraints,
        },
    )
