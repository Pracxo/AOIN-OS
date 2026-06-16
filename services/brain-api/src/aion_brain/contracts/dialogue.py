"""Dialogue contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.responses import (
    ResponseDraft,
    _reject_secret_like_keys,
    text_has_hidden_markers,
    text_has_secret_markers,
)

DialogueSessionStatus = Literal["active", "paused", "closed"]
DialogueSessionType = Literal["general", "goal", "task", "workflow", "review", "replay", "operator"]
DialogueRole = Literal["user", "assistant", "system", "tool", "operator"]
DialogueMessageType = Literal[
    "text",
    "clarification_answer",
    "clarification_question",
    "response",
    "note",
    "event_summary",
    "operator_note",
]
DialogueTurnMode = Literal["observe", "assist", "plan_only", "dry_run"]
ClarificationStatus = Literal["pending", "answered", "cancelled"]
DialogueFeedbackType = Literal["helpful", "unhelpful", "incorrect", "unclear", "unsafe", "generic"]


class DialogueSession(BaseModel):
    """A generic backend dialogue session."""

    model_config = ConfigDict(extra="forbid")

    dialogue_session_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: DialogueSessionStatus
    session_type: DialogueSessionType
    title: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    active_focus_session_id: str | None = None
    active_goal_id: str | None = None
    active_task_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class DialogueSessionCreateRequest(BaseModel):
    """Request to create a dialogue session."""

    model_config = ConfigDict(extra="forbid")

    dialogue_session_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    session_type: DialogueSessionType = "general"
    title: str = Field(min_length=1)
    owner_scope: list[str] = Field(default_factory=list)
    active_focus_session_id: str | None = None
    active_goal_id: str | None = None
    active_task_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class DialogueMessage(BaseModel):
    """Sanitized message stored for a dialogue session."""

    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=1)
    dialogue_session_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    role: DialogueRole
    message_type: DialogueMessageType
    content: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    content_redacted: bool
    grounding_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    response_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def content_must_be_safe(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content cannot be empty")
        if text_has_hidden_markers(value):
            raise ValueError("content must not contain chain-of-thought or hidden reasoning")
        if text_has_secret_markers(value):
            raise ValueError("content must not contain raw secrets")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class DialogueMessageCreateRequest(BaseModel):
    """Request to create one dialogue message."""

    model_config = ConfigDict(extra="forbid")

    message_id: str | None = None
    dialogue_session_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    role: DialogueRole = "user"
    message_type: DialogueMessageType = "text"
    content: str = Field(min_length=1)
    grounding_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class DialogueTurnRequest(BaseModel):
    """Request to run one bounded dialogue turn."""

    model_config = ConfigDict(extra="forbid")

    dialogue_session_id: str | None = None
    message: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    create_session: bool = True
    session_title: str | None = None
    use_brain_loop: bool = True
    require_grounding: bool = False
    mode: DialogueTurnMode = "assist"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("message")
    @classmethod
    def message_must_be_safe(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message cannot be empty")
        if text_has_secret_markers(value):
            raise ValueError("message must not contain raw secrets")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class ClarificationRequest(BaseModel):
    """One clarification request in a dialogue session."""

    model_config = ConfigDict(extra="forbid")

    clarification_id: str = Field(min_length=1)
    dialogue_session_id: str | None = None
    message_id: str | None = None
    trace_id: str | None = None
    status: ClarificationStatus
    question: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    required: bool
    answer_message_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    answered_at: datetime | None = None
    cancelled_at: datetime | None = None

    @field_validator("question", "reason")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class ClarificationAnswerRequest(BaseModel):
    """Request to answer a clarification."""

    model_config = ConfigDict(extra="forbid")

    clarification_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("answer")
    @classmethod
    def answer_must_be_safe(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("answer cannot be empty")
        if text_has_secret_markers(value):
            raise ValueError("answer must not contain raw secrets")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class DialogueFeedback(BaseModel):
    """Feedback record for a message or response."""

    model_config = ConfigDict(extra="forbid")

    feedback_id: str = Field(min_length=1)
    dialogue_session_id: str | None = None
    message_id: str | None = None
    response_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    feedback_type: DialogueFeedbackType
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("comment")
    @classmethod
    def comment_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None and text_has_secret_markers(value):
            raise ValueError("comment must not contain raw secrets")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class DialogueTurnResult(BaseModel):
    """Result of one bounded dialogue turn."""

    model_config = ConfigDict(extra="forbid")

    dialogue_session: DialogueSession
    user_message: DialogueMessage
    response: ResponseDraft | None = None
    clarification: ClarificationRequest | None = None
    trace_id: str | None = None
    attention_decision_id: str | None = None
    reasoning_id: str | None = None
    plan_id: str | None = None
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


__all__ = [
    "ClarificationAnswerRequest",
    "ClarificationRequest",
    "DialogueFeedback",
    "DialogueMessage",
    "DialogueMessageCreateRequest",
    "DialogueSession",
    "DialogueSessionCreateRequest",
    "DialogueTurnRequest",
    "DialogueTurnResult",
]
