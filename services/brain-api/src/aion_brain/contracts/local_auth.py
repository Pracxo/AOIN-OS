"""Dev-only local auth contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

LocalAuthRole = Literal[
    "viewer",
    "operator",
    "reviewer",
    "admin",
    "auditor",
    "system_service",
]
LocalOperatorIdentityStatus = Literal["simulated", "disabled", "unknown"]
LocalIdentitySource = Literal[
    "local_dev",
    "static_demo",
    "test_fixture",
    "system_service",
    "generic",
]

ALLOWED_LOCAL_AUTH_ROLES = {
    "viewer",
    "operator",
    "reviewer",
    "admin",
    "auditor",
    "system_service",
}


class LocalOperatorIdentity(BaseModel):
    """Synthetic operator identity for local development simulation only."""

    model_config = ConfigDict(extra="forbid")

    local_identity_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    status: LocalOperatorIdentityStatus
    identity_source: LocalIdentitySource
    production_identity: bool
    credentials_present: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("actor_id", "workspace_id")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be empty")
        return cleaned

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

    @field_validator("display_name")
    @classmethod
    def display_name_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "display_name")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def identity_must_remain_simulated(self) -> LocalOperatorIdentity:
        if self.production_identity:
            raise ValueError("production_identity must be false in AION-094")
        if self.credentials_present:
            raise ValueError("credentials_present must be false")
        return self


class LocalAuthContext(BaseModel):
    """Dev-only auth context derived from a synthetic local identity."""

    model_config = ConfigDict(extra="forbid")

    local_auth_context_id: str = Field(min_length=1)
    trace_id: str | None = None
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
    production_auth: bool
    session_present: bool
    credentials_present: bool
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
    def context_must_remain_non_privileged(self) -> LocalAuthContext:
        if self.write_allowed:
            raise ValueError("write_allowed must be false in AION-094")
        if self.execute_allowed:
            raise ValueError("execute_allowed must be false")
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false")
        if self.external_calls_allowed:
            raise ValueError("external_calls_allowed must be false")
        if self.production_auth:
            raise ValueError("production_auth must be false")
        if self.session_present:
            raise ValueError("session_present must be false")
        if self.credentials_present:
            raise ValueError("credentials_present must be false")
        return self


class DevIdentitySimulationRequest(BaseModel):
    """Request a synthetic local operator auth context."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    actor_id: str = "local.operator"
    workspace_id: str = "local"
    roles: list[str] = Field(default_factory=lambda: ["operator"])
    owner_scope: list[str] = Field(default_factory=lambda: ["workspace:main"])
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

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RolePermission(BaseModel):
    """Local role permission matrix entry."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(min_length=1)
    read_views: list[str] = Field(default_factory=list)
    dry_run_actions: list[str] = Field(default_factory=list)
    review_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RoleAccessDecision(BaseModel):
    """One read-only console access decision for a local role."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(min_length=1)
    view: str = Field(min_length=1)
    section_key: str | None = None
    action_key: str | None = None
    decision: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    read_allowed: bool
    dry_run_allowed: bool
    review_allowed: bool
    write_allowed: bool
    execute_allowed: bool
    activation_allowed: bool
    external_calls_allowed: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def decision_must_remain_read_only(self) -> RoleAccessDecision:
        if self.write_allowed:
            raise ValueError("write_allowed must be false")
        if self.execute_allowed:
            raise ValueError("execute_allowed must be false")
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false")
        if self.external_calls_allowed:
            raise ValueError("external_calls_allowed must be false")
        return self


