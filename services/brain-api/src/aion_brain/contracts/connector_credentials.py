"""Connector credential boundary, lifecycle, and readiness contracts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ConnectorCredentialReadinessStatus = Literal["preview", "blocked"]

_DOTTED_LOWERCASE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*$")
_URL_RE = re.compile(r"\bhttps?://", re.IGNORECASE)
_SENSITIVE_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "oauth_code",
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
    "oauth code",
)
_SAFE_FALSE_KEYS = {
    "browser_secret_storage_allowed",
    "connector_runtime_credential_access_enabled",
    "credential_access_allowed",
    "credential_material_present",
    "credential_ready",
    "credential_storage_allowed",
    "credential_storage_enabled",
    "external_identity_runtime_allowed",
    "external_identity_runtime_enabled",
    "log_secret_allowed",
    "plaintext_secret_allowed",
    "secret_detected",
    "secret_material_allowed",
    "secret_material_present",
    "storage_allowed",
    "token_access_allowed",
    "token_detected",
    "token_storage_allowed",
    "token_storage_enabled",
}


class ConnectorCredentialBoundary(BaseModel):
    """Read-only future connector credential store architecture boundary."""

    model_config = ConfigDict(extra="forbid")

    credential_boundary_id: str
    name: str
    description: str
    credential_storage_enabled: bool
    token_storage_enabled: bool
    secret_material_present: bool
    plaintext_secret_allowed: bool
    browser_secret_storage_allowed: bool
    log_secret_allowed: bool
    external_identity_runtime_enabled: bool
    connector_runtime_credential_access_enabled: bool
    rotation_required: bool
    revocation_required: bool
    audit_required: bool
    provenance_required: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("credential_boundary_id", "name", "description")
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
    def boundary_must_keep_storage_disabled(self) -> ConnectorCredentialBoundary:
        _assert_false(self.credential_storage_enabled, "credential_storage_enabled")
        _assert_false(self.token_storage_enabled, "token_storage_enabled")
        _assert_false(self.secret_material_present, "secret_material_present")
        _assert_false(self.plaintext_secret_allowed, "plaintext_secret_allowed")
        _assert_false(self.browser_secret_storage_allowed, "browser_secret_storage_allowed")
        _assert_false(self.log_secret_allowed, "log_secret_allowed")
        _assert_false(self.external_identity_runtime_enabled, "external_identity_runtime_enabled")
        _assert_false(
            self.connector_runtime_credential_access_enabled,
            "connector_runtime_credential_access_enabled",
        )
        _assert_true(self.rotation_required, "rotation_required")
        _assert_true(self.revocation_required, "revocation_required")
        _assert_true(self.audit_required, "audit_required")
        _assert_true(self.provenance_required, "provenance_required")
        return self


class ConnectorCredentialLifecycleState(BaseModel):
    """One future credential lifecycle state."""

    model_config = ConfigDict(extra="forbid")

    state_key: str
    title: str
    description: str
    allowed_today: bool
    future_only: bool
    requires_production_auth: bool
    requires_secret_store: bool
    requires_rotation_plan: bool
    requires_revocation_plan: bool
    requires_audit: bool
    requires_provenance: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("state_key")
    @classmethod
    def state_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "state_key")

    @field_validator("title", "description")
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
    def storage_states_must_be_future_only(self) -> ConnectorCredentialLifecycleState:
        if self.requires_secret_store:
            _assert_false(self.allowed_today, "allowed_today")
            _assert_true(self.future_only, "future_only")
        _assert_true(self.requires_audit, "requires_audit")
        _assert_true(self.requires_provenance, "requires_provenance")
        return self


class ConnectorCredentialAuthorizationEntry(BaseModel):
    """Role/action authorization entry for connector credential surfaces."""

    model_config = ConfigDict(extra="forbid")

    role: str
    action_key: str
    decision: str
    credential_access_allowed: bool
    token_access_allowed: bool
    secret_material_allowed: bool
    storage_allowed: bool
    rotation_allowed: bool
    revocation_allowed: bool
    audit_required: bool
    review_required: bool
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("role", "decision", "reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value.strip().lower() if value == value.lower() else value.strip()

    @field_validator("action_key")
    @classmethod
    def action_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _dotted_lowercase(value, "action_key")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @model_validator(mode="after")
    def authorization_must_not_allow_material_access(
        self,
    ) -> ConnectorCredentialAuthorizationEntry:
        _assert_false(self.credential_access_allowed, "credential_access_allowed")
        _assert_false(self.token_access_allowed, "token_access_allowed")
        _assert_false(self.secret_material_allowed, "secret_material_allowed")
        _assert_false(self.storage_allowed, "storage_allowed")
        _assert_false(self.rotation_allowed, "rotation_allowed")
        _assert_false(self.revocation_allowed, "revocation_allowed")
        _assert_true(self.audit_required, "audit_required")
        return self


class ConnectorCredentialReadinessRequest(BaseModel):
    """Request connector credential readiness without storing material."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    connector_key: str
    owner_scope: list[str] = Field(min_length=1)
    requested_credential_type: str | None = None
    requested_scopes: list[str] = Field(default_factory=list)
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

    @field_validator("requested_credential_type")
    @classmethod
    def requested_type_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        _reject_unsafe_text(value)
        return value.strip()

    @field_validator("requested_scopes", "evidence_refs")
    @classmethod
    def lists_must_be_safe(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "list")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ConnectorCredentialReadinessResult(BaseModel):
    """Readiness result proving credential storage remains unavailable."""

    model_config = ConfigDict(extra="forbid")

    connector_credential_readiness_id: str
    trace_id: str | None = None
    connector_key: str
    status: ConnectorCredentialReadinessStatus
    credential_ready: bool
    credential_storage_allowed: bool
    token_storage_allowed: bool
    credential_access_allowed: bool
    token_access_allowed: bool
    secret_material_present: bool
    external_identity_runtime_allowed: bool
    rotation_required: bool
    revocation_required: bool
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
    def readiness_result_must_keep_storage_disabled(
        self,
    ) -> ConnectorCredentialReadinessResult:
        _assert_false(self.credential_storage_allowed, "credential_storage_allowed")
        _assert_false(self.token_storage_allowed, "token_storage_allowed")
        _assert_false(self.credential_access_allowed, "credential_access_allowed")
        _assert_false(self.token_access_allowed, "token_access_allowed")
        _assert_false(self.secret_material_present, "secret_material_present")
        _assert_false(
            self.external_identity_runtime_allowed,
            "external_identity_runtime_allowed",
        )
        _assert_true(self.rotation_required, "rotation_required")
        _assert_true(self.revocation_required, "revocation_required")
        _assert_true(self.audit_required, "audit_required")
        _assert_true(self.provenance_required, "provenance_required")
        return self


