"""Capability conformance contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.readiness import ReadinessAssessment

ConformanceProfileStatus = Literal["active", "disabled"]
ConformanceProfileType = Literal[
    "extension",
    "module_slot",
    "capability_binding",
    "route_preview",
    "sandbox",
    "generic",
]
ConformanceCheckName = Literal[
    "manifest_valid",
    "extension_reviewed",
    "contract_compatible",
    "required_contracts_present",
    "required_policy_actions_present",
    "required_settings_present",
    "sandbox_declared",
    "sandbox_profile_valid",
    "input_schema_valid",
    "output_schema_valid",
    "mock_invocation_valid",
    "route_preview_safe",
    "no_activation_enabled",
    "no_code_loading",
    "no_external_source",
    "no_secret_schema",
    "no_domain_logic",
]
CapabilityTestVectorStatus = Literal["active", "disabled"]
CapabilityTestVectorType = Literal[
    "schema_only",
    "mock_input",
    "boundary_case",
    "negative_case",
    "policy_case",
    "sandbox_case",
    "generic",
]
MockInvocationStatus = Literal["passed", "warning", "failed", "blocked"]
MockInvocationType = Literal[
    "schema_simulation",
    "negative_case",
    "policy_case",
    "sandbox_case",
    "dry_run_metadata",
    "generic",
]
ConformanceMode = Literal["dry_run", "controlled"]
ConformanceRunStatus = Literal["passed", "warning", "failed", "blocked", "dry_run"]
ConformanceFindingType = Literal[
    "missing_contract",
    "missing_policy_action",
    "missing_setting",
    "missing_sandbox",
    "invalid_input_schema",
    "invalid_output_schema",
    "invalid_test_vector",
    "mock_invocation_failed",
    "unsafe_metadata",
    "activation_enabled",
    "code_loading_enabled",
    "external_source_enabled",
    "route_registration_enabled",
    "domain_logic_detected",
    "generic",
]
ConformanceFindingStatus = Literal["open", "resolved", "dismissed", "archived"]
ConformanceSeverity = Literal["low", "medium", "high", "critical"]

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
_EXECUTION_KEYS = {
    "code",
    "command",
    "exec",
    "execute",
    "function_body",
    "import",
    "script",
    "shell",
    "subprocess",
}


class ConformanceProfile(BaseModel):
    """Metadata-only conformance profile."""

    model_config = ConfigDict(extra="forbid")

    conformance_profile_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ConformanceProfileStatus
    profile_type: ConformanceProfileType
    owner_scope: list[str] = Field(min_length=1)
    required_checks: list[ConformanceCheckName] = Field(default_factory=list)
    optional_checks: list[ConformanceCheckName] = Field(default_factory=list)
    minimum_score: float = Field(ge=0.0, le=1.0)
    fail_on_critical: bool
    fail_on_missing_contract: bool
    fail_on_missing_policy_action: bool
    fail_on_missing_sandbox: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _safe_text(value, "conformance profile text")
        _reject_domain_term(value)
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


class ConformanceProfileCreateRequest(BaseModel):
    """Request to create a metadata-only conformance profile."""

    model_config = ConfigDict(extra="forbid")

    conformance_profile_id: str | None = None
    name: str
    description: str
    profile_type: ConformanceProfileType = "generic"
    owner_scope: list[str] = Field(default_factory=list)
    required_checks: list[ConformanceCheckName] = Field(default_factory=list)
    optional_checks: list[ConformanceCheckName] = Field(default_factory=list)
    minimum_score: float = Field(default=0.8, ge=0.0, le=1.0)
    fail_on_critical: bool = True
    fail_on_missing_contract: bool = True
    fail_on_missing_policy_action: bool = True
    fail_on_missing_sandbox: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _safe_text(value, "conformance profile text")
        _reject_domain_term(value)
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


class CapabilityTestVector(BaseModel):
    """Metadata test vector for schema and mock simulation."""

    model_config = ConfigDict(extra="forbid")

    test_vector_id: str = Field(min_length=1)
    trace_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    extension_package_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: CapabilityTestVectorStatus
    vector_type: CapabilityTestVectorType
    input_payload: dict[str, Any] = Field(default_factory=dict)
    expected_output_shape: dict[str, Any] = Field(default_factory=dict)
    expected_constraints: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _safe_text(value, "test vector text")
        return value.strip()

    @field_validator("input_payload", "expected_output_shape", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value

    @field_validator("expected_constraints")
    @classmethod
    def constraints_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            _safe_text(item, "test vector constraint")
        return value


class CapabilityTestVectorCreateRequest(BaseModel):
    """Request to create a metadata test vector."""

    model_config = ConfigDict(extra="forbid")

    test_vector_id: str | None = None
    trace_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    extension_package_id: str | None = None
    name: str
    description: str
    vector_type: CapabilityTestVectorType = "generic"
    input_payload: dict[str, Any] = Field(default_factory=dict)
    expected_output_shape: dict[str, Any] = Field(default_factory=dict)
    expected_constraints: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _safe_text(value, "test vector text")
        return value.strip()

    @field_validator("input_payload", "expected_output_shape", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


class MockInvocationRecord(BaseModel):
    """Record of simulated schema-only invocation."""

    model_config = ConfigDict(extra="forbid")

    mock_invocation_id: str = Field(min_length=1)
    trace_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    extension_package_id: str | None = None
    test_vector_id: str | None = None
    status: MockInvocationStatus
    invocation_type: MockInvocationType
    input_payload_hash: str = Field(min_length=1)
    redacted_input_payload: dict[str, Any]
    simulated_output: dict[str, Any]
    schema_valid: bool
    policy_valid: bool
    sandbox_valid: bool
    findings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("redacted_input_payload", "simulated_output", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


class ConformanceFinding(BaseModel):
    """Conformance-owned finding record."""

    model_config = ConfigDict(extra="forbid")

    conformance_finding_id: str = Field(min_length=1)
    trace_id: str | None = None
    conformance_run_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    extension_package_id: str | None = None
    finding_type: ConformanceFindingType
    severity: ConformanceSeverity
    status: ConformanceFindingStatus
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("title", "description", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _safe_text(value, "conformance finding text")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value


class ConformanceRunRequest(BaseModel):
    """Request to run deterministic conformance checks."""

    model_config = ConfigDict(extra="forbid")

    conformance_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: ConformanceMode = "dry_run"
    owner_scope: list[str] = Field(default_factory=list)
    conformance_profile_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    extension_package_id: str | None = None
    test_vector_ids: list[str] = Field(default_factory=list)
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_payload(value)
        return value

    @model_validator(mode="after")
    def target_required(self) -> ConformanceRunRequest:
        if not (self.module_slot_id or self.capability_binding_id or self.extension_package_id):
            raise ValueError("at least one conformance target id is required")
        return self


class ConformanceRun(BaseModel):
    """Deterministic conformance run result."""

    model_config = ConfigDict(extra="forbid")

    conformance_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: ConformanceRunStatus
    mode: ConformanceMode
    owner_scope: list[str] = Field(min_length=1)
    conformance_profile_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    extension_package_id: str | None = None
    checks_run: list[str] = Field(default_factory=list)
    test_vector_ids: list[str] = Field(default_factory=list)
    mock_invocations: list[MockInvocationRecord] = Field(default_factory=list)
    findings: list[ConformanceFinding] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ConformanceQuery(BaseModel):
    """Query conformance-owned records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    extension_package_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    status: str | None = None
    profile_type: str | None = None
    include_disabled: bool = False
    limit: int = Field(default=50, ge=1, le=500)


