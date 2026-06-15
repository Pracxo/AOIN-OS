"""Compatibility, migration, release artifact, and SDK check contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.versioning import reject_secret_like_keys

CompatibilityStatus = Literal["compatible", "warning", "incompatible"]
MigrationBaselineStatus = Literal["passed", "warning", "failed"]
ReleaseArtifactStatus = Literal["draft", "complete", "failed"]


class CompatibilityMatrix(BaseModel):
    """Compatibility record for one AION release version."""

    model_config = ConfigDict(extra="forbid")

    compatibility_matrix_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    api_version: str = Field(min_length=1)
    sdk_version: str = Field(min_length=1)
    python_version: str = Field(min_length=1)
    docker_compose_version: str | None = None
    postgres_version: str | None = None
    redis_version: str | None = None
    nats_version: str | None = None
    opa_version: str | None = None
    optional_adapters: dict[str, Any] = Field(default_factory=dict)
    compatibility: dict[str, Any] = Field(default_factory=dict)
    status: CompatibilityStatus
    created_at: datetime | None = None


class MigrationBaseline(BaseModel):
    """Deterministic migration baseline summary."""

    model_config = ConfigDict(extra="forbid")

    migration_baseline_id: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    migration_count: int = Field(ge=0)
    migration_hash: str = Field(min_length=1)
    destructive_migrations: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    status: MigrationBaselineStatus
    report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ReleaseArtifactManifest(BaseModel):
    """Metadata-only release artifact manifest."""

    model_config = ConfigDict(extra="forbid")

    release_artifact_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: ReleaseArtifactStatus
    artifacts: dict[str, Any] = Field(default_factory=dict)
    checksums: dict[str, str] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None


class SDKCompatibilityReport(BaseModel):
    """SDK/API compatibility check result."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(min_length=1)
    api_version: str = Field(min_length=1)
    sdk_version: str = Field(min_length=1)
    compatible: bool
    checked_endpoints: list[str] = Field(default_factory=list)
    missing_endpoints: list[str] = Field(default_factory=list)
    mismatched_contracts: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime

    def model_post_init(self, __context: object) -> None:
        """Reject secret-like warning or mismatch payloads."""
        for payload in [*self.mismatched_contracts, *self.warnings]:
            reject_secret_like_keys(payload)
