"""Root cause candidate and recovery review contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

IncidentSeverity = Literal["info", "low", "medium", "high", "critical"]
RootCauseCandidateStatus = Literal["proposed", "confirmed", "dismissed", "archived"]
RootCauseCandidateType = Literal[
    "dependency_unavailable",
    "policy_constraint",
    "autonomy_constraint",
    "approval_missing",
    "capability_unavailable",
    "prompt_injection",
    "unsafe_model_output",
    "insufficient_grounding",
    "audit_integrity_issue",
    "schedule_missed",
    "run_stalled",
    "timeout",
    "failed_outcome",
    "unknown",
    "generic",
]
RecoveryReviewType = Literal[
    "manual_review",
    "recovery_options",
    "compensation_options",
    "verification_review",
    "operator_review",
    "generic",
]
RecoveryReviewStatus = Literal["completed", "warning", "failed", "archived"]


class RootCauseCandidate(BaseModel):
    """Deterministic hypothesis linked to an incident. It is not truth."""

    model_config = ConfigDict(extra="forbid")

    root_cause_candidate_id: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: RootCauseCandidateStatus
    candidate_type: RootCauseCandidateType
    severity: IncidentSeverity
    title: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_refs: list[str] = Field(default_factory=list)
    opposing_refs: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    confirmed_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("title", "hypothesis")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "root cause candidate text")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def candidate_must_not_claim_truth(self) -> RootCauseCandidate:
        if self.metadata.get("is_truth") is True or self.metadata.get("confirmed_truth") is True:
            raise ValueError("root cause candidate must not be stored as truth")
        return self


class RootCauseCandidateRequest(BaseModel):
    """Request to create a deterministic root cause candidate."""

    model_config = ConfigDict(extra="forbid")

    root_cause_candidate_id: str | None = None
    incident_id: str = Field(min_length=1)
    trace_id: str | None = None
    candidate_type: RootCauseCandidateType = "generic"
    title: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    severity: IncidentSeverity = "medium"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    supporting_refs: list[str] = Field(default_factory=list)
    opposing_refs: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("title", "hypothesis")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "root cause candidate text")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RecoveryReview(BaseModel):
    """Local recovery review record. It never executes remediation."""

    model_config = ConfigDict(extra="forbid")

    recovery_review_id: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: RecoveryReviewStatus
    review_type: RecoveryReviewType
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    action_proposal_refs: list[str] = Field(default_factory=list)
    compensation_plan_refs: list[str] = Field(default_factory=list)
    notification_refs: list[str] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    created_records: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("title", "summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "recovery review text")
        return value.strip()

    @field_validator("findings", "recommendations", "created_records")
    @classmethod
    def records_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_payload(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def review_must_not_execute(self) -> RecoveryReview:
        if self.metadata.get("execute") is True or self.metadata.get("auto_execute") is True:
            raise ValueError("recovery review must not execute remediation")
        return self


class RecoveryReviewRequest(BaseModel):
    """Request to build a local recovery review."""

    model_config = ConfigDict(extra="forbid")

    recovery_review_id: str | None = None
    incident_id: str = Field(min_length=1)
    trace_id: str | None = None
    review_type: RecoveryReviewType = "generic"
    owner_scope: list[str] = Field(min_length=1)
    create_action_proposals: bool = False
    create_compensation_plans: bool = False
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "IncidentSeverity",
    "RecoveryReview",
    "RecoveryReviewRequest",
    "RecoveryReviewStatus",
    "RecoveryReviewType",
    "RootCauseCandidate",
    "RootCauseCandidateRequest",
    "RootCauseCandidateStatus",
    "RootCauseCandidateType",
]
