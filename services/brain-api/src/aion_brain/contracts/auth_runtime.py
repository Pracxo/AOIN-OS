"""Disabled production auth runtime contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.local_auth import ALLOWED_LOCAL_AUTH_ROLES
from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

AuthRuntimePreviewStatus = Literal["preview", "blocked", "warning"]
AuthRuntimeAuditStatus = Literal["passed", "failed"]
AuthRuntimeBlockerType = Literal[
    "production_auth_disabled",
    "external_identity_disabled",
    "credentials_disabled",
    "token_issuance_disabled",
    "cookie_issuance_disabled",
    "session_persistence_disabled",
    "login_endpoint_disabled",
    "logout_endpoint_disabled",
    "unsafe_claims",
    "secret_detected",
    "unsupported_issuer",
    "generic",
]
AuthRuntimeBlockerSeverity = Literal["low", "medium", "high", "critical"]
AuthRuntimeBlockerStatus = Literal["open", "resolved"]


class AuthRuntimeBlocker(BaseModel):
    """One disabled-auth blocker. It records why no production auth can run."""

    model_config = ConfigDict(extra="forbid")

    auth_runtime_blocker_id: str = Field(min_length=1)
    blocker_type: AuthRuntimeBlockerType
    severity: AuthRuntimeBlockerSeverity
    status: AuthRuntimeBlockerStatus
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    source_type: str | None = None
    source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("reason", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "auth runtime blocker text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload_except_controlled(value)
        return value


class AuthRuntimeStatus(BaseModel):
    """Current disabled production auth runtime status."""

    model_config = ConfigDict(extra="forbid")

    status_id: str = Field(min_length=1)
    production_auth_enabled: bool
    auth_runtime_enabled: bool
    mock_claims_preview_enabled: bool
    external_identity_provider_enabled: bool
    credentials_enabled: bool
    token_issuance_enabled: bool
    cookie_issuance_enabled: bool
    session_persistence_enabled: bool
    login_endpoint_enabled: bool
    logout_endpoint_enabled: bool
    actor_mapping_preview_enabled: bool
    blockers: list[AuthRuntimeBlocker] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("warnings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def status_must_stay_disabled(self) -> AuthRuntimeStatus:
        if self.production_auth_enabled:
            raise ValueError("production_auth_enabled must be false")
        if self.auth_runtime_enabled and self.metadata.get("disabled_by_default") is not True:
            raise ValueError("auth_runtime_enabled must be false or disabled_by_default")
        if self.external_identity_provider_enabled:
            raise ValueError("external_identity_provider_enabled must be false")
        if self.credentials_enabled:
            raise ValueError("credentials_enabled must be false")
        if self.token_issuance_enabled:
            raise ValueError("token_issuance_enabled must be false")
        if self.cookie_issuance_enabled:
            raise ValueError("cookie_issuance_enabled must be false")
        if self.session_persistence_enabled:
            raise ValueError("session_persistence_enabled must be false")
        if self.login_endpoint_enabled:
            raise ValueError("login_endpoint_enabled must be false")
        if self.logout_endpoint_enabled:
            raise ValueError("logout_endpoint_enabled must be false")
        return self


class MockClaimsPreviewRequest(BaseModel):
    """Request a synthetic mock-claims preview without authenticating anyone."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    issuer: str = "mock.local"
    subject: str = Field(min_length=1)
    audience: str = "aion.local"
    roles: list[str] = Field(min_length=1)
    workspace_id: str = "local"
    owner_scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
    claims: dict[str, Any] = Field(default_factory=dict)
    mode: str = "preview"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("issuer")
    @classmethod
    def issuer_must_be_mock_only(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in {"mock.local", "test.local"}:
            raise ValueError("issuer must be mock.local or test.local")
        return cleaned

    @field_validator("subject", "audience", "workspace_id")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be empty")
        reject_hidden_or_secret_text(cleaned, "mock claims preview text")
        return cleaned

    @field_validator("roles")
    @classmethod
    def roles_must_be_allowed(cls, value: list[str]) -> list[str]:
        roles = [item.strip() for item in value if item.strip()]
        if not roles:
            raise ValueError("roles cannot be empty")
        unknown = sorted(set(roles) - ALLOWED_LOCAL_AUTH_ROLES)
        if unknown:
            raise ValueError(f"unknown local auth roles: {unknown}")
        return roles

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("claims", "metadata")
    @classmethod
    def payloads_must_not_contain_auth_material(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator("mode")
    @classmethod
    def mode_must_be_preview(cls, value: str) -> str:
        if value != "preview":
            raise ValueError("mode must be preview")
        return value


class MockClaimsPreviewResult(BaseModel):
    """Synthetic claims preview result. It is not an identity or session."""

    model_config = ConfigDict(extra="forbid")

    mock_claims_preview_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: AuthRuntimePreviewStatus
    issuer: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    production_identity: bool
    credentials_present: bool
    token_present: bool
    cookie_present: bool
    session_persisted: bool
    actor_context_preview: dict[str, Any] = Field(default_factory=dict)
    role_decisions: dict[str, Any] = Field(default_factory=dict)
    blockers: list[AuthRuntimeBlocker] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("actor_context_preview", "role_decisions", "warnings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def result_must_not_be_auth_material(self) -> MockClaimsPreviewResult:
        if self.production_identity:
            raise ValueError("production_identity must be false")
        if self.credentials_present:
            raise ValueError("credentials_present must be false")
        if self.token_present:
            raise ValueError("token_present must be false")
        if self.cookie_present:
            raise ValueError("cookie_present must be false")
        if self.session_persisted:
            raise ValueError("session_persisted must be false")
        if self.actor_context_preview.get("preview_only") is not True:
            raise ValueError("actor_context_preview must be preview only")
        return self


class AuthRuntimeAuditRequest(BaseModel):
    """Request a local disabled-auth runtime audit."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    owner_scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
    include_examples: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class AuthRuntimeAuditResult(BaseModel):
    """Audit proof that production auth remains disabled."""

    model_config = ConfigDict(extra="forbid")

    auth_runtime_audit_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: AuthRuntimeAuditStatus
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    production_auth_disabled: bool
    external_identity_disabled: bool
    credentials_disabled: bool
    token_issuance_disabled: bool
    cookie_issuance_disabled: bool
    session_persistence_disabled: bool
    login_logout_absent: bool
    mock_only: bool
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("findings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        _reject_payload_except_controlled(value)
        return value

    @model_validator(mode="after")
    def audit_must_confirm_disabled_boundaries(self) -> AuthRuntimeAuditResult:
        if not self.production_auth_disabled:
            raise ValueError("production_auth_disabled must be true")
        if not self.external_identity_disabled:
            raise ValueError("external_identity_disabled must be true")
        if not self.credentials_disabled:
            raise ValueError("credentials_disabled must be true")
        if not self.token_issuance_disabled:
            raise ValueError("token_issuance_disabled must be true")
        if not self.cookie_issuance_disabled:
            raise ValueError("cookie_issuance_disabled must be true")
        if not self.session_persistence_disabled:
            raise ValueError("session_persistence_disabled must be true")
        if not self.login_logout_absent:
            raise ValueError("login_logout_absent must be true")
        if not self.mock_only:
            raise ValueError("mock_only must be true")
        return self


def utc_now() -> datetime:
    """Return timezone-aware UTC time."""

    return datetime.now(UTC)


def _reject_payload_except_controlled(value: object) -> None:
    """Reject unsafe material while allowing controlled disabled-boundary fields."""

    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) in {
                "blocker_type",
                "code",
                "finding",
                "status",
                "disabled_flags",
                "role_decisions",
                "actor_context_preview",
                "no_go_warnings",
                "roles",
                "read_views",
                "dry_run_actions",
                "review_actions",
                "forbidden_actions",
                "constraints",
            }:
                controlled_lists = {
                    "roles",
                    "read_views",
                    "dry_run_actions",
                    "review_actions",
                    "forbidden_actions",
                    "constraints",
                }
                if str(key) in controlled_lists:
                    continue
                _reject_payload_except_controlled(nested)
                continue
            lowered = str(key).lower().replace("-", "_")
            allowed_key_parts = (
                "token_issuance_disabled",
                "cookie_issuance_disabled",
                "session_persistence_disabled",
                "credentials_disabled",
                "external_identity_disabled",
                "production_auth_disabled",
                "login_logout_absent",
                "token_present",
                "cookie_present",
                "credentials_present",
                "session_persisted",
            )
            if any(part == lowered for part in allowed_key_parts):
                _reject_payload_except_controlled(nested)
                continue
            reject_secret_like_payload({key: nested})
        return
    if isinstance(value, list):
        for item in value:
            _reject_payload_except_controlled(item)
        return
    if isinstance(value, str):
        reject_hidden_or_secret_text(value, "auth runtime payload")


__all__ = [
    "AuthRuntimeAuditRequest",
    "AuthRuntimeAuditResult",
    "AuthRuntimeAuditStatus",
    "AuthRuntimeBlocker",
    "AuthRuntimeBlockerSeverity",
    "AuthRuntimeBlockerStatus",
    "AuthRuntimeBlockerType",
    "AuthRuntimePreviewStatus",
    "AuthRuntimeStatus",
    "MockClaimsPreviewRequest",
    "MockClaimsPreviewResult",
    "utc_now",
]
