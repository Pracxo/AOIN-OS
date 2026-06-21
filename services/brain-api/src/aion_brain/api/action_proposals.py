"""Action proposal broker API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.action_proposals import (
    ActionBlocker,
    ActionProposal,
    ActionProposalCreateRequest,
    ActionProposalQuery,
    ActionProposalQueryResult,
    ActionProposalReview,
    ActionProposalReviewRequest,
    ToolIntentReview,
    ToolIntentReviewRequest,
)
from aion_brain.contracts.execution_handoffs import ExecutionHandoff, ExecutionHandoffRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/action-proposals", tags=["action-proposals"])


class ReasonRequest(BaseModel):
    """Actor and reason body."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


@router.post("", response_model=ActionProposal)
def create_action_proposal(
    body: ActionProposalCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActionProposal:
    """Create an action proposal. Proposals do not execute themselves."""

    try:
        return container.action_proposal_service.with_actor_context(actor_context).create_proposal(
            _proposal_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/query", response_model=ActionProposalQueryResult)
def query_action_proposals(
    body: ActionProposalQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActionProposalQueryResult:
    """Query action proposal broker records."""

    try:
        return container.action_proposal_query_service.with_actor_context(actor_context).query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/tool-intents/{tool_intent_id}/review", response_model=ToolIntentReview)
def review_tool_intent(
    tool_intent_id: str,
    body: ToolIntentReviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ToolIntentReview:
    """Review a captured tool intent without executing it."""

    request = body.model_copy(update={"tool_intent_id": tool_intent_id})
    try:
        return container.tool_intent_review_service.with_actor_context(actor_context).review(
            _tool_review_with_context(request, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/tool-intent-reviews", response_model=list[ToolIntentReview])
def list_tool_intent_reviews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    tool_intent_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ToolIntentReview]:
    """List tool intent reviews."""

    return container.tool_intent_review_service.with_actor_context(actor_context).list_reviews(
        tool_intent_id=tool_intent_id, status=status, limit=limit
    )


@router.get("/blockers", response_model=list[ActionBlocker])
def list_action_blockers(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    action_proposal_id: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ActionBlocker]:
    """List action blockers."""

    try:
        return container.action_blocker_service.with_actor_context(actor_context).list_blockers(
            action_proposal_id=action_proposal_id,
            status=status,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/blockers/{action_blocker_id}/resolve", response_model=ActionBlocker)
def resolve_action_blocker(
    action_blocker_id: str,
    body: ReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActionBlocker:
    """Resolve a blocker without executing a proposal."""

    try:
        return container.action_blocker_service.with_actor_context(actor_context).resolve_blocker(
            action_blocker_id,
            actor_id=body.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/handoff", response_model=ExecutionHandoff)
def create_execution_handoff(
    body: ExecutionHandoffRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ExecutionHandoff:
    """Create an explicit execution handoff. Dry-run is the default."""

    try:
        return container.execution_handoff_service.with_actor_context(actor_context).handoff(
            _handoff_with_context(body, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/handoffs/{execution_handoff_id}", response_model=ExecutionHandoff)
def get_execution_handoff(
    execution_handoff_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ExecutionHandoff:
    """Return one execution handoff."""

    try:
        handoff = container.execution_handoff_service.with_actor_context(actor_context).get_handoff(
            execution_handoff_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if handoff is None:
        raise HTTPException(status_code=404, detail="execution_handoff_not_found")
    return handoff


@router.get("/handoffs", response_model=list[ExecutionHandoff])
def list_execution_handoffs(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    action_proposal_id: str | None = None,
    status: str | None = None,
    target_system: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ExecutionHandoff]:
    """List execution handoffs."""

    return container.execution_handoff_service.with_actor_context(actor_context).list_handoffs(
        action_proposal_id=action_proposal_id,
        status=status,
        target_system=target_system,
        limit=limit,
    )


@router.get("/{action_proposal_id}", response_model=ActionProposal)
def get_action_proposal(
    action_proposal_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ActionProposal:
    """Return one action proposal."""

    try:
        proposal = container.action_proposal_service.with_actor_context(actor_context).get_proposal(
            action_proposal_id, _scope(scope, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if proposal is None:
        raise HTTPException(status_code=404, detail="action_proposal_not_found")
    return proposal


@router.post("/{action_proposal_id}/archive", response_model=ActionProposal)
def archive_action_proposal(
    action_proposal_id: str,
    body: ReasonRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActionProposal:
    """Archive one action proposal."""

    try:
        return container.action_proposal_service.with_actor_context(actor_context).archive_proposal(
            action_proposal_id, actor_id=body.actor_id, reason=body.reason
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{action_proposal_id}")
def delete_action_proposal(
    action_proposal_id: str,
    body: Annotated[ReasonRequest, Body()],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Soft delete one action proposal."""

    try:
        deleted = container.action_proposal_service.with_actor_context(
            actor_context
        ).soft_delete_proposal(action_proposal_id, actor_id=body.actor_id, reason=body.reason)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": deleted, "action_proposal_id": action_proposal_id}


@router.post("/{action_proposal_id}/review", response_model=ActionProposalReview)
def review_action_proposal(
    action_proposal_id: str,
    body: ActionProposalReviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActionProposalReview:
    """Review a proposal. Review does not hand off."""

    request = body.model_copy(update={"action_proposal_id": action_proposal_id})
    try:
        return container.action_review_service.with_actor_context(actor_context).review(
            _review_with_context(request, actor_context)
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{action_proposal_id}/reviews", response_model=list[ActionProposalReview])
def list_action_reviews(
    action_proposal_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[ActionProposalReview]:
    """List reviews for one proposal."""

    return container.action_review_service.with_actor_context(actor_context).list_reviews(
        action_proposal_id=action_proposal_id
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    if scope:
        return scope
    if actor_context.security_scope:
        return actor_context.security_scope
    if actor_context.workspace_id:
        return [f"workspace:{actor_context.workspace_id}"]
    return ["workspace:main"]


def _proposal_with_context(
    body: ActionProposalCreateRequest,
    actor_context: ActorContext,
) -> ActionProposalCreateRequest:
    updates: dict[str, object] = {}
    if body.actor_id is None and actor_context.actor_id:
        updates["actor_id"] = actor_context.actor_id
    if body.workspace_id is None and actor_context.workspace_id:
        updates["workspace_id"] = actor_context.workspace_id
    if body.created_by is None and actor_context.actor_id:
        updates["created_by"] = actor_context.actor_id
    return body.model_copy(update=updates) if updates else body


def _review_with_context(
    body: ActionProposalReviewRequest,
    actor_context: ActorContext,
) -> ActionProposalReviewRequest:
    updates: dict[str, object] = {}
    if body.actor_id is None and actor_context.actor_id:
        updates["actor_id"] = actor_context.actor_id
    if body.workspace_id is None and actor_context.workspace_id:
        updates["workspace_id"] = actor_context.workspace_id
    return body.model_copy(update=updates) if updates else body


def _tool_review_with_context(
    body: ToolIntentReviewRequest,
    actor_context: ActorContext,
) -> ToolIntentReviewRequest:
    updates: dict[str, object] = {}
    if not body.owner_scope:
        updates["owner_scope"] = _scope(None, actor_context)
    if body.actor_id is None and actor_context.actor_id:
        updates["actor_id"] = actor_context.actor_id
    if body.workspace_id is None and actor_context.workspace_id:
        updates["workspace_id"] = actor_context.workspace_id
    if body.created_by is None and actor_context.actor_id:
        updates["created_by"] = actor_context.actor_id
    return body.model_copy(update=updates) if updates else body


def _handoff_with_context(
    body: ExecutionHandoffRequest,
    actor_context: ActorContext,
) -> ExecutionHandoffRequest:
    updates: dict[str, object] = {}
    if body.actor_id is None and actor_context.actor_id:
        updates["actor_id"] = actor_context.actor_id
    if body.workspace_id is None and actor_context.workspace_id:
        updates["workspace_id"] = actor_context.workspace_id
    if body.created_by is None and actor_context.actor_id:
        updates["created_by"] = actor_context.actor_id
    return body.model_copy(update=updates) if updates else body


__all__ = ["router"]
