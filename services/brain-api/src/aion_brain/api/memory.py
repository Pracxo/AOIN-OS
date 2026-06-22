"""Memory Fabric API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.audit.repository import AuditRepository
from aion_brain.config import get_settings
from aion_brain.contracts.memory import (
    MemoryDeleteResponse,
    MemoryRecord,
    MemoryRetrievalRequest,
    SemanticAdapterStatus,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
    TurboVecReindexRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.embeddings.hash_embedding import HashEmbeddingAdapter
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.memory.base import SemanticMemoryAdapter
from aion_brain.memory.in_memory_semantic_adapter import InMemorySemanticMemoryAdapter
from aion_brain.memory.pgvector_adapter import PgVectorSemanticMemoryAdapter
from aion_brain.memory.repository import MemoryRepository
from aion_brain.memory.semantic_service import (
    SemanticMemoryPolicyDenied,
    SemanticMemoryService,
    SemanticMemoryUnavailable,
)
from aion_brain.memory.service import (
    MemoryGovernanceDenied,
    MemoryPolicyDenied,
    PostgresMemoryService,
)
from aion_brain.memory.turbovec_adapter import TurboVecSemanticMemoryAdapter
from aion_brain.memory.turbovec_compat import TurboVecCompat
from aion_brain.memory.turbovec_repository import TurboVecRepository
from aion_brain.memory_governance.engine import MemoryGovernanceEngine
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain/memory", tags=["memory"])


class SemanticReindexAllRequest(BaseModel):
    """Development semantic reindex-all request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str]
    limit: int = Field(default=100, ge=1, le=1000)


class SemanticReindexAllResponse(BaseModel):
    """Development semantic reindex-all response."""

    model_config = ConfigDict(extra="forbid")

    requested: int
    indexed: int
    failed: int


