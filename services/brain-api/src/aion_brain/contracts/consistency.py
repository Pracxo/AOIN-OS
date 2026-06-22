"""Consistency guard contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LeaseStatus = Literal["active", "released", "expired"]
ConsistencyCheckType = Literal[
    "commands_without_trace",
    "outbox_stuck",
    "inbox_failed",
    "duplicate_idempotency",
    "orphan_reaction_actions",
    "orphan_workflow_steps",
    "pending_approvals_expired",
    "stale_processing_leases",
    "kernel_boundary",
    "all",
]
ConsistencyCheckStatus = Literal["passed", "warning", "failed", "repaired"]


class ProcessingLease(BaseModel):
    """Local DB-backed processing lease."""

    model_config = ConfigDict(extra="forbid")

    lease_id: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    status: LeaseStatus
    expires_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    released_at: datetime | None = None


class ConsistencyCheckRequest(BaseModel):
    """Request to run one consistency check."""

    model_config = ConfigDict(extra="forbid")

    check_type: ConsistencyCheckType
    scope: list[str] = Field(min_length=1)
    repair: bool = False
    limit: int = Field(default=1000, ge=1, le=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class ConsistencyCheckResult(BaseModel):
    """Result of a consistency check."""

    model_config = ConfigDict(extra="forbid")

    consistency_check_id: str
    trace_id: str | None = None
    check_type: ConsistencyCheckType
    status: ConsistencyCheckStatus
    scope: list[str]
    violations: list[dict[str, Any]] = Field(default_factory=list)
    repaired: bool
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None


_SECRET_KEYS = {"api_key", "apikey", "authorization", "password", "private_key", "secret", "token"}


def _reject_secret_like_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower().replace("-", "_") in _SECRET_KEYS:
                raise ValueError("metadata must not contain secret-like keys")
            _reject_secret_like_keys(nested)
    if isinstance(value, list):
        for item in value:
            _reject_secret_like_keys(item)
