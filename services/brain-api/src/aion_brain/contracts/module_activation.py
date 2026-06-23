"""Module activation request gate contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

ActivationRequestStatus = Literal[
    "requested",
    "blocked",
    "review_required",
    "reviewed",
    "rejected",
    "archived",
    "deleted",
]
ActivationRequestType = Literal[
    "module_activation",
    "capability_activation",
    "route_registration",
    "policy_registration",
    "setting_enablement",
    "future_activation",
    "generic",
]
ActivationTarget = Literal[
    "module_slot",
    "capability_binding",
    "runtime_registration",
    "metadata_only",
]
ActivationRequestedMode = Literal["dry_run", "controlled", "future_controlled"]
ActivationRiskLevel = Literal["low", "medium", "high", "critical"]
ActivationBlockerType = Literal[
    "activation_disabled",
    "code_loading_disabled",
    "package_install_disabled",
    "dynamic_route_registration_disabled",
    "capability_activation_disabled",
    "missing_readiness_assessment",
    "readiness_not_ready",
    "conformance_failed",
    "binding_validation_failed",
    "missing_policy_action",
    "missing_setting",
    "missing_contract",
    "missing_sandbox_profile",
    "approval_required",
    "high_risk_requires_review",
    "external_source_blocked",
    "unsafe_metadata",
    "generic",
]
ActivationBlockerSeverity = Literal["low", "medium", "high", "critical"]
ActivationBlockerStatus = Literal["open", "dismissed", "resolved", "archived"]
ActivationGateStatus = Literal["passed", "warning", "failed", "blocked", "dry_run"]
ActivationReviewDecision = Literal[
    "approve_for_future_activation",
    "reject",
    "block",
    "request_changes",
    "request_approval",
    "no_action",
]
ActivationReviewStatus = Literal["recorded", "approved", "rejected", "blocked", "changes_requested"]
ActivationPlanStatus = Literal["created", "blocked", "archived"]
ActivationPlanType = Literal[
    "metadata_only",
    "future_activation",
    "validation_only",
    "rollback_preview",
    "generic",
]
RuntimeRegistrationPreviewType = Literal[
    "module_runtime",
    "capability_runtime",
    "api_route",
    "sdk_method",
    "cli_command",
    "policy_action",
    "setting",
    "generic",
]


class ModuleActivationRequest(BaseModel):
    """Request to evaluate future activation without activating anything."""

    model_config = ConfigDict(extra="forbid")

    activation_request_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    extension_package_id: str | None = None
    module_slot_id: str = Field(min_length=1)
    capability_binding_ids: list[str] = Field(default_factory=list)
    readiness_assessment_ids: list[str] = Field(default_factory=list)
    conformance_run_ids: list[str] = Field(default_factory=list)
    status: ActivationRequestStatus
    request_type: ActivationRequestType
    activation_target: ActivationTarget
    requested_mode: ActivationRequestedMode
    risk_level: ActivationRiskLevel
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    required_sandbox_profiles: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    activation_plan_id: str | None = None
    registration_preview_id: str | None = None
    rollback_plan_id: str | None = None
    activation_allowed: bool
    execution_allowed: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    reviewed_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def request_must_not_activate(self) -> ModuleActivationRequest:
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false in AION-083")
        if self.execution_allowed:
            raise ValueError("execution_allowed must be false in AION-083")
        _reject_actual_activation(self.metadata)
        return self


class ModuleActivationCreateRequest(BaseModel):
    """Create a metadata-only activation request."""

    model_config = ConfigDict(extra="forbid")

    activation_request_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    extension_package_id: str | None = None
    module_slot_id: str
    capability_binding_ids: list[str] = Field(default_factory=list)
    readiness_assessment_ids: list[str] = Field(default_factory=list)
    conformance_run_ids: list[str] = Field(default_factory=list)
    request_type: ActivationRequestType = "future_activation"
    activation_target: ActivationTarget = "module_slot"
    requested_mode: ActivationRequestedMode = "dry_run"
    risk_level: ActivationRiskLevel = "medium"
    owner_scope: list[str] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("module_slot_id")
    @classmethod
    def module_slot_id_must_not_be_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("module_slot_id cannot be empty")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        _reject_actual_activation(value)
        return value


class ActivationBlocker(BaseModel):
    """Activation blocker ledger record."""

    model_config = ConfigDict(extra="forbid")

    activation_blocker_id: str = Field(min_length=1)
    trace_id: str | None = None
    activation_request_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    blocker_type: ActivationBlockerType
    severity: ActivationBlockerSeverity
    status: ActivationBlockerStatus
    reason: str = Field(min_length=1)
    missing_requirement: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    recommended_action: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("reason", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "activation blocker text")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ActivationGateRun(BaseModel):
    """Activation gate run result."""

    model_config = ConfigDict(extra="forbid")

    activation_gate_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    activation_request_id: str = Field(min_length=1)
    status: ActivationGateStatus
    mode: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    blockers: list[ActivationBlocker] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    activation_allowed: bool
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def gate_must_not_allow_activation(self) -> ActivationGateRun:
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false in AION-083")
        return self


class ActivationReviewRequest(BaseModel):
    """Review an activation request without activating it."""

    model_config = ConfigDict(extra="forbid")

    activation_request_id: str
    actor_id: str | None = None
    workspace_id: str | None = None
    decision: ActivationReviewDecision
    reviewer_id: str | None = None
    reason: str = Field(min_length=1)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "activation review reason")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ActivationReview(BaseModel):
    """Stored activation review."""

    model_config = ConfigDict(extra="forbid")

    activation_review_id: str = Field(min_length=1)
    trace_id: str | None = None
    activation_request_id: str
    actor_id: str | None = None
    workspace_id: str | None = None
    status: ActivationReviewStatus
    decision: ActivationReviewDecision
    reviewer_id: str | None = None
    reason: str
    approval_request_id: str | None = None
    policy_decision_id: str | None = None
    blocker_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None


class ActivationPlan(BaseModel):
    """Non-executable activation plan."""

    model_config = ConfigDict(extra="forbid")

    activation_plan_id: str = Field(min_length=1)
    trace_id: str | None = None
    activation_request_id: str
    module_slot_id: str
    status: ActivationPlanStatus
    plan_type: ActivationPlanType
    owner_scope: list[str] = Field(min_length=1)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    required_contracts: list[str] = Field(default_factory=list)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    required_sandbox_profiles: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    rollback_plan: list[dict[str, Any]] = Field(default_factory=list)
    blocked: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    executable: bool
    execution_allowed: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    archived_at: datetime | None = None

    @model_validator(mode="after")
    def plan_must_not_execute(self) -> ActivationPlan:
        if self.executable:
            raise ValueError("executable must be false in AION-083")
        if self.execution_allowed:
            raise ValueError("execution_allowed must be false in AION-083")
        return self


class RuntimeRegistrationPreview(BaseModel):
    """Runtime registration preview without runtime mutation."""

    model_config = ConfigDict(extra="forbid")

    registration_preview_id: str = Field(min_length=1)
    trace_id: str | None = None
    activation_request_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    status: str = Field(min_length=1)
    preview_type: RuntimeRegistrationPreviewType
    target_runtime: str = Field(min_length=1)
    target_ref: str | None = None
    route_previews: list[dict[str, Any]] = Field(default_factory=list)
    capability_previews: list[dict[str, Any]] = Field(default_factory=list)
    policy_action_previews: list[dict[str, Any]] = Field(default_factory=list)
    setting_previews: list[dict[str, Any]] = Field(default_factory=list)
    would_register: bool
    registration_allowed: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def preview_must_not_register(self) -> RuntimeRegistrationPreview:
        if self.registration_allowed:
            raise ValueError("registration_allowed must be false in AION-083")
        return self


class ModuleActivationQuery(BaseModel):
    """Query activation gate metadata."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    activation_request_id: str | None = None
    module_slot_id: str | None = None
    extension_package_id: str | None = None
    status: str | None = None
    risk_level: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)


