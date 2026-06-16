"""Expected and observed effect contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.concepts import reject_secret_like_keys

EffectSourceType = Literal[
    "decision_option",
    "decision_record",
    "counterfactual",
    "plan",
    "execution",
    "workflow",
    "task",
    "command",
    "event_reaction",
    "cycle",
    "generic",
]
EffectType = Literal[
    "state_change",
    "status_change",
    "record_created",
    "record_updated",
    "record_deleted_soft",
    "approval_requested",
    "policy_checked",
    "memory_written",
    "evidence_created",
    "command_completed",
    "workflow_completed",
    "response_delivered",
    "no_effect",
    "generic",
]
ObservationSourceType = Literal[
    "event",
    "audit_entry",
    "situation",
    "state_atom",
    "belief_claim",
    "evidence",
    "memory",
    "command",
    "workflow",
    "execution",
    "response",
    "operator",
    "system",
    "generic",
]
EffectSensitivity = Literal["public", "internal", "confidential", "restricted"]


class ExpectedEffect(BaseModel):
    """An effect AION expects after a decision, plan, command, workflow, or run."""

    model_config = ConfigDict(extra="forbid")

    expected_effect_id: str = Field(min_length=1)
    trace_id: str | None = None
    source_type: EffectSourceType
    source_id: str = Field(min_length=1)
    effect_type: EffectType = "generic"
    subject_ref: str | None = None
    predicate: str = Field(min_length=1)
    object_ref: str | None = None
    expected_value: dict[str, Any] = Field(default_factory=dict)
    success_criteria: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    confidence: float = Field(ge=0.0, le=1.0)
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("expected_value", "success_criteria", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ExpectedEffectCreateRequest(BaseModel):
    """Request to create an expected effect."""

    model_config = ConfigDict(extra="forbid")

    expected_effect_id: str | None = None
    trace_id: str | None = None
    source_type: EffectSourceType
    source_id: str = Field(min_length=1)
    effect_type: EffectType = "generic"
    subject_ref: str | None = None
    predicate: str = Field(min_length=1)
    object_ref: str | None = None
    expected_value: dict[str, Any] = Field(default_factory=dict)
    success_criteria: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    owner_scope: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("expected_value", "success_criteria", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ObservedEffect(BaseModel):
    """An effect AION observed from local Brain records."""

    model_config = ConfigDict(extra="forbid")

    observed_effect_id: str = Field(min_length=1)
    trace_id: str | None = None
    outcome_id: str | None = None
    source_type: EffectSourceType
    source_id: str = Field(min_length=1)
    effect_type: EffectType = "generic"
    subject_ref: str | None = None
    predicate: str = Field(min_length=1)
    object_ref: str | None = None
    observed_value: dict[str, Any] = Field(default_factory=dict)
    observation_source_type: ObservationSourceType
    observation_source_id: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    sensitivity: EffectSensitivity = "internal"
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    situation_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("observed_value", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ObservedEffectCreateRequest(BaseModel):
    """Request to create an observed effect."""

    model_config = ConfigDict(extra="forbid")

    observed_effect_id: str | None = None
    trace_id: str | None = None
    outcome_id: str | None = None
    source_type: EffectSourceType
    source_id: str = Field(min_length=1)
    effect_type: EffectType = "generic"
    subject_ref: str | None = None
    predicate: str = Field(min_length=1)
    object_ref: str | None = None
    observed_value: dict[str, Any] = Field(default_factory=dict)
    observation_source_type: ObservationSourceType
    observation_source_id: str = Field(min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    sensitivity: EffectSensitivity = "internal"
    owner_scope: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    situation_refs: list[str] = Field(default_factory=list)
    observed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("observed_value", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


__all__ = [
    "EffectSensitivity",
    "EffectSourceType",
    "EffectType",
    "ExpectedEffect",
    "ExpectedEffectCreateRequest",
    "ObservationSourceType",
    "ObservedEffect",
    "ObservedEffectCreateRequest",
]
