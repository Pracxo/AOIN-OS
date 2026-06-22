"""Memory governance API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.approvals import get_approval_service
from aion_brain.api.dependencies import get_skill_service
from aion_brain.api.evidence import get_evidence_service
from aion_brain.api.graph_memory import get_graph_memory_service
from aion_brain.api.memory import get_memory_service, get_semantic_memory_service
from aion_brain.api.risk import get_risk_engine
from aion_brain.audit.repository import AuditRepository
from aion_brain.config import get_settings
from aion_brain.contracts.memory import MemoryType
from aion_brain.contracts.memory_governance import (
    ForgetMemoryRequest,
    ForgetMemoryResult,
    MemoryCompactionRequest,
    MemoryCompactionResult,
    MemoryConflict,
    MemoryConflictResolutionRequest,
    MemoryConflictScanRequest,
    MemoryGovernanceDecision,
    MemoryGovernanceEvaluationRequest,
    MemoryGovernanceRule,
    MemoryRetentionSweepRequest,
    MemoryRetentionSweepResult,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.memory_governance.compaction import MemoryCompactionService
from aion_brain.memory_governance.conflicts import MemoryConflictService
from aion_brain.memory_governance.decay import MemoryDecayService
from aion_brain.memory_governance.engine import MemoryGovernanceEngine
from aion_brain.memory_governance.forgetting import MemoryForgettingService
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.memory_governance.retention import MemoryRetentionService
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain/memory", tags=["memory-governance"])


class RuleDisableRequest(BaseModel):
    """Disable governance rule request."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = None


class DecayRecomputeRequest(BaseModel):
    """Recompute decay request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    memory_types: list[MemoryType] = Field(default_factory=list)
    limit: int | None = Field(default=None, ge=1, le=10000)
    dry_run: bool = True


def get_memory_governance_repository() -> MemoryGovernanceRepository:
    """Return memory governance repository."""
    settings = get_settings()
    return get_cached_memory_governance_repository(settings.database_url)


@lru_cache
def get_cached_memory_governance_repository(database_url: str) -> MemoryGovernanceRepository:
    """Return cached governance repository."""
    return MemoryGovernanceRepository(database_url)


def get_memory_governance_engine() -> MemoryGovernanceEngine:
    """Return configured governance engine."""
    settings = get_settings()
    return get_cached_memory_governance_engine(
        settings.database_url,
        settings.opa_url,
        settings.memory_governance_enabled,
    )


@lru_cache
def get_cached_memory_governance_engine(
    database_url: str,
    opa_url: str,
    memory_governance_enabled: bool,
) -> MemoryGovernanceEngine:
    """Return cached governance engine."""
    settings = get_settings().model_copy(
        update={
            "database_url": database_url,
            "opa_url": opa_url,
            "memory_governance_enabled": memory_governance_enabled,
        }
    )
    return MemoryGovernanceEngine(
        governance_repository=get_cached_memory_governance_repository(database_url),
        risk_engine=get_risk_engine(),
        approval_service=get_approval_service(),
        policy_adapter=OPAAdapter(opa_url),
        telemetry_service=AuditRepository(database_url),
        settings=settings,
    )


def get_memory_decay_service() -> MemoryDecayService:
    """Return configured decay service."""
    settings = get_settings()
    return MemoryDecayService(
        governance_repository=get_memory_governance_repository(),
        memory_service=get_memory_service(),
        telemetry_service=AuditRepository(settings.database_url),
        settings=settings,
    )


def get_memory_retention_service() -> MemoryRetentionService:
    """Return configured retention service."""
    return MemoryRetentionService(
        memory_service=get_memory_service(),
        governance_engine=get_memory_governance_engine(),
        decay_service=get_memory_decay_service(),
        policy_adapter=OPAAdapter(get_settings().opa_url),
        telemetry_service=AuditRepository(get_settings().database_url),
    )


def get_memory_forgetting_service() -> MemoryForgettingService:
    """Return configured forgetting service."""
    settings = get_settings()
    return MemoryForgettingService(
        memory_service=get_memory_service(),
        semantic_memory_service=get_semantic_memory_service(),
        graph_memory_service=get_graph_memory_service(),
        evidence_service=get_evidence_service(),
        skill_service=get_skill_service(),
        trace_repository=AuditRepository(settings.database_url),
        risk_engine=get_risk_engine(),
        approval_service=get_approval_service(),
        policy_adapter=OPAAdapter(settings.opa_url),
        governance_repository=get_memory_governance_repository(),
        telemetry_service=AuditRepository(settings.database_url),
        settings=settings,
    )


def get_memory_conflict_service() -> MemoryConflictService:
    """Return configured conflict service."""
    settings = get_settings()
    return MemoryConflictService(
        memory_service=get_memory_service(),
        governance_repository=get_memory_governance_repository(),
        policy_adapter=OPAAdapter(settings.opa_url),
        telemetry_service=AuditRepository(settings.database_url),
        settings=settings,
    )


def get_memory_compaction_service() -> MemoryCompactionService:
    """Return configured compaction service."""
    settings = get_settings()
    return MemoryCompactionService(
        memory_service=get_memory_service(),
        governance_repository=get_memory_governance_repository(),
        policy_adapter=OPAAdapter(settings.opa_url),
        approval_service=get_approval_service(),
        telemetry_service=AuditRepository(settings.database_url),
        settings=settings,
    )


@router.post("/governance/rules", response_model=MemoryGovernanceRule)
def create_governance_rule(
    rule: MemoryGovernanceRule,
    engine: Annotated[MemoryGovernanceEngine, Depends(get_memory_governance_engine)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MemoryGovernanceRule:
    """Create one generic memory governance rule."""
    enriched = rule.model_copy(update={"created_by": rule.created_by or actor_context.actor_id})
    try:
        return engine.create_rule(enriched)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.get("/governance/rules", response_model=list[MemoryGovernanceRule])
def list_governance_rules(
    engine: Annotated[MemoryGovernanceEngine, Depends(get_memory_governance_engine)],
    status: Annotated[str | None, Query()] = None,
    rule_type: Annotated[str | None, Query()] = None,
) -> list[MemoryGovernanceRule]:
    """List generic memory governance rules."""
    try:
        return engine.list_rules(status=status, rule_type=rule_type)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.post("/governance/rules/{governance_rule_id}/disable", response_model=MemoryGovernanceRule)
def disable_governance_rule(
    governance_rule_id: str,
    request: RuleDisableRequest,
    engine: Annotated[MemoryGovernanceEngine, Depends(get_memory_governance_engine)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MemoryGovernanceRule:
    """Disable one generic memory governance rule."""
    try:
        return engine.disable_rule(governance_rule_id, request.reason, actor_context.actor_id)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.post("/governance/evaluate", response_model=MemoryGovernanceDecision)
def evaluate_memory_governance(
    request: MemoryGovernanceEvaluationRequest,
    engine: Annotated[MemoryGovernanceEngine, Depends(get_memory_governance_engine)],
) -> MemoryGovernanceDecision:
    """Evaluate memory governance for one memory action."""
    try:
        return engine.evaluate(request)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.post("/decay/recompute", response_model=MemoryRetentionSweepResult)
def recompute_memory_decay(
    request: DecayRecomputeRequest,
    service: Annotated[MemoryDecayService, Depends(get_memory_decay_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MemoryRetentionSweepResult:
    """Recompute decay scores for active memories."""
    scope = request.scope or actor_context.security_scope
    return service.recompute_decay(
        scope=scope,
        memory_types=[str(memory_type) for memory_type in request.memory_types],
        limit=request.limit or get_settings().memory_retention_sweep_limit_default,
        dry_run=request.dry_run,
    )


@router.post("/retention/sweep", response_model=MemoryRetentionSweepResult)
def sweep_memory_retention(
    request: MemoryRetentionSweepRequest,
    service: Annotated[MemoryRetentionService, Depends(get_memory_retention_service)],
) -> MemoryRetentionSweepResult:
    """Run retention and decay governance sweep."""
    return service.sweep(request)


@router.post("/forget", response_model=ForgetMemoryResult)
def forget_memory(
    request: ForgetMemoryRequest,
    service: Annotated[MemoryForgettingService, Depends(get_memory_forgetting_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ForgetMemoryResult:
    """Request memory-owned target forgetting."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
            "requested_by": request.requested_by or actor_context.actor_id,
        }
    )
    return service.forget(enriched)


