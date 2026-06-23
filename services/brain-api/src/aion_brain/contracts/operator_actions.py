"""Governed operator action contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

OperatorActionType = Literal[
    "dry_run_check",
    "review_record",
    "acknowledge",
    "dismiss_finding",
    "seed_defaults_dry_run",
    "run_golden_path_dry_run",
    "run_rc_gate_dry_run",
    "run_release_smoke_dry_run",
    "validate_manifest_dry_run",
    "validate_binding_dry_run",
    "run_conformance_dry_run",
    "run_module_mock_dry_run",
    "run_provider_simulation_dry_run",
    "generic",
]
OperatorActionTargetType = Literal[
    "operator",
    "notification",
    "incident",
    "release_candidate",
    "freeze_gate",
    "release_package",
    "extension",
    "module_slot",
    "capability_binding",
    "module_activation",
    "module_mock_runtime",
    "model_provider",
    "registry",
    "lifecycle",
    "generic",
]
OperatorActionStatus = Literal[
    "requested",
    "previewed",
    "blocked",
    "reviewed",
    "dismissed",
    "archived",
]
OperatorActionMode = Literal["dry_run"]
OperatorActionRiskLevel = Literal["low", "medium", "high", "critical"]
OperatorActionPreviewStatus = Literal["created", "blocked"]
OperatorActionPreviewType = Literal["dry_run"]
OperatorActionBlockerType = Literal[
    "execution_disabled",
    "external_calls_disabled",
    "activation_disabled",
    "policy_required",
    "approval_required",
    "unsupported_action",
    "unsafe_payload",
    "raw_prompt_detected",
    "hidden_reasoning_detected",
    "secret_detected",
    "controlled_mode_blocked",
    "generic",
]
OperatorActionBlockerSeverity = Literal["low", "medium", "high", "critical"]
OperatorActionBlockerStatus = Literal["open", "dismissed", "resolved"]
OperatorActionReviewStatus = Literal["completed"]
OperatorActionReviewDecision = Literal[
    "acknowledge",
    "dismiss",
    "request_changes",
    "approve_preview_only",
    "reject",
    "block",
]

_ACTION_KEY = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")


class OperatorActionRequest(BaseModel):
    """Dry-run operator action request record. It is never executable."""

    model_config = ConfigDict(extra="forbid")

    operator_action_request_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    action_key: str = Field(min_length=1)
    action_type: OperatorActionType
    target_type: OperatorActionTargetType
    target_id: str | None = None
    status: OperatorActionStatus
    mode: OperatorActionMode
    risk_level: OperatorActionRiskLevel
    owner_scope: list[str] = Field(min_length=1)
    request_payload_hash: str = Field(min_length=1)
    redacted_request_payload: dict[str, Any] = Field(default_factory=dict)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    required_evidence_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    preview_id: str | None = None
    review_id: str | None = None
    execution_allowed: bool = False
    external_calls_allowed: bool = False
    activation_allowed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("action_key")
    @classmethod
    def action_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _ACTION_KEY.fullmatch(value):
            raise ValueError("action_key must be dotted lowercase text")
        return value

    @field_validator("redacted_request_payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def request_must_remain_non_executable(self) -> OperatorActionRequest:
        _require_disabled(
            self.execution_allowed,
            self.external_calls_allowed,
            self.activation_allowed,
        )
        return self


class OperatorActionCreateRequest(BaseModel):
    """Create a dry-run operator action request."""

    model_config = ConfigDict(extra="forbid")

    operator_action_request_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    action_key: str = Field(min_length=1)
    action_type: OperatorActionType = "generic"
    target_type: OperatorActionTargetType = "generic"
    target_id: str | None = None
    mode: OperatorActionMode = "dry_run"
    risk_level: OperatorActionRiskLevel = "medium"
    owner_scope: list[str] = Field(min_length=1)
    request_payload: dict[str, Any] = Field(default_factory=dict)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    required_evidence_refs: list[str] = Field(default_factory=list)
    create_preview: bool = True
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("action_key")
    @classmethod
    def action_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _ACTION_KEY.fullmatch(value):
            raise ValueError("action_key must be dotted lowercase text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class OperatorActionPreview(BaseModel):
    """Dry-run preview for an operator action request."""

    model_config = ConfigDict(extra="forbid")

    operator_action_preview_id: str = Field(min_length=1)
    trace_id: str | None = None
    operator_action_request_id: str = Field(min_length=1)
    status: OperatorActionPreviewStatus
    preview_type: OperatorActionPreviewType
    owner_scope: list[str] = Field(min_length=1)
    expected_effects: list[dict[str, Any]] = Field(default_factory=list)
    blocked_effects: list[dict[str, Any]] = Field(default_factory=list)
    dry_run_result: dict[str, Any] = Field(default_factory=dict)
    would_execute: bool = False
    execution_allowed: bool = False
    external_calls_allowed: bool = False
    activation_allowed: bool = False
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator(
        "expected_effects",
        "blocked_effects",
        "blockers",
        "warnings",
        mode="after",
    )
    @classmethod
    def lists_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_payload(item)
        return value

    @field_validator("dry_run_result", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def preview_must_remain_non_executable(self) -> OperatorActionPreview:
        if self.would_execute:
            raise ValueError("operator action preview must not execute")
        _require_disabled(
            self.execution_allowed,
            self.external_calls_allowed,
            self.activation_allowed,
        )
        return self


class OperatorActionBlocker(BaseModel):
    """Blocker attached to a governed operator action request."""

    model_config = ConfigDict(extra="forbid")

    operator_action_blocker_id: str = Field(min_length=1)
    trace_id: str | None = None
    operator_action_request_id: str | None = None
    blocker_type: OperatorActionBlockerType
    severity: OperatorActionBlockerSeverity
    status: OperatorActionBlockerStatus
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    source_type: str | None = None
    source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("reason", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "operator action blocker text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class OperatorActionReviewRequest(BaseModel):
    """Request to review a dry-run operator action request."""

    model_config = ConfigDict(extra="forbid")

    operator_action_request_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    reviewer_id: str | None = None
    decision: OperatorActionReviewDecision
    reason: str = Field(min_length=1)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "operator action review reason")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class OperatorActionReview(BaseModel):
    """Review record. Approval does not execute."""

    model_config = ConfigDict(extra="forbid")

    operator_action_review_id: str = Field(min_length=1)
    trace_id: str | None = None
    operator_action_request_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    reviewer_id: str | None = None
    status: OperatorActionReviewStatus
    decision: OperatorActionReviewDecision
    reason: str = Field(min_length=1)
    approval_present: bool = False
    execution_allowed: bool = False
    blocker_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "operator action review reason")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def review_must_not_execute(self) -> OperatorActionReview:
        if self.execution_allowed:
            raise ValueError("operator action review must not execute")
        return self


class OperatorActionQuery(BaseModel):
    """Query governed operator action records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    status: str | None = None
    action_type: str | None = None
    target_type: str | None = None
    risk_level: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class OperatorActionQueryResult(BaseModel):
    """Operator action query result."""

    model_config = ConfigDict(extra="forbid")

    requests: list[OperatorActionRequest] = Field(default_factory=list)
    previews: list[OperatorActionPreview] = Field(default_factory=list)
    blockers: list[OperatorActionBlocker] = Field(default_factory=list)
    reviews: list[OperatorActionReview] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


def _require_disabled(
    execution_allowed: bool,
    external_calls_allowed: bool,
    activation_allowed: bool,
) -> None:
    if execution_allowed:
        raise ValueError("operator action execution must remain disabled")
    if external_calls_allowed:
        raise ValueError("operator action external calls must remain disabled")
    if activation_allowed:
        raise ValueError("operator action activation must remain disabled")


__all__ = [
    "OperatorActionBlocker",
    "OperatorActionBlockerStatus",
    "OperatorActionBlockerType",
    "OperatorActionCreateRequest",
    "OperatorActionPreview",
    "OperatorActionQuery",
    "OperatorActionQueryResult",
    "OperatorActionRequest",
    "OperatorActionReview",
    "OperatorActionReviewDecision",
    "OperatorActionReviewRequest",
    "OperatorActionStatus",
]
