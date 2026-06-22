"""Local observability contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ObservabilityLevel = Literal["debug", "info", "warning", "error"]
SECRET_KEYS = {"password", "secret", "token", "api_key", "private_key", "authorization"}


class ObservabilityEvent(BaseModel):
    """A sanitized local observability event."""

    model_config = ConfigDict(extra="forbid")

    observability_event_id: str = Field(min_length=1)
    trace_id: str | None = None
    correlation_id: str | None = None
    event_type: str = Field(min_length=1)
    component: str = Field(min_length=1)
    level: ObservabilityLevel
    message: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("payload")
    @classmethod
    def reject_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys at any payload depth."""
        _reject_secret_keys(value)
        return value


class ObservabilitySummary(BaseModel):
    """Aggregate local observability and telemetry counts."""

    model_config = ConfigDict(extra="forbid")

    trace_count: int = Field(ge=0)
    telemetry_event_count: int = Field(ge=0)
    observability_event_count: int = Field(ge=0)
    active_node_count: int = Field(ge=0)
    blocked_event_count: int = Field(ge=0)
    failed_event_count: int = Field(ge=0)
    latest_trace_id: str | None
    generated_at: datetime


def _reject_secret_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(secret in normalized for secret in SECRET_KEYS):
                raise ValueError("observability payload must not contain secret-like keys")
            _reject_secret_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_keys(item)
