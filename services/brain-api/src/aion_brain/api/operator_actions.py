"""Governed operator actions API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.operator_actions import (
    OperatorActionBlocker,
    OperatorActionCreateRequest,
    OperatorActionPreview,
    OperatorActionQuery,
    OperatorActionQueryResult,
    OperatorActionRequest,
    OperatorActionReview,
    OperatorActionReviewRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/operator-actions", tags=["operator-actions"])


class PreviewRequest(BaseModel):
    """Create preview request body."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    created_by: str | None = None


class DismissRequest(BaseModel):
    """Dismiss blocker body."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


@router.post("/requests", response_model=OperatorActionRequest)
def create_operator_action_request(
    body: OperatorActionCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OperatorActionRequest:
    """Create a dry-run operator action request. This never executes."""

    try:
        return container.operator_action_request_service.with_actor_context(
            actor_context
        ).create_request(_create_with_context(body, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/requests/{operator_action_request_id}", response_model=OperatorActionRequest)
def get_operator_action_request(
    operator_action_request_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> OperatorActionRequest:
    """Return one dry-run operator action request."""

    try:
        request = container.operator_action_request_service.with_actor_context(
            actor_context
        ).get_request(operator_action_request_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if request is None:
        raise HTTPException(status_code=404, detail="operator_action_request_not_found")
    return request


@router.get("/requests", response_model=list[OperatorActionRequest])
def list_operator_action_requests(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    action_type: str | None = None,
    target_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[OperatorActionRequest]:
    """List dry-run operator action requests."""

    try:
        return container.operator_action_request_service.with_actor_context(
            actor_context
        ).list_requests(
            _scope(scope, actor_context),
            status=status,
            action_type=action_type,
            target_type=target_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/requests/{operator_action_request_id}/preview",
    response_model=OperatorActionPreview,
)
def create_operator_action_preview(
    operator_action_request_id: str,
    body: PreviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OperatorActionPreview:
    """Create a dry-run preview. It does not execute."""

    try:
        return container.operator_action_preview_service.with_actor_context(
            actor_context
        ).create_preview(
            operator_action_request_id,
            _scope(body.scope or None, actor_context),
            created_by=body.created_by or actor_context.actor_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/previews", response_model=list[OperatorActionPreview])
def list_operator_action_previews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[OperatorActionPreview]:
    """List dry-run operator action previews."""

    try:
        return container.operator_action_preview_service.with_actor_context(
            actor_context
        ).list_previews(_scope(scope, actor_context), status=status, limit=limit)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/blockers", response_model=list[OperatorActionBlocker])
def list_operator_action_blockers(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    operator_action_request_id: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[OperatorActionBlocker]:
    """List operator action blockers."""

    try:
        return container.operator_action_blocker_service.with_actor_context(
            actor_context
        ).list_blockers(
            _scope(scope, actor_context),
            operator_action_request_id=operator_action_request_id,
            status=status,
            severity=severity,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post(
    "/blockers/{operator_action_blocker_id}/dismiss",
    response_model=OperatorActionBlocker,
)
def dismiss_operator_action_blocker(
    operator_action_blocker_id: str,
    body: DismissRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OperatorActionBlocker:
    """Dismiss one blocker. Dismissal does not enable execution."""

    try:
        return container.operator_action_blocker_service.with_actor_context(
            actor_context
        ).dismiss_blocker(
            operator_action_blocker_id,
            actor_id=body.actor_id or actor_context.actor_id,
            reason=body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/requests/{operator_action_request_id}/review",
    response_model=OperatorActionReview,
)
def review_operator_action_request(
    operator_action_request_id: str,
    body: OperatorActionReviewRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OperatorActionReview:
    """Create a review record. Review does not execute."""

    try:
        return container.operator_action_review_service.with_actor_context(
            actor_context
        ).review(_review_with_context(body, operator_action_request_id, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/reviews", response_model=list[OperatorActionReview])
def list_operator_action_reviews(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    operator_action_request_id: str | None = None,
    decision: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[OperatorActionReview]:
    """List operator action reviews."""

    try:
        return container.operator_action_review_service.with_actor_context(
            actor_context
        ).list_reviews(
            _scope(scope, actor_context),
            operator_action_request_id=operator_action_request_id,
            decision=decision,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/query", response_model=OperatorActionQueryResult)
def query_operator_actions(
    body: OperatorActionQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OperatorActionQueryResult:
    """Query dry-run operator action records."""

    try:
        return container.operator_action_query_service.with_actor_context(actor_context).query(body)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    if scope:
        return scope
    if actor_context.security_scope:
        return actor_context.security_scope
    if actor_context.workspace_id:
        return [f"workspace:{actor_context.workspace_id}"]
    return ["workspace:main"]


def _create_with_context(
    body: OperatorActionCreateRequest,
    actor_context: ActorContext,
) -> OperatorActionCreateRequest:
    updates: dict[str, object] = {}
    if body.actor_id is None and actor_context.actor_id:
        updates["actor_id"] = actor_context.actor_id
    if body.workspace_id is None and actor_context.workspace_id:
        updates["workspace_id"] = actor_context.workspace_id
    if body.created_by is None and actor_context.actor_id:
        updates["created_by"] = actor_context.actor_id
    return body.model_copy(update=updates) if updates else body


def _review_with_context(
    body: OperatorActionReviewRequest,
    operator_action_request_id: str,
    actor_context: ActorContext,
) -> OperatorActionReviewRequest:
    updates: dict[str, object] = {"operator_action_request_id": operator_action_request_id}
    if body.actor_id is None and actor_context.actor_id:
        updates["actor_id"] = actor_context.actor_id
    if body.workspace_id is None and actor_context.workspace_id:
        updates["workspace_id"] = actor_context.workspace_id
    return body.model_copy(update=updates)


__all__ = ["router"]
