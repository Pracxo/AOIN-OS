"""First-run setup doctor contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

SetupFindingType = Literal[
    "missing_setting",
    "invalid_setting",
    "service_unavailable",
    "policy_unavailable",
    "route_missing",
    "sdk_missing",
    "cli_missing",
    "script_missing",
    "script_not_executable",
    "migration_pending",
    "golden_path_failed",
    "release_smoke_failed",
    "external_feature_enabled",
    "unsafe_default",
    "generic",
]
SetupFindingCategory = Literal[
    "health",
    "config",
    "policy",
    "database",
    "service",
    "sdk",
    "cli",
    "scripts",
    "docker",
    "golden_path",
    "release_smoke",
    "security",
    "operator",
    "generic",
]
SetupSeverity = Literal["low", "medium", "high", "critical"]
SetupFindingStatus = Literal["open", "resolved", "dismissed", "archived"]
SetupDoctorStatus = Literal["passed", "warning", "failed"]


class SetupFinding(BaseModel):
    """One local setup readiness finding."""

    model_config = ConfigDict(extra="forbid")

    setup_finding_id: str = Field(min_length=1)
    trace_id: str | None = None
    finding_type: SetupFindingType
    category: SetupFindingCategory
    severity: SetupSeverity
    status: SetupFindingStatus
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    check_key: str = Field(min_length=1)
    expected: dict[str, Any] = Field(default_factory=dict)
    actual: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("title", "description", "check_key", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "setup finding text")
        return value.strip()

    @field_validator("expected", "actual", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class SetupDoctorRequest(BaseModel):
    """Request for deterministic local setup inspection."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    checks: list[str] = Field(default_factory=list)
    include_golden_path: bool = True
    include_release_smoke: bool = True
    create_findings: bool = False
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("checks")
    @classmethod
    def checks_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "setup doctor check")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class SetupDoctorResult(BaseModel):
    """Computed local setup readiness result."""

    model_config = ConfigDict(extra="forbid")

    status: SetupDoctorStatus
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    findings: list[SetupFinding] = Field(default_factory=list)
    readiness_score: float = Field(ge=0.0, le=1.0)
    local_ready: bool
    health_ready: bool
    policy_ready: bool
    sdk_ready: bool
    cli_ready: bool
    golden_path_ready: bool
    release_smoke_ready: bool
    docker_ready: bool
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class SetupReport(BaseModel):
    """Persisted first-run setup report."""

    model_config = ConfigDict(extra="forbid")

    setup_report_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: SetupDoctorStatus
    owner_scope: list[str] = Field(min_length=1)
    bootstrap_run_id: str | None = None
    readiness_score: float = Field(ge=0.0, le=1.0)
    local_ready: bool
    health_ready: bool
    policy_ready: bool
    sdk_ready: bool
    cli_ready: bool
    golden_path_ready: bool
    release_smoke_ready: bool
    docker_ready: bool
    finding_count: int = Field(ge=0)
    critical_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("findings", "recommendations")
    @classmethod
    def list_payload_must_be_safe(cls, value: list[Any]) -> list[Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator("report", "metadata")
    @classmethod
    def dict_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def critical_findings_force_not_ready(self) -> SetupReport:
        if self.critical_count > 0 or any(
            str(item.get("severity", "")).lower() == "critical" for item in self.findings
        ):
            self.local_ready = False
        return self


__all__ = [
    "SetupDoctorRequest",
    "SetupDoctorResult",
    "SetupDoctorStatus",
    "SetupFinding",
    "SetupFindingCategory",
    "SetupFindingStatus",
    "SetupFindingType",
    "SetupReport",
    "SetupSeverity",
]
