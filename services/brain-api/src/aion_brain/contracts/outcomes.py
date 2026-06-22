"""Outcome ledger and effect verification contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.concepts import reject_secret_like_keys
from aion_brain.contracts.effects import ExpectedEffect, ObservedEffect

OutcomeStatus = Literal[
    "proposed",
    "verified",
    "partial",
    "failed",
    "unknown",
    "contradicted",
    "archived",
]
OutcomeType = Literal[
    "command",
    "execution",
    "workflow",
    "task",
    "decision",
    "response",
    "cycle",
    "backup",
    "release",
    "operator",
    "generic",
]
VerificationMode = Literal["dry_run", "controlled"]
VerificationStatus = Literal[
    "passed",
    "partial",
    "failed",
    "warning",
    "dry_run",
    "blocked_by_policy",
]
CausalCauseType = Literal[
    "command",
    "decision",
    "option",
    "plan",
    "execution",
    "workflow",
    "task",
    "event",
    "response",
    "cycle",
    "policy",
    "approval",
    "autonomy",
    "risk",
    "generic",
]
CausalRelationType = Literal[
    "caused",
    "contributed_to",
    "blocked",
    "prevented",
    "enabled",
    "correlated_with",
    "unknown",
]
OutcomeFeedbackType = Literal[
    "success_pattern",
    "failure_pattern",
    "partial_success",
    "unexpected_effect",
    "missing_effect",
    "contradiction",
    "regression_candidate",
    "reflection_candidate",
    "skill_candidate",
    "generic",
]
OutcomeFeedbackStatus = Literal["open", "acknowledged", "resolved", "dismissed"]
OutcomeFeedbackSeverity = Literal["low", "medium", "high", "critical"]


class OutcomeRecord(BaseModel):
    """Canonical record of what happened after a Brain source produced effects."""

    model_config = ConfigDict(extra="forbid")

    outcome_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    status: OutcomeStatus
    outcome_type: OutcomeType = "generic"
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    expected_effects: list[str] = Field(default_factory=list)
    observed_effects: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    situation_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    execution_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class OutcomeCreateRequest(BaseModel):
    """Request to create an outcome record."""

    model_config = ConfigDict(extra="forbid")

    outcome_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    outcome_type: OutcomeType = "generic"
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(default_factory=list)
    expected_effects: list[str] = Field(default_factory=list)
    observed_effects: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    situation_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    execution_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime | None = None
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class EffectVerificationRequest(BaseModel):
    """Request to verify expected effects against observed effects."""

    model_config = ConfigDict(extra="forbid")

    verification_run_id: str | None = None
    trace_id: str | None = None
    outcome_id: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    mode: VerificationMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    expected_effect_ids: list[str] = Field(default_factory=list)
    observed_effect_ids: list[str] = Field(default_factory=list)
    collect_observed_effects: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def requires_lookup_target(self) -> EffectVerificationRequest:
        if self.outcome_id or self.source_id or self.expected_effect_ids:
            return self
        raise ValueError("outcome_id, source_id, or expected_effect_ids must be present")


class EffectVerificationRun(BaseModel):
    """Persisted deterministic effect verification result."""

    model_config = ConfigDict(extra="forbid")

    verification_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    outcome_id: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    status: VerificationStatus
    mode: VerificationMode
    owner_scope: list[str] = Field(min_length=1)
    expected_effect_ids: list[str] = Field(default_factory=list)
    observed_effect_ids: list[str] = Field(default_factory=list)
    matched_effects: list[dict[str, Any]] = Field(default_factory=list)
    missing_effects: list[dict[str, Any]] = Field(default_factory=list)
    unexpected_effects: list[dict[str, Any]] = Field(default_factory=list)
    contradicted_effects: list[dict[str, Any]] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator(
        "matched_effects",
        "missing_effects",
        "unexpected_effects",
        "contradicted_effects",
    )
    @classmethod
    def effect_payloads_must_be_safe(
        cls,
        value: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        reject_secret_like_keys(value)
        return value

    @field_validator("result")
    @classmethod
    def result_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class CausalAttribution(BaseModel):
    """A generic causal relation between a source and an outcome/effect."""

    model_config = ConfigDict(extra="forbid")

    causal_attribution_id: str = Field(min_length=1)
    trace_id: str | None = None
    outcome_id: str = Field(min_length=1)
    cause_type: CausalCauseType
    cause_id: str = Field(min_length=1)
    effect_type: str = Field(min_length=1)
    effect_id: str = Field(min_length=1)
    relation_type: CausalRelationType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    reasoning: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def caused_requires_support(self) -> CausalAttribution:
        if self.relation_type != "caused":
            return self
        support = (
            self.evidence_refs
            or self.metadata.get("audit_refs")
            or self.metadata.get("provenance_refs")
        )
        if not support:
            raise ValueError("relation_type=caused requires evidence or audit/provenance support")
        return self


class OutcomeFeedback(BaseModel):
    """Feedback derived from outcome verification for later learning."""

    model_config = ConfigDict(extra="forbid")

    outcome_feedback_id: str = Field(min_length=1)
    trace_id: str | None = None
    outcome_id: str | None = None
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    feedback_type: OutcomeFeedbackType = "generic"
    status: OutcomeFeedbackStatus = "open"
    severity: OutcomeFeedbackSeverity = "medium"
    message: str = Field(min_length=1)
    recommended_followup: str = Field(min_length=1)
    learning_signal_id: str | None = None
    reflection_id: str | None = None
    regression_case_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class OutcomeQuery(BaseModel):
    """Query outcome-ledger records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    query: str | None = None
    source_types: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)
    outcome_types: list[str] = Field(default_factory=list)
    trace_id: str | None = None
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)


class OutcomeQueryResult(BaseModel):
    """Outcome query result envelope."""

    model_config = ConfigDict(extra="forbid")

    outcomes: list[OutcomeRecord] = Field(default_factory=list)
    expected_effects: list[ExpectedEffect] = Field(default_factory=list)
    observed_effects: list[ObservedEffect] = Field(default_factory=list)
    verifications: list[EffectVerificationRun] = Field(default_factory=list)
    feedback: list[OutcomeFeedback] = Field(default_factory=list)
    total_count: int = 0
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "CausalAttribution",
    "CausalCauseType",
    "CausalRelationType",
    "EffectVerificationRequest",
    "EffectVerificationRun",
    "OutcomeCreateRequest",
    "OutcomeFeedback",
    "OutcomeFeedbackSeverity",
    "OutcomeFeedbackStatus",
    "OutcomeFeedbackType",
    "OutcomeQuery",
    "OutcomeQueryResult",
    "OutcomeRecord",
    "OutcomeStatus",
    "OutcomeType",
    "VerificationMode",
    "VerificationStatus",
]
