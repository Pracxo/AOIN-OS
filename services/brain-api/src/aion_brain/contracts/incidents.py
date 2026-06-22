"""Incident correlation contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.root_cause import (
    IncidentSeverity,
    RecoveryReview,
    RootCauseCandidate,
)

IncidentSignalSourceType = Literal[
    "notification",
    "alert",
    "operator_action",
    "run_supervision",
    "action_proposal",
    "model_output",
    "prompt_boundary",
    "grounding",
    "security",
    "resilience",
    "audit",
    "scheduler",
    "backup",
    "release",
    "freeze",
    "outcome",
    "learning",
    "approval",
    "system",
    "generic",
]
IncidentSignalType = Literal[
    "blocked",
    "failed",
    "stalled",
    "timed_out",
    "degraded",
    "unsafe",
    "unsupported",
    "missed",
    "pending_approval",
    "contradiction",
    "high_risk",
    "verification_failed",
    "generic",
]
IncidentSignalStatus = Literal["new", "linked", "dismissed", "archived", "deleted"]
IncidentStatus = Literal[
    "open",
    "acknowledged",
    "investigating",
    "resolved",
    "dismissed",
    "archived",
    "deleted",
]
IncidentType = Literal[
    "operational",
    "safety",
    "grounding",
    "model_output",
    "prompt_injection",
    "run_failure",
    "scheduler_miss",
    "resilience_degradation",
    "security_failure",
    "audit_integrity",
    "release_failure",
    "backup_failure",
    "learning_signal",
    "generic",
]
CorrelationRuleStatus = Literal["active", "disabled"]
CorrelationRuleType = Literal[
    "same_trace",
    "same_source",
    "same_target",
    "same_correlation_key",
    "same_fingerprint",
    "severity_cluster",
    "temporal_cluster",
    "generic",
]
IncidentCorrelationMode = Literal["dry_run", "controlled"]
IncidentCorrelationStatus = Literal[
    "completed",
    "dry_run",
    "warning",
    "failed",
    "blocked_by_policy",
]


class IncidentSignal(BaseModel):
    """Normalized local signal that can be grouped into an incident."""

    model_config = ConfigDict(extra="forbid")

    incident_signal_id: str = Field(min_length=1)
    incident_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: IncidentSignalSourceType
    source_id: str = Field(min_length=1)
    signal_type: IncidentSignalType
    severity: IncidentSeverity
    status: IncidentSignalStatus
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    correlation_key: str = Field(min_length=1)
    fingerprint: str = Field(min_length=1)
    refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
    created_by: str | None = None
    created_at: datetime | None = None
    linked_at: datetime | None = None
    dismissed_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("title", "summary", "correlation_key", "fingerprint", "source_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "incident signal text")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class IncidentSignalCreateRequest(BaseModel):
    """Request to create a normalized incident signal."""

    model_config = ConfigDict(extra="forbid")

    incident_signal_id: str | None = None
    incident_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: IncidentSignalSourceType
    source_id: str = Field(min_length=1)
    signal_type: IncidentSignalType
    severity: IncidentSeverity
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    refs: list[str] = Field(default_factory=list)
    occurred_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class IncidentRecord(BaseModel):
    """Local incident grouping. It does not perform remediation."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: IncidentStatus
    incident_type: IncidentType
    severity: IncidentSeverity
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    primary_signal_type: str | None = None
    primary_signal_id: str | None = None
    signal_refs: list[str] = Field(default_factory=list)
    alert_refs: list[str] = Field(default_factory=list)
    notification_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    model_output_refs: list[str] = Field(default_factory=list)
    prompt_refs: list[str] = Field(default_factory=list)
    grounding_refs: list[str] = Field(default_factory=list)
    security_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    scheduler_refs: list[str] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    learning_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    root_cause_candidate_refs: list[str] = Field(default_factory=list)
    recovery_review_refs: list[str] = Field(default_factory=list)
    related_incident_ids: list[str] = Field(default_factory=list)
    correlation_key: str = Field(min_length=1)
    fingerprint: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("title", "summary", "correlation_key", "fingerprint")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "incident text")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class IncidentCreateRequest(BaseModel):
    """Request to create an incident-owned grouping record."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    incident_type: IncidentType = "generic"
    severity: IncidentSeverity = "medium"
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    primary_signal_type: str | None = None
    primary_signal_id: str | None = None
    signal_refs: list[str] = Field(default_factory=list)
    alert_refs: list[str] = Field(default_factory=list)
    notification_refs: list[str] = Field(default_factory=list)
    run_refs: list[str] = Field(default_factory=list)
    action_refs: list[str] = Field(default_factory=list)
    model_output_refs: list[str] = Field(default_factory=list)
    prompt_refs: list[str] = Field(default_factory=list)
    grounding_refs: list[str] = Field(default_factory=list)
    security_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    scheduler_refs: list[str] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    learning_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    related_incident_ids: list[str] = Field(default_factory=list)
    correlation_key: str | None = None
    fingerprint: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class IncidentCorrelationRule(BaseModel):
    """Deterministic local grouping rule."""

    model_config = ConfigDict(extra="forbid")

    correlation_rule_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: CorrelationRuleStatus
    rule_type: CorrelationRuleType
    severity_threshold: IncidentSeverity = "medium"
    source_types: list[IncidentSignalSourceType] = Field(default_factory=list)
    signal_types: list[IncidentSignalType] = Field(default_factory=list)
    window_seconds: int = Field(ge=1, le=86400)
    grouping_fields: list[str] = Field(default_factory=list)
    conditions: dict[str, Any] = Field(default_factory=dict)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "incident rule text")
        return value.strip()

    @field_validator("conditions", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class IncidentCorrelationRequest(BaseModel):
    """Request to group existing signals into incident-owned records."""

    model_config = ConfigDict(extra="forbid")

    correlation_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: IncidentCorrelationMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    window_start: datetime | None = None
    window_end: datetime | None = None
    source_types: list[IncidentSignalSourceType] = Field(default_factory=list)
    signal_types: list[IncidentSignalType] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    create_incidents: bool = True
    update_existing: bool = True
    create_notifications: bool = False
    create_operator_items: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def window_must_be_ordered(self) -> IncidentCorrelationRequest:
        if self.window_start is not None and self.window_end is not None:
            if self.window_start > self.window_end:
                raise ValueError("window_start must be before window_end")
        return self


class IncidentCorrelationRun(BaseModel):
    """Result of one deterministic incident correlation pass."""

    model_config = ConfigDict(extra="forbid")

    correlation_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: IncidentCorrelationStatus
    mode: IncidentCorrelationMode
    owner_scope: list[str] = Field(min_length=1)
    window_start: datetime | None = None
    window_end: datetime | None = None
    rules_applied: list[str] = Field(default_factory=list)
    signals_seen: int = Field(ge=0)
    signals_linked: int = Field(ge=0)
    incidents_created: int = Field(ge=0)
    incidents_updated: int = Field(ge=0)
    incidents_unchanged: int = Field(ge=0)
    incidents: list[IncidentRecord] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class IncidentQuery(BaseModel):
    """Scope-bound query for incidents and incident-owned records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    trace_id: str | None = None
    status: str | None = None
    incident_type: str | None = None
    severity: str | None = None
    correlation_key: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)


class IncidentQueryResult(BaseModel):
    """Incident query result containing AION-owned contracts only."""

    model_config = ConfigDict(extra="forbid")

    incidents: list[IncidentRecord] = Field(default_factory=list)
    signals: list[IncidentSignal] = Field(default_factory=list)
    root_causes: list[RootCauseCandidate] = Field(default_factory=list)
    recovery_reviews: list[RecoveryReview] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "CorrelationRuleStatus",
    "CorrelationRuleType",
    "IncidentCorrelationMode",
    "IncidentCorrelationRequest",
    "IncidentCorrelationRule",
    "IncidentCorrelationRun",
    "IncidentCorrelationStatus",
    "IncidentCreateRequest",
    "IncidentQuery",
    "IncidentQueryResult",
    "IncidentRecord",
    "IncidentSeverity",
    "IncidentSignal",
    "IncidentSignalCreateRequest",
    "IncidentSignalSourceType",
    "IncidentSignalStatus",
    "IncidentSignalType",
    "IncidentStatus",
    "IncidentType",
]
