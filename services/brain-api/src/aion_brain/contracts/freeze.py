"""Release freeze gate contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.versioning import reject_secret_like_keys

FreezeGateCheckStatus = Literal["passed", "failed", "warning", "skipped"]
FreezeGateSeverity = Literal["low", "medium", "high", "critical"]
FreezeGateRunStatus = Literal["passed", "failed", "warning"]


class FreezeGateCheck(BaseModel):
    """One deterministic freeze gate check result."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    status: FreezeGateCheckStatus
    severity: FreezeGateSeverity
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("details")
    @classmethod
    def details_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like check details."""
        reject_secret_like_keys(value)
        return value


class FreezeGateRunRequest(BaseModel):
    """Request to run AION's deterministic freeze gate."""

    model_config = ConfigDict(extra="forbid")

    freeze_gate_id: str | None = None
    version: str = Field(min_length=1)
    requested_by: str | None = None
    owner_scope: list[str] = Field(
        default_factory=list,
        min_length=1,
        validation_alias=AliasChoices("owner_scope", "scope"),
    )
    include_release_baseline: bool = True
    include_kernel_self_test: bool = True
    include_contract_export: bool = True
    include_sdk_check: bool = True
    include_policy_coverage: bool = True
    include_openapi_hygiene: bool = True
    include_boundary_check: bool = True
    include_migration_baseline: bool = True
    include_no_domain_drift: bool = True
    include_repo_health: bool = True
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like freeze metadata."""
        reject_secret_like_keys(value)
        return value


class FreezeGateRun(BaseModel):
    """Persisted freeze gate run."""

    model_config = ConfigDict(extra="forbid")

    freeze_gate_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: FreezeGateRunStatus
    requested_by: str | None = None
    checks: list[FreezeGateCheck] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("failures", "warnings")
    @classmethod
    def lists_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reject secret-like failure or warning payloads."""
        for payload in value:
            reject_secret_like_keys(payload)
        return value

    @field_validator("report")
    @classmethod
    def report_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like report payloads."""
        reject_secret_like_keys(value)
        return value
