"""Extension Registry contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

PackageType = Literal[
    "module",
    "adapter",
    "connector",
    "capability_pack",
    "policy_pack",
    "prompt_pack",
    "visualization_pack",
    "generic",
]
ExtensionSourceType = Literal[
    "local_manifest",
    "local_directory",
    "manual",
    "test_fixture",
    "generated_metadata",
]
ExtensionPackageStatus = Literal[
    "proposed",
    "validated",
    "incompatible",
    "review_required",
    "accepted",
    "rejected",
    "archived",
    "deleted",
]
ExtensionCompatibilityStatus = Literal["unknown", "passed", "warning", "failed", "blocked"]
ExtensionReviewStatus = Literal["not_reviewed", "pending", "approved", "rejected", "blocked"]
ExtensionCapabilityType = Literal[
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
ExtensionCapabilityStatus = Literal["declared", "accepted", "rejected", "blocked"]
ExtensionDependencyType = Literal[
    "aion_contract",
    "aion_capability",
    "aion_feature_flag",
    "aion_policy_action",
    "aion_setting",
    "python_package_metadata",
    "local_service",
    "generic",
]
ExtensionDependencySource = Literal["manifest", "inferred", "manual"]
ExtensionDependencyStatus = Literal["declared", "available", "missing", "blocked", "warning"]
ExtensionMode = Literal["dry_run", "controlled"]
ExtensionIntakeStatus = Literal["completed", "dry_run", "warning", "failed", "blocked_by_policy"]
ExtensionReviewDecision = Literal[
    "approve",
    "reject",
    "block",
    "request_changes",
    "request_approval",
]
ExtensionInstallPlanType = Literal[
    "intake_only",
    "review_only",
    "compatibility_only",
    "future_install",
    "generic",
]
ExtensionInstallPlanStatus = Literal["planned", "blocked", "archived"]
RiskLevel = Literal["low", "medium", "high", "critical"]

_DOTTED_LOWER_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")
_POLICY_ACTION_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")
_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "payment",
    "procurement",
    "human_resources",
}
_EXECUTABLE_KEYS = {
    "binary",
    "code",
    "code_payload",
    "dockerfile",
    "entrypoint",
    "executable",
    "hook",
    "package_bytes",
    "script",
    "source_code",
    "subprocess",
}


class ExtensionManifest(BaseModel):
    """Metadata-only manifest for a future AION extension."""

    model_config = ConfigDict(extra="forbid")

    extension_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    version: str = Field(min_length=1)
    package_type: PackageType
    aion_min_version: str | None = None
    aion_max_version: str | None = None
    declared_capabilities: list[dict[str, Any]] = Field(default_factory=list)
    declared_contracts: list[dict[str, Any]] = Field(default_factory=list)
    declared_dependencies: list[dict[str, Any]] = Field(default_factory=list)
    declared_policy_actions: list[str] = Field(default_factory=list)
    declared_settings: list[dict[str, Any]] = Field(default_factory=list)
    declared_routes: list[dict[str, Any]] = Field(default_factory=list)
    declared_events: list[str] = Field(default_factory=list)
    declared_resources: list[str] = Field(default_factory=list)
    sandbox_requirements: dict[str, Any] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("extension_key")
    @classmethod
    def extension_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("extension_key must be dotted lowercase text")
        _reject_domain_text(value)
        return value

    @field_validator("name", "description", "version")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be empty")
        reject_hidden_or_secret_text(cleaned, "extension manifest text")
        _reject_domain_text(cleaned)
        return cleaned

    @field_validator("declared_policy_actions")
    @classmethod
    def policy_actions_must_be_dotted_lowercase(cls, value: list[str]) -> list[str]:
        for action in value:
            if not _POLICY_ACTION_RE.match(action):
                raise ValueError("declared_policy_actions must be dotted lowercase")
        return value

    @field_validator(
        "declared_capabilities",
        "declared_contracts",
        "declared_dependencies",
        "declared_settings",
        "declared_routes",
    )
    @classmethod
    def list_payloads_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            _reject_unsafe_payload(item)
        return value

    @field_validator("sandbox_requirements", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @field_validator("permissions", "declared_events", "declared_resources")
    @classmethod
    def text_lists_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "extension manifest list item")
            _reject_domain_text(item)
        return value

    @model_validator(mode="after")
    def manifest_must_be_metadata_only(self) -> ExtensionManifest:
        payload = self.model_dump(mode="python")
        if _requests_full_autonomy(payload):
            raise ValueError("manifest must not request full autonomy")
        if _requests_external_execution(payload):
            raise ValueError("manifest must not request external execution by default")
        if _requests_raw_secret_access(payload):
            raise ValueError("manifest must not request raw secret access")
        return self


class ExtensionPackage(BaseModel):
    """Stored extension package metadata. This is not installation or activation."""

    model_config = ConfigDict(extra="forbid")

    extension_package_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    extension_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: ExtensionPackageStatus
    package_type: PackageType
    source_type: ExtensionSourceType
    source_ref: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    manifest_hash: str = Field(min_length=1)
    manifest: ExtensionManifest
    declared_capabilities: list[dict[str, Any]] = Field(default_factory=list)
    declared_contracts: list[dict[str, Any]] = Field(default_factory=list)
    declared_dependencies: list[dict[str, Any]] = Field(default_factory=list)
    declared_policy_actions: list[str] = Field(default_factory=list)
    declared_settings: list[dict[str, Any]] = Field(default_factory=list)
    declared_routes: list[dict[str, Any]] = Field(default_factory=list)
    declared_events: list[str] = Field(default_factory=list)
    declared_resources: list[str] = Field(default_factory=list)
    compatibility_status: ExtensionCompatibilityStatus
    review_status: ExtensionReviewStatus
    install_plan_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    reviewed_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ExtensionCapabilityDeclaration(BaseModel):
    """Declared capability metadata. This does not register an active capability."""

    model_config = ConfigDict(extra="forbid")

    capability_declaration_id: str = Field(min_length=1)
    extension_package_id: str = Field(min_length=1)
    capability_key: str = Field(min_length=1)
    capability_type: ExtensionCapabilityType
    status: ExtensionCapabilityStatus
    risk_level: RiskLevel
    requires_policy: bool
    requires_approval: bool
    requires_sandbox: bool
    dry_run_supported: bool
    controlled_supported: bool
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("capability_key")
    @classmethod
    def capability_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("capability_key must be dotted lowercase text")
        _reject_domain_text(value)
        return value

    @field_validator("input_schema", "output_schema", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ExtensionDependencyDeclaration(BaseModel):
    """Declared dependency metadata. This never downloads dependencies."""

    model_config = ConfigDict(extra="forbid")

    dependency_declaration_id: str = Field(min_length=1)
    extension_package_id: str = Field(min_length=1)
    dependency_key: str = Field(min_length=1)
    dependency_type: ExtensionDependencyType
    version_constraint: str | None = None
    required: bool
    status: ExtensionDependencyStatus
    source: ExtensionDependencySource
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("dependency_key")
    @classmethod
    def dependency_key_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "dependency_key")
        _reject_domain_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        if _requires_external_download(value):
            raise ValueError("dependency must not require external download")
        return value


class ExtensionIntakeRequest(BaseModel):
    """Request to validate or record a local extension manifest."""

    model_config = ConfigDict(extra="forbid")

    extension_intake_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: ExtensionMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    manifest: ExtensionManifest
    source_type: ExtensionSourceType = "manual"
    source_ref: str | None = None
    run_compatibility: bool = True
    create_install_plan: bool = True
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ExtensionIntakeRun(BaseModel):
    """Result of a manifest intake pass."""

    model_config = ConfigDict(extra="forbid")

    extension_intake_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: ExtensionIntakeStatus
    mode: ExtensionMode
    owner_scope: list[str] = Field(min_length=1)
    extension_package: ExtensionPackage | None = None
    manifest_hash: str = Field(min_length=1)
    validation_status: str = Field(min_length=1)
    compatibility_status: ExtensionCompatibilityStatus
    review_required: bool
    install_plan_created: bool
    findings: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ExtensionReviewRequest(BaseModel):
    """Request to record an extension review decision."""

    model_config = ConfigDict(extra="forbid")

    extension_package_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    decision: ExtensionReviewDecision
    reviewer_id: str | None = None
    reason: str = Field(min_length=1)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "reason")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ExtensionReview(BaseModel):
    """Recorded review decision. Review does not install an extension."""

    model_config = ConfigDict(extra="forbid")

    extension_review_id: str = Field(min_length=1)
    extension_package_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: str = Field(min_length=1)
    decision: ExtensionReviewDecision
    reviewer_id: str | None = None
    reason: str = Field(min_length=1)
    approval_request_id: str | None = None
    policy_decision_id: str | None = None
    blocker_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None


class ExtensionInstallPlan(BaseModel):
    """Future install plan. It never installs or executes in v0.1."""

    model_config = ConfigDict(extra="forbid")

    install_plan_id: str = Field(min_length=1)
    extension_package_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: ExtensionInstallPlanStatus
    plan_type: ExtensionInstallPlanType
    owner_scope: list[str] = Field(min_length=1)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    required_settings: list[str] = Field(default_factory=list)
    required_policy_actions: list[str] = Field(default_factory=list)
    required_contracts: list[str] = Field(default_factory=list)
    required_sandbox_profiles: list[str] = Field(default_factory=list)
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
    def plan_must_not_execute(self) -> ExtensionInstallPlan:
        if self.executable:
            raise ValueError("executable must be false in v0.1")
        if self.execution_allowed:
            raise ValueError("execution_allowed must be false in v0.1")
        return self


class ExtensionQuery(BaseModel):
    """Query extension registry records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    query: str | None = None
    status: str | None = None
    package_type: str | None = None
    compatibility_status: str | None = None
    review_status: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)


