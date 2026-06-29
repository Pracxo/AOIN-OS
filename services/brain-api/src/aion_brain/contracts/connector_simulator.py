"""Synthetic connector dry-run simulator contracts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ConnectorSimulationStatus = Literal["passed", "blocked", "warning", "failed"]
ConnectorSimulationType = Literal["dry_run"]
ConnectorSimulatorFindingType = Literal[
    "unsafe_request_shape",
    "unsafe_response_shape",
    "secret_detected",
    "raw_prompt_detected",
    "hidden_reasoning_detected",
    "external_url_detected",
    "credential_field_detected",
    "token_field_detected",
    "connector_runtime_disabled",
    "external_calls_disabled",
    "untrusted_ingress",
    "missing_policy_action",
    "sandbox_required",
    "generic",
]
ConnectorSimulatorFindingSeverity = Literal["low", "medium", "high", "critical"]
ConnectorSimulatorFindingStatus = Literal["open", "resolved"]

_DOTTED_LOWERCASE_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9]+)*$")
_URL_RE = re.compile(r"\bhttps?://", re.IGNORECASE)
_SENSITIVE_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "secret",
}
_TOKEN_KEY_PARTS = {"access_token", "refresh_token", "id_token", "token"}
_URL_KEY_PARTS = {"endpoint", "url", "uri", "host", "dns"}
_RAW_PROMPT_KEY_PARTS = {"raw_prompt", "prompt_text", "system_prompt", "developer_prompt"}
_HIDDEN_REASONING_KEY_PARTS = {
    "chain_of_thought",
    "hidden_reasoning",
    "private_reasoning",
}
_SECRET_VALUE_MARKERS = (
    "sk-",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
    "bearer ",
    "basic ",
)
_RAW_PROMPT_VALUE_MARKERS = (
    "raw prompt",
    "raw_prompt",
    "system prompt:",
    "developer prompt:",
)
_HIDDEN_REASONING_VALUE_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
)


class ConnectorSimulationRequest(BaseModel):
    """Request one deterministic synthetic connector dry run."""

    model_config = ConfigDict(extra="forbid")

    connector_simulation_request_id: str | None = None
    trace_id: str | None = None
    connector_key: str
    owner_scope: list[str] = Field(min_length=1)
    simulation_type: ConnectorSimulationType = "dry_run"
    request_shape: dict[str, Any] = Field(default_factory=dict)
    expected_response_shape: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        cleaned = value.strip()
        if not _DOTTED_LOWERCASE_RE.match(cleaned):
            raise ValueError("connector_key must be dotted lowercase text")
        return cleaned

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("simulation_type")
    @classmethod
    def simulation_type_must_be_dry_run(cls, value: str) -> str:
        if value != "dry_run":
            raise ValueError("simulation_type must be dry_run")
        return value

    @field_validator("request_shape", "metadata")
    @classmethod
    def request_payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @field_validator("expected_response_shape")
    @classmethod
    def expected_response_must_not_use_endpoints_or_secrets(
        cls, value: dict[str, Any]
    ) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ConnectorSimulationResult(BaseModel):
    """Synthetic connector dry-run result. It is never trusted execution data."""

    model_config = ConfigDict(extra="forbid")

    connector_simulation_result_id: str
    trace_id: str | None = None
    connector_key: str
    status: ConnectorSimulationStatus
    simulation_type: ConnectorSimulationType
    synthetic: bool
    trusted: bool
    external_calls_made: bool
    credentials_used: bool
    tokens_used: bool
    connector_runtime_enabled: bool
    request_hash: str
    response_hash: str
    redacted_request_shape: dict[str, Any] = Field(default_factory=dict)
    synthetic_response: dict[str, Any] = Field(default_factory=dict)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    score: float = Field(ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator(
        "redacted_request_shape",
        "synthetic_response",
        "blockers",
        "warnings",
        "findings",
        "metadata",
    )
    @classmethod
    def payloads_must_be_safe(cls, value: Any) -> Any:
        _reject_result_payload(value)
        return value

    @model_validator(mode="after")
    def result_must_stay_synthetic_and_disabled(self) -> ConnectorSimulationResult:
        if not self.synthetic:
            raise ValueError("synthetic must be true")
        if self.trusted:
            raise ValueError("trusted must be false")
        if self.external_calls_made:
            raise ValueError("external_calls_made must be false")
        if self.credentials_used:
            raise ValueError("credentials_used must be false")
        if self.tokens_used:
            raise ValueError("tokens_used must be false")
        if self.connector_runtime_enabled:
            raise ValueError("connector_runtime_enabled must be false")
        return self


class ConnectorReplayFixture(BaseModel):
    """Local synthetic fixture used to replay connector request and response shapes."""

    model_config = ConfigDict(extra="forbid")

    replay_fixture_id: str
    connector_key: str
    name: str
    description: str
    owner_scope: list[str] = Field(min_length=1)
    fixture_type: str
    request_shape: dict[str, Any]
    response_shape: dict[str, Any]
    expected_findings: list[str] = Field(default_factory=list)
    synthetic: bool
    trusted: bool
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        cleaned = value.strip()
        if not _DOTTED_LOWERCASE_RE.match(cleaned):
            raise ValueError("connector_key must be dotted lowercase text")
        return cleaned

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("name", "description", "fixture_type")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value.strip()

    @field_validator("request_shape", "response_shape", "metadata")
    @classmethod
    def fixture_payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value

    @model_validator(mode="after")
    def fixture_must_stay_synthetic_and_untrusted(self) -> ConnectorReplayFixture:
        if not self.synthetic:
            raise ValueError("synthetic must be true")
        if self.trusted:
            raise ValueError("trusted must be false")
        return self


class ConnectorPolicyReadinessRequest(BaseModel):
    """Request a connector policy readiness evaluation without approval."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    connector_key: str
    owner_scope: list[str] = Field(min_length=1)
    declared_policy_actions: list[str] = Field(default_factory=list)
    declared_scopes: list[str] = Field(default_factory=list)
    sandbox_required: bool = True
    audit_required: bool = True
    provenance_required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        cleaned = value.strip()
        if not _DOTTED_LOWERCASE_RE.match(cleaned):
            raise ValueError("connector_key must be dotted lowercase text")
        return cleaned

    @field_validator("owner_scope")
    @classmethod
    def owner_scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("owner_scope cannot be empty")
        return cleaned

    @field_validator("declared_policy_actions", "declared_scopes")
    @classmethod
    def lists_must_be_safe(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        for item in cleaned:
            _reject_unsafe_text(item)
        return cleaned

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_unsafe_payload(value)
        return value


class ConnectorPolicyReadinessResult(BaseModel):
    """Policy readiness result that does not approve runtime execution."""

    model_config = ConfigDict(extra="forbid")

    connector_policy_readiness_id: str
    trace_id: str | None = None
    connector_key: str
    status: ConnectorSimulationStatus
    policy_ready: bool
    sandbox_ready: bool
    audit_ready: bool
    provenance_ready: bool
    external_calls_allowed: bool
    credentials_allowed: bool
    activation_allowed: bool
    missing_policy_actions: list[str] = Field(default_factory=list)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("blockers", "warnings", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: Any) -> Any:
        _reject_result_payload(value)
        return value

    @model_validator(mode="after")
    def readiness_must_not_approve_runtime(self) -> ConnectorPolicyReadinessResult:
        if self.external_calls_allowed:
            raise ValueError("external_calls_allowed must be false")
        if self.credentials_allowed:
            raise ValueError("credentials_allowed must be false")
        if self.activation_allowed:
            raise ValueError("activation_allowed must be false")
        return self


class ConnectorSimulatorFinding(BaseModel):
    """One connector simulator finding."""

    model_config = ConfigDict(extra="forbid")

    connector_simulator_finding_id: str
    connector_key: str
    finding_type: ConnectorSimulatorFindingType
    severity: ConnectorSimulatorFindingSeverity
    status: ConnectorSimulatorFindingStatus
    title: str
    description: str
    recommended_action: str
    refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("connector_key")
    @classmethod
    def connector_key_must_be_dotted_lowercase(cls, value: str) -> str:
        cleaned = value.strip()
        if not _DOTTED_LOWERCASE_RE.match(cleaned):
            raise ValueError("connector_key must be dotted lowercase text")
        return cleaned

    @field_validator("title", "description", "recommended_action")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_result_payload(value)
        return value


def utc_now() -> datetime:
    """Return timezone-aware UTC now."""

    return datetime.now(UTC)


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in _URL_KEY_PARTS):
                raise ValueError("URL endpoint fields are not allowed")
            if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                raise ValueError("credential fields are not allowed")
            if any(part in normalized for part in _TOKEN_KEY_PARTS):
                raise ValueError("token fields are not allowed")
            if any(part in normalized for part in _RAW_PROMPT_KEY_PARTS):
                raise ValueError("raw prompts are not allowed")
            if any(part in normalized for part in _HIDDEN_REASONING_KEY_PARTS):
                raise ValueError("hidden reasoning is not allowed")
            _reject_unsafe_payload(nested)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_text(value)


