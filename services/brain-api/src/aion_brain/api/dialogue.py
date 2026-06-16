"""Dialogue API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.dialogue import (
    ClarificationAnswerRequest,
    ClarificationRequest,
    DialogueFeedback,
    DialogueMessage,
    DialogueMessageCreateRequest,
    DialogueSession,
    DialogueSessionCreateRequest,
    DialogueTurnRequest,
    DialogueTurnResult,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/dialogue", tags=["dialogue"])


class CloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class DeleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


def _container(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> KernelContainer:
    return container


@router.post("/sessions", response_model=DialogueSession)
def create_session(
    body: DialogueSessionCreateRequest,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DialogueSession:
    """Create one dialogue session."""

    try:
        return container.dialogue_session_service.create_session(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                    "created_by": body.created_by or actor_context.actor_id,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/sessions/{dialogue_session_id}", response_model=DialogueSession)
def get_session(
    dialogue_session_id: str,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> DialogueSession:
    """Return one dialogue session."""

    try:
        session = container.dialogue_session_service.get_session(
            dialogue_session_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if session is None:
        raise HTTPException(status_code=404, detail="dialogue_session_not_found")
    return session


@router.get("/sessions", response_model=list[DialogueSession])
def list_sessions(
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    session_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[DialogueSession]:
    """List dialogue sessions."""

    try:
        return container.dialogue_session_service.list_sessions(
            _scope(scope, actor_context),
            status=status,
            session_type=session_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/sessions/{dialogue_session_id}/close", response_model=DialogueSession)
def close_session(
    dialogue_session_id: str,
    body: CloseRequest,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DialogueSession:
    """Close a dialogue session."""

    try:
        return container.dialogue_session_service.close_session(
            dialogue_session_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/messages", response_model=DialogueMessage)
def create_message(
    body: DialogueMessageCreateRequest,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DialogueMessage:
    """Create one sanitized dialogue message."""

    try:
        return container.dialogue_message_service.create_message(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "trace_id": body.trace_id or actor_context.trace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/messages/{message_id}", response_model=DialogueMessage)
def get_message(
    message_id: str,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> DialogueMessage:
    """Return one dialogue message."""

    try:
        message = container.dialogue_message_service.get_message(
            message_id,
            _scope(scope, actor_context),
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if message is None:
        raise HTTPException(status_code=404, detail="dialogue_message_not_found")
    return message


@router.get("/sessions/{dialogue_session_id}/messages", response_model=list[DialogueMessage])
def list_messages(
    dialogue_session_id: str,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[DialogueMessage]:
    """List messages in a dialogue session."""

    try:
        return container.dialogue_message_service.list_messages(
            dialogue_session_id,
            _scope(scope, actor_context),
            limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: str,
    body: DeleteRequest,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Soft-delete a dialogue message."""

    try:
        deleted = container.dialogue_message_service.soft_delete_message(
            message_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    return {"deleted": deleted, "message_id": message_id}


@router.post("/turn", response_model=DialogueTurnResult)
def dialogue_turn(
    body: DialogueTurnRequest,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DialogueTurnResult:
    """Run one bounded dialogue turn."""

    try:
        return container.dialogue_turn_service.turn(
            body.model_copy(
                update={
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                    "owner_scope": body.owner_scope or actor_context.security_scope,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/clarifications/pending", response_model=list[ClarificationRequest])
def pending_clarifications(
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    dialogue_session_id: str | None = None,
) -> list[ClarificationRequest]:
    """List pending clarification requests."""

    try:
        return container.clarification_manager.list_pending(
            _scope(scope, actor_context),
            dialogue_session_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/clarifications/{clarification_id}/answer", response_model=ClarificationRequest)
def answer_clarification(
    clarification_id: str,
    body: ClarificationAnswerRequest,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ClarificationRequest:
    """Answer a pending clarification."""

    try:
        return container.clarification_manager.answer(
            body.model_copy(
                update={
                    "clarification_id": clarification_id,
                    "actor_id": body.actor_id or actor_context.actor_id,
                    "workspace_id": body.workspace_id or actor_context.workspace_id,
                }
            )
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/clarifications/{clarification_id}/cancel", response_model=ClarificationRequest)
def cancel_clarification(
    clarification_id: str,
    body: CloseRequest,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ClarificationRequest:
    """Cancel a pending clarification."""

    try:
        return container.clarification_manager.cancel(
            clarification_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/feedback", response_model=DialogueFeedback)
def create_feedback(
    body: DialogueFeedback,
    container: Annotated[KernelContainer, Depends(_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DialogueFeedback:
    """Create dialogue feedback."""

    try:
        return container.dialogue_feedback_service.create_feedback(
            body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id})
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/feedback", response_model=list[DialogueFeedback])
def list_feedback(
    container: Annotated[KernelContainer, Depends(_container)],
    dialogue_session_id: str | None = None,
    response_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[DialogueFeedback]:
    """List dialogue feedback."""

    try:
        return container.dialogue_feedback_service.list_feedback(
            dialogue_session_id=dialogue_session_id,
            response_id=response_id,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value