class ConformanceQueryResult(BaseModel):
    """Query result across conformance record types."""

    model_config = ConfigDict(extra="forbid")

    profiles: list[ConformanceProfile]
    test_vectors: list[CapabilityTestVector]
    runs: list[ConformanceRun]
    findings: list[ConformanceFinding]
    readiness_assessments: list[ReadinessAssessment]
    total_count: int
    constraints: list[str]
    metadata: dict[str, Any]


def _safe_text(value: str, field_name: str) -> None:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    reject_hidden_or_secret_text(cleaned, field_name)


def _reject_payload(value: object) -> None:
    reject_secret_like_payload(value)
    _reject_execution_payload(value)
    if _contains_domain_term(value):
        raise ValueError("conformance payload must not contain domain-specific logic")


def _reject_execution_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _EXECUTION_KEYS:
                raise ValueError("conformance payload must not contain executable code fields")
            _reject_execution_payload(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_execution_payload(item)


def _reject_domain_term(value: str) -> None:
    if _contains_domain_term(value):
        raise ValueError("conformance must not contain domain-specific terms")


def _contains_domain_term(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_domain_term(key) or _contains_domain_term(item) for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_domain_term(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(term in lowered for term in _BANNED_DOMAIN_TERMS)
    return False


__all__ = [
    "CapabilityTestVector",
    "CapabilityTestVectorCreateRequest",
    "ConformanceFinding",
    "ConformanceProfile",
    "ConformanceProfileCreateRequest",
    "ConformanceQuery",
    "ConformanceQueryResult",
    "ConformanceRun",
    "ConformanceRunRequest",
    "MockInvocationRecord",
]
