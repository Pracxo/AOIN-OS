"""Local backup and restore-preview contracts."""

from __future__ import annotations

from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.versioning import reject_secret_like_keys

BackupResourceType = Literal[
    "events",
    "memory",
    "semantic_index_metadata",
    "graph",
    "evidence",
    "evidence_links",
    "traces",
    "reasoning",
    "plans",
    "executions",
    "workflows",
    "goals",
    "tasks",
    "schedules",
    "skills",
    "reflections",
    "policy_catalog",
    "identity",
    "autonomy",
    "approvals",
    "modules",
    "sandbox",
    "connectors",
    "scenarios",
    "visual_telemetry",
    "release_metadata",
    "kernel_records",
]

BackupType = Literal["full_local", "scoped_local", "resource_subset", "dry_run"]
BackupRedactionMode = Literal["none", "metadata_only", "redact_sensitive", "exclude_sensitive"]
BackupJobStatus = Literal[
    "dry_run",
    "running",
    "completed",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
    "waiting_for_approval",
]
RestoreConflictType = Literal[
    "id_exists",
    "dependency_missing",
    "checksum_mismatch",
    "version_mismatch",
    "scope_mismatch",
    "sensitive_data_blocked",
    "unsupported_resource",
    "policy_block",
]
RestoreConflictSeverity = Literal["low", "medium", "high", "critical"]
RestoreConflictStrategy = Literal[
    "skip_conflicts",
    "keep_existing",
    "require_manual",
    "fail_on_conflict",
]
RestorePreviewStatus = Literal[
    "passed",
    "warning",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
]
RestoreMode = Literal["dry_run", "apply"]
RestoreJobStatus = Literal[
    "dry_run",
    "completed",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
    "waiting_for_approval",
    "unsupported",
]
BackupValidationStatus = Literal["passed", "warning", "failed"]


class BackupManifest(BaseModel):
    """Portable manifest for one local application-level backup."""

    model_config = ConfigDict(extra="forbid")

    backup_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    created_at: datetime
    created_by: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    backup_type: BackupType
    resource_types: list[BackupResourceType] = Field(min_length=1)
    redaction_mode: BackupRedactionMode
    file_count: int = Field(ge=0)
    total_record_count: int = Field(ge=0)
    total_size_bytes: int = Field(ge=0)
    root_checksum: str = Field(min_length=1)
    compatibility: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata", "compatibility")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_like_keys(value)
        return value


