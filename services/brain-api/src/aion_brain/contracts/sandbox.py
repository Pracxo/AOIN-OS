"""Sandbox control-plane contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.secrets import (
    reject_secret_like_keys,
    reject_secret_like_values,
)

SandboxStatus = Literal["active", "disabled"]
SandboxType = Literal["local_noop", "docker", "firecracker", "external_placeholder"]
DestinationType = Literal["none", "internal", "connector", "domain", "cidr", "wildcard"]
EgressProtocol = Literal["tcp", "udp", "http", "https"]
RuleAction = Literal["allow", "deny"]
FilesystemAccess = Literal["read", "write", "read_write"]
RuntimePermissionName = Literal[
    "runtime.execute",
    "runtime.network",
    "runtime.filesystem.read",
    "runtime.filesystem.write",
    "runtime.secret.read",
    "runtime.connector.use",
    "runtime.process.spawn",
    "runtime.model.use",
    "runtime.memory.read",
    "runtime.memory.write",
    "runtime.audit.write",
]
ValidationCheckStatus = Literal["passed", "failed", "warning", "skipped"]
ValidationSeverity = Literal["low", "medium", "high", "critical"]
SandboxValidationStatus = Literal["passed", "warning", "failed"]
SandboxRunTargetType = Literal[
    "capability",
    "module",
    "mcp_tool",
    "command",
    "workflow_step",
    "test",
]
SandboxRunMode = Literal["dry_run", "controlled"]
SandboxRunStatus = Literal[
    "dry_run",
    "completed",
    "blocked_by_policy",
    "blocked_by_autonomy",
    "waiting_for_approval",
    "unsupported",
    "failed",
]
RuntimeGrantTargetType = Literal["module", "capability", "mcp_server", "workflow", "command"]
RuntimeGrantStatus = Literal["active", "revoked", "expired"]


class ResourceLimits(BaseModel):
    """Resource limits for future sandbox execution."""

    model_config = ConfigDict(extra="forbid")

    cpu_millis: int = Field(ge=100, le=8000)
    memory_mb: int = Field(ge=64, le=8192)
    timeout_seconds: int = Field(ge=1, le=3600)
    max_output_bytes: int = Field(ge=1024, le=104857600)
    max_files: int = Field(ge=0, le=10000)
    max_file_bytes: int = Field(ge=0, le=104857600)


class EgressRule(BaseModel):
    """Network egress metadata rule."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1)
    destination_type: DestinationType
    destination_ref: str
    ports: list[int]
    protocol: EgressProtocol
    action: RuleAction
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("ports")
    @classmethod
    def ports_must_be_valid(cls, value: list[int]) -> list[int]:
        if any(port < 1 or port > 65535 for port in value):
            raise ValueError("ports must be between 1 and 65535")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value

    @model_validator(mode="after")
    def wildcard_requires_explicit_marker(self) -> EgressRule:
        if self.destination_type == "wildcard" and self.metadata.get("allow_wildcard") is not True:
            raise ValueError("wildcard egress requires explicit allow_wildcard metadata")
        return self


