"""Transactional outbox contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

OutboxDestination = Literal["nats", "internal", "webhook_placeholder", "noop"]
OutboxStatus = Literal["pending", "sending", "sent", "failed", "dead_lettered", "cancelled"]

_SECRET_KEYS = {"api_key", "apikey", "authorization", "password", "private_key", "secret", "token"}


class OutboxMessage(BaseModel):
    """Local message that may be delivered manually after persistence."""

    model_config = ConfigDict(extra="forbid")

    outbox_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    message_type: str = Field(min_length=1)
    destination: OutboxDestination
    subject: str | None = None
    payload: dict[str, Any]
    headers: dict[str, Any] = Field(default_factory=dict)
    status: OutboxStatus
    attempt_count: int = Field(ge=0)
    max_attempts: int = Field(ge=1, le=10)
    next_attempt_at: datetime | None = None
    last_error: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    sent_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("payload", "headers", "last_error")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like values."""
        _reject_secret_like_keys(value)
        return value


class OutboxPublishRequest(BaseModel):
    """Request to enqueue one local outbox message."""

    model_config = ConfigDict(extra="forbid")

    message_type: str = Field(min_length=1)
    destination: OutboxDestination
    subject: str | None = None
    payload: dict[str, Any]
    headers: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None
    correlation_id: str | None = None
    max_attempts: int = Field(default=3, ge=1, le=10)

    @field_validator("payload", "headers")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like values."""
        _reject_secret_like_keys(value)
        return value


class OutboxProcessRequest(BaseModel):
    """Manual request to process pending outbox messages once."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=100)
    destination: OutboxDestination | None = None
    dry_run: bool = True


class OutboxProcessResult(BaseModel):
    """Result of one bounded outbox processing pass."""

    model_config = ConfigDict(extra="forbid")

    processed: int
    sent: int
    failed: int
    skipped: int
    dry_run: bool
    messages: list[OutboxMessage]


def has_secret_like_key(value: object) -> bool:
    """Return whether a nested payload contains secret-like keys."""
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower().replace("-", "_") in _SECRET_KEYS:
                return True
            if has_secret_like_key(nested):
                return True
    if isinstance(value, list):
        return any(has_secret_like_key(item) for item in value)
    return False


def _reject_secret_like_keys(value: object) -> None:
    if has_secret_like_key(value):
        raise ValueError("payload must not contain secret-like keys")