def _reject_result_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            allowed = {
                "activation_allowed",
                "audit_ready",
                "audit_required",
                "connector_runtime_enabled",
                "credentials_allowed",
                "credentials_used",
                "external_calls_allowed",
                "external_calls_made",
                "external_calls_disabled",
                "finding_type",
                "policy_ready",
                "provenance_ready",
                "provenance_required",
                "sandbox_ready",
                "sandbox_required",
                "synthetic",
                "tokens_used",
                "trusted",
            }
            if normalized in allowed:
                _reject_result_payload(nested)
                continue
            _reject_unsafe_payload({key: nested})
        return
    if isinstance(value, list):
        for item in value:
            _reject_result_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_text(value)


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if _URL_RE.search(value):
        raise ValueError("external URLs are not allowed")
    if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
        raise ValueError("secret-like values are not allowed")
    if any(marker in lowered for marker in _RAW_PROMPT_VALUE_MARKERS):
        raise ValueError("raw prompts are not allowed")
    if any(marker in lowered for marker in _HIDDEN_REASONING_VALUE_MARKERS):
        raise ValueError("hidden reasoning is not allowed")


__all__ = [
    "ConnectorPolicyReadinessRequest",
    "ConnectorPolicyReadinessResult",
    "ConnectorReplayFixture",
    "ConnectorSimulationRequest",
    "ConnectorSimulationResult",
    "ConnectorSimulatorFinding",
    "utc_now",
]
