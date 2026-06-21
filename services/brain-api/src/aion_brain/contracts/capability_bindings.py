"""Capability binding contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.module_slots import ModuleSlot

CapabilityBindingType = Literal[
    "reasoning",
    "retrieval",
    "memory",
    "evidence",
    "planning",
    "execution",
    "workflow",
    "connector",
    "adapter",
    "visualization",
    "policy",
    "operator",
    "generic",
]
BindingType = Literal["declared", "planned", "preview", "blocked", "generic"]
CapabilityBindingStatus = Literal["proposed", "validated", "blocked", "disabled", "archived"]
TargetRuntime = Literal[
    "module_runtime",
    "capability_runtime",
    "mcp_adapter",
    "sandbox",
    "noop",
    "metadata_only",
]
RiskLevel = Literal["low", "medium", "high", "critical"]
BindingMode = Literal["dry_run", "controlled"]
BindingValidationStatus = Literal["passed", "warning", "failed", "blocked", "dry_run"]
MountPlanStatus = Literal["created", "blocked", "archived"]
MountPlanType = Literal["mount_preview", "validation_only", "future_activation", "generic"]
RouteBindingType = Literal[
    "api_route",
    "sdk_method",
    "cli_command",
    "capability_route",
    "event_route",
    "generic",
]
ConflictType = Literal[
    "duplicate_capability_key",
    "missing_contract",
    "missing_policy_action",
    "missing_setting",
    "sandbox_required",
    "unsupported_runtime",
    "route_registration_disabled",
    "activation_disabled",
    "high_risk_requires_review",
    "generic",
]
BindingConflictStatus = Literal["open", "resolved", "dismissed", "archived"]
ConflictSeverity = Literal["low", "medium", "high", "critical"]

_DOTTED_LOWER_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")
_EXTERNAL_RUNTIME_MARKERS = {"external", "remote", "http", "webhook", "shell", "subprocess"}


class CapabilityBinding(BaseModel):
    """Inactive capability binding metadata."""

    model_config = ConfigDict(extra="forbid")

    capability_binding_id: str = Field(min_length=1)
    trace_id: str | None = None
    module_slot_id: str = Field(min_length=1)
    extension_package_id: str | None = None
    capability_key: str = Field(min_length=1)
    capability_type: CapabilityBindingType
    binding_type: BindingType
    status: CapabilityBindingStatus
    route_key: str | None = None
    target_runtime: TargetRuntime
    target_ref: str | None = None
    risk_level: RiskLevel
    allowed_modes: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    required_contracts: list[str] = Field(default_factory=list)
    requires_approval: bool
    requires_sandbox: bool
    sandbox_profile_id: str | None = None
    dry_run_supported: bool
    controlled_supported: bool
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("capability_key")
    @classmethod
    def capability_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("capability_key must be dotted lowercase text")
        return value

    @field_validator("input_schema", "output_schema", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator(
        "allowed_modes",
        "required_policy_actions",
        "required_settings",
        "required_contracts",
        "constraints",
    )
    @classmethod
    def string_lists_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "capability binding list item")
        return value

    @model_validator(mode="after")
    def binding_must_remain_inactive(self) -> CapabilityBinding:
        if self.controlled_supported and not self.requires_sandbox:
            raise ValueError("controlled_supported requires sandbox in v0.1")
        if self.risk_level in {"high", "critical"} and not self.requires_approval:
            raise ValueError("high and critical bindings require approval")
        if str(self.target_runtime).lower() in _EXTERNAL_RUNTIME_MARKERS:
            raise ValueError("target_runtime cannot be external")
        if bool(self.metadata.get("activate") or self.metadata.get("active")):
            raise ValueError("binding must not activate capability")
        return self


class CapabilityBindingCreateRequest(BaseModel):
    """Request to create inactive capability binding metadata."""

    model_config = ConfigDict(extra="forbid")

    capability_binding_id: str | None = None
    trace_id: str | None = None
    module_slot_id: str
    extension_package_id: str | None = None
    capability_key: str
    capability_type: CapabilityBindingType = "generic"
    binding_type: BindingType = "declared"
    route_key: str | None = None
    target_runtime: TargetRuntime = "metadata_only"
    target_ref: str | None = None
    risk_level: RiskLevel = "medium"
    allowed_modes: list[str] = Field(default_factory=lambda: ["dry_run"])
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    required_contracts: list[str] = Field(default_factory=list)
    requires_approval: bool = True
    requires_sandbox: bool = True
    sandbox_profile_id: str | None = None
    dry_run_supported: bool = True
    controlled_supported: bool = False
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("capability_key")
    @classmethod
    def capability_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("capability_key must be dotted lowercase text")
        return value

    @field_validator("input_schema", "output_schema", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator(
        "allowed_modes",
        "required_policy_actions",
        "required_settings",
        "required_contracts",
        "constraints",
    )
    @classmethod
    def string_lists_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "capability binding list item")
        return value

    @model_validator(mode="after")
    def request_must_remain_inactive(self) -> CapabilityBindingCreateRequest:
        if self.controlled_supported and not self.requires_sandbox:
            raise ValueError("controlled_supported requires sandbox in v0.1")
        if self.risk_level in {"high", "critical"} and not self.requires_approval:
            raise ValueError("high and critical bindings require approval")
        if bool(self.metadata.get("activate") or self.metadata.get("active")):
            raise ValueError("binding must not activate capability")
        return self


class BindingValidationRequest(BaseModel):
    """Request to validate module slots and capability bindings."""

    model_config = ConfigDict(extra="forbid")

    binding_validation_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: BindingMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    module_slot_id: str | None = None
    extension_package_id: str | None = None
    capability_binding_ids: list[str] = Field(default_factory=list)
    include_contract_checks: bool = True
    include_policy_checks: bool = True
    include_setting_checks: bool = True
    include_sandbox_checks: bool = True
    include_security_checks: bool = True
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class BindingValidationRun(BaseModel):
    """Deterministic validation result for inactive module bindings."""

    model_config = ConfigDict(extra="forbid")

    binding_validation_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: BindingValidationStatus
    mode: BindingMode
    owner_scope: list[str] = Field(min_length=1)
    module_slot_id: str | None = None
    extension_package_id: str | None = None
    capability_binding_ids: list[str] = Field(default_factory=list)
    checks: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ModuleMountPlan(BaseModel):
    """Non-executable future mount plan."""

    model_config = ConfigDict(extra="forbid")

    mount_plan_id: str = Field(min_length=1)
    trace_id: str | None = None
    module_slot_id: str = Field(min_length=1)
    extension_package_id: str | None = None
    status: MountPlanStatus
    plan_type: MountPlanType
    owner_scope: list[str] = Field(min_length=1)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    required_contracts: list[str] = Field(default_factory=list)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    required_sandbox_profiles: list[str] = Field(default_factory=list)
    capability_binding_ids: list[str] = Field(default_factory=list)
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
    def plan_must_not_execute(self) -> ModuleMountPlan:
        if self.executable:
            raise ValueError("executable must be false in v0.1")
        if self.execution_allowed:
            raise ValueError("execution_allowed must be false in v0.1")
        return self


class RouteBindingPreview(BaseModel):
    """Preview of route binding metadata without route registration."""

    model_config = ConfigDict(extra="forbid")

    route_preview_id: str = Field(min_length=1)
    trace_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    status: str = Field(min_length=1)
    route_key: str = Field(min_length=1)
    route_type: RouteBindingType
    method: str | None = None
    path: str | None = None
    target_runtime: TargetRuntime
    target_ref: str | None = None
    would_register: bool
    registration_allowed: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @model_validator(mode="after")
    def preview_must_not_register(self) -> RouteBindingPreview:
        if self.registration_allowed:
            raise ValueError("registration_allowed must be false in v0.1")
        return self


class BindingConflict(BaseModel):
    """Deterministic binding conflict record."""

    model_config = ConfigDict(extra="forbid")

    binding_conflict_id: str = Field(min_length=1)
    trace_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    conflict_type: ConflictType
    severity: ConflictSeverity
    status: BindingConflictStatus
    reason: str = Field(min_length=1)
    conflicting_refs: list[str] = Field(default_factory=list)
    recommended_action: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("reason", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "binding conflict text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ModuleBindingQuery(BaseModel):
    """Query module binding registry records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    query: str | None = None
    module_slot_id: str | None = None
    extension_package_id: str | None = None
    status: str | None = None
    capability_type: str | None = None
    risk_level: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)


