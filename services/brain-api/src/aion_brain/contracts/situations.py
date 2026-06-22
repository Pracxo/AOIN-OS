"""Situation model contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.concepts import reject_secret_like_keys, text_has_secret_markers
from aion_brain.contracts.temporal_state import StateAtom, StateTransition

SituationStatus = Literal["active", "stale", "closed", "archived"]
SituationType = Literal[
    "general",
    "dialogue",
    "goal",
    "task",
    "workflow",
    "operator",
    "review",
    "replay",
    "incident",
    "maintenance",
]
SituationProjectionMode = Literal["dry_run", "controlled"]
SituationProjectionStatus = Literal[
    "completed",
    "dry_run",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
]
ContinuityType = Literal[
    "dialogue_turn",
    "focus_shift",
    "task_resume",
    "workflow_resume",
    "review",
    "replay",
    "generic",
]
ContinuityStatus = Literal["recorded", "warning", "failed"]

_DOMAIN_TERMS = {
    "finance",
    "trading",
    "stock",
    "legal",
    "healthcare",
    "medical",
    "procurement",
    "payroll",
}


class SituationRecord(BaseModel):
    """A current, generic projection of what is going on."""

    model_config = ConfigDict(extra="forbid")

    situation_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: SituationStatus = "active"
    situation_type: SituationType = "general"
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    active_goal_ids: list[str] = Field(default_factory=list)
    active_task_ids: list[str] = Field(default_factory=list)
    active_workflow_run_ids: list[str] = Field(default_factory=list)
    active_focus_session_ids: list[str] = Field(default_factory=list)
    entity_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None

    @field_validator("title", "summary")
    @classmethod
    def text_must_be_safe_and_generic(cls, value: str) -> str:
        _reject_text(value, reject_domain_terms=True)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe_and_generic(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        _reject_domain_payload(value)
        return value


class SituationCreateRequest(BaseModel):
    """Request to create one situation projection record."""

    model_config = ConfigDict(extra="forbid")

    situation_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    situation_type: SituationType = "general"
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    active_goal_ids: list[str] = Field(default_factory=list)
    active_task_ids: list[str] = Field(default_factory=list)
    active_workflow_run_ids: list[str] = Field(default_factory=list)
    active_focus_session_ids: list[str] = Field(default_factory=list)
    entity_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("title", "summary")
    @classmethod
    def text_must_be_safe_and_generic(cls, value: str) -> str:
        _reject_text(value, reject_domain_terms=True)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe_and_generic(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        _reject_domain_payload(value)
        return value


class SituationCloseRequest(BaseModel):
    """Request to close one active situation."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class SituationQuery(BaseModel):
    """Read-side query for situation records and optional atoms."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    scope: list[str] = Field(min_length=1)
    statuses: list[SituationStatus] = Field(default_factory=list)
    situation_types: list[SituationType] = Field(default_factory=list)
    text: str | None = None
    refs: list[str] = Field(default_factory=list)
    include_state_atoms: bool = False
    limit: int = Field(default=100, ge=1, le=1000)

    @field_validator("text")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            _reject_text(value, reject_domain_terms=False)
        return value


class SituationQueryResult(BaseModel):
    """Result of querying current situation projections."""

    model_config = ConfigDict(extra="forbid")

    situations: list[SituationRecord]
    state_atoms: list[StateAtom] = Field(default_factory=list)
    total: int
    constraints: list[str] = Field(default_factory=list)


class SituationProjectionRequest(BaseModel):
    """Request to project state from selected local Brain records."""

    model_config = ConfigDict(extra="forbid")

    projection_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: SituationProjectionMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    source_refs: list[dict[str, str]] = Field(default_factory=list)
    since: datetime | None = None
    until: datetime | None = None
    max_state_atoms: int = Field(default=500, ge=1, le=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def times_must_be_ordered(self) -> SituationProjectionRequest:
        if self.since and self.until and self.since >= self.until:
            raise ValueError("since must be before until")
        return self


class SituationProjectionResult(BaseModel):
    """Result of one deterministic situation projection run."""

    model_config = ConfigDict(extra="forbid")

    projection_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: SituationProjectionStatus
    mode: SituationProjectionMode
    owner_scope: list[str] = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    situation_ids: list[str] = Field(default_factory=list)
    state_atom_ids: list[str] = Field(default_factory=list)
    transition_ids: list[str] = Field(default_factory=list)
    situations: list[SituationRecord] = Field(default_factory=list)
    state_atoms: list[StateAtom] = Field(default_factory=list)
    transitions: list[StateTransition] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("input", "result")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ContextContinuityRecord(BaseModel):
    """Record of references carried across turns, focus shifts, or resumes."""

    model_config = ConfigDict(extra="forbid")

    continuity_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    dialogue_session_id: str | None = None
    focus_session_id: str | None = None
    situation_id: str | None = None
    continuity_type: ContinuityType
    status: ContinuityStatus = "recorded"
    carried_refs: list[str] = Field(default_factory=list)
    dropped_refs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        _reject_text(value, reject_domain_terms=False)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ContextContinuityRequest(BaseModel):
    """Request to record deterministic context continuity."""

    model_config = ConfigDict(extra="forbid")

    continuity_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    dialogue_session_id: str | None = None
    focus_session_id: str | None = None
    situation_id: str | None = None
    continuity_type: ContinuityType = "generic"
    refs: list[str] = Field(default_factory=list, max_length=100)
    carried_refs: list[str] = Field(default_factory=list, max_length=100)
    dropped_refs: list[str] = Field(default_factory=list, max_length=100)
    constraints: list[str] = Field(default_factory=list)
    reason: str = Field(default="Context continuity recorded.")
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("refs", "carried_refs", "dropped_refs")
    @classmethod
    def refs_have_max_and_values(cls, value: list[str]) -> list[str]:
        if len(value) > 100:
            raise ValueError("max_refs is 100")
        return [item for item in value if item]

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        _reject_text(value, reject_domain_terms=False)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


def _reject_text(value: str, *, reject_domain_terms: bool) -> None:
    if not value.strip():
        raise ValueError("value cannot be empty")
    if text_has_secret_markers(value):
        raise ValueError("value must not contain raw secrets")
    if reject_domain_terms and any(term in value.lower() for term in _DOMAIN_TERMS):
        raise ValueError("value must remain domain-neutral")


def _reject_domain_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in _DOMAIN_TERMS):
                raise ValueError("metadata must remain domain-neutral")
            _reject_domain_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_domain_payload(item)
    elif isinstance(value, str) and any(term in value.lower() for term in _DOMAIN_TERMS):
        raise ValueError("metadata must remain domain-neutral")


__all__ = [
    "ContextContinuityRecord",
    "ContextContinuityRequest",
    "ContinuityStatus",
    "ContinuityType",
    "SituationCloseRequest",
    "SituationCreateRequest",
    "SituationProjectionMode",
    "SituationProjectionRequest",
    "SituationProjectionResult",
    "SituationProjectionStatus",
    "SituationQuery",
    "SituationQueryResult",
    "SituationRecord",
    "SituationStatus",
    "SituationType",
]
