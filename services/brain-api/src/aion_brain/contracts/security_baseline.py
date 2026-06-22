"""Local security baseline contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.versioning import reject_secret_like_keys

ThreatModelStatus = Literal["open", "mitigated", "accepted", "dismissed"]
ThreatCategory = Literal[
    "api",
    "auth",
    "policy",
    "autonomy",
    "memory",
    "evidence",
    "model_gateway",
    "module_runtime",
    "mcp",
    "sandbox",
    "connector",
    "backup",
    "release",
    "observability",
    "dependency",
    "configuration",
    "supply_chain",
]
RiskLevel = Literal["low", "medium", "high", "critical"]
Likelihood = Literal["low", "medium", "high"]
ThreatImpact = Literal["low", "medium", "high", "critical"]
AttackSurfaceType = Literal[
    "http_api",
    "event_bus",
    "command_bus",
    "module_runtime",
    "mcp_server",
    "model_gateway",
    "connector",
    "sandbox",
    "backup_file",
    "release_package",
    "sdk_cli",
    "configuration",
    "database",
    "object_store_placeholder",
    "optional_adapter",
]
ExposureLevel = Literal["internal", "local", "optional_external", "disabled"]
SecurityControlStatus = Literal["implemented", "partial", "missing", "not_applicable"]
SecretFindingType = Literal[
    "api_key_like",
    "bearer_token_like",
    "private_key_like",
    "password_like",
    "env_file",
    "credential_file",
    "secret_named_file",
    "raw_secret_value",
    "suspicious_config",
]
SecretFindingStatus = Literal["open", "ignored", "false_positive", "resolved"]
SecurityScanType = Literal[
    "secrets",
    "config",
    "api_exposure",
    "adapter_risk",
    "dependency_metadata",
    "threat_model",
    "controls",
    "full",
]
SecurityRunStatus = Literal["passed", "warning", "failed"]

_CONTROL_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_RAW_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
_BANNED_PATH_PARTS = {".."}


class ThreatModelRecord(BaseModel):
    """One generic threat model entry for local AION posture inspection."""

    model_config = ConfigDict(extra="forbid")

    threat_model_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ThreatModelStatus
    category: ThreatCategory
    asset_type: str = Field(min_length=1)
    threat_type: str = Field(min_length=1)
    severity: RiskLevel
    likelihood: Likelihood
    impact: ThreatImpact
    controls: list[str] = Field(default_factory=list)
    residual_risk: RiskLevel
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class AttackSurfaceRecord(BaseModel):
    """One locally cataloged AION attack surface."""

    model_config = ConfigDict(extra="forbid")

    attack_surface_id: str = Field(min_length=1)
    surface_type: AttackSurfaceType
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    exposure_level: ExposureLevel
    risk_level: RiskLevel
    owner_scope: list[str] = Field(min_length=1)
    controls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class SecurityControlRecord(BaseModel):
    """One generic local security baseline control."""

    model_config = ConfigDict(extra="forbid")

    security_control_id: str = Field(min_length=1)
    control_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: ThreatCategory
    status: SecurityControlStatus
    required: bool
    evidence_refs: list[str] = Field(default_factory=list)
    implementation_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("control_key")
    @classmethod
    def control_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _CONTROL_KEY_PATTERN.match(value):
            raise ValueError("control_key must be dotted lowercase text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class SecretScanFinding(BaseModel):
    """One redacted local secret scan finding."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1)
    scan_id: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    line_number: int | None = Field(default=None, ge=1)
    finding_type: SecretFindingType
    severity: RiskLevel
    redacted_match: str = Field(min_length=1)
    status: SecretFindingStatus = "open"
    reason: str | None = None
    created_at: datetime | None = None

    @field_validator("redacted_match")
    @classmethod
    def redacted_match_must_not_be_raw_secret(cls, value: str) -> str:
        has_redaction_marker = "***" in value or "[redacted]" in value
        contains_raw_secret = any(pattern.search(value) for pattern in _RAW_SECRET_PATTERNS)
        if not has_redaction_marker and contains_raw_secret:
            raise ValueError("redacted_match must not contain raw secret value")
        return value


class SecurityScanRequest(BaseModel):
    """Request for a deterministic local security scan."""

    model_config = ConfigDict(extra="forbid")

    security_scan_id: str | None = None
    scan_type: SecurityScanType
    owner_scope: list[str] = Field(min_length=1)
    paths: list[str] = Field(default_factory=list)
    include_docs: bool = True
    include_tests: bool = True
    include_examples: bool = True
    max_file_size_mb: int = Field(default=5, ge=1, le=50)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("paths")
    @classmethod
    def paths_must_not_traverse(cls, value: list[str]) -> list[str]:
        for item in value:
            parts = PurePosixPath(item.replace("\\", "/")).parts
            if any(part in _BANNED_PATH_PARTS for part in parts):
                raise ValueError("paths must not contain path traversal")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class SecurityScanRun(BaseModel):
    """Completed deterministic local security scan."""

    model_config = ConfigDict(extra="forbid")

    security_scan_id: str = Field(min_length=1)
    scan_type: SecurityScanType
    status: SecurityRunStatus
    owner_scope: list[str] = Field(min_length=1)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[SecretScanFinding] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("checks", "failures", "warnings")
    @classmethod
    def check_payloads_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_keys(item)
        return value

    @field_validator("report")
    @classmethod
    def report_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class HardeningGateRequest(BaseModel):
    """Request for the deterministic local hardening gate."""

    model_config = ConfigDict(extra="forbid")

    hardening_gate_id: str | None = None
    version: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    include_secret_scan: bool = True
    include_config_check: bool = True
    include_api_exposure_check: bool = True
    include_adapter_risk_check: bool = True
    include_policy_coverage_check: bool = True
    include_autonomy_defaults_check: bool = True
    include_sandbox_check: bool = True
    include_backup_redaction_check: bool = True
    include_release_package_check: bool = True
    include_dependency_metadata_check: bool = True
    fail_on_high: bool = True
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class HardeningGateRun(BaseModel):
    """Completed local hardening gate run."""

    model_config = ConfigDict(extra="forbid")

    hardening_gate_id: str = Field(min_length=1)
    version: str | None = None
    status: SecurityRunStatus
    owner_scope: list[str] = Field(min_length=1)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("checks", "failures", "warnings")
    @classmethod
    def payloads_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_keys(item)
        return value

    @field_validator("report")
    @classmethod
    def report_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class DependencyMetadataFinding(BaseModel):
    """Local dependency metadata finding."""

    model_config = ConfigDict(extra="forbid")

    dependency_name: str = Field(min_length=1)
    source: str = Field(min_length=1)
    declared_version: str | None = None
    optional: bool
    category: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)


class SeedThreatModelsRequest(BaseModel):
    """Request to seed or preview default threat model records."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = True
    owner_scope: list[str] = Field(min_length=1)


class SeedControlsRequest(BaseModel):
    """Request to seed or preview default security controls."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = True


class StatusUpdateRequest(BaseModel):
    """Generic status update request for baseline records."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(min_length=1)
    actor_id: str | None = None
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def reason_must_be_safe(self) -> StatusUpdateRequest:
        if any(pattern.search(self.reason) for pattern in _RAW_SECRET_PATTERNS):
            raise ValueError("reason must not contain raw secret value")
        return self
