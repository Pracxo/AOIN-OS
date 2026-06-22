"""Runtime configuration control-plane contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.versioning import reject_secret_like_keys

ConfigValueType = Literal["string", "integer", "float", "boolean", "list", "object"]
ConfigValueSource = Literal[
    "env",
    "default",
    "runtime_override",
    "feature_registry",
    "adapter_status",
    "computed",
]
ConfigRecordStatus = Literal["active", "disabled"]
ConfigProfileType = Literal["local_dev", "test", "release_candidate", "safe_defaults", "custom"]
FeatureOverrideSource = Literal["runtime", "test", "release_gate", "operator"]
FeatureOverrideStatus = Literal["active", "disabled", "expired"]
ConfigSnapshotType = Literal[
    "boot",
    "manual",
    "freeze_gate",
    "release_candidate",
    "pre_change",
    "post_change",
]
ConfigSnapshotStatus = Literal["active", "archived"]
ConfigValidationStatus = Literal["passed", "failed", "warning", "skipped"]
ConfigValidationSeverity = Literal["low", "medium", "high", "critical"]
ConfigRunStatus = Literal["passed", "warning", "failed"]
ConfigChangeTargetType = Literal[
    "config_value",
    "config_profile",
    "feature_flag_override",
    "config_snapshot",
]
ConfigChangeType = Literal["create", "update", "disable", "expire", "snapshot"]

_CONFIG_KEY_RE = re.compile(
    r"^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+|[A-Z][A-Z0-9_]*(?:_[A-Z0-9]+)+)$"
)
_FEATURE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
_BANNED_KEY_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "payment",
    "procurement",
}
_UNSAFE_TRUE_KEYS = {
    "autonomy.full",
    "autonomy.full_control",
    "autonomy.external_tools",
    "autonomy.external_models",
    "autonomy.background_workflows",
    "model_gateway.external",
    "model_gateway.enabled",
    "mcp.enabled",
    "external.tools",
    "external.models",
}


class RuntimeConfigValue(BaseModel):
    """One safe runtime configuration metadata value."""

    model_config = ConfigDict(extra="forbid")

    config_value_id: str = Field(min_length=1)
    config_key: str = Field(min_length=1)
    config_value: dict[str, Any]
    value_type: ConfigValueType
    source: ConfigValueSource
    status: ConfigRecordStatus
    sensitive: bool
    mutable: bool
    requires_restart: bool
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("config_key")
    @classmethod
    def config_key_must_be_safe(cls, value: str) -> str:
        _validate_config_key(value, "config_key")
        return value

    @field_validator("config_value", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def sensitive_values_must_be_redacted(self) -> RuntimeConfigValue:
        if self.sensitive and self.config_value != {"redacted": True}:
            allowed = {"redacted", "present", "source", "kind"}
            if not set(self.config_value).issubset(allowed):
                raise ValueError("sensitive config_value must be redacted metadata")
        return self


class ConfigProfile(BaseModel):
    """Safe metadata profile for local runtime behavior."""

    model_config = ConfigDict(extra="forbid")

    config_profile_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ConfigRecordStatus
    profile_type: ConfigProfileType
    owner_scope: list[str] = Field(min_length=1)
    values: dict[str, Any] = Field(default_factory=dict)
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("values", "metadata")
    @classmethod
    def profile_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        for key in value:
            _reject_domain_text(str(key))
        return value

    @field_validator("feature_flags")
    @classmethod
    def feature_flags_must_be_safe(cls, value: dict[str, bool]) -> dict[str, bool]:
        for key in value:
            _validate_feature_key(key)
        return value

    @model_validator(mode="after")
    def unsafe_defaults_must_stay_disabled(self) -> ConfigProfile:
        _reject_unsafe_enabled(self.values)
        _reject_unsafe_enabled(self.feature_flags)
        return self


class ConfigProfileCreateRequest(BaseModel):
    """Request to create a safe runtime config profile."""

    model_config = ConfigDict(extra="forbid")

    config_profile_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    profile_type: ConfigProfileType = "custom"
    owner_scope: list[str] = Field(min_length=1)
    values: dict[str, Any] = Field(default_factory=dict)
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    activate: bool = True


class FeatureFlagOverride(BaseModel):
    """One local feature flag override."""

    model_config = ConfigDict(extra="forbid")

    feature_override_id: str = Field(min_length=1)
    feature_key: str = Field(min_length=1)
    enabled: bool
    source: FeatureOverrideSource
    status: FeatureOverrideStatus
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("feature_key")
    @classmethod
    def feature_key_must_be_safe(cls, value: str) -> str:
        _validate_feature_key(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class FeatureFlagOverrideRequest(BaseModel):
    """Request to create a feature flag override."""

    model_config = ConfigDict(extra="forbid")

    feature_override_id: str | None = None
    feature_key: str = Field(min_length=1)
    enabled: bool
    source: FeatureOverrideSource = "runtime"
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class ConfigSnapshot(BaseModel):
    """Redacted runtime configuration snapshot."""

    model_config = ConfigDict(extra="forbid")

    config_snapshot_id: str = Field(min_length=1)
    snapshot_type: ConfigSnapshotType
    status: ConfigSnapshotStatus
    owner_scope: list[str] = Field(min_length=1)
    settings: dict[str, Any]
    feature_flags: dict[str, bool]
    adapter_status: dict[str, Any]
    config_hash: str = Field(min_length=1)
    drift_from_snapshot_id: str | None = None
    drift: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("settings")
    @classmethod
    def snapshot_settings_must_be_redacted(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unredacted_secret_like_values(value)
        return value

    @field_validator("metadata")
    @classmethod
    def snapshot_metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ConfigSnapshotRequest(BaseModel):
    """Request to capture a redacted runtime config snapshot."""

    model_config = ConfigDict(extra="forbid")

    config_snapshot_id: str | None = None
    snapshot_type: ConfigSnapshotType = "manual"
    owner_scope: list[str] = Field(min_length=1)
    compare_to_snapshot_id: str | None = None
    include_adapter_status: bool = True
    include_feature_flags: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class ConfigValidationCheck(BaseModel):
    """One runtime configuration validation check."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    status: ConfigValidationStatus
    severity: ConfigValidationSeverity
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class ConfigValidationRun(BaseModel):
    """Completed runtime configuration validation run."""

    model_config = ConfigDict(extra="forbid")

    config_validation_id: str = Field(min_length=1)
    trace_id: str | None = None
    profile_id: str | None = None
    snapshot_id: str | None = None
    status: ConfigRunStatus
    checks: list[ConfigValidationCheck]
    failures: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    report: dict[str, Any]
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ConfigValidationRequest(BaseModel):
    """Request to validate runtime configuration posture."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str | None = None
    snapshot_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    include_security_checks: bool = True
    include_autonomy_checks: bool = True
    include_adapter_checks: bool = True
    include_feature_checks: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class ConfigChangeRecord(BaseModel):
    """Audit record for safe runtime config metadata changes."""

    model_config = ConfigDict(extra="forbid")

    config_change_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    target_type: ConfigChangeTargetType
    target_id: str = Field(min_length=1)
    change_type: ConfigChangeType
    before: dict[str, Any]
    after: dict[str, Any]
    reason: str = Field(min_length=1)
    policy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("before", "after")
    @classmethod
    def change_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class RuntimeConfigStatus(BaseModel):
    """Runtime config status summary."""

    model_config = ConfigDict(extra="forbid")

    active_profile: ConfigProfile | None
    feature_overrides: list[FeatureFlagOverride]
    effective_feature_flags: dict[str, bool]
    safe_defaults_ok: bool
    validation_status: ConfigRunStatus
    latest_snapshot_id: str | None
    generated_at: datetime


class StatusUpdateRequest(BaseModel):
    """Simple status-change request."""

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class SnapshotCompareRequest(BaseModel):
    """Request to compare two config snapshots."""

    snapshot_id_a: str = Field(min_length=1)
    snapshot_id_b: str = Field(min_length=1)


def _validate_config_key(value: str, field_name: str) -> None:
    if not _CONFIG_KEY_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be dotted lowercase or uppercase env-style text")
    _reject_domain_text(value)


def _validate_feature_key(value: str) -> None:
    if not _FEATURE_KEY_RE.fullmatch(value):
        raise ValueError("feature_key must be dotted lowercase text")
    _reject_domain_text(value)


def _reject_domain_text(value: str) -> None:
    lowered = value.lower().replace("-", "_")
    if any(term in lowered for term in _BANNED_KEY_TERMS):
        raise ValueError("runtime config keys must remain generic and Brain-level")


def _reject_unsafe_enabled(values: dict[str, Any]) -> None:
    for key, value in values.items():
        lowered = str(key).lower()
        enabled = value is True or value == "true"
        if enabled and any(term in lowered for term in _UNSAFE_TRUE_KEYS):
            raise ValueError("runtime config profile must not enable unsafe defaults")


def _reject_unredacted_secret_like_values(value: dict[str, Any]) -> None:
    for key, item in value.items():
        lowered = str(key).lower()
        secret_like = any(
            part in lowered
            for part in (
                "api_key",
                "apikey",
                "authorization",
                "bearer",
                "client_secret",
                "credential",
                "password",
                "private_key",
                "secret",
                "token",
            )
        ) or (lowered.endswith("_url") and "database" in lowered)
        if secret_like and item != {"redacted": True}:
            raise ValueError("secret-like settings must be redacted")
        if isinstance(item, dict) and not secret_like:
            _reject_unredacted_secret_like_values(item)
        elif isinstance(item, list):
            for element in item:
                if isinstance(element, dict):
                    _reject_unredacted_secret_like_values(element)
