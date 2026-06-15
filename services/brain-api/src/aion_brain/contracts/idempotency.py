"""Idempotency contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

IdempotencyStatus = Literal["started", "completed", "failed", "expired"]


class IdempotencyRecord(BaseModel):
    """Stored idempotency state for one route and request hash."""

    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    route: str = Field(min_length=1)
    request_hash: str = Field(min_length=1)
    response_hash: str | None = None
    status: IdempotencyStatus
    response: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("idempotency_key", "route", "request_hash")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank identifiers."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value


class IdempotencyCheckRequest(BaseModel):
    """Request to check or start idempotent processing."""

    model_config = ConfigDict(extra="forbid")

    idempotency_key: str = Field(min_length=1)
    route: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    request_payload: dict[str, Any]
    expires_at: datetime | None = None


class IdempotencyCheckResult(BaseModel):
    """Idempotency lookup result."""

    model_config = ConfigDict(extra="forbid")

    duplicate: bool
    conflict: bool
    record: IdempotencyRecord | None
    reason: str | None
