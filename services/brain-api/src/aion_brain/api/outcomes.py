"""Outcome ledger and effect verification API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.effects import (
    ExpectedEffect,
    ExpectedEffectCreateRequest,
    ObservedEffect,
    ObservedEffectCreateRequest,
)
from aion_brain.contracts.outcomes import (
    CausalAttribution,
    EffectVerificationRequest,
    EffectVerificationRun,
    OutcomeCreateRequest,
    OutcomeFeedback,
    OutcomeQuery,
    OutcomeQueryResult,
    OutcomeRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/outcomes", tags=["outcomes"])


class CloseOutcomeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class LearningBridgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dry_run: bool = True


@router.post("/expected-effects", response_model=ExpectedEffect)
def create_expected_effect(
    body: ExpectedEffectCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExpectedEffect:
    try:
        return container.expected_effect_service.create_expected_effect(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/expected-effects", response_model=list[ExpectedEffect])
def list_expected_effects(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    source_type: str | None = None,
    source_id: str | None = None,
    trace_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ExpectedEffect]:
    try:
        return container.expected_effect_service.list_expected_effects(
            source_type=source_type,
            source_id=source_id,
            trace_id=trace_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/observed-effects", response_model=ObservedEffect)
def create_observed_effect(
    body: ObservedEffectCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ObservedEffect:
    try:
        return container.observed_effect_collector.create_observed_effect(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/observed-effects", response_model=list[ObservedEffect])
def list_observed_effects(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    outcome_id: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ObservedEffect]:
    try:
        return container.observed_effect_collector.list_observed_effects(
            outcome_id=outcome_id,
            source_type=source_type,
            source_id=source_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/verify", response_model=EffectVerificationRun)
def verify_effects(
    body: EffectVerificationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EffectVerificationRun:
    try:
        return container.effect_verifier.verify(
            body.model_copy(
                update={
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "trace_id": body.trace_id or actor_context.trace_id,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/verifications/{verification_run_id}", response_model=EffectVerificationRun)
def get_verification(
    verification_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> EffectVerificationRun:
    run = container.effect_verifier.get(verification_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="verification_run_not_found")
    return run


@router.post("/attributions", response_model=CausalAttribution)
def create_attribution(
    body: CausalAttribution,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> CausalAttribution:
    try:
        return container.causal_attribution_service.create_attribution(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/attributions", response_model=list[CausalAttribution])
def list_attributions(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    outcome_id: str | None = None,
    cause_type: str | None = None,
    cause_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[CausalAttribution]:
    try:
        return container.causal_attribution_service.list_attributions(
            outcome_id=outcome_id,
            cause_type=cause_type,
            cause_id=cause_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/feedback", response_model=OutcomeFeedback)
def create_feedback(
    body: OutcomeFeedback,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> OutcomeFeedback:
    try:
        return container.outcome_feedback_service.create_feedback(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/feedback", response_model=list[OutcomeFeedback])
def list_feedback(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    outcome_id: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[OutcomeFeedback]:
    try:
        return container.outcome_feedback_service.list_feedback(
            outcome_id=outcome_id,
            status=status,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/feedback/{outcome_feedback_id}/resolve", response_model=OutcomeFeedback)
def resolve_feedback(
    outcome_feedback_id: str,
    body: CloseOutcomeRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OutcomeFeedback:
    try:
        return container.outcome_feedback_service.resolve_feedback(
            outcome_feedback_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/query", response_model=OutcomeQueryResult)
def query_outcomes(
    body: OutcomeQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OutcomeQueryResult:
    try:
        return container.outcome_query_service.query(
            body.model_copy(update={"scope": body.scope or actor_context.security_scope})
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("", response_model=OutcomeRecord)
@router.post("/", response_model=OutcomeRecord)
def create_outcome(
    body: OutcomeCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OutcomeRecord:
    try:
        return container.outcome_service.create_outcome(
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


@router.get("/{outcome_id}", response_model=OutcomeRecord)
def get_outcome(
    outcome_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> OutcomeRecord:
    try:
        outcome = container.outcome_service.get_outcome(outcome_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if outcome is None:
        raise HTTPException(status_code=404, detail="outcome_not_found")
    return outcome


@router.post("/{outcome_id}/close", response_model=OutcomeRecord)
def close_outcome(
    outcome_id: str,
    body: CloseOutcomeRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> OutcomeRecord:
    try:
        return container.outcome_service.close_outcome(
            outcome_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{outcome_id}", response_model=dict[str, object])
def delete_outcome(
    outcome_id: str,
    body: CloseOutcomeRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> dict[str, object]:
    try:
        deleted = container.outcome_service.soft_delete_outcome(
            outcome_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="outcome_not_found")
    return {"deleted": True, "outcome_id": outcome_id}


@router.post("/{outcome_id}/learning-bridge", response_model=dict[str, object])
def learning_bridge(
    outcome_id: str,
    body: LearningBridgeRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> dict[str, object]:
    try:
        return container.outcome_feedback_service.bridge_to_learning(
            outcome_id,
            dry_run=body.dry_run,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope


__all__ = ["router"]
