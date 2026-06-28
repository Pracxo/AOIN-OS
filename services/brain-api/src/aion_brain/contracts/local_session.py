"""Read-only local session prototype contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.local_auth import ALLOWED_LOCAL_AUTH_ROLES
from aion_brain.contracts.model_outputs import reject_secret_like_payload

LocalSessionStatus = Literal[
    "preview",
    "active_local_preview",
    "expired",
    "blocked",
    "invalid",
]
LocalSessionType = Literal[
    "local_preview",
    "static_demo",
    "test_fixture",
    "dev_only",
    "generic",
]
LocalSessionBoundaryStatus = Literal["passed", "failed"]
LocalSessionAuditStatus = Literal["passed", "failed"]


class LocalSessionPreview(BaseModel):
    """Synthetic session preview for local Operator Console display only."""

    model_config = ConfigDict(extra="forbid")

    local_session_preview_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    status: LocalSessionStatus
    session_type: LocalSessionType
    read_only: bool
    dev_only: bool
    production_session: bool
    credential_backed: bool
    token_issued: bool
    cookie_issued: bool
    persistent: bool
    write_allowed: bool
    execute_allowed: bool
    activation_allowed: bool
    external_calls_allowed: bool
    expires_at: datetime | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("roles")
    @classmethod
    def roles_must_be_allowed(cls, value: list[str]) -> list[str]:
        roles = _clean_non_empty(value, "roles")
        unknown = sorted(set(roles) - ALLOWED_LOCAL_AUTH_ROLES)
        if unknown:
            raise ValueError(f"unknown local auth roles: {unknown}")
        return roles

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _clean_non_empty(value, "owner_scope")

    @field_validator("warnings", "blockers", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def preview_must_remain_non_privileged(self) -> LocalSessionPreview:
        if not self.read_only:
            raise ValueError("read_only must be true")
        if not self.dev_only:
            raise ValueError("dev_only must be true")
        if self.production_session:
            raise ValueError("production_session must be false")
        if self.credential_backed:
            raise ValueError("credential_backed must be false")
        if self.token_issued:
            raise ValueError("token_issued must be false")
        if self.cookie_issued:
            raise ValueError("cookie_issued must be false")
        if self.persistent:
            raise ValueError("persistent must be false")
        if self.write_allowed:
            raise ValueError("write_allowed must be false")
        if self.execute_allowed:
            raise ValueError("execute_allowed must be false")
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false")
        if self.external_calls_allowed:
            raise ValueError("external_calls_allowed must be false")
        return self


class LocalSessionPreviewRequest(BaseModel):
    """Request a synthetic local session preview without authenticating a user."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    actor_id: str = "local.operator"
    workspace_id: str = "local"
    roles: list[str] = Field(default_factory=lambda: ["operator"])
    owner_scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
    session_type: LocalSessionType = "local_preview"
    ttl_seconds: int = Field(default=1800, ge=60, le=86400)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("roles")
    @classmethod
    def roles_must_be_allowed(cls, value: list[str]) -> list[str]:
        roles = _clean_non_empty(value, "roles")
        unknown = sorted(set(roles) - ALLOWED_LOCAL_AUTH_ROLES)
        if unknown:
            raise ValueError(f"unknown local auth roles: {unknown}")
        return roles

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _clean_non_empty(value, "owner_scope")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class LocalSessionContext(BaseModel):
    """Read-only local session context derived from a preview."""

    model_config = ConfigDict(extra="forbid")

    local_session_preview_id: str = Field(min_length=1)
    auth_context_id: str | None = None
    actor_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    read_allowed: bool
    dry_run_allowed: bool
    review_allowed: bool
    write_allowed: bool
    execute_allowed: bool
    activation_allowed: bool
    external_calls_allowed: bool
    session_valid: bool
    session_read_only: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("roles")
    @classmethod
    def roles_must_be_allowed(cls, value: list[str]) -> list[str]:
        roles = _clean_non_empty(value, "roles")
        unknown = sorted(set(roles) - ALLOWED_LOCAL_AUTH_ROLES)
        if unknown:
            raise ValueError(f"unknown local auth roles: {unknown}")
        return roles

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _clean_non_empty(value, "owner_scope")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def context_must_remain_read_only(self) -> LocalSessionContext:
        if not self.session_read_only:
            raise ValueError("session_read_only must be true")
        if self.write_allowed:
            raise ValueError("write_allowed must be false")
        if self.execute_allowed:
            raise ValueError("execute_allowed must be false")
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false")
        if self.external_calls_allowed:
            raise ValueError("external_calls_allowed must be false")
        return self


class LocalSessionBoundaryCheck(BaseModel):
    """Result for local session safety boundary validation."""

    model_config = ConfigDict(extra="forbid")

    boundary_check_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: LocalSessionBoundaryStatus
    checks_run: list[str] = Field(default_factory=list)
    read_only_passed: bool
    dev_only_passed: bool
    no_credentials_passed: bool
    no_tokens_passed: bool
    no_cookies_passed: bool
    no_persistence_passed: bool
    no_execution_passed: bool
    no_activation_passed: bool
    no_external_calls_passed: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("blockers", "warnings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def passed_status_requires_all_checks(self) -> LocalSessionBoundaryCheck:
        checks = (
            self.read_only_passed,
            self.dev_only_passed,
            self.no_credentials_passed,
            self.no_tokens_passed,
            self.no_cookies_passed,
            self.no_persistence_passed,
            self.no_execution_passed,
            self.no_activation_passed,
            self.no_external_calls_passed,
        )
        if self.status == "passed" and not all(checks):
            raise ValueError("passed status requires all boundary checks to pass")
        return self


class LocalSessionAuditRequest(BaseModel):
    """Request a local session safety audit."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    include_examples: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _clean_non_empty(value, "owner_scope")

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class LocalSessionAuditResult(BaseModel):
    """Local session safety audit result."""

    model_config = ConfigDict(extra="forbid")

    local_session_audit_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: LocalSessionAuditStatus
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    sessions_are_dev_only: bool
    sessions_are_read_only: bool
    credentials_absent: bool
    tokens_absent: bool
    cookies_absent: bool
    persistence_absent: bool
    production_auth_absent: bool
    write_actions_disabled: bool
    execution_disabled: bool
    activation_disabled: bool
    external_calls_disabled: bool
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("findings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def safety_booleans_must_pass(self) -> LocalSessionAuditResult:
        checks = (
            self.sessions_are_dev_only,
            self.sessions_are_read_only,
            self.credentials_absent,
            self.tokens_absent,
            self.cookies_absent,
            self.persistence_absent,
            self.production_auth_absent,
            self.write_actions_disabled,
            self.execution_disabled,
            self.activation_disabled,
            self.external_calls_disabled,
        )
        if self.status == "passed" and not all(checks):
            raise ValueError("passed status requires all safety checks to pass")
        return self


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(UTC)


def _clean_non_empty(value: list[str], field_name: str) -> list[str]:
    cleaned = [item.strip() for item in value if item.strip()]
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned


__all__ = [
    "LocalSessionAuditRequest",
    "LocalSessionAuditResult",
    "LocalSessionBoundaryCheck",
    "LocalSessionContext",
    "LocalSessionPreview",
    "LocalSessionPreviewRequest",
    "LocalSessionStatus",
    "LocalSessionType",
    "utc_now",
]
