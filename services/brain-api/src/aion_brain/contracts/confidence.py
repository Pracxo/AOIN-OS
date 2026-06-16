"""Confidence calibration and introspection contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.capability_awareness import CapabilityAwarenessRecord
from aion_brain.contracts.concepts import reject_secret_like_keys
from aion_brain.contracts.self_model import LimitationRecord

ConfidenceSourceType = Literal[
    "response", "reasoning", "decision", "belief", "outcome", "situation", "operator", "generic"
]
ConfidenceLevel = Literal["low", "medium", "high"]
GroundingStatus = Literal["grounded", "partially_grounded", "ungrounded", "not_applicable"]
SelfAssessmentType = Literal[
    "full", "capability", "limitation", "readiness", "confidence", "release", "operator"
]
SelfAssessmentStatus = Literal["passed", "warning", "failed"]
IntrospectionSnapshotType = Literal[
    "manual", "dialogue", "operator", "release", "freeze", "troubleshooting", "boot"
]
IntrospectionSnapshotStatus = Literal["created", "failed"]


class ConfidenceCalibration(BaseModel):
    """Deterministic confidence calibration for a Brain-owned source."""

    model_config = ConfigDict(extra="forbid")

    calibration_id: str = Field(min_length=1)
    trace_id: str | None = None
    response_id: str | None = None
    reasoning_id: str | None = None
    decision_frame_id: str | None = None
    source_type: ConfidenceSourceType
    source_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    grounding_status: GroundingStatus
    uncertainty_factors: list[str] = Field(default_factory=list)
    required_disclosures: list[str] = Field(default_factory=list)
    clarification_recommended: bool
    verification_recommended: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ConfidenceCalibrationRequest(BaseModel):
    """Request deterministic confidence calibration."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    response_id: str | None = None
    reasoning_id: str | None = None
    decision_frame_id: str | None = None
    source_type: ConfidenceSourceType
    source_id: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    require_grounding: bool = False
    uncertainty_factors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class SelfAssessmentRequest(BaseModel):
    """Request a read-only self-assessment run."""

    model_config = ConfigDict(extra="forbid")

    self_assessment_id: str | None = None
    trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    assessment_type: SelfAssessmentType = "full"
    include_capabilities: bool = True
    include_limitations: bool = True
    include_config: bool = True
    include_security: bool = True
    include_resilience: bool = True
    include_operator: bool = True
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class SelfAssessmentRun(BaseModel):
    """Result of a read-only self-assessment run."""

    model_config = ConfigDict(extra="forbid")

    self_assessment_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: SelfAssessmentStatus
    owner_scope: list[str] = Field(min_length=1)
    assessment_type: SelfAssessmentType
    capability_count: int = Field(ge=0)
    active_capability_count: int = Field(ge=0)
    disabled_capability_count: int = Field(ge=0)
    unavailable_capability_count: int = Field(ge=0)
    limitation_count: int = Field(ge=0)
    critical_limitation_count: int = Field(ge=0)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("findings", mode="after")
    @classmethod
    def findings_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_keys(item)
        return value

    @field_validator("report")
    @classmethod
    def report_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class IntrospectionSnapshotRequest(BaseModel):
    """Request a descriptive introspection snapshot."""

    model_config = ConfigDict(extra="forbid")

    introspection_snapshot_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    snapshot_type: IntrospectionSnapshotType = "manual"
    owner_scope: list[str] = Field(min_length=1)
    include_operator_summary: bool = True
    include_config_summary: bool = True
    include_audit_refs: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class IntrospectionSnapshot(BaseModel):
    """Stored descriptive state snapshot for AION introspection."""

    model_config = ConfigDict(extra="forbid")

    introspection_snapshot_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    snapshot_type: IntrospectionSnapshotType
    status: IntrospectionSnapshotStatus
    owner_scope: list[str] = Field(min_length=1)
    self_model: dict[str, Any]
    capability_inventory: list[CapabilityAwarenessRecord]
    limitations: list[LimitationRecord]
    calibration_summary: dict[str, Any]
    operator_summary: dict[str, Any]
    config_summary: dict[str, Any]
    audit_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator(
        "self_model", "calibration_summary", "operator_summary", "config_summary", "metadata"
    )
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


__all__ = [
    "ConfidenceCalibration",
    "ConfidenceCalibrationRequest",
    "ConfidenceLevel",
    "ConfidenceSourceType",
    "GroundingStatus",
    "IntrospectionSnapshot",
    "IntrospectionSnapshotRequest",
    "IntrospectionSnapshotStatus",
    "IntrospectionSnapshotType",
    "SelfAssessmentRequest",
    "SelfAssessmentRun",
    "SelfAssessmentStatus",
    "SelfAssessmentType",
]