@router.get("/forget/{forget_request_id}", response_model=ForgetMemoryResult)
def get_forget_memory_result(
    forget_request_id: str,
    service: Annotated[MemoryForgettingService, Depends(get_memory_forgetting_service)],
) -> ForgetMemoryResult:
    """Return one forgetting request result."""
    result = service.get_result(forget_request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="forget_request_not_found")
    return result


@router.post("/conflicts", response_model=list[MemoryConflict])
def scan_memory_conflicts(
    request: MemoryConflictScanRequest,
    service: Annotated[MemoryConflictService, Depends(get_memory_conflict_service)],
) -> list[MemoryConflict]:
    """Scan for generic memory conflicts."""
    return service.scan(request)


@router.get("/conflicts", response_model=list[MemoryConflict])
def list_memory_conflicts(
    service: Annotated[MemoryConflictService, Depends(get_memory_conflict_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[MemoryConflict]:
    """List persisted memory conflicts."""
    return service.list_conflicts(scope or actor_context.security_scope, status=status, limit=limit)


@router.post("/conflicts/{conflict_id}/resolve", response_model=MemoryConflict)
def resolve_memory_conflict(
    conflict_id: str,
    request: MemoryConflictResolutionRequest,
    service: Annotated[MemoryConflictService, Depends(get_memory_conflict_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MemoryConflict:
    """Resolve or dismiss one memory conflict."""
    enriched = request.model_copy(
        update={
            "conflict_id": conflict_id,
            "actor_id": request.actor_id or actor_context.actor_id,
        }
    )
    try:
        return service.resolve(enriched)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.post("/compact", response_model=MemoryCompactionResult)
def compact_memory(
    request: MemoryCompactionRequest,
    service: Annotated[MemoryCompactionService, Depends(get_memory_compaction_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> MemoryCompactionResult:
    """Run deterministic memory compaction."""
    enriched = request.model_copy(
        update={
            "actor_id": request.actor_id or actor_context.actor_id,
            "workspace_id": request.workspace_id or actor_context.workspace_id,
        }
    )
    return service.compact(enriched)


@router.get("/compact/{compaction_run_id}", response_model=MemoryCompactionResult)
def get_compaction_run(
    compaction_run_id: str,
    service: Annotated[MemoryCompactionService, Depends(get_memory_compaction_service)],
) -> MemoryCompactionResult:
    """Return one memory compaction result."""
    result = service.get_run(compaction_run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="compaction_run_not_found")
    return result


def _http_error(exc: ValueError) -> HTTPException:
    detail = str(exc)
    status = 404 if detail.endswith("_not_found") else 403
    return HTTPException(status_code=status, detail=detail)
