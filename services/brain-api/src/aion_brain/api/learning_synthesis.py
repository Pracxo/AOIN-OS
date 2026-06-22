"""Experience ledger and learning synthesis API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.experience import (
    ExperienceCreateRequest,
    ExperienceQuery,
    ExperienceRecord,
)
from aion_brain.contracts.learning_synthesis import (
    ExperienceQueryResult,
    LearningPattern,
    LearningSynthesisRequest,
    LearningSynthesisRun,
    LessonRecord,
    PatternMiningRequest,
    PatternMiningRun,
    RegressionCandidateSuggestion,
    SkillCandidateSuggestion,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/learning", tags=["learning-synthesis"])


class ReasonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class ConvertSkillSuggestionRequest(ReasonRequest):
    approval_present: bool = False


@router.post("/experiences", response_model=ExperienceRecord)
def create_experience(
    body: ExperienceCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExperienceRecord:
    try:
        return container.experience_service.create_experience(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/experiences/{experience_id}", response_model=ExperienceRecord)
def get_experience(
    experience_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExperienceRecord:
    try:
        experience = container.experience_service.get_experience(
            experience_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if experience is None:
        raise HTTPException(status_code=404, detail="experience_not_found")
    return experience


@router.post("/query", response_model=ExperienceQueryResult)
def query_learning(
    body: ExperienceQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ExperienceQueryResult:
    try:
        return container.learning_query_service.query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/experiences/{experience_id}/archive", response_model=ExperienceRecord)
def archive_experience(
    experience_id: str,
    body: ReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExperienceRecord:
    try:
        return container.experience_service.archive_experience(
            experience_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/patterns/mine", response_model=PatternMiningRun)
def mine_patterns(
    body: PatternMiningRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PatternMiningRun:
    try:
        return container.pattern_miner.mine(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/patterns", response_model=list[LearningPattern])
def list_patterns(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    pattern_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[LearningPattern]:
    return container.learning_synthesis_repository.list_patterns(
        _scope(scope, actor_context),
        status=status,
        pattern_type=pattern_type,
        limit=limit,
    )


@router.get("/lessons", response_model=list[LessonRecord])
def list_lessons(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    lesson_type: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[LessonRecord]:
    try:
        return container.lesson_service.list_lessons(
            _scope(scope, actor_context),
            lesson_type=lesson_type,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/synthesize", response_model=LearningSynthesisRun)
def synthesize(
    body: LearningSynthesisRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> LearningSynthesisRun:
    try:
        return container.learning_synthesizer.synthesize(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/synthesis/{synthesis_run_id}", response_model=LearningSynthesisRun)
def get_synthesis(
    synthesis_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> LearningSynthesisRun:
    run = container.learning_synthesizer.get(synthesis_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="synthesis_run_not_found")
    return run


@router.get("/skill-suggestions", response_model=list[SkillCandidateSuggestion])
def list_skill_suggestions(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[SkillCandidateSuggestion]:
    try:
        return container.skill_suggestion_service.list_suggestions(
            _scope(scope, actor_context),
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/skill-suggestions/{suggestion_id}/accept", response_model=SkillCandidateSuggestion)
def accept_skill_suggestion(
    suggestion_id: str,
    body: ReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SkillCandidateSuggestion:
    return container.skill_suggestion_service.accept_suggestion(
        suggestion_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


@router.post("/skill-suggestions/{suggestion_id}/reject", response_model=SkillCandidateSuggestion)
def reject_skill_suggestion(
    suggestion_id: str,
    body: ReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SkillCandidateSuggestion:
    return container.skill_suggestion_service.reject_suggestion(
        suggestion_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


@router.post(
    "/skill-suggestions/{suggestion_id}/convert-to-candidate",
    response_model=SkillCandidateSuggestion,
)
def convert_skill_suggestion(
    suggestion_id: str,
    body: ConvertSkillSuggestionRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> SkillCandidateSuggestion:
    return container.skill_suggestion_service.convert_to_skill_candidate(
        suggestion_id,
        body.actor_id or actor_context.actor_id,
        body.approval_present,
        body.reason,
    )


@router.get("/regression-suggestions", response_model=list[RegressionCandidateSuggestion])
def list_regression_suggestions(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[RegressionCandidateSuggestion]:
    try:
        return container.regression_suggestion_service.list_suggestions(
            _scope(scope, actor_context),
            status=status,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/regression-suggestions/{regression_suggestion_id}/accept",
    response_model=RegressionCandidateSuggestion,
)
def accept_regression_suggestion(
    regression_suggestion_id: str,
    body: ReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RegressionCandidateSuggestion:
    return container.regression_suggestion_service.accept_suggestion(
        regression_suggestion_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


@router.post(
    "/regression-suggestions/{regression_suggestion_id}/reject",
    response_model=RegressionCandidateSuggestion,
)
def reject_regression_suggestion(
    regression_suggestion_id: str,
    body: ReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RegressionCandidateSuggestion:
    return container.regression_suggestion_service.reject_suggestion(
        regression_suggestion_id,
        body.actor_id or actor_context.actor_id,
        body.reason,
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope


__all__ = ["router"]
