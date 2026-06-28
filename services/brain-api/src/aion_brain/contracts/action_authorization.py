"""Dry-run action authorization contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

ActionAuthorizationStatus = Literal["allowed", "denied", "blocked", "warning"]
ActionAuthorizationDecisionValue = Literal[
    "allow_dry_run_preview",
    "allow_review_record",
    "deny",
    "block",
    "require_review",
    "unsupported",
]
ActionAuthorizationBlockerType = Literal[
    "role_denied",
    "policy_denied",
    "session_denied",
    "unsupported_action",
    "non_dry_run_mode",
    "write_blocked",
    "execution_blocked",
    "activation_blocked",
    "external_calls_blocked",
    "missing_role",
    "unsafe_payload",
    "raw_prompt_detected",
    "hidden_reasoning_detected",
    "secret_detected",
    "generic",
]
ActionAuthorizationBlockerSeverity = Literal["low", "medium", "high", "critical"]
ActionAuthorizationBlockerStatus = Literal["open", "resolved"]

_ACTION_KEY = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")


class DryRunActionAuthorizationRequest(BaseModel):
    """Request dry-run-only authorization for an operator action preview or review."""

    model_config = ConfigDict(extra="forbid")

    authorization_request_id: str | None = None
    trace_id: str | None = None
    actor_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    action_key: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str | None = None
    mode: str = "dry_run"
    requested_operation: str = "preview"
    local_auth_context_ref: str | None = None
    local_session_preview_id: str | None = None
    operator_action_request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("action_key")
    @classmethod
    def action_key_must_be_dotted_lowercase(cls, value: str) -> str:
        cleaned = value.strip()
        if not _ACTION_KEY.fullmatch(cleaned):
            raise ValueError("action_key must be dotted lowercase text")
        return cleaned

    @field_validator("roles", "owner_scope")
    @classmethod
    def lists_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("value cannot be empty")
        return cleaned

    @field_validator("mode")
    @classmethod
    def mode_must_be_dry_run(cls, value: str) -> str:
        if value != "dry_run":
            raise ValueError("mode must be dry_run")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secret_material(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_values(value)
        return value


class ActionAuthorizationBlocker(BaseModel):
    """One authorization blocker. It never grants execution."""

    model_config = ConfigDict(extra="forbid")

    authz_blocker_id: str = Field(min_length=1)
    trace_id: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    blocker_type: ActionAuthorizationBlockerType
    severity: ActionAuthorizationBlockerSeverity
    status: ActionAuthorizationBlockerStatus
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("reason", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "action authorization blocker text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class DryRunActionAuthorizationDecision(BaseModel):
    """Dry-run authorization decision for preview or review record creation."""

    model_config = ConfigDict(extra="forbid")

    authorization_decision_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    roles: list[str] = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    action_key: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str | None = None
    mode: str
    requested_operation: str
    status: ActionAuthorizationStatus
    decision: ActionAuthorizationDecisionValue
    reason: str = Field(min_length=1)
    policy_allowed: bool
    role_allowed: bool
    session_allowed: bool
    dry_run_only: bool
    write_allowed: bool
    execution_allowed: bool
    activation_allowed: bool
    external_calls_allowed: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    required_policy_actions: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator("blockers")
    @classmethod
    def blockers_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            _reject_blocker_payload(item)
        return value

    @field_validator("warnings")
    @classmethod
    def warnings_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_payload(item)
        return value

    @model_validator(mode="after")
    def decision_must_remain_dry_run_only(self) -> DryRunActionAuthorizationDecision:
        if not self.dry_run_only:
            raise ValueError("dry_run_only must be true")
        if self.write_allowed:
            raise ValueError("write_allowed must be false")
        if self.execution_allowed:
            raise ValueError("execution_allowed must be false")
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false")
        if self.external_calls_allowed:
            raise ValueError("external_calls_allowed must be false")
        return self


class ActionAuthorizationAuditRequest(BaseModel):
    """Request a local dry-run action authorization audit."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
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


class ActionAuthorizationAuditResult(BaseModel):
    """Audit proof that dry-run authorization boundaries are enforced."""

    model_config = ConfigDict(extra="forbid")

    action_authorization_audit_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    dry_run_only_enforced: bool
    write_blocked: bool
    execution_blocked: bool
    activation_blocked: bool
    external_calls_blocked: bool
    role_matrix_enforced: bool
    policy_enforced: bool
    session_boundary_enforced: bool
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator("findings")
    @classmethod
    def findings_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_payload(item)
        return value

    @model_validator(mode="after")
    def audit_must_prove_disabled_boundaries(self) -> ActionAuthorizationAuditResult:
        if not self.dry_run_only_enforced:
            raise ValueError("dry_run_only_enforced must be true")
        if not self.write_blocked:
            raise ValueError("write_blocked must be true")
        if not self.execution_blocked:
            raise ValueError("execution_blocked must be true")
        if not self.activation_blocked:
            raise ValueError("activation_blocked must be true")
        if not self.external_calls_blocked:
            raise ValueError("external_calls_blocked must be true")
        return self


def utc_now() -> datetime:
    """Return timezone-aware UTC time."""

    return datetime.now(UTC)


def _reject_secret_values(value: object) -> None:
    """Reject obvious secret values while leaving unsafe-prompt markers to blockers."""

    secret_value_markers = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")
    if isinstance(value, dict):
        for nested in value.values():
            _reject_secret_values(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_values(item)
    elif isinstance(value, str) and any(marker in value.lower() for marker in secret_value_markers):
        raise ValueError("metadata must not contain secret-like values")


def _reject_blocker_payload(value: object) -> None:
    """Reject unsafe blocker payload fields while allowing controlled blocker codes."""

    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "blocker_type":
                continue
            reject_secret_like_payload({key: nested})
        return
    reject_secret_like_payload(value)


__all__ = [
    "ActionAuthorizationAuditRequest",
    "ActionAuthorizationAuditResult",
    "ActionAuthorizationBlocker",
    "ActionAuthorizationBlockerStatus",
    "ActionAuthorizationBlockerType",
    "ActionAuthorizationDecisionValue",
    "ActionAuthorizationStatus",
    "DryRunActionAuthorizationDecision",
    "DryRunActionAuthorizationRequest",
    "utc_now",
]
