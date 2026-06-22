"""Data lifecycle management contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.retention import RetentionClassification

LifecycleMode = Literal["dry_run", "controlled"]
LifecycleRunStatus = Literal["completed", "dry_run", "warning", "failed", "blocked_by_policy"]
ArchiveCandidateStatus = Literal[
    "proposed",
    "reviewed",
    "dismissed",
    "converted_to_action_proposal",
    "archived",
]
LifecycleSeverity = Literal["low", "medium", "high", "critical"]
RedactionMode = Literal["metadata_only", "redact_sensitive", "exclude_sensitive", "manual_review"]
PurgePreviewStatus = Literal["created", "blocked", "warning", "failed"]
LifecycleCandidateType = Literal[
    "archive", "redaction", "purge_preview", "classification", "generic"
]
LifecycleReviewStatus = Literal["recorded", "failed"]
LifecycleReviewDecision = Literal[
    "approve_for_action_proposal",
    "reject",
    "dismiss",
    "request_approval",
    "request_backup",
    "manual_review",
    "no_action",
]
LifecycleReportStatus = Literal["passed", "warning", "failed"]


class ArchiveCandidate(BaseModel):
    """Advisory archive candidate. It does not execute archival."""

    model_config = ConfigDict(extra="forbid")

    archive_candidate_id: str = Field(min_length=1)
    trace_id: str | None = None
    resource_uri: str
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    status: ArchiveCandidateStatus
    severity: LifecycleSeverity
    reason: str = Field(min_length=1)
    lifecycle_policy_id: str | None = None
    classification_id: str | None = None
    backup_required: bool
    backup_verified: bool
    action_proposal_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    dismissed_at: datetime | None = None
    converted_at: datetime | None = None

    @field_validator("resource_uri")
    @classmethod
    def uri_must_be_aion_uri(cls, value: str) -> str:
        if not value.startswith("aion://"):
            raise ValueError("resource_uri must start with aion://")
        return value

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "archive candidate reason")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def backup_blocks_conversion_without_override(self) -> ArchiveCandidate:
        dry_run_only = self.metadata.get("dry_run_only") is True
        if (
            self.status == "converted_to_action_proposal"
            and self.backup_required
            and not self.backup_verified
            and not dry_run_only
        ):
            raise ValueError("backup verification required before archive candidate conversion")
        return self


class RedactionCandidate(BaseModel):
    """Advisory redaction candidate. It does not execute redaction."""

    model_config = ConfigDict(extra="forbid")

    redaction_candidate_id: str = Field(min_length=1)
    trace_id: str | None = None
    resource_uri: str
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    status: ArchiveCandidateStatus
    severity: LifecycleSeverity
    reason: str = Field(min_length=1)
    sensitive_paths: list[str] = Field(default_factory=list)
    suggested_redaction_mode: RedactionMode
    lifecycle_policy_id: str | None = None
    classification_id: str | None = None
    action_proposal_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    dismissed_at: datetime | None = None
    converted_at: datetime | None = None

    @field_validator("resource_uri")
    @classmethod
    def uri_must_be_aion_uri(cls, value: str) -> str:
        if not value.startswith("aion://"):
            raise ValueError("resource_uri must start with aion://")
        return value

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "redaction candidate reason")
        return value.strip()

    @field_validator("sensitive_paths")
    @classmethod
    def paths_must_not_contain_secret_values(cls, value: list[str]) -> list[str]:
        forbidden_markers = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")
        for path in value:
            lowered = path.lower()
            if any(marker in lowered for marker in forbidden_markers):
                raise ValueError("sensitive_paths must not contain raw secret values")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class PurgePreview(BaseModel):
    """Purge impact preview. It never purges in v0.1."""

    model_config = ConfigDict(extra="forbid")

    purge_preview_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: PurgePreviewStatus
    owner_scope: list[str] = Field(min_length=1)
    resource_uris: list[str] = Field(default_factory=list)
    resource_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    allowed_count: int = Field(ge=0)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    estimated_impact: dict[str, Any] = Field(default_factory=dict)
    requires_backup: bool
    backup_verified: bool
    hard_delete_allowed: bool
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("resource_uris")
    @classmethod
    def uris_must_be_aion_uris(cls, value: list[str]) -> list[str]:
        for uri in value:
            if not uri.startswith("aion://"):
                raise ValueError("resource_uris must start with aion://")
        return value

    @field_validator("blockers", "warnings")
    @classmethod
    def lists_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_payload(value)
        return value

    @field_validator("estimated_impact", "result", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def hard_delete_must_be_disabled(self) -> PurgePreview:
        if self.hard_delete_allowed:
            raise ValueError("hard_delete_allowed must be false in v0.1")
        return self


class LifecycleReviewRecord(BaseModel):
    """Review record for lifecycle candidates. It does not execute actions."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_review_id: str = Field(min_length=1)
    trace_id: str | None = None
    resource_uri: str | None = None
    candidate_type: LifecycleCandidateType
    candidate_id: str | None = None
    status: LifecycleReviewStatus
    decision: LifecycleReviewDecision
    actor_id: str | None = None
    workspace_id: str | None = None
    reason: str = Field(min_length=1)
    policy_decision_id: str | None = None
    approval_request_id: str | None = None
    action_proposal_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "lifecycle review reason")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class LifecycleEvaluationRequest(BaseModel):
    """Request for a deterministic lifecycle evaluation."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_evaluation_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: LifecycleMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    resource_types: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    policy_ids: list[str] = Field(default_factory=list)
    include_archive_candidates: bool = True
    include_redaction_candidates: bool = True
    include_purge_previews: bool = True
    create_notifications: bool = False
    create_incident_signals: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class LifecycleEvaluationRun(BaseModel):
    """Result of one lifecycle evaluation run."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_evaluation_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: LifecycleRunStatus
    mode: LifecycleMode
    owner_scope: list[str] = Field(min_length=1)
    resource_types: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    policy_ids: list[str] = Field(default_factory=list)
    resources_evaluated: int = Field(ge=0)
    classifications_created: int = Field(default=0, ge=0)
    archive_candidates_created: int = Field(default=0, ge=0)
    redaction_candidates_created: int = Field(default=0, ge=0)
    purge_previews_created: int = Field(default=0, ge=0)
    reviews_created: int = Field(default=0, ge=0)
    classifications: list[RetentionClassification] = Field(default_factory=list)
    archive_candidates: list[ArchiveCandidate] = Field(default_factory=list)
    redaction_candidates: list[RedactionCandidate] = Field(default_factory=list)
    purge_previews: list[PurgePreview] = Field(default_factory=list)
    review_records: list[LifecycleReviewRecord] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class LifecycleReport(BaseModel):
    """Deterministic lifecycle summary report."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_report_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: LifecycleReportStatus
    owner_scope: list[str] = Field(min_length=1)
    resource_count: int = Field(ge=0)
    classified_count: int = Field(ge=0)
    archive_candidate_count: int = Field(ge=0)
    redaction_candidate_count: int = Field(ge=0)
    purge_preview_count: int = Field(ge=0)
    overdue_review_count: int = Field(ge=0)
    sensitive_resource_count: int = Field(ge=0)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("findings")
    @classmethod
    def findings_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_payload(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "ArchiveCandidate",
    "ArchiveCandidateStatus",
    "LifecycleCandidateType",
    "LifecycleEvaluationRequest",
    "LifecycleEvaluationRun",
    "LifecycleMode",
    "LifecycleReport",
    "LifecycleReportStatus",
    "LifecycleReviewDecision",
    "LifecycleReviewRecord",
    "LifecycleReviewStatus",
    "LifecycleRunStatus",
    "LifecycleSeverity",
    "PurgePreview",
    "PurgePreviewStatus",
    "RedactionCandidate",
    "RedactionMode",
]