class ModuleBindingQueryResult(BaseModel):
    """Aggregated module binding query result."""

    model_config = ConfigDict(extra="forbid")

    module_slots: list[ModuleSlot] = Field(default_factory=list)
    capability_bindings: list[CapabilityBinding] = Field(default_factory=list)
    validation_runs: list[BindingValidationRun] = Field(default_factory=list)
    mount_plans: list[ModuleMountPlan] = Field(default_factory=list)
    route_previews: list[RouteBindingPreview] = Field(default_factory=list)
    conflicts: list[BindingConflict] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BindingMutationRequest(BaseModel):
    """Request body for archive, delete, disable, or dismiss operations."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class MountPlanCreateRequest(BaseModel):
    """Request to create a non-executable module mount plan."""

    model_config = ConfigDict(extra="forbid")

    module_slot_id: str
    scope: list[str] | None = None
    created_by: str | None = None


class RoutePreviewCreateRequest(BaseModel):
    """Request to create a route binding preview."""

    model_config = ConfigDict(extra="forbid")

    capability_binding_id: str
    scope: list[str] | None = None
    created_by: str | None = None


__all__ = [
    "BindingConflict",
    "BindingMutationRequest",
    "BindingValidationRequest",
    "BindingValidationRun",
    "CapabilityBinding",
    "CapabilityBindingCreateRequest",
    "ModuleBindingQuery",
    "ModuleBindingQueryResult",
    "ModuleMountPlan",
    "MountPlanCreateRequest",
    "RouteBindingPreview",
    "RoutePreviewCreateRequest",
]