class FilesystemRule(BaseModel):
    """Filesystem access metadata rule."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1)
    path_ref: str = Field(min_length=1)
    access: FilesystemAccess
    action: RuleAction
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("path_ref")
    @classmethod
    def path_ref_must_be_safe(cls, value: str) -> str:
        normalized = value.lower()
        if ".." in value:
            raise ValueError("path_ref cannot contain path traversal")
        if normalized.startswith("/etc"):
            raise ValueError("path_ref cannot reference /etc")
        if normalized.startswith("/var/run/docker.sock"):
            raise ValueError("path_ref cannot reference Docker socket")
        if any(part in normalized for part in ("secret", "token", "password", "private_key")):
            raise ValueError("path_ref cannot contain secret-like names")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value


class RuntimePermission(BaseModel):
    """One generic runtime permission flag."""

    model_config = ConfigDict(extra="forbid")

    permission: RuntimePermissionName
    allowed: bool
    reason: str | None = None


class SandboxProfile(BaseModel):
    """Reusable sandbox profile for future isolated execution."""

    model_config = ConfigDict(extra="forbid")

    sandbox_profile_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: SandboxStatus
    sandbox_type: SandboxType
    owner_scope: list[str] = Field(min_length=1)
    resource_limits: ResourceLimits
    egress_rules: list[EgressRule] = Field(default_factory=list)
    filesystem_rules: list[FilesystemRule] = Field(default_factory=list)
    allowed_runtime_permissions: list[RuntimePermission] = Field(default_factory=list)
    secret_refs_allowed: list[str] = Field(default_factory=list)
    connector_refs_allowed: list[str] = Field(default_factory=list)
    network_enabled: bool = False
    filesystem_write_enabled: bool = False
    process_spawn_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value

    @model_validator(mode="after")
    def v01_process_spawn_guard(self) -> SandboxProfile:
        if self.process_spawn_enabled and not (
            self.sandbox_type == "external_placeholder" and self.status == "disabled"
        ):
            raise ValueError("process_spawn_enabled is not supported for active v0.1 profiles")
        return self


class SandboxProfileCreateRequest(BaseModel):
    """Request to create a sandbox profile."""

    model_config = ConfigDict(extra="forbid")

    sandbox_profile_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    sandbox_type: SandboxType = "local_noop"
    owner_scope: list[str] = Field(min_length=1)
    resource_limits: ResourceLimits
    egress_rules: list[EgressRule] = Field(default_factory=list)
    filesystem_rules: list[FilesystemRule] = Field(default_factory=list)
    allowed_runtime_permissions: list[RuntimePermission] = Field(default_factory=list)
    secret_refs_allowed: list[str] = Field(default_factory=list)
    connector_refs_allowed: list[str] = Field(default_factory=list)
    network_enabled: bool = False
    filesystem_write_enabled: bool = False
    process_spawn_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    activate: bool = True

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value

    @model_validator(mode="after")
    def v01_process_spawn_guard(self) -> SandboxProfileCreateRequest:
        if self.process_spawn_enabled and not (
            self.sandbox_type == "external_placeholder" and not self.activate
        ):
            raise ValueError("process_spawn_enabled is not supported for active v0.1 profiles")
        return self


class SandboxValidationCheck(BaseModel):
    """One deterministic sandbox validation check."""

    model_config = ConfigDict(extra="forbid")

    check_id: str
    name: str
    status: ValidationCheckStatus
    severity: ValidationSeverity
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class SandboxValidationResult(BaseModel):
    """Persistable sandbox validation result."""

    model_config = ConfigDict(extra="forbid")

    validation_id: str
    sandbox_profile_id: str | None = None
    target_type: str
    target_id: str | None = None
    status: SandboxValidationStatus
    score: float = Field(ge=0.0, le=1.0)
    checks: list[SandboxValidationCheck]
    failures: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class SandboxRunRequest(BaseModel):
    """Request to validate or run through the sandbox control plane."""

    model_config = ConfigDict(extra="forbid")

    sandbox_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    sandbox_profile_id: str = Field(min_length=1)
    target_type: SandboxRunTargetType
    target_id: str | None = None
    mode: SandboxRunMode = "dry_run"
    input: dict[str, Any] = Field(default_factory=dict)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("input", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value


class SandboxRunResult(BaseModel):
    """Result record for sandbox control-plane runs."""

    model_config = ConfigDict(extra="forbid")

    sandbox_run_id: str
    trace_id: str | None = None
    sandbox_profile_id: str
    target_type: SandboxRunTargetType
    target_id: str | None = None
    mode: SandboxRunMode
    status: SandboxRunStatus
    output: dict[str, Any]
    error: dict[str, Any]
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    autonomy_decision_id: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RuntimePermissionGrant(BaseModel):
    """Explicit permission grant for a runtime target."""

    model_config = ConfigDict(extra="forbid")

    runtime_permission_id: str = Field(min_length=1)
    target_type: RuntimeGrantTargetType
    target_id: str = Field(min_length=1)
    sandbox_profile_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    permissions: list[RuntimePermission]
    secret_refs: list[str] = Field(default_factory=list)
    connector_refs: list[str] = Field(default_factory=list)
    status: RuntimeGrantStatus
    granted_by: str | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    revoked_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value


class RuntimePermissionGrantRequest(BaseModel):
    """Request to grant runtime permissions."""

    model_config = ConfigDict(extra="forbid")

    runtime_permission_id: str | None = None
    target_type: RuntimeGrantTargetType
    target_id: str = Field(min_length=1)
    sandbox_profile_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    permissions: list[RuntimePermission]
    secret_refs: list[str] = Field(default_factory=list)
    connector_refs: list[str] = Field(default_factory=list)
    granted_by: str | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_secret_like_values(value)
        return value


__all__ = [
    "EgressRule",
    "FilesystemRule",
    "ResourceLimits",
    "RuntimePermission",
    "RuntimePermissionGrant",
    "RuntimePermissionGrantRequest",
    "SandboxProfile",
    "SandboxProfileCreateRequest",
    "SandboxRunRequest",
    "SandboxRunResult",
    "SandboxValidationCheck",
    "SandboxValidationResult",
]
