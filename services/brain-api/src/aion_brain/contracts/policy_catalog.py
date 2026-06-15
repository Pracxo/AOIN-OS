"""Policy catalog, permission matrix, and policy test contracts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.secrets import (
    reject_secret_like_keys,
    reject_secret_like_values,
)

CatalogStatus = Literal["active", "disabled"]
PolicyRiskLevel = Literal["low", "medium", "high", "critical"]
PolicyTestRunStatus = Literal["passed", "failed", "warning"]
PolicyCoverageStatus = Literal["passed", "warning", "failed"]
PolicyBundleType = Literal["catalog", "test", "full"]
PolicyBundleStatus = Literal["created", "exported"]

_DOTTED_LOWER_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
_DOMAIN_PREFIXES = {
    "finance",
    "trading",
    "it",
    "legal",
    "healthcare",
    "hr",
    "procurement",
    "medical",
    "payments",
}


class PolicyActionCatalogEntry(BaseModel):
    """One generic AION policy action definition."""

    model_config = ConfigDict(extra="forbid")

    policy_action_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    category: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    default_risk_level: PolicyRiskLevel
    required_permission: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: CatalogStatus = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("action_type")
    @classmethod
    def action_type_must_be_generic(cls, value: str) -> str:
        _validate_dotted_lower(value, "action_type")
        _reject_domain_prefix(value, "action_type")
        return value

    @field_validator("required_permission")
    @classmethod
    def required_permission_must_be_generic(cls, value: str) -> str:
        _validate_dotted_lower(value, "required_permission")
        _reject_domain_prefix(value, "required_permission")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_payload(value)
        return value


class PermissionCatalogEntry(BaseModel):
    """One generic permission definition."""

    model_config = ConfigDict(extra="forbid")

    permission_id: str = Field(min_length=1)
    permission: str = Field(min_length=1)
    category: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    action_pattern: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: CatalogStatus = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("permission")
    @classmethod
    def permission_must_be_generic(cls, value: str) -> str:
        _validate_dotted_lower(value, "permission")
        _reject_domain_prefix(value, "permission")
        return value

    @field_validator("action_pattern")
    @classmethod
    def action_pattern_must_be_generic(cls, value: str) -> str:
        if value != "*":
            _validate_dotted_lower(value.replace("*", "read"), "action_pattern")
            _reject_domain_prefix(value, "action_pattern")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_payload(value)
        return value


class RoleTemplate(BaseModel):
    """Reusable generic role template."""

    model_config = ConfigDict(extra="forbid")

    role_template_id: str = Field(min_length=1)
    role_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: CatalogStatus = "active"
    permissions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("permissions")
    @classmethod
    def permissions_must_be_generic(cls, value: list[str]) -> list[str]:
        for permission in value:
            _validate_dotted_lower(permission, "permission")
            _reject_domain_prefix(permission, "permission")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_payload(value)
        return value


class PolicySimulationRequest(BaseModel):
    """Request to simulate one policy decision without executing an action."""

    model_config = ConfigDict(extra="forbid")

    simulation_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str | None = None
    risk_level: PolicyRiskLevel = "medium"
    approval_present: bool = False
    requested_permissions: list[str] = Field(default_factory=list)
    security_scope: list[str] = Field(min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("action_type")
    @classmethod
    def action_type_must_be_generic(cls, value: str) -> str:
        _validate_dotted_lower(value, "action_type")
        _reject_domain_prefix(value, "action_type")
        return value

    @field_validator("context", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_payload(value)
        return value


class PolicySimulationResult(BaseModel):
    """Persisted simulation result."""

    model_config = ConfigDict(extra="forbid")

    simulation_id: str
    request: PolicySimulationRequest
    decision: PolicyDecision
    explanation: dict[str, Any]
    created_at: datetime


class PolicyTestCase(BaseModel):
    """One deterministic policy test case."""

    model_config = ConfigDict(extra="forbid")

    policy_test_case_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: CatalogStatus = "active"
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    input: dict[str, Any]
    expected: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("action_type")
    @classmethod
    def action_type_must_be_generic(cls, value: str) -> str:
        _validate_dotted_lower(value, "action_type")
        _reject_domain_prefix(value, "action_type")
        return value

    @field_validator("tags")
    @classmethod
    def tags_must_be_generic(cls, value: list[str]) -> list[str]:
        for tag in value:
            if not tag.strip():
                raise ValueError("tags cannot be empty")
            _reject_domain_prefix(tag.lower().replace("-", "."), "tag")
        return value

    @field_validator("input", "expected", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_payload(value)
        return value

    @model_validator(mode="after")
    def expected_must_assert_decision(self) -> PolicyTestCase:
        if "allow" not in self.expected and "approval_required" not in self.expected:
            raise ValueError("expected must include allow or approval_required")
        return self


class PolicyTestRunRequest(BaseModel):
    """Request to run deterministic policy tests."""

    model_config = ConfigDict(extra="forbid")

    policy_test_run_id: str | None = None
    test_case_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    include_disabled: bool = False
    dry_run: bool = True
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_payload(value)
        return value


class PolicyTestRun(BaseModel):
    """Policy test run result."""

    model_config = ConfigDict(extra="forbid")

    policy_test_run_id: str
    status: PolicyTestRunStatus
    total_count: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    results: list[dict[str, Any]]
    report: dict[str, Any]
    created_by: str | None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class PolicyCoverageReport(BaseModel):
    """Policy catalog coverage report."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    action_count: int = Field(ge=0)
    catalogued_action_count: int = Field(ge=0)
    uncatalogued_actions: list[str]
    permission_count: int = Field(ge=0)
    role_template_count: int = Field(ge=0)
    test_case_count: int = Field(ge=0)
    untested_actions: list[str]
    duplicate_permissions: list[str]
    domain_specific_violations: list[str]
    status: PolicyCoverageStatus
    generated_at: datetime


