"""Release candidate verification matrix contracts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

VerificationCheckType = Literal[
    "unit_tests",
    "sdk_tests",
    "lint",
    "typecheck",
    "domain_drift",
    "boundary",
    "policy_coverage",
    "openapi",
    "repo_health",
    "docker_config",
    "docker_smoke",
    "health_readiness",
    "bootstrap",
    "golden_path",
    "release_smoke",
    "freeze_gate",
    "release_package",
    "contract_registry",
    "resource_registry",
    "lifecycle",
    "extension",
    "module_binding",
    "conformance",
    "security",
    "runtime_config",
    "operator",
    "generic",
]
VerificationCheckStatus = Literal["passed", "warning", "failed", "skipped", "blocked", "unknown"]
VerificationSeverity = Literal["low", "medium", "high", "critical"]
VerificationMatrixStatus = Literal["active", "disabled"]

_DOTTED_LOWERCASE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$")


class VerificationCheck(BaseModel):
    """One normalized release-candidate verification check result."""

    model_config = ConfigDict(extra="forbid")

    verification_check_id: str = Field(min_length=1)
    trace_id: str | None = None
    rc_run_id: str | None = None
    check_key: str = Field(min_length=1)
    check_type: VerificationCheckType
    status: VerificationCheckStatus
    severity: VerificationSeverity
    required: bool
    passed: bool
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    command_hint: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int | None = Field(default=None, ge=0)
    error: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("check_key")
    @classmethod
    def check_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWERCASE.fullmatch(value):
            raise ValueError("check_key must be dotted lowercase text")
        return value

    @field_validator("title", "summary", "command_hint")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return value
        reject_hidden_or_secret_text(value, "verification check text")
        return value.strip()

    @field_validator("evidence", "error", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def status_and_passed_must_match(self) -> VerificationCheck:
        if self.status in {"failed", "blocked"} and self.passed:
            raise ValueError("failed or blocked checks cannot be marked passed")
        if self.status == "passed" and not self.passed:
            raise ValueError("passed checks must set passed=true")
        return self


class VerificationMatrix(BaseModel):
    """Named verification matrix for release-candidate scoring."""

    model_config = ConfigDict(extra="forbid")

    verification_matrix_id: str = Field(min_length=1)
    trace_id: str | None = None
    matrix_key: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: VerificationMatrixStatus
    owner_scope: list[str] = Field(min_length=1)
    required_checks: list[str] = Field(min_length=1)
    optional_checks: list[str] = Field(default_factory=list)
    required_threshold: float = Field(ge=0.0, le=1.0)
    release_ready_threshold: float = Field(ge=0.0, le=1.0)
    fail_on_critical: bool
    fail_on_missing_required: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("matrix_key")
    @classmethod
    def matrix_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWERCASE.fullmatch(value):
            raise ValueError("matrix_key must be dotted lowercase text")
        return value

    @field_validator("required_checks", "optional_checks")
    @classmethod
    def checks_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            if not _DOTTED_LOWERCASE.fullmatch(item):
                raise ValueError("verification matrix check keys must be dotted lowercase text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class VerificationMatrixCreateRequest(BaseModel):
    """Request to create a release-candidate verification matrix."""

    model_config = ConfigDict(extra="forbid")

    verification_matrix_id: str | None = None
    trace_id: str | None = None
    matrix_key: str
    version: str = "0.1.0"
    owner_scope: list[str] = Field(min_length=1)
    required_checks: list[str] = Field(min_length=1)
    optional_checks: list[str] = Field(default_factory=list)
    required_threshold: float = Field(default=1.0, ge=0.0, le=1.0)
    release_ready_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    fail_on_critical: bool = True
    fail_on_missing_required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("matrix_key")
    @classmethod
    def matrix_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWERCASE.fullmatch(value):
            raise ValueError("matrix_key must be dotted lowercase text")
        return value

    @field_validator("version")
    @classmethod
    def version_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("version cannot be empty")
        return value.strip()

    @field_validator("required_checks", "optional_checks")
    @classmethod
    def checks_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            if not _DOTTED_LOWERCASE.fullmatch(item):
                raise ValueError("verification matrix check keys must be dotted lowercase text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "VerificationCheck",
    "VerificationCheckStatus",
    "VerificationCheckType",
    "VerificationMatrix",
    "VerificationMatrixCreateRequest",
    "VerificationMatrixStatus",
    "VerificationSeverity",
]
