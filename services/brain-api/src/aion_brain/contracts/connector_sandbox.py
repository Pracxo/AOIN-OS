"""Connector sandbox boundary and readiness contracts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ConnectorSandboxReadinessStatus = Literal["preview", "ready", "blocked"]

_DOTTED_LOWERCASE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$")
_URL_RE = re.compile(r"\bhttps?://", re.IGNORECASE)
_SENSITIVE_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "secret",
}
_TOKEN_KEY_PARTS = {"access_token", "refresh_token", "id_token", "token"}
_URL_KEY_PARTS = {"endpoint", "url", "uri", "host", "dns"}
_RAW_PROMPT_KEY_PARTS = {"raw_prompt", "prompt_text", "system_prompt", "developer_prompt"}
_HIDDEN_REASONING_KEY_PARTS = {
    "chain_of_thought",
    "hidden_reasoning",
    "private_reasoning",
}
_SECRET_VALUE_MARKERS = (
    "sk-",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
    "bearer ",
    "basic ",
)
_RAW_PROMPT_VALUE_MARKERS = (
    "raw prompt",
    "raw_prompt",
    "system prompt:",
    "developer prompt:",
)
_HIDDEN_REASONING_VALUE_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
)
_SAFE_FALSE_KEYS = {
    "connector_activation_allowed",
    "connector_sandbox_activation_enabled",
    "connector_sandbox_credentials_enabled",
    "connector_sandbox_dynamic_import_enabled",
    "connector_sandbox_filesystem_enabled",
    "connector_sandbox_network_enabled",
    "connector_sandbox_package_install_enabled",
    "connector_sandbox_process_spawn_enabled",
    "connector_sandbox_runtime_execution_enabled",
    "connector_sandbox_tokens_enabled",
    "credential_access_allowed",
    "dynamic_import_allowed",
    "filesystem_access_allowed",
    "network_access_allowed",
    "package_install_allowed",
    "process_spawn_allowed",
    "runtime_allowed",
    "runtime_execution_allowed",
    "token_access_allowed",
}
_RESTRICTED_CAPABILITY_PARTS = {
    "activate",
    "credentials",
    "dynamic_import",
    "filesystem",
    "network",
    "package_install",
    "process",
    "runtime",
    "tokens",
}


class ConnectorSandboxBoundary(BaseModel):
    """Read-only connector sandbox isolation boundary."""

    model_config = ConfigDict(extra="forbid")

    sandbox_boundary_id: str
    name: str
    description: str
    filesystem_access_allowed: bool
    network_access_allowed: bool
    credential_access_allowed: bool
    token_access_allowed: bool
    process_spawn_allowed: bool
    dynamic_import_allowed: bool
    package_install_allowed: bool
    runtime_execution_allowed: bool
    connector_activation_allowed: bool
    audit_required: bool
    provenance_required: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("sandbox_boundary_id", "name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value.strip()

    @field_validator("blockers", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: Any) -> Any:
        _reject_unsafe_payload(value)
        return value

    @model_validator(mode="after")
    def boundary_must_not_enable_sandbox_runtime(self) -> ConnectorSandboxBoundary:
        _assert_false(self.filesystem_access_allowed, "filesystem_access_allowed")
        _assert_false(self.network_access_allowed, "network_access_allowed")
        _assert_false(self.credential_access_allowed, "credential_access_allowed")
        _assert_false(self.token_access_allowed, "token_access_allowed")
        _assert_false(self.process_spawn_allowed, "process_spawn_allowed")
        _assert_false(self.dynamic_import_allowed, "dynamic_import_allowed")
        _assert_false(self.package_install_allowed, "package_install_allowed")
        _assert_false(self.runtime_execution_allowed, "runtime_execution_allowed")
        _assert_false(self.connector_activation_allowed, "connector_activation_allowed")
        if not self.audit_required:
            raise ValueError("audit_required must be true")
        if not self.provenance_required:
            raise ValueError("provenance_required must be true")
        return self


class ConnectorSandboxCapabilityRule(BaseModel):
    """One connector sandbox capability rule."""

    model_config = ConfigDict(extra="forbid")

    rule_key: str
    title: str
    description: str
    category: str
    allowed: bool
    dry_run_allowed: bool
    runtime_allowed: bool
    requires_review: bool
    requires_policy: bool
    requires_audit: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("rule_key")
    @classmethod
    def rule_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "rule_key")

    @field_validator("title", "description", "category")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value.strip()

    @field_validator("blockers", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: Any) -> Any:
        _reject_unsafe_payload(value)
        return value

    @model_validator(mode="after")
    def capability_rule_must_not_enable_runtime(self) -> ConnectorSandboxCapabilityRule:
        if self.runtime_allowed:
            raise ValueError("runtime_allowed must be false")
        if self.allowed and (
            any(part in self.rule_key for part in _RESTRICTED_CAPABILITY_PARTS)
            or self.category in _RESTRICTED_CAPABILITY_PARTS
        ):
            raise ValueError("restricted sandbox capability rules must not be allowed")
        return self


class ConnectorSandboxReadinessRequest(BaseModel):
    """Request connector sandbox readiness without executing sandbox code."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    connector_key: str
    owner_scope: list[str] = Field(min_length=1)
    requested_capabilities: list[str] = Field(default_factory=list)
    declared_policy_actions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "connector_key")

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "owner_scope")

    @field_validator("requested_capabilities", "declared_policy_actions", "evidence_refs")
    @classmethod
    def lists_must_be_safe(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "list")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ConnectorSandboxReadinessResult(BaseModel):
    """Readiness result proving sandbox execution remains unavailable."""

    model_config = ConfigDict(extra="forbid")

    connector_sandbox_readiness_id: str
    trace_id: str | None = None
    connector_key: str
    status: ConnectorSandboxReadinessStatus
    sandbox_ready: bool
    runtime_execution_allowed: bool
    filesystem_access_allowed: bool
    network_access_allowed: bool
    credential_access_allowed: bool
    token_access_allowed: bool
    process_spawn_allowed: bool
    dynamic_import_allowed: bool
    package_install_allowed: bool
    connector_activation_allowed: bool
    audit_required: bool
    provenance_required: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "connector_key")

    @field_validator("blockers", "warnings", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: Any) -> Any:
        _reject_unsafe_payload(value)
        return value

    @field_validator("recommendations")
    @classmethod
    def recommendations_must_be_safe(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "recommendations")

    @model_validator(mode="after")
    def readiness_result_must_not_enable_sandbox_runtime(
        self,
    ) -> ConnectorSandboxReadinessResult:
        _assert_false(self.runtime_execution_allowed, "runtime_execution_allowed")
        _assert_false(self.filesystem_access_allowed, "filesystem_access_allowed")
        _assert_false(self.network_access_allowed, "network_access_allowed")
        _assert_false(self.credential_access_allowed, "credential_access_allowed")
        _assert_false(self.token_access_allowed, "token_access_allowed")
        _assert_false(self.process_spawn_allowed, "process_spawn_allowed")
        _assert_false(self.dynamic_import_allowed, "dynamic_import_allowed")
        _assert_false(self.package_install_allowed, "package_install_allowed")
        _assert_false(self.connector_activation_allowed, "connector_activation_allowed")
        if not self.audit_required:
            raise ValueError("audit_required must be true")
        if not self.provenance_required:
            raise ValueError("provenance_required must be true")
        return self


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def _assert_false(value: bool, field_name: str) -> None:
    if value:
        raise ValueError(f"{field_name} must be false")