class PolicyBundleExportRequest(BaseModel):
    """Request to export policy governance bundle metadata."""

    model_config = ConfigDict(extra="forbid")

    bundle_type: PolicyBundleType = "catalog"
    include_rego: bool = True
    include_catalog: bool = True
    include_permissions: bool = True
    include_role_templates: bool = True
    include_tests: bool = True
    created_by: str | None = None


class PolicyBundleRecord(BaseModel):
    """Persisted policy bundle export."""

    model_config = ConfigDict(extra="forbid")

    policy_bundle_id: str
    bundle_type: PolicyBundleType
    version: str
    content_hash: str
    content: dict[str, Any]
    status: PolicyBundleStatus
    created_by: str | None
    created_at: datetime | None = None


class OPAStatus(BaseModel):
    """OPA adapter status."""

    model_config = ConfigDict(extra="forbid")

    available: bool
    url: str | None
    policy_loaded: bool
    decision_path: str
    reason: str | None
    checked_at: datetime


def is_domain_specific(value: str) -> bool:
    """Return whether a policy or permission string has a banned domain prefix."""
    prefix = value.lower().replace("-", ".").split(".", 1)[0]
    return prefix in _DOMAIN_PREFIXES


def _validate_dotted_lower(value: str, field_name: str) -> None:
    if not _DOTTED_LOWER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be dotted lowercase text")


def _reject_domain_prefix(value: str, field_name: str) -> None:
    if is_domain_specific(value):
        raise ValueError(f"{field_name} must not use domain-specific prefixes")


def _reject_secret_payload(value: dict[str, Any]) -> None:
    reject_secret_like_keys(value)
    reject_secret_like_values(value)


__all__ = [
    "OPAStatus",
    "PermissionCatalogEntry",
    "PolicyActionCatalogEntry",
    "PolicyBundleExportRequest",
    "PolicyBundleRecord",
    "PolicyCoverageReport",
    "PolicySimulationRequest",
    "PolicySimulationResult",
    "PolicyTestCase",
    "PolicyTestRun",
    "PolicyTestRunRequest",
    "RoleTemplate",
    "is_domain_specific",
]