def get_memory_service() -> PostgresMemoryService:
    """Create the configured memory service."""
    settings = get_settings()
    return get_cached_memory_service(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_memory_service(database_url: str, opa_url: str) -> PostgresMemoryService:
    """Return a cached canonical memory service."""
    policy_adapter = OPAAdapter(opa_url)
    governance_repository = MemoryGovernanceRepository(database_url)
    governance_engine = MemoryGovernanceEngine(
        governance_repository=governance_repository,
        risk_engine=None,
        approval_service=None,
        policy_adapter=policy_adapter,
        telemetry_service=AuditRepository(database_url),
        settings=get_settings(),
    )
    return PostgresMemoryService(
        memory_adapter=MemoryRepository(database_url),
        policy_adapter=policy_adapter,
        governance_engine=governance_engine,
    )


def get_semantic_memory_service() -> SemanticMemoryService:
    """Create the configured semantic memory service."""
    settings = get_settings()
    return get_cached_semantic_memory_service(
        settings.database_url,
        settings.opa_url,
        settings.default_semantic_adapter,
        settings.embedding_adapter,
        settings.semantic_vector_dimensions,
        settings.turbovec_enabled,
        settings.turbovec_index_name,
        settings.turbovec_index_dir,
        settings.turbovec_bit_width,
        settings.turbovec_auto_persist,
        settings.turbovec_fail_open_to_pgvector,
    )


@lru_cache
def get_cached_semantic_memory_service(
    database_url: str,
    opa_url: str,
    default_semantic_adapter: str,
    embedding_adapter_name: str,
    dimensions: int,
    turbovec_enabled: bool = False,
    turbovec_index_name: str = "default",
    turbovec_index_dir: str = "./.aion_indexes/turbovec",
    turbovec_bit_width: int = 4,
    turbovec_auto_persist: bool = True,
    turbovec_fail_open_to_pgvector: bool = True,
) -> SemanticMemoryService:
    """Return a cached semantic memory service."""
    policy_adapter = OPAAdapter(opa_url)
    memory_repository = MemoryRepository(database_url)
    embedding_adapter = HashEmbeddingAdapter(dimensions)
    if embedding_adapter_name != "hash":
        raise ValueError("Only hash embedding adapter is supported in v0.1")
    turbovec_adapter = TurboVecSemanticMemoryAdapter(
        memory_repository=memory_repository,
        turbovec_repository=TurboVecRepository(database_url),
        embedding_adapter=embedding_adapter,
        telemetry_service=AuditRepository(database_url),
        compat=TurboVecCompat(),
        enabled=turbovec_enabled,
        index_name=turbovec_index_name,
        index_dir=turbovec_index_dir,
        dimensions=dimensions,
        bit_width=turbovec_bit_width,
        auto_persist=turbovec_auto_persist,
    )
    semantic_adapter: SemanticMemoryAdapter
    fallback_reason: str | None = None
    normalized_default = default_semantic_adapter.replace("-", "_")
    if normalized_default == "in_memory":
        semantic_adapter = InMemorySemanticMemoryAdapter(embedding_adapter)
    elif normalized_default == "turbovec":
        turbovec_status = turbovec_adapter.status(turbovec_index_name)
        if turbovec_status.available:
            semantic_adapter = turbovec_adapter
        elif turbovec_fail_open_to_pgvector:
            fallback_reason = turbovec_status.reason or "turbovec_unavailable"
            semantic_adapter = PgVectorSemanticMemoryAdapter(
                memory_repository=memory_repository,
                database_url=database_url,
                embedding_adapter=embedding_adapter,
                dimensions=dimensions,
            )
        else:
            semantic_adapter = turbovec_adapter
    else:
        semantic_adapter = PgVectorSemanticMemoryAdapter(
            memory_repository=memory_repository,
            database_url=database_url,
            embedding_adapter=embedding_adapter,
            dimensions=dimensions,
        )
    return SemanticMemoryService(
        adapter=semantic_adapter,
        policy_adapter=policy_adapter,
        telemetry_repository=AuditRepository(database_url),
        configured_adapter=default_semantic_adapter,
        fallback_reason=fallback_reason,
        turbovec_adapter=turbovec_adapter,
    )


@router.post("", response_model=MemoryRecord)
def create_memory(
    record: MemoryRecord,
    service: Annotated[PostgresMemoryService, Depends(get_memory_service)],
) -> MemoryRecord:
    """Create a memory record after policy authorization."""
    try:
        return service.create(record)
    except MemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except MemoryGovernanceDenied as exc:
        raise HTTPException(status_code=403, detail=exc.decision.reason) from exc


@router.post("/retrieve", response_model=list[MemoryRecord])
def retrieve_memory(
    request: MemoryRetrievalRequest,
    service: Annotated[PostgresMemoryService, Depends(get_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[MemoryRecord]:
    """Retrieve memories after policy authorization."""
    scoped_request = request.model_copy(
        update={"scope": request.scope or actor_context.security_scope}
    )
    try:
        return service.retrieve(scoped_request)
    except MemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except MemoryGovernanceDenied as exc:
        raise HTTPException(status_code=403, detail=exc.decision.reason) from exc


@router.post("/semantic/index/{memory_id}", response_model=SemanticIndexResponse)
def index_semantic_memory(
    memory_id: str,
    service: Annotated[SemanticMemoryService, Depends(get_semantic_memory_service)],
) -> SemanticIndexResponse:
    """Reindex one memory record through the configured semantic adapter."""
    try:
        return service.reindex(memory_id, scope=[])
    except SemanticMemoryPolicyDenied as exc:
        raise _semantic_policy_denied(exc) from exc
    except SemanticMemoryUnavailable as exc:
        raise _semantic_unavailable(exc) from exc


@router.post("/semantic/retrieve", response_model=list[SemanticMemoryResult])
def retrieve_semantic_memory(
    request: SemanticMemoryQuery,
    service: Annotated[SemanticMemoryService, Depends(get_semantic_memory_service)],
) -> list[SemanticMemoryResult]:
    """Retrieve memory using semantic recall."""
    try:
        return service.retrieve(request)
    except SemanticMemoryPolicyDenied as exc:
        raise _semantic_policy_denied(exc) from exc
    except SemanticMemoryUnavailable as exc:
        raise _semantic_unavailable(exc) from exc


@router.get("/semantic/adapters", response_model=list[SemanticAdapterStatus])
def list_semantic_adapters(
    service: Annotated[SemanticMemoryService, Depends(get_semantic_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[SemanticAdapterStatus]:
    """Return semantic adapter statuses."""
    try:
        return service.adapter_statuses(actor_context.security_scope)
    except SemanticMemoryPolicyDenied as exc:
        raise _semantic_policy_denied(exc) from exc


@router.get("/semantic/turbovec/status", response_model=TurboVecIndexStatus)
def get_turbovec_status(
    service: Annotated[SemanticMemoryService, Depends(get_semantic_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    index_name: str = "default",
) -> TurboVecIndexStatus:
    """Return TurboVec index status."""
    try:
        return service.turbovec_status(index_name, actor_context.security_scope)
    except SemanticMemoryPolicyDenied as exc:
        raise _semantic_policy_denied(exc) from exc


@router.post("/semantic/turbovec/rebuild", response_model=TurboVecRebuildResponse)
def rebuild_turbovec(
    request: TurboVecRebuildRequest,
    service: Annotated[SemanticMemoryService, Depends(get_semantic_memory_service)],
) -> TurboVecRebuildResponse:
    """Rebuild the TurboVec compressed recall index."""
    try:
        return service.rebuild_turbovec(request)
    except SemanticMemoryPolicyDenied as exc:
        raise _semantic_policy_denied(exc) from exc
    except SemanticMemoryUnavailable as exc:
        raise _semantic_unavailable(exc) from exc


@router.post("/semantic/turbovec/reindex/{memory_id}", response_model=SemanticIndexResponse)
def reindex_turbovec_memory(
    memory_id: str,
    request: TurboVecReindexRequest,
    service: Annotated[SemanticMemoryService, Depends(get_semantic_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SemanticIndexResponse:
    """Reindex one memory record through TurboVec."""
    try:
        return service.reindex_turbovec(
            memory_id,
            index_name=request.index_name,
            force=request.force,
            scope=actor_context.security_scope,
        )
    except SemanticMemoryPolicyDenied as exc:
        raise _semantic_policy_denied(exc) from exc
    except SemanticMemoryUnavailable as exc:
        raise _semantic_unavailable(exc) from exc


@router.post("/semantic/reindex-all", response_model=SemanticReindexAllResponse)
def reindex_all_semantic_memory(
    request: SemanticReindexAllRequest,
    memory_service: Annotated[PostgresMemoryService, Depends(get_memory_service)],
    semantic_service: Annotated[SemanticMemoryService, Depends(get_semantic_memory_service)],
) -> SemanticReindexAllResponse:
    """Development endpoint to reindex active memory records in scope."""
    records = _list_memory_records(memory_service, request)
    indexed = 0
    failed = 0
    for record in records:
        try:
            response = semantic_service.reindex(record.memory_id, scope=request.scope)
        except SemanticMemoryPolicyDenied as exc:
            raise _semantic_policy_denied(exc) from exc
        if response.indexed:
            indexed += 1
        else:
            failed += 1
    return SemanticReindexAllResponse(requested=request.limit, indexed=indexed, failed=failed)


@router.get("/{memory_id}", response_model=MemoryRecord)
def get_memory(
    memory_id: str,
    service: Annotated[PostgresMemoryService, Depends(get_memory_service)],
) -> MemoryRecord:
    """Return a memory record by ID."""
    record = service.get(memory_id)
    if record is None:
        raise HTTPException(status_code=404, detail="memory_not_found")
    return record


@router.delete("/{memory_id}", response_model=MemoryDeleteResponse)
def delete_memory(
    memory_id: str,
    service: Annotated[PostgresMemoryService, Depends(get_memory_service)],
) -> MemoryDeleteResponse:
    """Soft-delete a memory record."""
    try:
        deleted = service.delete(memory_id)
    except MemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="memory_not_found")
    return MemoryDeleteResponse(deleted=True, memory_id=memory_id)


def _policy_denied(exc: MemoryPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "reason": exc.decision.reason,
            "decision_id": exc.decision.decision_id,
            "constraints": exc.decision.constraints,
        },
    )


def _semantic_policy_denied(exc: SemanticMemoryPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "reason": exc.decision.reason,
            "decision_id": exc.decision.decision_id,
            "constraints": exc.decision.constraints,
        },
    )


def _semantic_unavailable(exc: SemanticMemoryUnavailable) -> HTTPException:
    return HTTPException(status_code=503, detail={"reason": exc.reason})


def _list_memory_records(
    service: PostgresMemoryService,
    request: SemanticReindexAllRequest,
) -> list[MemoryRecord]:
    return service.list_active(request.scope, limit=request.limit)
