"""Connector policy action catalog and dry-run contracts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ConnectorPolicyRiskLevel = Literal["low", "medium", "high", "critical"]
ConnectorPolicyDecision = Literal["allow_read", "allow_dry_run", "deny"]
ConnectorPolicyTraceabilityStatus = Literal["ready", "blocked", "preview"]

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
    "activation_allowed",
    "allowed_in_runtime",
    "connector_policy_activation_enabled",
    "connector_policy_credentials_enabled",
    "connector_policy_external_calls_enabled",
    "connector_policy_runtime_allow_enabled",
    "connector_policy_tokens_enabled",
    "credential_access_allowed",
    "external_call_allowed",
    "requires_connector_runtime",
    "requires_credentials",
    "requires_external_call",
    "requires_production_auth",
    "runtime_allowed",
    "token_access_allowed",
}


class ConnectorPolicyAction(BaseModel):
    """One connector policy action catalog row."""

    model_config = ConfigDict(extra="forbid")

    action_key: str
    title: str
    description: str
    category: str
    risk_level: ConnectorPolicyRiskLevel
    allowed_in_dry_run: bool
    allowed_in_runtime: bool
    requires_operator_review: bool
    requires_production_auth: bool
    requires_connector_runtime: bool
    requires_credentials: bool
    requires_external_call: bool
    requires_audit: bool
    requires_provenance: bool
    blockers: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("action_key")
    @classmethod
    def action_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "action_key")

    @field_validator("title", "description", "category")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value.strip()

    @field_validator("blockers")
    @classmethod
    def blockers_must_be_safe(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        for item in cleaned:
            _reject_unsafe_text(item)
        return cleaned

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @model_validator(mode="after")
    def action_must_not_enable_runtime(self) -> ConnectorPolicyAction:
        if self.allowed_in_runtime:
            raise ValueError("allowed_in_runtime must be false")
        if self.requires_connector_runtime:
            raise ValueError("requires_connector_runtime must be false")
        if self.requires_credentials:
            raise ValueError("requires_credentials must be false")
        if self.requires_external_call:
            raise ValueError("requires_external_call must be false")
        return self


class ConnectorAuthorizationMatrixEntry(BaseModel):
    """Role-aware connector policy authorization row."""

    model_config = ConfigDict(extra="forbid")

    role: str
    action_key: str
    decision: ConnectorPolicyDecision
    reason: str
    dry_run_allowed: bool
    runtime_allowed: bool
    external_call_allowed: bool
    credential_access_allowed: bool
    token_access_allowed: bool
    activation_allowed: bool
    review_required: bool
    audit_required: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("action_key")
    @classmethod
    def action_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "action_key")

    @field_validator("role", "reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @model_validator(mode="after")
    def matrix_must_not_grant_runtime(self) -> ConnectorAuthorizationMatrixEntry:
        if self.runtime_allowed:
            raise ValueError("runtime_allowed must be false")
        if self.external_call_allowed:
            raise ValueError("external_call_allowed must be false")
        if self.credential_access_allowed:
            raise ValueError("credential_access_allowed must be false")
        if self.token_access_allowed:
            raise ValueError("token_access_allowed must be false")
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false")
        return self


class ConnectorPolicyDryRunRequest(BaseModel):
    """Request a connector policy dry-run decision without action execution."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    connector_key: str
    role: str
    requested_action_key: str
    owner_scope: list[str] = Field(min_length=1)
    declared_scopes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("connector_key", "requested_action_key")
    @classmethod
    def dotted_fields_must_be_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "connector_key or requested_action_key")

    @field_validator("role")
    @classmethod
    def role_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value.strip()

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "owner_scope")

    @field_validator("declared_scopes", "evidence_refs")
    @classmethod
    def lists_must_be_safe(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "list")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ConnectorPolicyDryRunResult(BaseModel):
    """Dry-run result proving connector policy does not enable runtime paths."""

    model_config = ConfigDict(extra="forbid")

    connector_policy_dry_run_id: str
    trace_id: str | None = None
    connector_key: str
    requested_action_key: str
    role: str
    decision: ConnectorPolicyDecision
    dry_run_allowed: bool
    runtime_allowed: bool
    external_call_allowed: bool
    credential_access_allowed: bool
    token_access_allowed: bool
    activation_allowed: bool
    review_required: bool
    audit_required: bool
    provenance_required: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("connector_key", "requested_action_key")
    @classmethod
    def dotted_fields_must_be_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "connector_key or requested_action_key")

    @field_validator("blockers", "warnings", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: Any) -> Any:
        _reject_result_payload(value)
        return value

    @field_validator("recommendations")
    @classmethod
    def recommendations_must_be_safe(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "recommendations")

    @model_validator(mode="after")
    def dry_run_result_must_not_grant_runtime(self) -> ConnectorPolicyDryRunResult:
        if self.runtime_allowed:
            raise ValueError("runtime_allowed must be false")
        if self.external_call_allowed:
            raise ValueError("external_call_allowed must be false")
        if self.credential_access_allowed:
            raise ValueError("credential_access_allowed must be false")
        if self.token_access_allowed:
            raise ValueError("token_access_allowed must be false")
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false")
        return self


