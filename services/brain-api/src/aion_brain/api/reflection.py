"""Reflection Engine API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion_brain.api.dependencies import get_reflection_engine, get_reflection_repository
from aion_brain.contracts.reflection import ReflectionRecord, ReflectionRequest
from aion_brain.reflection.engine import ReflectionEngine
from aion_brain.reflection.repository import ReflectionRepository

router = APIRouter(prefix="/brain/reflections", tags=["reflection"])


@router.post("", response_model=ReflectionRecord)
def create_reflection(
    request: ReflectionRequest,
    engine: Annotated[ReflectionEngine, Depends(get_reflection_engine)],
) -> ReflectionRecord:
    """Create a deterministic reflection."""
    try:
        return engine.reflect(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{reflection_id}", response_model=ReflectionRecord)
def get_reflection(
    reflection_id: str,
    repository: Annotated[ReflectionRepository, Depends(get_reflection_repository)],
) -> ReflectionRecord:
    """Return a reflection record."""
    reflection = repository.get_reflection(reflection_id)
    if reflection is None:
        raise HTTPException(status_code=404, detail="reflection_not_found")
    return reflection


@router.get("", response_model=list[ReflectionRecord])
def list_reflections(
    repository: Annotated[ReflectionRepository, Depends(get_reflection_repository)],
    trace_id: str | None = None,
    task_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[ReflectionRecord]:
    """List reflection records."""
    return repository.list_reflections(
        trace_id=trace_id,
        task_id=task_id,
        status=status,
        limit=limit,
    )
