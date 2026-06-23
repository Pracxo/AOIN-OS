"""Deterministic metadata-only module mock runtime contracts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

ModuleMockProfileStatus = Literal["active", "disabled"]
ModuleMockProfileType = Literal[
    "schema_echo",
    "shape_simulation",
    "knowledge_stub",
    "explanation_stub",
    "grounding_stub",
    "answer_stub",
    "generic",
]
ModuleMockInvocationType = Literal[
    "schema_simulation",
    "dry_run_metadata",
    "mock_knowledge",
    "mock_retrieval",
    "mock_summary",
    "mock_grounding",
    "mock_explanation",
    "mock_answer",
    "generic",
]
ModuleMockMode = Literal["dry_run"]
ModuleMockRunStatus = Literal["passed", "warning", "failed", "blocked", "dry_run"]
ModuleMockOutputType = Literal[
    "synthetic_schema",
    "synthetic_knowledge",
    "synthetic_summary",
    "synthetic_grounding",
    "synthetic_explanation",
    "synthetic_answer",
    "generic",
]
ModuleMockOutputStatus = Literal["created", "warning", "failed"]
ModuleMockFindingType = Literal[
    "missing_binding",
    "missing_mock_profile",
    "invalid_input_shape",
    "invalid_output_shape",
    "unsafe_input",
    "unsafe_output",
    "missing_policy_ref",
    "missing_sandbox_ref",
    "activation_enabled",
    "execution_enabled",
    "external_call_attempt",
    "code_loading_attempt",
    "generic",
]
ModuleMockFindingSeverity = Literal["low", "medium", "high", "critical"]
ModuleMockFindingStatus = Literal["open", "resolved", "dismissed", "archived"]

_DOTTED_LOWER_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")
_EXECUTION_KEYS = {
    "code",
    "command",
    "entrypoint",
    "exec",
    "execute",
    "function_body",
    "import",
    "module_path",
    "package",
    "script",
    "shell",
    "source",
    "subprocess",
}
_REAL_EXECUTION_MARKERS = {
    "activate",
    "activation_allowed",
    "code_loaded",
    "external_calls_made",
    "execution_allowed",
    "load_code",
    "register_route",
}


class ModuleMockProfile(BaseModel):
    """Metadata profile describing deterministic simulation rules only."""

    model_config = ConfigDict(extra="forbid")

    mock_profile_id: str = Field(min_length=1)
    profile_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ModuleMockProfileStatus
    profile_type: ModuleMockProfileType
    owner_scope: list[str] = Field(min_length=1)
    supported_capability_types: list[str] = Field(default_factory=list)
    supported_capability_keys: list[str] = Field(default_factory=list)
    input_schema_hints: dict[str, Any] = Field(default_factory=dict)
    output_schema_hints: dict[str, Any] = Field(default_factory=dict)
    simulation_rules: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("profile_key")
    @classmethod
    def profile_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("profile_key must be dotted lowercase text")
        return value

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be empty")
        reject_hidden_or_secret_text(cleaned, "module mock profile text")
        return cleaned

    @field_validator(
        "supported_capability_types",
        "supported_capability_keys",
        "constraints",
    )
    @classmethod
    def string_lists_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "module mock list item")
        return value

    @field_validator(
        "input_schema_hints",
        "output_schema_hints",
        "metadata",
    )
    @classmethod
    def dict_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @field_validator("simulation_rules")
    @classmethod
    def rules_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        _reject_unsafe_payload(value)
        return value

    @model_validator(mode="after")
    def profile_must_not_execute(self) -> ModuleMockProfile:
        _reject_real_execution(self.model_dump(mode="python"))
        return self


class ModuleMockProfileCreateRequest(BaseModel):
    """Create a deterministic module mock profile."""

    model_config = ConfigDict(extra="forbid")

    mock_profile_id: str | None = None
    profile_key: str
    name: str
    description: str
    profile_type: ModuleMockProfileType = "generic"
    owner_scope: list[str] = Field(min_length=1)
    supported_capability_types: list[str] = Field(default_factory=list)
    supported_capability_keys: list[str] = Field(default_factory=list)
    input_schema_hints: dict[str, Any] = Field(default_factory=dict)
    output_schema_hints: dict[str, Any] = Field(default_factory=dict)
    simulation_rules: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("profile_key")
    @classmethod
    def profile_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("profile_key must be dotted lowercase text")
        return value

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("field cannot be empty")
        reject_hidden_or_secret_text(cleaned, "module mock profile text")
        return cleaned

    @field_validator("input_schema_hints", "output_schema_hints", "metadata")
    @classmethod
    def dict_payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @field_validator("simulation_rules")
    @classmethod
    def rules_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        _reject_unsafe_payload(value)
        return value


class ModuleMockInvocationRequest(BaseModel):
    """Persisted dry-run mock invocation request."""

    model_config = ConfigDict(extra="forbid")

    mock_invocation_request_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mock_profile_id: str | None = None
    extension_package_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str = Field(min_length=1)
    capability_key: str = Field(min_length=1)
    invocation_type: ModuleMockInvocationType
    mode: ModuleMockMode
    owner_scope: list[str] = Field(min_length=1)
    input_payload_hash: str = Field(min_length=1)
    redacted_input_payload: dict[str, Any]
    expected_output_shape: dict[str, Any]
    evidence_refs: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    sandbox_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("capability_key")
    @classmethod
    def capability_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("capability_key must be dotted lowercase text")
        return value

    @field_validator("redacted_input_payload", "expected_output_shape", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ModuleMockInvocationCreateRequest(BaseModel):
    """Create and run a dry-run module mock invocation."""

    model_config = ConfigDict(extra="forbid")

    mock_invocation_request_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mock_profile_id: str | None = None
    extension_package_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str
    capability_key: str
    invocation_type: ModuleMockInvocationType = "schema_simulation"
    mode: ModuleMockMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    expected_output_shape: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    policy_refs: list[str] = Field(default_factory=list)
    sandbox_refs: list[str] = Field(default_factory=list)
    create_notifications: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("capability_binding_id")
    @classmethod
    def capability_binding_id_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("capability_binding_id cannot be empty")
        return value

    @field_validator("capability_key")
    @classmethod
    def capability_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("capability_key must be dotted lowercase text")
        return value

    @field_validator("input_payload", "expected_output_shape", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ModuleMockFinding(BaseModel):
    """A finding created by deterministic mock runtime validation."""

    model_config = ConfigDict(extra="forbid")

    module_mock_finding_id: str = Field(min_length=1)
    trace_id: str | None = None
    module_mock_run_id: str | None = None
    mock_invocation_request_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    finding_type: ModuleMockFindingType
    severity: ModuleMockFindingSeverity
    status: ModuleMockFindingStatus
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
        cleaned = value.strip()
        reject_hidden_or_secret_text(cleaned, "module mock finding text")
        return cleaned

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ModuleMockOutput(BaseModel):
    """Synthetic output produced by the module mock runtime."""

    model_config = ConfigDict(extra="forbid")

    module_mock_output_id: str = Field(min_length=1)
    trace_id: str | None = None
    module_mock_run_id: str = Field(min_length=1)
    capability_binding_id: str = Field(min_length=1)
    capability_key: str = Field(min_length=1)
    output_type: ModuleMockOutputType
    status: ModuleMockOutputStatus
    output_payload_hash: str = Field(min_length=1)
    redacted_output_payload: dict[str, Any]
    output_summary: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("capability_key")
    @classmethod
    def capability_key_must_be_dotted_lowercase(cls, value: str) -> str:
        if not _DOTTED_LOWER_RE.match(value):
            raise ValueError("capability_key must be dotted lowercase text")
        return value

    @field_validator("redacted_output_payload", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @field_validator("output_summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "module mock output summary")
        return value.strip()

    @model_validator(mode="after")
    def output_must_be_synthetic(self) -> ModuleMockOutput:
        if self.redacted_output_payload.get("synthetic") is not True:
            raise ValueError("module mock output must include synthetic=true")
        return self


class ModuleMockRun(BaseModel):
    """Dry-run module mock invocation result."""

    model_config = ConfigDict(extra="forbid")

    module_mock_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    mock_invocation_request_id: str = Field(min_length=1)
    mock_profile_id: str | None = None
    extension_package_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str = Field(min_length=1)
    status: ModuleMockRunStatus
    mode: ModuleMockMode
    owner_scope: list[str] = Field(min_length=1)
    checks_run: list[str] = Field(default_factory=list)
    output: ModuleMockOutput | None = None
    findings: list[ModuleMockFinding] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    schema_valid: bool
    policy_valid: bool
    sandbox_valid: bool
    activation_allowed: bool
    execution_allowed: bool
    external_calls_made: bool
    code_loaded: bool
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def run_must_not_execute(self) -> ModuleMockRun:
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false in AION-085")
        if self.execution_allowed:
            raise ValueError("execution_allowed must be false in AION-085")
        if self.external_calls_made:
            raise ValueError("external_calls_made must be false in AION-085")
        if self.code_loaded:
            raise ValueError("code_loaded must be false in AION-085")
        return self


class ModuleMockQuery(BaseModel):
    """Query module mock runtime records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    mock_profile_id: str | None = None
    module_slot_id: str | None = None
    capability_binding_id: str | None = None
    status: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