class RoleAccessAudit(BaseModel):
    """Read-only audit of role-aware console filtering decisions."""

    model_config = ConfigDict(extra="forbid")

    role_access_audit_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: str = Field(min_length=1)
    roles_checked: list[str] = Field(min_length=1)
    views_checked: list[str] = Field(min_length=1)
    decisions: list[RoleAccessDecision] = Field(default_factory=list)
    forbidden_actions_visible: bool
    write_actions_absent: bool
    execution_absent: bool
    activation_absent: bool
    external_calls_absent: bool
    redaction_applied: bool
    findings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("roles_checked")
    @classmethod
    def roles_must_be_allowed(cls, value: list[str]) -> list[str]:
        roles = _clean_non_empty(value, "roles_checked")
        unknown = sorted(set(roles) - ALLOWED_LOCAL_AUTH_ROLES)
        if unknown:
            raise ValueError(f"unknown local auth roles: {unknown}")
        return roles

    @field_validator("findings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def audit_must_pass_safety_booleans(self) -> RoleAccessAudit:
        if not self.forbidden_actions_visible:
            raise ValueError("forbidden_actions_visible must be true")
        if not self.write_actions_absent:
            raise ValueError("write_actions_absent must be true")
        if not self.execution_absent:
            raise ValueError("execution_absent must be true")
        if not self.activation_absent:
            raise ValueError("activation_absent must be true")
        if not self.external_calls_absent:
            raise ValueError("external_calls_absent must be true")
        if not self.redaction_applied:
            raise ValueError("redaction_applied must be true")
        return self


class ConsoleRoleFilterRequest(BaseModel):
    """Filter a console view model using a dev-only local auth context."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    view_model: dict[str, Any]
    auth_context: LocalAuthContext
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ConsoleRoleFilterResult(BaseModel):
    """Read-only role-filtering result for Operator Console view models."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(min_length=1)
    read_only: bool
    redaction_applied: bool
    actor_id: str = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    filtered_view_model: dict[str, Any]
    removed_sections: list[str] = Field(default_factory=list)
    removed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    safety_findings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("metadata", "safety_findings")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def result_must_remain_read_only_and_redacted(self) -> ConsoleRoleFilterResult:
        if not self.read_only:
            raise ValueError("read_only must be true")
        if not self.redaction_applied:
            raise ValueError("redaction_applied must be true")
        if _payload_has_unsafe_content(self.filtered_view_model):
            raise ValueError("filtered_view_model contains unsafe auth or prompt content")
        return self


class LocalAuthAuditRequest(BaseModel):
    """Request local auth safety audit."""

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


class LocalAuthAuditResult(BaseModel):
    """Local auth safety audit result."""

    model_config = ConfigDict(extra="forbid")

    local_auth_audit_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    production_auth_absent: bool
    credentials_absent: bool
    sessions_absent: bool
    external_identity_absent: bool
    write_actions_disabled: bool
    execution_disabled: bool
    activation_disabled: bool
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("findings", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def safety_booleans_must_pass(self) -> LocalAuthAuditResult:
        if not self.production_auth_absent:
            raise ValueError("production_auth_absent must be true")
        if not self.credentials_absent:
            raise ValueError("credentials_absent must be true")
        if not self.sessions_absent:
            raise ValueError("sessions_absent must be true")
        if not self.external_identity_absent:
            raise ValueError("external_identity_absent must be true")
        if not self.write_actions_disabled:
            raise ValueError("write_actions_disabled must be true")
        if not self.execution_disabled:
            raise ValueError("execution_disabled must be true")
        if not self.activation_disabled:
            raise ValueError("activation_disabled must be true")
        return self


def utc_now() -> datetime:
    """Return current UTC time."""
    from datetime import UTC

    return datetime.now(UTC)


def _clean_non_empty(value: list[str], field_name: str) -> list[str]:
    cleaned = [item.strip() for item in value if item.strip()]
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned


def _payload_has_unsafe_content(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(
                part in normalized
                for part in (
                    "api_key",
                    "apikey",
                    "authorization",
                    "bearer",
                    "credential",
                    "hidden_reasoning",
                    "password",
                    "private_key",
                    "provider_payload",
                    "raw_model_payload",
                    "raw_prompt",
                    "secret",
                    "token",
                )
            ):
                return True
            if _payload_has_unsafe_content(nested):
                return True
    elif isinstance(value, list):
        return any(_payload_has_unsafe_content(item) for item in value)
    elif isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "sk-",
                "xoxb-",
                "ghp_",
                "-----begin private key-----",
                "raw_prompt",
                "raw prompt",
                "hidden_reasoning",
                "hidden reasoning",
                "chain-of-thought",
                "chain_of_thought",
            )
        )
    return False


__all__ = [
    "ALLOWED_LOCAL_AUTH_ROLES",
    "ConsoleRoleFilterRequest",
    "ConsoleRoleFilterResult",
    "DevIdentitySimulationRequest",
    "LocalAuthAuditRequest",
    "LocalAuthAuditResult",
    "LocalAuthContext",
    "LocalAuthRole",
    "LocalOperatorIdentity",
    "RoleAccessAudit",
    "RoleAccessDecision",
    "RolePermission",
    "utc_now",
]
