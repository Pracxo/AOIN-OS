"""Execution Orchestrator API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from aion_brain.api.approvals import get_cached_approval_service
from aion_brain.api.dependencies import get_capability_registry, get_capability_runtime_gateway
from aion_brain.config import get_settings
from aion_brain.contracts.execution import (
    ApprovalCheckpoint,
    ExecutionRequest,
    ExecutionRun,
    ExecutionStepRun,
)
from aion_brain.execution.capability_invoker import CapabilityInvoker
from aion_brain.execution.orchestrator import ExecutionOrchestrator
from aion_brain.execution.repository import ExecutionRepository
from aion_brain.policy.opa_adapter import OPAAdapter

router = APIRouter(prefix="/brain", tags=["execution"])


class CancelExecutionRequest(BaseModel):
    """Execution cancellation request."""

    model_config = ConfigDict(extra="forbid")

    reason: str


class ApprovalResolutionRequest(BaseModel):
    """Approval checkpoint resolution request."""

    model_config = ConfigDict(extra="forbid")

    approved: bool
    approved_by: str
    reason: str


def get_execution_repository() -> ExecutionRepository:
    """Create the configured execution repository."""
    settings = get_settings()
    return get_cached_execution_repository(settings.database_url)


@lru_cache
def get_cached_execution_repository(database_url: str) -> ExecutionRepository:
    """Return a cached execution repository."""
    return ExecutionRepository(database_url)


def get_execution_orchestrator() -> ExecutionOrchestrator:
    """Create the configured execution orchestrator."""
    settings = get_settings()
    return get_cached_execution_orchestrator(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_execution_orchestrator(database_url: str, opa_url: str) -> ExecutionOrchestrator:
    """Return a cached execution orchestrator."""
    settings = get_settings()
    policy_adapter = OPAAdapter(opa_url)
    repository = get_cached_execution_repository(database_url)
    runtime_gateway = get_capability_runtime_gateway()
    capability_invoker = CapabilityInvoker(
        capability_registry=get_capability_registry(),
        policy_adapter=policy_adapter,
        execution_repository=repository,
        telemetry_service=None,
        runtime_gateway=runtime_gateway,
    )
    return ExecutionOrchestrator(
        policy_adapter=policy_adapter,
        capability_invoker=capability_invoker,
        execution_repository=repository,
        telemetry_service=None,
        approval_service=get_cached_approval_service(
            database_url,
            opa_url,
            settings.risk_engine_enabled,
            settings.guardrails_enabled,
            settings.approvals_enabled,
            settings.approval_default_expiry_hours,
            settings.high_risk_requires_approval,
            settings.critical_risk_blocks_by_default,
        ),
    )


@router.post("/execute", response_model=ExecutionRun)
def execute_plan(
    request: ExecutionRequest,
    orchestrator: Annotated[ExecutionOrchestrator, Depends(get_execution_orchestrator)],
) -> ExecutionRun:
    """Execute a plan through the policy-gated state machine."""
    return orchestrator.execute(request)


@router.get("/executions/{execution_id}", response_model=ExecutionRun)
def get_execution(
    execution_id: str,
    repository: Annotated[ExecutionRepository, Depends(get_execution_repository)],
) -> ExecutionRun:
    """Return a persisted execution run."""
    run = repository.get_execution(execution_id)
    if run is None:
        raise HTTPException(status_code=404, detail="execution_not_found")
    return run


@router.get("/executions/{execution_id}/steps", response_model=list[ExecutionStepRun])
def get_execution_steps(
    execution_id: str,
    repository: Annotated[ExecutionRepository, Depends(get_execution_repository)],
) -> list[ExecutionStepRun]:
    """Return persisted execution step runs."""
    return repository.list_steps(execution_id)


@router.get("/executions/{execution_id}/approvals", response_model=list[ApprovalCheckpoint])
def get_execution_approvals(
    execution_id: str,
    repository: Annotated[ExecutionRepository, Depends(get_execution_repository)],
) -> list[ApprovalCheckpoint]:
    """Return persisted approval checkpoints."""
    return repository.list_approvals(execution_id)


@router.post("/executions/{execution_id}/cancel", response_model=ExecutionRun)
def cancel_execution(
    execution_id: str,
    request: CancelExecutionRequest,
    repository: Annotated[ExecutionRepository, Depends(get_execution_repository)],
) -> ExecutionRun:
    """Cancel a running or waiting execution."""
    run = repository.cancel_execution(execution_id, reason=request.reason)
    if run is None:
        raise HTTPException(status_code=404, detail="execution_not_found")
    return run


@router.post("/approvals/{approval_id}/resolve", response_model=ApprovalCheckpoint)
def resolve_approval(
    approval_id: str,
    request: ApprovalResolutionRequest,
    repository: Annotated[ExecutionRepository, Depends(get_execution_repository)],
) -> ApprovalCheckpoint:
    """Resolve an approval checkpoint without resuming execution."""
    approval = repository.resolve_approval(
        approval_id,
        approved=request.approved,
        approved_by=request.approved_by,
        reason=request.reason,
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="approval_not_found")
    return approval
