"""Skill Registry API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.dependencies import get_skill_service
from aion_brain.contracts.skills import (
    SkillActivationRequest,
    SkillCandidate,
    SkillCandidateStatus,
    SkillMatchRequest,
    SkillMatchResult,
    SkillPromotionRequest,
    SkillPromotionResponse,
    SkillRecord,
    SkillStatus,
)
from aion_brain.skills.service import SkillService

router = APIRouter(prefix="/brain/skills", tags=["skills"])


class CandidateStatusBody(BaseModel):
    """Candidate status update body."""

    model_config = ConfigDict(extra="forbid")

    status: SkillCandidateStatus
    reason: str = Field(min_length=1)


class SkillTransitionBody(BaseModel):
    """Skill transition body without path ID."""

    model_config = ConfigDict(extra="forbid")

    to_status: SkillStatus
    actor_id: str | None = None
    reason: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)


@router.post("/candidates/from-reflection/{reflection_id}", response_model=SkillCandidate | None)
def create_candidate_from_reflection(
    reflection_id: str,
    service: Annotated[SkillService, Depends(get_skill_service)],
) -> SkillCandidate | None:
    """Create a skill candidate from a reflection when evidence supports it."""
    try:
        return service.create_candidate_from_reflection(reflection_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/candidates/{candidate_id}", response_model=SkillCandidate)
def get_candidate(
    candidate_id: str,
    service: Annotated[SkillService, Depends(get_skill_service)],
) -> SkillCandidate:
    """Return a skill candidate."""
    candidate = service.get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate_not_found")
    return candidate


@router.get("/candidates", response_model=list[SkillCandidate])
def list_candidates(
    service: Annotated[SkillService, Depends(get_skill_service)],
    status: str | None = None,
    limit: int = 50,
) -> list[SkillCandidate]:
    """List skill candidates."""
    return service.list_candidates(status=status, limit=limit)


@router.post("/candidates/{candidate_id}/status", response_model=SkillCandidate)
def update_candidate_status(
    candidate_id: str,
    body: CandidateStatusBody,
    service: Annotated[SkillService, Depends(get_skill_service)],
) -> SkillCandidate:
    """Update skill candidate review status."""
    try:
        return service.update_candidate_status(candidate_id, body.status, body.reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/promote", response_model=SkillPromotionResponse)
def promote_candidate(
    request: SkillPromotionRequest,
    service: Annotated[SkillService, Depends(get_skill_service)],
) -> SkillPromotionResponse:
    """Promote a reviewed skill candidate into a data-only skill."""
    return service.promote_candidate(request)


@router.get("/{skill_id}", response_model=SkillRecord)
def get_skill(
    skill_id: str,
    service: Annotated[SkillService, Depends(get_skill_service)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> SkillRecord:
    """Return a skill."""
    skill = service.get_skill(skill_id, scope or ["workspace:main"])
    if skill is None:
        raise HTTPException(status_code=404, detail="skill_not_found")
    return skill


@router.get("", response_model=list[SkillRecord])
def list_skills(
    service: Annotated[SkillService, Depends(get_skill_service)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: int = 50,
) -> list[SkillRecord]:
    """List skills."""
    return service.list_skills(scope or ["workspace:main"], status=status, limit=limit)


@router.post("/{skill_id}/transition", response_model=SkillRecord)
def transition_skill(
    skill_id: str,
    body: SkillTransitionBody,
    service: Annotated[SkillService, Depends(get_skill_service)],
) -> SkillRecord:
    """Transition a skill status."""
    try:
        return service.transition_skill(
            SkillActivationRequest(
                skill_id=skill_id,
                to_status=body.to_status,
                actor_id=body.actor_id,
                reason=body.reason,
                metadata=dict(body.metadata),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/match", response_model=list[SkillMatchResult])
def match_skills(
    request: SkillMatchRequest,
    service: Annotated[SkillService, Depends(get_skill_service)],
) -> list[SkillMatchResult]:
    """Match active procedural skills."""
    try:
        return service.match_skills(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