class ConnectorSecretRedactionResult(BaseModel):
    """Preview result for redacting secret-like fields without storing them."""

    model_config = ConfigDict(extra="forbid")

    redaction_id: str
    status: str
    redaction_applied: bool
    secret_detected: bool
    token_detected: bool
    credential_field_detected: bool
    redacted_payload: dict[str, Any] = Field(default_factory=dict)
    blocked_fields: list[str] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("redaction_id", "status")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value.strip()

    @field_validator("blocked_fields")
    @classmethod
    def blocked_fields_must_be_safe(cls, value: list[str]) -> list[str]:
        return _safe_string_list(value, "blocked_fields")

    @field_validator("warnings", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: Any) -> Any:
        _reject_unsafe_payload(value)
        return value


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def _assert_false(value: bool, field_name: str) -> None:
    if value:
        raise ValueError(f"{field_name} must be false")


def _assert_true(value: bool, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} must be true")


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
        raise ValueError("credential metadata must not contain secrets or credentials")
    if any(part in key_lower for part in _TOKEN_KEY_PARTS):
        raise ValueError("credential metadata must not contain tokens")
    if any(part in key_lower for part in _URL_KEY_PARTS):
        raise ValueError("credential metadata must not contain external locations")
    if any(part in key_lower for part in _RAW_PROMPT_KEY_PARTS):
        raise ValueError("credential metadata must not contain raw prompts")
    if any(part in key_lower for part in _HIDDEN_REASONING_KEY_PARTS):
        raise ValueError("credential metadata must not contain hidden reasoning")
    if key_path and key_path[-1] in _SAFE_FALSE_KEYS and value is False:
        return


def _reject_unsafe_text(value: str, *, key_path: tuple[str, ...] = ()) -> None:
    lower = value.lower()
    if _URL_RE.search(value):
        raise ValueError("credential metadata must not contain external URLs")
    if any(marker in lower for marker in _SECRET_VALUE_MARKERS):
        raise ValueError("credential metadata must not contain secret markers")
    if "raw prompt" in lower or "hidden reasoning" in lower or "chain-of-thought" in lower:
        raise ValueError("credential metadata must not contain hidden reasoning or raw prompts")
    if key_path and key_path[-1] in _SAFE_FALSE_KEYS:
        return


__all__ = [
    "ConnectorCredentialAuthorizationEntry",
    "ConnectorCredentialBoundary",
    "ConnectorCredentialLifecycleState",
    "ConnectorCredentialReadinessRequest",
    "ConnectorCredentialReadinessResult",
    "ConnectorCredentialReadinessStatus",
    "ConnectorSecretRedactionResult",
    "utc_now",
]