class ConnectorPolicyTraceabilityRecord(BaseModel):
    """Traceability row from connector policy action to evidence artifacts."""

    model_config = ConfigDict(extra="forbid")

    traceability_id: str
    connector_key: str
    action_key: str
    policy_refs: list[str] = Field(default_factory=list)
    matrix_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    dry_run_refs: list[str] = Field(default_factory=list)
    denial_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    status: ConnectorPolicyTraceabilityStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("connector_key", "action_key")
    @classmethod
    def dotted_fields_must_be_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "connector_key or action_key")

    @field_validator(
        "policy_refs",
        "matrix_refs",
        "evidence_refs",
        "dry_run_refs",
        "denial_refs",
        "audit_refs",
    )
    @classmethod
    def refs_must_be_safe(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "refs")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_result_payload(value)
        return value


def utc_now() -> datetime:
    """Return timezone-aware UTC now."""

    return datetime.now(UTC)


def _dotted_lowercase(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not _DOTTED_LOWERCASE_RE.match(cleaned):
        raise ValueError(f"{field_name} must be dotted lowercase text")
    return cleaned


def _safe_string_list(value: list[str], field_name: str) -> list[str]:
    cleaned = [item.strip() for item in value if item.strip()]
    if field_name == "owner_scope" and not cleaned:
        raise ValueError("owner_scope cannot be empty")
    for item in cleaned:
        _reject_unsafe_text(item)
    return cleaned


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized not in _SAFE_FALSE_KEYS:
                if any(part in normalized for part in _URL_KEY_PARTS):
                    raise ValueError("URL endpoint fields are not allowed")
                if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                    raise ValueError("credential fields are not allowed")
                if any(part in normalized for part in _TOKEN_KEY_PARTS):
                    raise ValueError("token fields are not allowed")
                if any(part in normalized for part in _RAW_PROMPT_KEY_PARTS):
                    raise ValueError("raw prompts are not allowed")
                if any(part in normalized for part in _HIDDEN_REASONING_KEY_PARTS):
                    raise ValueError("hidden reasoning is not allowed")
            _reject_unsafe_payload(nested)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_text(value)


def _reject_result_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _SAFE_FALSE_KEYS:
                _reject_result_payload(nested)
                continue
            _reject_unsafe_payload({key: nested})
        return
    if isinstance(value, list):
        for item in value:
            _reject_result_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_text(value)


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if _URL_RE.search(value):
        raise ValueError("external URLs are not allowed")
    if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
        raise ValueError("secret-like values are not allowed")
    if any(marker in lowered for marker in _RAW_PROMPT_VALUE_MARKERS):
        raise ValueError("raw prompts are not allowed")
    if any(marker in lowered for marker in _HIDDEN_REASONING_VALUE_MARKERS):
        raise ValueError("hidden reasoning is not allowed")


__all__ = [
    "ConnectorAuthorizationMatrixEntry",
    "ConnectorPolicyAction",
    "ConnectorPolicyDecision",
    "ConnectorPolicyDryRunRequest",
    "ConnectorPolicyDryRunResult",
    "ConnectorPolicyTraceabilityRecord",
    "utc_now",
]