class ModuleActivationQueryResult(BaseModel):
    """Aggregate activation gate query result."""

    model_config = ConfigDict(extra="forbid")

    activation_requests: list[ModuleActivationRequest]
    gate_runs: list[ActivationGateRun]
    blockers: list[ActivationBlocker]
    reviews: list[ActivationReview]
    plans: list[ActivationPlan]
    registration_previews: list[RuntimeRegistrationPreview]
    total_count: int
    constraints: list[str]
    metadata: dict[str, Any]


class ActivationMutationRequest(BaseModel):
    """Shared archive, dismiss, and delete request payload."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "activation mutation reason")
        return value.strip()


class ActivationGateRunRequest(BaseModel):
    """Run the activation gate in safe preview mode."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    mode: str = "dry_run"
    created_by: str | None = None


class ActivationPlanCreateRequest(BaseModel):
    """Create a non-executable activation plan."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    created_by: str | None = None


class RuntimeRegistrationPreviewCreateRequest(BaseModel):
    """Create a runtime registration preview without registration."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    created_by: str | None = None


def _reject_actual_activation(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if lowered in {
                "activate",
                "activated",
                "activation_performed",
                "activation_allowed",
                "execution_allowed",
                "registration_allowed",
                "code_loading_allowed",
                "package_install_allowed",
            } and nested not in (False, None, "", [], {}):
                raise ValueError("activation request must not imply actual activation")
            _reject_actual_activation(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_actual_activation(item)


__all__ = [
    "ActivationBlocker",
    "ActivationGateRun",
    "ActivationGateRunRequest",
    "ActivationMutationRequest",
    "ActivationPlan",
    "ActivationPlanCreateRequest",
    "ActivationReview",
    "ActivationReviewRequest",
    "ModuleActivationCreateRequest",
    "ModuleActivationQuery",
    "ModuleActivationQueryResult",
    "ModuleActivationRequest",
    "RuntimeRegistrationPreview",
    "RuntimeRegistrationPreviewCreateRequest",
]
