"""Extension readiness contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_secret_like_payload

ReadinessStatus = Literal["ready", "warning", "blocked", "failed"]
ReadinessLevel = Literal["metadata_only", "reviewed", "conformant", "blocked", "not_ready"]


class ReadinessAssessmentRequest(BaseModel):
    """Request to assess metadata readiness without activation."""

    model_config = ConfigDict(extra="forbid")

    readiness_assessment_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(default_factory=list)
    extension_package_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    conformance_profile_id: str | None = None
    require_approved_review: bool = True
    require_passing_conformance: bool = True
    require_no_blockers: bool = True
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def target_required(self) -> ReadinessAssessmentRequest:
        if not (self.extension_package_id or self.module_slot_id or self.capability_binding_id):
            raise ValueError("at least one readiness target id is required")
        return self


class ReadinessAssessment(BaseModel):
    """Readiness result that never activates an extension."""

    model_config = ConfigDict(extra="forbid")

    readiness_assessment_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    extension_package_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    status: ReadinessStatus
    readiness_level: ReadinessLevel
    activation_ready: bool
    minimum_score: float = Field(ge=0.0, le=1.0)
    actual_score: float = Field(ge=0.0, le=1.0)
    conformance_run_ids: list[str] = Field(default_factory=list)
    compatibility_run_ids: list[str] = Field(default_factory=list)
    validation_run_ids: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    warning_refs: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def readiness_must_not_activate(self) -> ReadinessAssessment:
        if self.activation_ready:
            raise ValueError("activation_ready must remain false in v0.1")
        return self


__all__ = [
    "ReadinessAssessment",
    "ReadinessAssessmentRequest",
    "ReadinessLevel",
    "ReadinessStatus",
]
