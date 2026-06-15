"""Goal Manager API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.dependencies import get_goal_service
from aion_brain.contracts.goals import (
    GoalCreateRequest,
    GoalRecord,
    GoalStatus,
    GoalTransitionRequest,
)
from aion_brain.goals.service import GoalService

router = APIRouter(prefix="/brain/goals", tags=["goals"])


class GoalTransitionBody(BaseModel):
    """Goal transition body without path ID."""

    model_config = ConfigDict(extra="forbid")

    to_status: GoalStatus
    reason: str | None = None
    actor_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


@router.post("", response_model=GoalRecord)
def create_goal(
    request: GoalCreateRequest,
    service: Annotated[GoalService, Depends(get_goal_service)],
) -> GoalRecord:
    """Create a proposed goal."""
    try:
        return service.create_goal(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{goal_id}", response_model=GoalRecord)
def get_goal(
    goal_id: str,
    service: Annotated[GoalService, Depends(get_goal_service)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> GoalRecord:
    """Return a goal."""
    goal = service.get_goal(goal_id, scope or ["workspace:main"])
    if goal is None:
        raise HTTPException(status_code=404, detail="goal_not_found")
    return goal


@router.get("", response_model=list[GoalRecord])
def list_goals(
    service: Annotated[GoalService, Depends(get_goal_service)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: int = 50,
) -> list[GoalRecord]:
    """List goals."""
    return service.list_goals(scope or ["workspace:main"], status=status, limit=limit)


@router.post("/{goal_id}/transition", response_model=GoalRecord)
def transition_goal(
    goal_id: str,
    body: GoalTransitionBody,
    service: Annotated[GoalService, Depends(get_goal_service)],
) -> GoalRecord:
    """Transition a goal."""
    try:
        return service.transition_goal(
            GoalTransitionRequest(
                goal_id=goal_id,
                to_status=body.to_status,
                reason=body.reason,
                actor_id=body.actor_id,
                metadata=dict(body.metadata),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