class BackupRequest(BaseModel):
    """Request to export local AION state through application contracts."""

    model_config = ConfigDict(extra="forbid")

    backup_job_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    backup_type: BackupType = "scoped_local"
    owner_scope: list[str] = Field(default_factory=list, min_length=1)
    resource_types: list[BackupResourceType] = Field(min_length=1)
    redaction_mode: BackupRedactionMode = "redact_sensitive"
    output_dir: str = "artifacts/backups"
    dry_run: bool = True
    include_deleted: bool = False
    include_visual_telemetry: bool = False
    max_records_per_resource: int = Field(default=100000, ge=1, le=1000000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("output_dir")
    @classmethod
    def output_dir_must_be_safe(cls, value: str) -> str:
        """Reject absolute or traversing output directories."""
        _reject_unsafe_path(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_like_keys(value)
        return value


class BackupFile(BaseModel):
    """One exported resource file in a backup."""

    model_config = ConfigDict(extra="forbid")

    backup_file_id: str = Field(min_length=1)
    backup_job_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    resource_type: BackupResourceType
    record_count: int = Field(ge=0)
    size_bytes: int = Field(ge=0)
    sha256: str
    included: bool
    reason: str | None = None
    created_at: datetime | None = None

    @field_validator("file_path")
    @classmethod
    def file_path_must_be_safe(cls, value: str) -> str:
        """Reject unsafe file paths."""
        _reject_unsafe_path(value)
        return value

    @model_validator(mode="after")
    def checksum_required_when_included(self) -> BackupFile:
        """Require a checksum for included files."""
        if self.included and not self.sha256.strip():
            raise ValueError("sha256 is required when included is true")
        return self


class BackupJob(BaseModel):
    """Persisted local backup job record."""

    model_config = ConfigDict(extra="forbid")

    backup_job_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: BackupJobStatus
    backup_type: BackupType
    owner_scope: list[str] = Field(min_length=1)
    resource_types: list[BackupResourceType] = Field(min_length=1)
    redaction_mode: BackupRedactionMode
    output_dir: str
    manifest: BackupManifest | None = None
    files: list[BackupFile] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("output_dir")
    @classmethod
    def output_dir_must_be_safe(cls, value: str) -> str:
        """Reject unsafe output directories."""
        _reject_unsafe_path(value)
        return value

    @field_validator("result")
    @classmethod
    def result_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like result keys."""
        reject_secret_like_keys(value)
        return value


class RestoreConflict(BaseModel):
    """Conflict discovered while previewing a restore."""

    model_config = ConfigDict(extra="forbid")

    conflict_id: str = Field(min_length=1)
    resource_type: BackupResourceType
    record_id: str = Field(min_length=1)
    conflict_type: RestoreConflictType
    severity: RestoreConflictSeverity
    existing_ref: str | None = None
    incoming_ref: str | None = None
    reason: str = Field(min_length=1)
    resolution_options: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_like_keys(value)
        return value


class RestorePreviewRequest(BaseModel):
    """Request to inspect whether a local backup can be restored."""

    model_config = ConfigDict(extra="forbid")

    restore_preview_id: str | None = None
    backup_job_id: str | None = None
    backup_path: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(default_factory=list, min_length=1)
    resource_types: list[BackupResourceType] = Field(default_factory=list)
    conflict_strategy: RestoreConflictStrategy = "skip_conflicts"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("backup_path")
    @classmethod
    def backup_path_must_be_safe(cls, value: str | None) -> str | None:
        """Reject unsafe backup paths when present."""
        if value is not None:
            _reject_unsafe_path(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def require_source(self) -> RestorePreviewRequest:
        """Require a stored job or local backup path."""
        if not self.backup_job_id and not self.backup_path:
            raise ValueError("backup_job_id or backup_path is required")
        return self


class RestorePreview(BaseModel):
    """Policy-gated dry-run restore plan."""

    model_config = ConfigDict(extra="forbid")

    restore_preview_id: str = Field(min_length=1)
    backup_job_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: RestorePreviewStatus
    input_manifest: BackupManifest | None = None
    conflict_count: int = Field(ge=0)
    missing_dependency_count: int = Field(ge=0)
    records_seen: int = Field(ge=0)
    records_restorable: int = Field(ge=0)
    records_blocked: int = Field(ge=0)
    conflicts: list[RestoreConflict] = Field(default_factory=list)
    plan: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("plan")
    @classmethod
    def plan_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like plan keys."""
        reject_secret_like_keys(value)
        return value


class RestoreRequest(BaseModel):
    """Request to dry-run or apply a previously previewed restore."""

    model_config = ConfigDict(extra="forbid")

    restore_job_id: str | None = None
    restore_preview_id: str = Field(min_length=1)
    mode: RestoreMode = "dry_run"
    approval_present: bool = False
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(default_factory=list, min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def apply_requires_approval(self) -> RestoreRequest:
        """Require explicit approval for apply mode in v0.1."""
        if self.mode == "apply" and not self.approval_present:
            raise ValueError("approval_present is required for apply mode")
        return self


class RestoreJob(BaseModel):
    """Persisted restore job record."""

    model_config = ConfigDict(extra="forbid")

    restore_job_id: str = Field(min_length=1)
    restore_preview_id: str = Field(min_length=1)
    backup_job_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: RestoreJobStatus
    mode: RestoreMode
    approval_request_id: str | None = None
    risk_assessment_id: str | None = None
    autonomy_decision_id: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("result")
    @classmethod
    def result_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like result keys."""
        reject_secret_like_keys(value)
        return value


class BackupValidationReport(BaseModel):
    """Validation report for a stored or path-based local backup."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(min_length=1)
    backup_job_id: str | None = None
    backup_path: str | None = None
    status: BackupValidationStatus
    checks: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("backup_path")
    @classmethod
    def backup_path_must_be_safe(cls, value: str | None) -> str | None:
        """Reject unsafe backup paths when present."""
        if value is not None:
            _reject_unsafe_path(value)
        return value

    @field_validator("checks", "failures", "warnings")
    @classmethod
    def validation_payloads_must_be_safe(
        cls,
        value: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Reject secret-like validation payload keys."""
        for payload in value:
            reject_secret_like_keys(payload)
        return value


def _reject_unsafe_path(value: str) -> None:
    path = PurePosixPath(value.replace("\\", "/"))
    if not value.strip():
        raise ValueError("path cannot be empty")
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("path must not contain path traversal")
