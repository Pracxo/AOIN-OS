"""Local release package contracts."""

from __future__ import annotations

from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.versioning import reject_secret_like_keys

ReleasePackageArtifactType = Literal[
    "source",
    "contract",
    "openapi",
    "policy",
    "migration",
    "docs",
    "sdk",
    "docker",
    "changelog",
    "release_notes",
    "sbom",
    "checksum",
    "manifest",
    "report",
    "script",
    "config",
]
ReleasePackageValidationStatus = Literal["passed", "warning", "failed"]
ReleaseHandoffStatus = Literal["ready", "warning", "blocked"]
ReleasePackageStatus = Literal["dry_run", "created", "failed"]
SBOMPlaceholderFormat = Literal["aion-local-json-placeholder"]


class ReleasePackageFile(BaseModel):
    """One file considered for a local release package."""

    model_config = ConfigDict(extra="forbid")

    release_package_file_id: str = Field(min_length=1)
    release_package_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    artifact_type: ReleasePackageArtifactType
    size_bytes: int = Field(ge=0)
    sha256: str
    included: bool
    reason: str | None = None
    created_at: datetime | None = None

    @field_validator("file_path")
    @classmethod
    def file_path_must_be_safe(cls, value: str) -> str:
        """Reject empty or traversing file paths."""
        _reject_unsafe_path(value)
        return value

    @model_validator(mode="after")
    def checksum_required_when_included(self) -> ReleasePackageFile:
        """Require a checksum for included files."""
        if self.included and not self.sha256.strip():
            raise ValueError("sha256 is required when included is true")
        return self


class ReleasePackageManifest(BaseModel):
    """Summary manifest for a local release package."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    package_name: str = Field(min_length=1)
    created_at: datetime
    included_artifacts: list[str] = Field(default_factory=list)
    excluded_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    file_count: int = Field(ge=0)
    total_size_bytes: int = Field(ge=0)
    root_checksum: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        reject_secret_like_keys(value)
        return value


class ReleasePackageValidation(BaseModel):
    """Validation result for a release package."""

    model_config = ConfigDict(extra="forbid")

    status: ReleasePackageValidationStatus
    checks: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("checks", "failures", "warnings")
    @classmethod
    def validation_payloads_must_be_safe(
        cls,
        value: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Reject secret-like validation payloads."""
        for payload in value:
            reject_secret_like_keys(payload)
        return value


class ReleaseHandoffReport(BaseModel):
    """Final local handoff report for a release package."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    status: ReleaseHandoffStatus
    summary: str = Field(min_length=1)
    included_reports: dict[str, Any] = Field(default_factory=dict)
    local_verification_commands: list[str] = Field(default_factory=list)
    known_limits: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("included_reports")
    @classmethod
    def included_reports_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like included report metadata."""
        reject_secret_like_keys(value)
        return value


class ReleasePackageRequest(BaseModel):
    """Request to create a local release package."""

    model_config = ConfigDict(extra="forbid")

    release_package_id: str | None = None
    version: str = Field(min_length=1)
    created_by: str | None = None
    owner_scope: list[str] = Field(
        default_factory=list,
        min_length=1,
        validation_alias=AliasChoices("owner_scope", "scope"),
    )
    output_dir: str = "artifacts/releases"
    include_source_manifest: bool = True
    include_contracts: bool = True
    include_policy_bundle: bool = True
    include_migration_baseline: bool = True
    include_release_baseline: bool = True
    include_freeze_gate: bool = True
    include_sbom_placeholder: bool = True
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("output_dir")
    @classmethod
    def output_dir_must_be_safe(cls, value: str) -> str:
        """Reject unsafe output directories."""
        _reject_unsafe_path(value)
        return value

    @field_validator("metadata")
    @classmethod
    def request_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like request metadata."""
        reject_secret_like_keys(value)
        return value


class ReleasePackage(BaseModel):
    """Persisted local release package record."""

    model_config = ConfigDict(extra="forbid")

    release_package_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: ReleasePackageStatus
    package_name: str = Field(min_length=1)
    package_path: str = Field(min_length=1)
    manifest: ReleasePackageManifest
    files: list[ReleasePackageFile] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    validation: ReleasePackageValidation
    handoff_report: ReleaseHandoffReport
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class SBOMPlaceholder(BaseModel):
    """Local metadata-only SBOM placeholder."""

    model_config = ConfigDict(extra="forbid")

    sbom_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    format: SBOMPlaceholderFormat
    packages: list[dict[str, Any]] = Field(default_factory=list)
    generated_by: str = Field(min_length=1)
    generated_at: datetime
    limitations: list[str] = Field(default_factory=list)

    @field_validator("packages")
    @classmethod
    def packages_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reject secret-like package metadata."""
        for package in value:
            reject_secret_like_keys(package)
        return value


def _reject_unsafe_path(value: str) -> None:
    path = PurePosixPath(value.replace("\\", "/"))
    if not value.strip():
        raise ValueError("path cannot be empty")
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("path must not contain path traversal")