def _dotted_lowercase(value: str, field_name: str) -> str:
    stripped = value.strip()
    if not _DOTTED_LOWERCASE_RE.fullmatch(stripped):
        raise ValueError(f"{field_name} must be dotted lowercase text")
    _reject_unsafe_text(stripped)
    return stripped


def _safe_string_list(value: list[str], field_name: str) -> list[str]:
    cleaned = [item.strip() for item in value if item.strip()]
    if field_name == "owner_scope" and not cleaned:
        raise ValueError("owner_scope must not be empty")
    for item in cleaned:
        _reject_unsafe_text(item)
    return cleaned


def _reject_unsafe_payload(value: Any, *, key_path: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key).strip()
            key_lower = key_text.lower()
            _reject_unsafe_key_value(key_lower, nested, key_path)
            _reject_unsafe_payload(nested, key_path=(*key_path, key_lower))
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item, key_path=key_path)
    elif isinstance(value, str):
        _reject_unsafe_text(value, key_path=key_path)


def _reject_unsafe_key_value(key_lower: str, value: Any, key_path: tuple[str, ...]) -> None:
    if key_lower in _SAFE_FALSE_KEYS and value is False:
        return
    if any(part in key_lower for part in _SENSITIVE_KEY_PARTS):
        raise ValueError("sandbox metadata must not contain secrets or credentials")
    if any(part in key_lower for part in _TOKEN_KEY_PARTS):
        raise ValueError("sandbox metadata must not contain tokens")
    if any(part in key_lower for part in _URL_KEY_PARTS):
        raise ValueError("sandbox metadata must not contain external locations")
    if any(part in key_lower for part in _RAW_PROMPT_KEY_PARTS):
        raise ValueError("sandbox metadata must not contain raw prompts")
    if any(part in key_lower for part in _HIDDEN_REASONING_KEY_PARTS):
        raise ValueError("sandbox metadata must not contain hidden reasoning")
    if key_path and key_path[-1] in _SAFE_FALSE_KEYS and value is False:
        return


def _reject_unsafe_text(value: str, *, key_path: tuple[str, ...] = ()) -> None:
    lower = value.lower()
    if _URL_RE.search(value):
        raise ValueError("sandbox metadata must not contain external URLs")
    if any(marker in lower for marker in _SECRET_VALUE_MARKERS):
        raise ValueError("sandbox metadata must not contain secret markers")
    if any(marker in lower for marker in _RAW_PROMPT_VALUE_MARKERS):
        raise ValueError("sandbox metadata must not contain raw prompts")
    if any(marker in lower for marker in _HIDDEN_REASONING_VALUE_MARKERS):
        raise ValueError("sandbox metadata must not contain hidden reasoning")
    if key_path and key_path[-1] in _SAFE_FALSE_KEYS:
        return


__all__ = [
    "ConnectorSandboxBoundary",
    "ConnectorSandboxCapabilityRule",
    "ConnectorSandboxReadinessRequest",
    "ConnectorSandboxReadinessResult",
    "ConnectorSandboxReadinessStatus",
    "utc_now",
]