class ModuleMockQueryResult(BaseModel):
    """Aggregated query result across module mock records."""

    model_config = ConfigDict(extra="forbid")

    profiles: list[ModuleMockProfile]
    requests: list[ModuleMockInvocationRequest]
    runs: list[ModuleMockRun]
    outputs: list[ModuleMockOutput]
    findings: list[ModuleMockFinding]
    total_count: int
    constraints: list[str]
    metadata: dict[str, Any]


class ModuleMockProfileSeedRequest(BaseModel):
    """Seed default mock profiles."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    dry_run: bool = True
    created_by: str | None = None


class ModuleMockFindingDismissRequest(BaseModel):
    """Dismiss a module mock finding without changing run status."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "module mock finding dismiss reason")
        return value.strip()


def _reject_unsafe_payload(value: object) -> None:
    reject_secret_like_payload(value)
    _reject_executable_payload(value)
    _reject_real_execution(value)


def _reject_executable_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _EXECUTION_KEYS:
                raise ValueError("module mock payload must not contain executable fields")
            _reject_executable_payload(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_executable_payload(item)


def _reject_real_execution(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in _REAL_EXECUTION_MARKERS and nested not in (False, None, "", [], {}):
                raise ValueError("module mock payload must not imply real execution")
            _reject_real_execution(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_real_execution(item)


__all__ = [
    "ModuleMockFinding",
    "ModuleMockFindingDismissRequest",
    "ModuleMockInvocationCreateRequest",
    "ModuleMockInvocationRequest",
    "ModuleMockOutput",
    "ModuleMockProfile",
    "ModuleMockProfileCreateRequest",
    "ModuleMockProfileSeedRequest",
    "ModuleMockQuery",
    "ModuleMockQueryResult",
    "ModuleMockRun",
]
