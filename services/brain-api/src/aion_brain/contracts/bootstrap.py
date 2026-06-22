"""First-run bootstrap contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.setup_doctor import SetupFinding

BootstrapProfileStatus = Literal["active", "disabled"]
BootstrapProfileType = Literal[
    "local_dev",
    "docker_local",
    "test",
    "golden_path",
    "release_candidate",
    "generic",
]
SeedBundleStatus = Literal["active", "disabled"]
SeedBundleType = Literal[
    "core_defaults",
    "operator_defaults",
    "policy_defaults",
    "notification_defaults",
    "registry_defaults",
    "contract_defaults",
    "lifecycle_defaults",
    "extension_defaults",
    "conformance_defaults",
    "golden_path_defaults",
    "local_dev",
    "generic",
]
BootstrapRunMode = Literal["dry_run", "controlled"]
SeedExecutionStatus = Literal[
    "completed",
    "dry_run",
    "warning",
    "failed",
    "blocked_by_policy",
]
BootstrapRunStatus = Literal[
    "completed",
    "warning",
    "failed",
    "blocked_by_policy",
    "dry_run",
]

_DOTTED_LOWERCASE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$")
_EXTERNAL_SERVICE_TERMS = {
    "openai",
    "anthropic",
    "gemini",
    "brave",
    "alpha_vantage",
    "stripe",
    "github",
    "slack",
    "aws",
    "gcp",
    "azure",
    "external_service",
    "http://",
    "https://",
}
_BANNED_PROFILE_TEXT = {"production", "prod"}
_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "payment",
    "procurement",
    "human_resources",
}


class BootstrapProfile(BaseModel):
    """Local first-run bootstrap profile."""

    model_config = ConfigDict(extra="forbid")

    bootstrap_profile_id: str = Field(min_length=1)
    profile_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: BootstrapProfileStatus
    profile_type: BootstrapProfileType
    owner_scope: list[str] = Field(min_length=1)
    required_services: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    seed_bundle_keys: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("profile_key")
    @classmethod
    def profile_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _safe_key(value, "profile_key")

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _safe_text(value, "bootstrap profile text")
        return value.strip()

    @field_validator("required_services", "required_settings", "seed_bundle_keys", "checks")
    @classmethod
    def keys_must_be_local(cls, value: list[str]) -> list[str]:
        for item in value:
            _safe_reference(item)
            _reject_external(item)
        return value

    @field_validator("constraints")
    @classmethod
    def constraints_must_be_safe(cls, value: list[str]) -> list[str]:
        reject_secret_like_payload(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value

    @model_validator(mode="after")
    def production_profiles_are_blocked(self) -> BootstrapProfile:
        combined = f"{self.profile_key} {self.name} {self.description} {self.profile_type}".lower()
        if any(term in combined for term in _BANNED_PROFILE_TEXT):
            raise ValueError("production bootstrap profiles are not supported in v0.1")
        return self


class SeedBundle(BaseModel):
    """Idempotent local seed bundle metadata."""

    model_config = ConfigDict(extra="forbid")

    seed_bundle_id: str = Field(min_length=1)
    seed_bundle_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: SeedBundleStatus
    bundle_type: SeedBundleType
    owner_scope: list[str] = Field(min_length=1)
    seed_steps: list[dict[str, Any]] = Field(default_factory=list)
    idempotency_keys: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("seed_bundle_key")
    @classmethod
    def seed_bundle_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _safe_key(value, "seed_bundle_key")

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _safe_text(value, "seed bundle text")
        return value.strip()

    @field_validator("seed_steps")
    @classmethod
    def steps_must_be_safe_and_idempotent(
        cls,
        value: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        _reject_payload(value)
        safe: list[dict[str, Any]] = []
        for step in value:
            if step.get("external_calls") is True or step.get("external_call") is True:
                raise ValueError("seed steps must not call external services")
            if "idempotency_key" not in step:
                raise ValueError("seed steps must include idempotency_key")
            safe.append(step)
        return safe

    @field_validator("idempotency_keys", "dependencies")
    @classmethod
    def seed_keys_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            _safe_reference(item)
            _reject_external(item)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


class SeedExecutionRequest(BaseModel):
    """Request to execute one local seed bundle."""

    model_config = ConfigDict(extra="forbid")

    seed_execution_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    seed_bundle_key: str
    mode: BootstrapRunMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    force: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("seed_bundle_key")
    @classmethod
    def seed_bundle_key_must_be_safe(cls, value: str) -> str:
        return _safe_key(value, "seed_bundle_key")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


class SeedExecutionRecord(BaseModel):
    """Persisted result of one seed execution."""

    model_config = ConfigDict(extra="forbid")

    seed_execution_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    seed_bundle_id: str
    seed_bundle_key: str
    status: SeedExecutionStatus
    mode: BootstrapRunMode
    owner_scope: list[str] = Field(min_length=1)
    steps_attempted: int = Field(ge=0)
    steps_completed: int = Field(ge=0)
    steps_skipped: int = Field(ge=0)
    steps_failed: int = Field(ge=0)
    created_resource_refs: list[str] = Field(default_factory=list)
    skipped_resource_refs: list[str] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("failures", "warnings")
    @classmethod
    def list_payload_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        _reject_payload(value)
        return value

    @field_validator("result", "metadata")
    @classmethod
    def dict_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


class BootstrapRunRequest(BaseModel):
    """Request to run local first-run bootstrap."""

    model_config = ConfigDict(extra="forbid")

    bootstrap_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    profile_key: str = "local.dev"
    mode: BootstrapRunMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    seed_defaults: bool = True
    run_setup_doctor: bool = True
    run_golden_path: bool = True
    run_release_smoke: bool = True
    create_notifications: bool = False
    create_operator_items: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("profile_key")
    @classmethod
    def profile_key_must_be_safe(cls, value: str) -> str:
        return _safe_key(value, "profile_key")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        if value.get("enable_external_providers") is True:
            raise ValueError("bootstrap must not enable external providers")
        if value.get("enable_full_autonomy") is True:
            raise ValueError("bootstrap must not enable full autonomy")
        return value


class BootstrapRun(BaseModel):
    """Persisted local first-run bootstrap run."""

    model_config = ConfigDict(extra="forbid")

    bootstrap_run_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    bootstrap_profile: BootstrapProfile | None = None
    status: BootstrapRunStatus
    mode: BootstrapRunMode
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    seed_executions: list[SeedExecutionRecord] = Field(default_factory=list)
    setup_findings: list[SetupFinding] = Field(default_factory=list)
    golden_path_run_id: str | None = None
    release_smoke_ref: str | None = None
    readiness_score: float = Field(ge=0.0, le=1.0)
    local_ready: bool
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("warnings", "failures")
    @classmethod
    def list_payload_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        _reject_payload(value)
        return value

    @field_validator("result", "metadata")
    @classmethod
    def dict_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


def _safe_key(value: str, field_name: str) -> str:
    value = value.strip()
    reject_hidden_or_secret_text(value, field_name)
    if not _DOTTED_LOWERCASE.match(value):
        raise ValueError(f"{field_name} must be dotted lowercase text")
    _reject_external(value)
    _reject_domain(value)
    return value


def _safe_reference(value: str) -> str:
    value = value.strip()
    reject_hidden_or_secret_text(value, "bootstrap reference")
    _reject_domain(value)
    return value


def _safe_text(value: str, field_name: str) -> None:
    reject_hidden_or_secret_text(value, field_name)
    _reject_domain(value)
    _reject_external(value)


def _reject_payload(value: object) -> None:
    reject_secret_like_payload(value)
    _reject_external_payload(value)
    _reject_domain(value)


def _reject_external_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered_key = str(key).lower().replace("-", "_")
            if lowered_key in {"external_call", "external_calls"} and nested is True:
                raise ValueError("bootstrap payload must not request external calls")
            if (
                lowered_key in {"package_install", "package_installation", "install_packages"}
                and nested is True
            ):
                raise ValueError("bootstrap data must not install packages")
            if lowered_key in {
                "external_call",
                "external_calls",
                "package_install",
                "package_installation",
                "install_packages",
                "source_mutation",
                "source_code_mutation",
            }:
                _reject_external_payload(nested)
                continue
            _reject_external(lowered_key)
            _reject_external_payload(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_external_payload(item)
    elif isinstance(value, str):
        _reject_external(value)


def _reject_external(value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _EXTERNAL_SERVICE_TERMS):
        raise ValueError("bootstrap data must not reference external services")
    if "install" in lowered and "package" in lowered:
        raise ValueError("bootstrap data must not install packages")


def _reject_domain(value: object) -> None:
    text = str(value).lower()
    if any(term in text for term in _DOMAIN_TERMS):
        raise ValueError("bootstrap data must not contain domain-specific setup logic")


__all__ = [
    "BootstrapProfile",
    "BootstrapProfileStatus",
    "BootstrapProfileType",
    "BootstrapRun",
    "BootstrapRunMode",
    "BootstrapRunRequest",
    "BootstrapRunStatus",
    "SeedBundle",
    "SeedBundleStatus",
    "SeedBundleType",
    "SeedExecutionRecord",
    "SeedExecutionRequest",
    "SeedExecutionStatus",
]
