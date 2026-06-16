"""Dialogue response contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ResponseStatus = Literal["draft", "verified", "blocked", "delivered", "superseded"]
ResponseType = Literal[
    "answer",
    "clarification",
    "plan_summary",
    "refusal",
    "status",
    "operator_summary",
]
ResponseVerificationStatus = Literal["passed", "warning", "failed", "blocked"]
ResponseDeliveryType = Literal["api_return", "local_record", "sdk_return", "cli_return"]
ResponseDeliveryStatus = Literal["recorded", "delivered", "blocked", "failed"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}
_HIDDEN_MARKERS = {
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "hidden reasoning",
    "raw_prompt",
    "raw prompt",
}
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")


class ResponseDraft(BaseModel):
    """Deterministic response draft prepared by AION Brain."""

    model_config = ConfigDict(extra="forbid")

    response_id: str = Field(min_length=1)
    dialogue_session_id: str | None = None
    message_id: str | None = None
    trace_id: str | None = None
    reasoning_id: str | None = None
    plan_id: str | None = None
    status: ResponseStatus
    response_type: ResponseType
    content: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    grounded: bool
    grounding_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    clarification_refs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def content_must_be_safe(cls, value: str) -> str:
        _reject_hidden_or_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class ResponseComposeRequest(BaseModel):
    """Request to compose a deterministic response draft."""

    model_config = ConfigDict(extra="forbid")

    response_id: str | None = None
    dialogue_session_id: str | None = None
    message_id: str | None = None
    trace_id: str | None = None
    reasoning_id: str | None = None
    plan_id: str | None = None
    goal: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    reasoning_result: dict[str, Any] = Field(default_factory=dict)
    plan: dict[str, Any] = Field(default_factory=dict)
    require_grounding: bool = False
    response_type: ResponseType = "answer"
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("context", "reasoning_result", "plan", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class ResponseVerification(BaseModel):
    """Local response verification result."""

    model_config = ConfigDict(extra="forbid")

    verification_id: str = Field(min_length=1)
    response_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: ResponseVerificationStatus
    grounded: bool
    policy_ok: bool
    autonomy_ok: bool
    approval_required: bool
    issues: list[dict[str, Any]] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("issues", mode="after")
    @classmethod
    def issues_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for issue in value:
            _reject_secret_like_keys(issue)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class ResponseDeliveryRecord(BaseModel):
    """Local-only record that a response was returned through an AION API boundary."""

    model_config = ConfigDict(extra="forbid")

    delivery_id: str = Field(min_length=1)
    response_id: str = Field(min_length=1)
    dialogue_session_id: str | None = None
    trace_id: str | None = None
    delivery_type: ResponseDeliveryType
    status: ResponseDeliveryStatus
    delivered_to: str | None = None
    output_channel: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


def text_has_hidden_markers(value: str) -> bool:
    """Return true when response or message text contains hidden-reasoning markers."""

    lowered = value.lower()
    return any(marker in lowered for marker in _HIDDEN_MARKERS)


def text_has_secret_markers(value: str) -> bool:
    """Return true when text contains obvious raw secret value markers."""

    lowered = value.lower()
    return any(marker in lowered for marker in _SECRET_VALUE_MARKERS)


def _reject_hidden_or_secret_text(value: str) -> None:
    if not value.strip():
        raise ValueError("content cannot be empty")
    if text_has_hidden_markers(value):
        raise ValueError("content must not contain chain-of-thought or hidden reasoning")
    if text_has_secret_markers(value):
        raise ValueError("content must not contain raw secrets")


def _reject_secret_like_keys(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise ValueError(f"metadata contains secret-like key: {path}{key}")
            _reject_secret_like_keys(item, f"{path}{key}.")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_secret_like_keys(item, f"{path}{index}.")


__all__ = [
    "ResponseComposeRequest",
    "ResponseDeliveryRecord",
    "ResponseDraft",
    "ResponseVerification",
    "text_has_hidden_markers",
    "text_has_secret_markers",
]
