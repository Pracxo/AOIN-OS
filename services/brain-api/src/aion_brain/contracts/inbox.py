"""Inbox deduplication contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

InboxStatus = Literal["received", "processing", "processed", "duplicate", "failed"]


class InboxMessage(BaseModel):
    """Recorded incoming message used for duplicate suppression."""

    model_config = ConfigDict(extra="forbid")

    inbox_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    external_message_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    message_type: str = Field(min_length=1)
    payload_hash: str = Field(min_length=1)
    status: InboxStatus
    processed_by: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    received_at: datetime | None = None
    processed_at: datetime | None = None


class InboxReceiveRequest(BaseModel):
    """Request to record an incoming message without processing it."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    external_message_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    message_type: str = Field(min_length=1)
    payload: dict[str, Any]

    @field_validator("source", "external_message_id", "message_type")
    @classmethod
    def values_cannot_be_blank(cls, value: str) -> str:
        """Reject blank identifiers."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value


class InboxReceiveResult(BaseModel):
    """Inbox receipt result."""

    model_config = ConfigDict(extra="forbid")

    accepted: bool
    duplicate: bool
    inbox: InboxMessage
    reason: str | None
