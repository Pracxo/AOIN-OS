"""Explanation Engine API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.explanations import (
    ExplanationFeedback,
    ExplanationRecord,
    ExplanationRequest,
    ExplanationVerification,
    WhyNotAnswer,
    WhyNotRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.trace_narratives import TraceNarrative, TraceNarrativeRequest
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["explanations"])


@router.post("/brain/explanations", response_model=ExplanationRecord)
def create_explanation(
    body: ExplanationRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExplanationRecord:
    """Create a deterministic grounded explanation."""

    try:
        return container.explanation_builder.explain(
            body.model_copy(update=_context_updates(body, actor_context))
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/explanations", response_model=list[ExplanationRecord])
def list_explanations(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    trace_id: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[ExplanationRecord]:
    """List stored explanations."""

    return container.explanation_builder.list(
        trace_id=trace_id,
        target_type=target_type,
        target_id=target_id,
        limit=limit,
    )


@router.post("/brain/explanations/why-not", response_model=WhyNotAnswer)
def create_why_not(
    body: WhyNotRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> WhyNotAnswer:
    """Create a why-not answer."""

    try:
        return container.why_not_service.answer(
            body.model_copy(update=_context_updates(body, actor_context))
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/explanations/why-not/{why_not_id}", response_model=WhyNotAnswer)
def get_why_not(
    why_not_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> WhyNotAnswer:
    """Return a why-not answer."""

    try:
        answer = container.why_not_service.get(why_not_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if answer is None:
        raise HTTPException(status_code=404, detail="why_not_not_found")
    return answer


@router.post("/brain/explanations/feedback", response_model=ExplanationFeedback)
def create_feedback(
    body: ExplanationFeedback,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExplanationFeedback:
    """Record explanation feedback."""

    metadata = {**body.metadata}
    metadata.setdefault("owner_scope", actor_context.security_scope or ["workspace:main"])
    try:
        return container.explanation_feedback_service.create_feedback(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "metadata": metadata,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/explanations/feedback", response_model=list[ExplanationFeedback])
def list_feedback(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    explanation_id: str | None = None,
    trace_narrative_id: str | None = None,
    why_not_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ExplanationFeedback]:
    """List explanation feedback."""

    try:
        return container.explanation_feedback_service.list_feedback(
            explanation_id=explanation_id,
            trace_narrative_id=trace_narrative_id,
            why_not_id=why_not_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/brain/explanations/{explanation_id}/verify", response_model=ExplanationVerification)
def verify_explanation(
    explanation_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ExplanationVerification:
    """Verify a stored explanation."""

    explanation = container.explanation_repository.get_explanation(explanation_id)
    if explanation is None:
        raise HTTPException(status_code=404, detail="explanation_not_found")
    return container.explanation_verifier.verify_explanation(explanation)


@router.get("/brain/explanations/{explanation_id}", response_model=ExplanationRecord)
def get_explanation(
    explanation_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExplanationRecord:
    """Return one stored explanation."""

    try:
        explanation = container.explanation_builder.get(
            explanation_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if explanation is None:
        raise HTTPException(status_code=404, detail="explanation_not_found")
    return explanation


@router.post("/brain/traces/{trace_id}/narrative", response_model=TraceNarrative)
def create_trace_narrative(
    trace_id: str,
    body: TraceNarrativeRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> TraceNarrative:
    """Build a deterministic trace narrative."""

    try:
        return container.trace_narrative_builder.build(
            body.model_copy(
                update={
                    "trace_id": trace_id,
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "created_by": body.created_by or actor_context.actor_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/brain/traces/narratives/{trace_narrative_id}", response_model=TraceNarrative)
def get_trace_narrative(
    trace_narrative_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> TraceNarrative:
    """Return one trace narrative."""

    try:
        narrative = container.trace_narrative_builder.get(
            trace_narrative_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if narrative is None:
        raise HTTPException(status_code=404, detail="trace_narrative_not_found")
    return narrative


@router.get("/brain/traces/{trace_id}/narratives", response_model=list[TraceNarrative])
def list_trace_narratives(
    trace_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[TraceNarrative]:
    """List narratives for one trace."""

    return container.trace_narrative_builder.list(trace_id=trace_id, limit=limit)


def _context_updates(body: object, actor_context: ActorContext) -> dict[str, object]:
    owner_scope = getattr(body, "owner_scope", None) or actor_context.security_scope
    return {
        "owner_scope": owner_scope or ["workspace:main"],
        "actor_id": getattr(body, "actor_id", None) or actor_context.actor_id,
        "workspace_id": getattr(body, "workspace_id", None) or actor_context.workspace_id,
        "created_by": getattr(body, "created_by", None) or actor_context.actor_id,
    }


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope or ["workspace:main"]


__all__ = ["router"]
