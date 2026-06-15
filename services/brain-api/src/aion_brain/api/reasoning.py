"""Reasoning Mesh API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from aion_brain.config import get_settings
from aion_brain.contracts.reasoning import ModelCallRecord, ReasoningRequest, ReasoningResult
from aion_brain.kernel.container import KernelContainer
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter
from aion_brain.reasoning.mesh import ReasoningMesh
from aion_brain.reasoning.prompt_builder import PromptBuilder
from aion_brain.reasoning.repository import ReasoningRepository
from aion_brain.reasoning.router import ModelRouter

router = APIRouter(prefix="/brain", tags=["reasoning"])


def get_reasoning_mesh(request: Request) -> ReasoningMesh:
    """Create the configured Reasoning Mesh."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.reasoning_mesh
    settings = get_settings()
    return get_cached_reasoning_mesh(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_reasoning_mesh(database_url: str, opa_url: str) -> ReasoningMesh:
    """Return a cached Reasoning Mesh."""
    policy_adapter = OPAAdapter(opa_url)
    repository = get_cached_reasoning_repository(database_url)
    return ReasoningMesh(
        model_router=ModelRouter(),
        prompt_builder=PromptBuilder(),
        model_gateway_adapter=DeterministicReasoningAdapter(),
        policy_adapter=policy_adapter,
        reasoning_repository=repository,
        telemetry_service=None,
    )


def get_reasoning_repository(request: Request) -> ReasoningRepository:
    """Create the configured reasoning repository."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.reasoning_repository
    settings = get_settings()
    return get_cached_reasoning_repository(settings.database_url)


@lru_cache
def get_cached_reasoning_repository(database_url: str) -> ReasoningRepository:
    """Return a cached reasoning repository."""
    return ReasoningRepository(database_url)


@router.post("/reason", response_model=ReasoningResult)
def reason(
    request: ReasoningRequest,
    reasoning_mesh: Annotated[ReasoningMesh, Depends(get_reasoning_mesh)],
) -> ReasoningResult:
    """Run the Reasoning Mesh."""
    return reasoning_mesh.reason(request)


@router.get("/reason/{reasoning_id}", response_model=ReasoningResult)
def get_reasoning(
    reasoning_id: str,
    repository: Annotated[ReasoningRepository, Depends(get_reasoning_repository)],
) -> ReasoningResult:
    """Return a persisted reasoning result."""
    result = repository.get_reasoning(reasoning_id)
    if result is None:
        raise HTTPException(status_code=404, detail="reasoning_not_found")
    return result


@router.get("/model-calls/{model_call_id}", response_model=ModelCallRecord)
def get_model_call(
    model_call_id: str,
    repository: Annotated[ReasoningRepository, Depends(get_reasoning_repository)],
) -> ModelCallRecord:
    """Return a persisted model call ledger record."""
    record = repository.get_model_call(model_call_id)
    if record is None:
        raise HTTPException(status_code=404, detail="model_call_not_found")
    return record
