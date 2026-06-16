"""Temporal state contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.concepts import reject_secret_like_keys, text_has_secret_markers

StateAtomType = Literal[
    "event_state",
    "goal_state",
    "task_state",
    "workflow_state",
    "dialogue_state",
    "belief_state",
    "entity_state",
    "memory_state",
    "evidence_state",
    "approval_state",
    "policy_state",
    "autonomy_state",
    "operator_state",
    "system_state",
    "generic",
]
StateAtomSourceType = Literal[
    "event",
    "goal",
    "task",
    "workflow",
    "dialogue",
    "message",
    "response",
    "belief_claim",
    "entity",
    "concept",
    "memory",
    "evidence",
    "graph",
    "approval",
    "policy",
    "autonomy",
    "audit",
    "operator",
    "kernel",
    "system",
    "generic",
]
StateAtomStatus = Literal[
    "current",
    "previous",
    "stale",
    "contradicted",
    "superseded",
    "rejected",
    "unknown",
]
StateAtomSensitivity = Literal["public", "internal", "confidential", "restricted"]
TemporalWindowType = Literal["recent", "session", "focus", "trace", "daily", "custom"]
StateTransitionType = Literal[
    "created",
    "updated",
    "completed",
    "blocked",
    "failed",
    "superseded",
    "contradicted",
    "stale",
    "resolved",
    "reopened",
    "generic",
]
StateTransitionStatus = Literal["detected", "confirmed", "dismissed"]


class StateAtom(BaseModel):
    """One projected, non-authoritative state observation."""

    model_config = ConfigDict(extra="forbid")

    state_atom_id: str = Field(min_length=1)
    situation_id: str | None = None
    trace_id: str | None = None
    atom_type: StateAtomType = "generic"
    source_type: StateAtomSourceType = "generic"
    source_id: str = Field(min_length=1)
    subject_ref: str | None = None
    predicate: str = Field(min_length=1)
    object_ref: str | None = None
    value: dict[str, Any] = Field(default_factory=dict)
    status: StateAtomStatus = "current"
    confidence: float = Field(ge=0.0, le=1.0)
    sensitivity: StateAtomSensitivity = "internal"
    observed_at: datetime
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    entity_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    superseded_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("source_id", "predicate")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_secret_text(value)
        return value

    @field_validator("value", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def times_must_be_ordered(self) -> StateAtom:
        if self.valid_from and self.valid_to and self.valid_from >= self.valid_to:
            raise ValueError("valid_from must be before valid_to")
        return self


class StateAtomCreateRequest(BaseModel):
    """Request to create one projected state atom."""

    model_config = ConfigDict(extra="forbid")

    state_atom_id: str | None = None
    situation_id: str | None = None
    trace_id: str | None = None
    atom_type: StateAtomType = "generic"
    source_type: StateAtomSourceType = "generic"
    source_id: str = Field(min_length=1)
    subject_ref: str | None = None
    predicate: str = Field(min_length=1)
    object_ref: str | None = None
    value: dict[str, Any] = Field(default_factory=dict)
    status: StateAtomStatus = "current"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    sensitivity: StateAtomSensitivity = "internal"
    observed_at: datetime | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    entity_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_id", "predicate")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_secret_text(value)
        return value

    @field_validator("value", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def times_must_be_ordered(self) -> StateAtomCreateRequest:
        if self.valid_from and self.valid_to and self.valid_from >= self.valid_to:
            raise ValueError("valid_from must be before valid_to")
        return self


class StateTransition(BaseModel):
    """Detected relation between two projected state atoms."""

    model_config = ConfigDict(extra="forbid")

    state_transition_id: str = Field(min_length=1)
    trace_id: str | None = None
    situation_id: str | None = None
    transition_type: StateTransitionType
    from_state_atom_id: str | None = None
    to_state_atom_id: str | None = None
    source_type: StateAtomSourceType = "generic"
    source_id: str | None = None
    status: StateTransitionStatus = "detected"
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        _reject_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class TemporalStateWindow(BaseModel):
    """A bounded projection window over state atoms and source events."""

    model_config = ConfigDict(extra="forbid")

    temporal_window_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    window_type: TemporalWindowType
    owner_scope: list[str] = Field(min_length=1)
    start_at: datetime
    end_at: datetime
    state_atom_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    situation_ids: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        _reject_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def start_must_precede_end(self) -> TemporalStateWindow:
        if self.start_at >= self.end_at:
            raise ValueError("start_at must be before end_at")
        return self


class TemporalStateWindowRequest(BaseModel):
    """Request to create a deterministic temporal state window."""

    model_config = ConfigDict(extra="forbid")

    temporal_window_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    window_type: TemporalWindowType = "recent"
    owner_scope: list[str] = Field(min_length=1)
    start_at: datetime
    end_at: datetime
    state_atom_ids: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    situation_ids: list[str] = Field(default_factory=list)
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def start_must_precede_end(self) -> TemporalStateWindowRequest:
        if self.start_at >= self.end_at:
            raise ValueError("start_at must be before end_at")
        return self


def _reject_secret_text(value: str) -> None:
    if not value.strip():
        raise ValueError("value cannot be empty")
    if text_has_secret_markers(value):
        raise ValueError("value must not contain raw secrets")


__all__ = [
    "StateAtom",
    "StateAtomCreateRequest",
    "StateAtomSensitivity",
    "StateAtomSourceType",
    "StateAtomStatus",
    "StateAtomType",
    "StateTransition",
    "StateTransitionStatus",
    "StateTransitionType",
    "TemporalStateWindow",
    "TemporalStateWindowRequest",
    "TemporalWindowType",
]
