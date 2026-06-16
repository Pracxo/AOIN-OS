"""Decision intelligence API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.counterfactuals import CounterfactualRun, CounterfactualRunRequest
from aion_brain.contracts.decisions import (
    DecisionEvaluationRequest,
    DecisionFrame,
    DecisionFrameCreateRequest,
    DecisionOption,
    DecisionOptionCreateRequest,
    DecisionRecommendation,
    DecisionRecord,
    DecisionRecordRequest,
    UtilityProfile,
    UtilityProfileCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/decisions", tags=["decisions"])


class CloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class SeedProfilesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    dry_run: bool = True


class RecommendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    utility_profile_id: str | None = None
    approval_present: bool = False
    dry_run: bool = True


@router.get("/frames", response_model=list[DecisionFrame])
def list_frames(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    frame_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[DecisionFrame]:
    try:
        return container.decision_frame_service.list_frames(
            _scope(scope, actor_context),
            status=status,
            frame_type=frame_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/frames", response_model=DecisionFrame)
def create_frame(
    body: DecisionFrameCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DecisionFrame:
    try:
        return container.decision_frame_service.create_frame(
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


@router.get("/frames/{decision_frame_id}", response_model=DecisionFrame)
def get_frame(
    decision_frame_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> DecisionFrame:
    try:
        frame = container.decision_frame_service.get_frame(
            decision_frame_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if frame is None:
        raise HTTPException(status_code=404, detail="decision_frame_not_found")
    return frame


@router.post("/frames/{decision_frame_id}/close", response_model=DecisionFrame)
def close_frame(
    decision_frame_id: str,
    body: CloseRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> DecisionFrame:
    try:
        return container.decision_frame_service.close_frame(
            decision_frame_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/options", response_model=DecisionOption)
def create_option(
    body: DecisionOptionCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> DecisionOption:
    try:
        return container.decision_option_service.create_option(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/frames/{decision_frame_id}/options", response_model=list[DecisionOption])
def list_options(
    decision_frame_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    status: str | None = None,
) -> list[DecisionOption]:
    return container.decision_option_service.list_options(decision_frame_id, status=status)


@router.post("/options/{decision_option_id}/archive", response_model=DecisionOption)
def archive_option(
    decision_option_id: str,
    body: CloseRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DecisionOption:
    try:
        return container.decision_option_service.archive_option(
            decision_option_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/utility-profiles", response_model=UtilityProfile)
def create_utility_profile(
    body: UtilityProfileCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> UtilityProfile:
    try:
        return container.utility_profile_service.create_profile(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/utility-profiles", response_model=list[UtilityProfile])
def list_utility_profiles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
) -> list[UtilityProfile]:
    try:
        return container.utility_profile_service.list_profiles(_scope(scope, actor_context), status)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/utility-profiles/seed-defaults", response_model=dict[str, object])
def seed_utility_profiles(
    body: SeedProfilesRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    return container.utility_profile_service.seed_default_profiles(
        dry_run=body.dry_run,
        owner_scope=body.scope or actor_context.security_scope,
    )


@router.post("/evaluate", response_model=DecisionRecommendation)
def evaluate_decision(
    body: DecisionEvaluationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> DecisionRecommendation:
    try:
        return container.option_evaluator.evaluate(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/recommend/{decision_frame_id}", response_model=DecisionRecommendation)
def recommend_decision(
    decision_frame_id: str,
    body: RecommendRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> DecisionRecommendation:
    try:
        return container.decision_recommendation_service.recommend(
            decision_frame_id,
            utility_profile_id=body.utility_profile_id,
            approval_present=body.approval_present,
            dry_run=body.dry_run,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/counterfactuals/run", response_model=CounterfactualRun)
def run_counterfactual(
    body: CounterfactualRunRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CounterfactualRun:
    return container.counterfactual_simulator.run(
        body.model_copy(
            update={
                "owner_scope": body.owner_scope or actor_context.security_scope,
                "trace_id": body.trace_id or actor_context.trace_id,
                "created_by": body.created_by or actor_context.actor_id,
            }
        )
    )


@router.get("/counterfactuals/{counterfactual_run_id}", response_model=CounterfactualRun)
def get_counterfactual(
    counterfactual_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> CounterfactualRun:
    run = container.counterfactual_simulator.get(counterfactual_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="counterfactual_run_not_found")
    return run


@router.post("/journal", response_model=DecisionRecord)
def record_decision(
    body: DecisionRecordRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DecisionRecord:
    try:
        return container.decision_journal_service.record_decision(
            body.model_copy(
                update={
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/journal", response_model=list[DecisionRecord])
def list_decision_records(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    decision_frame_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[DecisionRecord]:
    try:
        return container.decision_journal_service.list_records(
            _scope(scope, actor_context),
            decision_frame_id=decision_frame_id,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/journal/{decision_record_id}", response_model=DecisionRecord)
def get_decision_record(
    decision_record_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> DecisionRecord:
    try:
        record = container.decision_journal_service.get_record(
            decision_record_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="decision_record_not_found")
    return record


@router.post("/journal/{decision_record_id}/supersede", response_model=DecisionRecord)
def supersede_decision_record(
    decision_record_id: str,
    body: CloseRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> DecisionRecord:
    try:
        return container.decision_journal_service.supersede_record(
            decision_record_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope
