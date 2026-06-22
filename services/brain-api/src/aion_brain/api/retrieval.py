"""Retrieval Router API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion_brain.api.graph_memory import get_cached_graph_memory_service
from aion_brain.api.memory import get_cached_semantic_memory_service
from aion_brain.audit.repository import AuditRepository
from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.config import get_settings
from aion_brain.contracts.retrieval import (
    ContextBundle,
    ContextFusionRequest,
    RetrievalRequest,
    RetrievalResult,
)
from aion_brain.evidence.repository import EvidenceRepository
from aion_brain.evidence.service import EvidenceService
from aion_brain.memory.repository import MemoryRepository
from aion_brain.memory.service import PostgresMemoryService
from aion_brain.memory_governance.decay import MemoryDecayService
from aion_brain.memory_governance.engine import MemoryGovernanceEngine
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.retrieval.fusion import ContextFusionEngine
from aion_brain.retrieval.repository import RetrievalRepository
from aion_brain.retrieval.router import RetrievalRouter
from aion_brain.skills.matcher import SkillMatcher
from aion_brain.skills.repository import SkillRepository
from aion_brain.working_memory.repository import WorkingMemoryRepository
from aion_brain.working_memory.service import WorkingMemoryService

router = APIRouter(prefix="/brain/retrieval", tags=["retrieval"])


def get_retrieval_router() -> RetrievalRouter:
    """Create the configured retrieval router."""
    settings = get_settings()
    return get_cached_retrieval_router(
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
        settings.default_graph_memory_adapter,
        settings.graphiti_enabled,
        settings.graphiti_config_name,
        settings.graphiti_backend_type,
        settings.graphiti_endpoint_ref,
        settings.graphiti_fail_open_to_postgres_graph,
        settings.model_gateway_enabled,
    )


@lru_cache
def get_cached_retrieval_router(
    database_url: str,
    opa_url: str,
    default_semantic_adapter: str,
    embedding_adapter: str,
    semantic_vector_dimensions: int,
    turbovec_enabled: bool = False,
    turbovec_index_name: str = "default",
    turbovec_index_dir: str = "./.aion_indexes/turbovec",
    turbovec_bit_width: int = 4,
    turbovec_auto_persist: bool = True,
    turbovec_fail_open_to_pgvector: bool = True,
    default_graph_memory_adapter: str = "postgres_graph",
    graphiti_enabled: bool = False,
    graphiti_config_name: str = "default",
    graphiti_backend_type: str = "unknown",
    graphiti_endpoint_ref: str | None = None,
    graphiti_fail_open_to_postgres_graph: bool = True,
    model_gateway_enabled: bool = False,
) -> RetrievalRouter:
    """Return a cached retrieval router."""
    policy_adapter = OPAAdapter(opa_url)
    settings = get_settings()
    governance_repository = MemoryGovernanceRepository(database_url)
    governance_engine = MemoryGovernanceEngine(
        governance_repository=governance_repository,
        risk_engine=None,
        approval_service=None,
        policy_adapter=policy_adapter,
        telemetry_service=AuditRepository(database_url),
        settings=settings,
    )
    memory_service = PostgresMemoryService(
        memory_adapter=MemoryRepository(database_url),
        policy_adapter=policy_adapter,
        governance_engine=governance_engine,
    )
    decay_service = MemoryDecayService(
        governance_repository=governance_repository,
        memory_service=memory_service,
        telemetry_service=AuditRepository(database_url),
        settings=settings,
    )
    return RetrievalRouter(
        policy_adapter=policy_adapter,
        memory_service=memory_service,
        semantic_memory_service=get_cached_semantic_memory_service(
            database_url,
            opa_url,
            default_semantic_adapter,
            embedding_adapter,
            semantic_vector_dimensions,
            turbovec_enabled,
            turbovec_index_name,
            turbovec_index_dir,
            turbovec_bit_width,
            turbovec_auto_persist,
            turbovec_fail_open_to_pgvector,
        ),
        graph_memory_service=get_cached_graph_memory_service(
            database_url,
            opa_url,
            default_graph_memory_adapter,
            graphiti_enabled,
            graphiti_config_name,
            graphiti_backend_type,
            graphiti_endpoint_ref,
            graphiti_fail_open_to_postgres_graph,
            model_gateway_enabled,
        ),
        capability_registry=CapabilityRegistry(),
        skill_matcher=SkillMatcher(SkillRepository(database_url)),
        trace_repository=AuditRepository(database_url),
        evidence_service=EvidenceService(
            evidence_repository=EvidenceRepository(database_url),
            policy_adapter=policy_adapter,
            telemetry_service=AuditRepository(database_url),
        ),
        working_memory_service=WorkingMemoryService(
            WorkingMemoryRepository(database_url),
            policy_adapter,
            settings=settings,
            telemetry_service=AuditRepository(database_url),
        ),
        telemetry_service=AuditRepository(database_url),
        retrieval_repository=RetrievalRepository(database_url),
        memory_governance_engine=governance_engine,
        memory_decay_service=decay_service,
    )


def get_context_fusion_engine() -> ContextFusionEngine:
    """Return the deterministic Context Fusion Engine."""
    return ContextFusionEngine()


def get_retrieval_repository() -> RetrievalRepository:
    """Create the configured retrieval repository."""
    settings = get_settings()
    return get_cached_retrieval_repository(settings.database_url)


@lru_cache
def get_cached_retrieval_repository(database_url: str) -> RetrievalRepository:
    """Return a cached retrieval repository."""
    return RetrievalRepository(database_url)


@router.post("/query", response_model=RetrievalResult)
def query_retrieval(
    request: RetrievalRequest,
    retrieval_router: Annotated[RetrievalRouter, Depends(get_retrieval_router)],
) -> RetrievalResult:
    """Run the Retrieval Router."""
    return retrieval_router.retrieve(request)


@router.post("/fuse", response_model=ContextBundle)
def fuse_context(
    request: ContextFusionRequest,
    fusion_engine: Annotated[ContextFusionEngine, Depends(get_context_fusion_engine)],
) -> ContextBundle:
    """Fuse retrieval output into a deterministic context bundle."""
    return fusion_engine.fuse(request)


@router.get("/{retrieval_id}", response_model=RetrievalResult)
def get_retrieval(
    retrieval_id: str,
    repository: Annotated[RetrievalRepository, Depends(get_retrieval_repository)],
) -> RetrievalResult:
    """Return a persisted retrieval result."""
    result = repository.get(retrieval_id)
    if result is None:
        raise HTTPException(status_code=404, detail="retrieval_not_found")
    return result
