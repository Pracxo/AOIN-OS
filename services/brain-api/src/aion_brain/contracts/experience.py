"""Experience ledger contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.concepts import reject_secret_like_keys

ExperienceSourceType = Literal[
    "outcome",
    "decision",
    "command",
    "workflow",
    "task",
    "execution",
    "event_reaction",
    "replay",
    "regression",
    "approval",
    "audit",
    "operator",
    "manual",
    "generic",
]
ExperienceType = Literal[
    "success",
    "failure",
    "partial_success",
    "blocked_action",
    "approval_required",
    "regression_drift",
    "replay_drift",
    "unexpected_effect",
    "missing_effect",
    "contradiction",
    "recovery",
    "generic",
]
ExperienceStatus = Literal["active", "archived", "dismissed"]


class ExperienceRecord(BaseModel):
    """Generic experience observed from Brain-owned records."""

    model_config = ConfigDict(extra="forbid")

    experience_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: ExperienceSourceType
    source_id: str = Field(min_length=1)
    experience_type: ExperienceType
    status: ExperienceStatus
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    outcome_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    command_refs: list[str] = Field(default_factory=list)
    workflow_refs: list[str] = Field(default_factory=list)
    regression_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    signal_refs: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ExperienceCreateRequest(BaseModel):
    """Request to create one experience record."""

    model_config = ConfigDict(extra="forbid")

    experience_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: ExperienceSourceType
    source_id: str = Field(min_length=1)
    experience_type: ExperienceType
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    command_refs: list[str] = Field(default_factory=list)
    workflow_refs: list[str] = Field(default_factory=list)
    regression_refs: list[str] = Field(default_factory=list)
    replay_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    signal_refs: list[str] = Field(default_factory=list)
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime | None = None
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ExperienceQuery(BaseModel):
    """Query learning experiences and synthesized material."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    query: str | None = None
    source_types: list[str] = Field(default_factory=list)
    experience_types: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    trace_id: str | None = None
    include_archived: bool = False
    limit: int = Field(default=50, ge=1, le=500)


__all__ = [
    "ExperienceCreateRequest",
    "ExperienceQuery",
    "ExperienceRecord",
    "ExperienceSourceType",
    "ExperienceStatus",
    "ExperienceType",
]