class ExtensionQueryResult(BaseModel):
    """Aggregated extension query result."""

    model_config = ConfigDict(extra="forbid")

    packages: list[ExtensionPackage] = Field(default_factory=list)
    compatibility_runs: list[Any] = Field(default_factory=list)
    reviews: list[ExtensionReview] = Field(default_factory=list)
    install_plans: list[ExtensionInstallPlan] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtensionArchiveRequest(BaseModel):
    """Request to archive or soft-delete an extension package."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class ExtensionInstallPlanCreateRequest(BaseModel):
    """Request to create a future install plan."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] | None = None
    created_by: str | None = None


def _reject_unsafe_payload(value: object) -> None:
    reject_secret_like_payload(value)
    _reject_executable_payload(value)
    if _contains_domain_term(value):
        raise ValueError("extension payload must not contain domain-specific logic")


def _reject_executable_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _EXECUTABLE_KEYS:
                raise ValueError("extension manifest must not include executable code payloads")
            _reject_executable_payload(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_executable_payload(item)


def _reject_domain_text(value: str) -> None:
    lowered = value.lower().replace("-", "_")
    if any(term in lowered for term in _BANNED_DOMAIN_TERMS):
        raise ValueError("extension manifest must not contain domain-specific terms")


def _contains_domain_term(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_domain_term(key) or _contains_domain_term(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_domain_term(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(term in lowered for term in _BANNED_DOMAIN_TERMS)
    return False


def _requests_full_autonomy(value: object) -> bool:
    return _has_flag_or_text(value, ("full_autonomy", "autonomy.full", "unrestricted_autonomy"))


def _requests_external_execution(value: object) -> bool:
    return _has_flag_or_text(
        value,
        ("external_execution", "external_exec", "external_source", "remote_execution"),
    )


def _requests_raw_secret_access(value: object) -> bool:
    return _has_flag_or_text(value, ("raw_secret", "raw_secrets", "secret_raw_access"))


def _requires_external_download(value: object) -> bool:
    return _has_flag_or_text(
        value,
        ("download_url", "external_download", "pip_install", "npm_install"),
    )


def _has_flag_or_text(value: object, markers: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in markers and nested not in (False, None, "", [], {}):
                return True
            if _has_flag_or_text(nested, markers):
                return True
    elif isinstance(value, list):
        return any(_has_flag_or_text(item, markers) for item in value)
    elif isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(marker in lowered for marker in markers)
    return False


__all__ = [
    "ExtensionArchiveRequest",
    "ExtensionCapabilityDeclaration",
    "ExtensionDependencyDeclaration",
    "ExtensionInstallPlan",
    "ExtensionInstallPlanCreateRequest",
    "ExtensionIntakeRequest",
    "ExtensionIntakeRun",
    "ExtensionManifest",
    "ExtensionPackage",
    "ExtensionQuery",
    "ExtensionQueryResult",
    "ExtensionReview",
    "ExtensionReviewRequest",
]
