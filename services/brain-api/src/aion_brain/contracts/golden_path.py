"""Golden Path Scenario Harness contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

GoldenPathScenarioStatus = Literal["active", "disabled"]
GoldenPathScenarioType = Literal[
    "boot",
    "dialogue",
    "prompt",
    "model_output",
    "grounding",
    "action",
    "run_supervision",
    "notification",
    "scheduler",
    "incident",
    "registry",
    "lifecycle",
    "contract",
    "extension",
    "binding",
    "conformance",
    "operator",
    "release",
    "generic",
]
GoldenPathRunMode = Literal["dry_run", "controlled"]
GoldenPathResultStatus = Literal["passed", "warning", "failed", "skipped", "blocked"]
GoldenPathRunStatus = Literal["passed", "warning", "failed", "blocked", "dry_run"]
GoldenPathReportStatus = Literal["passed", "warning", "failed"]
GoldenPathAssertionType = Literal[
    "status_equals",
    "field_present",
    "field_absent",
    "count_at_least",
    "count_equals",
    "boolean_true",
    "boolean_false",
    "no_external_call",
    "no_execution",
    "no_secret",
    "no_hidden_reasoning",
    "no_domain_drift",
    "policy_allowed",
    "policy_denied",
    "generic",
]
GoldenPathAssertionStatus = Literal["passed", "warning", "failed", "skipped"]
GoldenPathSeverity = Literal["low", "medium", "high", "critical"]

_DOTTED_LOWERCASE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
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
_EXTERNAL_SERVICE_TERMS = {
    "openai",
    "anthropic",
    "gemini",
    "brave",
    "alpha_vantage",
    "stripe",
    "github",
    "slack",
    "aws",
    "gcp",
    "azure",
}


class GoldenPathScenario(BaseModel):
    """One deterministic end-to-end golden path scenario definition."""

    model_config = ConfigDict(extra="forbid")

    golden_path_scenario_id: str = Field(min_length=1)
    scenario_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: GoldenPathScenarioStatus
    scenario_type: GoldenPathScenarioType
    owner_scope: list[str] = Field(min_length=1)
    required_services: list[str] = Field(default_factory=list)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    assertions: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("scenario_key")
    @classmethod
    def scenario_key_must_be_dotted_lowercase(cls, value: str) -> str:
        """Validate scenario key shape."""
        return _safe_key(value, "scenario_key")

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        """Reject unsafe or domain-specific display text."""
        _safe_text(value, "golden path scenario text")
        return value.strip()

    @field_validator("required_services")
    @classmethod
    def required_services_must_be_local(cls, value: list[str]) -> list[str]:
        """Reject external service names."""
        for item in value:
            _safe_key(item, "required_service")
            _reject_external_service(item)
        return value

    @field_validator("steps", "assertions")
    @classmethod
    def scenario_payloads_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reject unsafe scenario payloads."""
        _reject_payload(value)
        return value

    @field_validator("tags")
    @classmethod
    def tags_must_be_safe(cls, value: list[str]) -> list[str]:
        """Reject unsafe tags."""
        _reject_payload(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject unsafe metadata."""
        _reject_payload(value)
        return value


class GoldenPathFixturePack(BaseModel):
    """Synthetic fixture pack for golden path runs."""

    model_config = ConfigDict(extra="forbid")

    fixture_pack_id: str = Field(min_length=1)
    fixture_pack_key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: GoldenPathScenarioStatus
    owner_scope: list[str] = Field(min_length=1)
    workspace_id: str | None = None
    fixtures: list[dict[str, Any]] = Field(default_factory=list)
    seeded_resource_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("fixture_pack_key")
    @classmethod
    def fixture_pack_key_must_be_dotted_lowercase(cls, value: str) -> str:
        """Validate fixture pack key shape."""
        return _safe_key(value, "fixture_pack_key")

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        """Reject unsafe display text."""
        _safe_text(value, "fixture pack text")
        return value.strip()

    @field_validator("fixtures")
    @classmethod
    def fixtures_must_be_synthetic(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reject unsafe fixture payloads and mark missing synthetic flags."""
        _reject_payload(value)
        safe: list[dict[str, Any]] = []
        for fixture in value:
            if fixture.get("synthetic") is False:
                raise ValueError("fixture data must be synthetic")
            safe.append({**fixture, "synthetic": True})
        return safe

    @field_validator("seeded_resource_refs")
    @classmethod
    def refs_must_be_safe(cls, value: list[str]) -> list[str]:
        """Reject external refs."""
        for item in value:
            _reject_external_service(item)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject unsafe metadata."""
        _reject_payload(value)
        return value


class GoldenPathRunRequest(BaseModel):
    """Request to run deterministic golden path scenarios."""

    model_config = ConfigDict(extra="forbid")

    golden_path_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: GoldenPathRunMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    scenario_keys: list[str] = Field(default_factory=list)
    fixture_pack_keys: list[str] = Field(default_factory=list)
    run_all_defaults: bool = True
    create_notifications: bool = False
    create_operator_items: bool = True
    include_release_smoke: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("scenario_keys", "fixture_pack_keys")
    @classmethod
    def keys_must_be_safe(cls, value: list[str]) -> list[str]:
        """Validate optional key filters."""
        return [_safe_key(item, "golden path key") for item in value]

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject unsafe metadata."""
        _reject_payload(value)
        return value


class GoldenPathStepResult(BaseModel):
    """Result of one golden path scenario step."""

    model_config = ConfigDict(extra="forbid")

    step_result_id: str = Field(min_length=1)
    golden_path_run_id: str = Field(min_length=1)
    golden_path_scenario_id: str = Field(min_length=1)
    trace_id: str | None = None
    step_key: str = Field(min_length=1)
    step_order: int = Field(ge=1)
    status: GoldenPathResultStatus
    service_name: str = Field(min_length=1)
    action_name: str = Field(min_length=1)
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    resource_refs: list[str] = Field(default_factory=list)
    duration_ms: int | None = Field(default=None, ge=0)
    error: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("service_name")
    @classmethod
    def service_name_must_be_local(cls, value: str) -> str:
        """Reject external services."""
        _reject_external_service(value)
        return value

    @field_validator("input_summary", "output_summary", "error", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject unsafe payloads."""
        _reject_payload(value)
        return value


class GoldenPathAssertionResult(BaseModel):
    """Result of one deterministic golden path assertion."""

    model_config = ConfigDict(extra="forbid")

    assertion_result_id: str = Field(min_length=1)
    golden_path_run_id: str = Field(min_length=1)
    golden_path_scenario_id: str = Field(min_length=1)
    step_result_id: str | None = None
    trace_id: str | None = None
    assertion_key: str = Field(min_length=1)
    assertion_type: GoldenPathAssertionType
    status: GoldenPathAssertionStatus
    expected: dict[str, Any] = Field(default_factory=dict)
    actual: dict[str, Any] = Field(default_factory=dict)
    message: str = Field(min_length=1)
    severity: GoldenPathSeverity
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("expected", "actual", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject unsafe payloads."""
        _reject_payload(value)
        return value

    @field_validator("message")
    @classmethod
    def message_must_be_safe(cls, value: str) -> str:
        """Reject unsafe messages."""
        _safe_text(value, "golden path assertion message")
        return value.strip()


class GoldenPathRun(BaseModel):
    """Complete golden path run result."""

    model_config = ConfigDict(extra="forbid")

    golden_path_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: GoldenPathRunStatus
    mode: GoldenPathRunMode
    owner_scope: list[str] = Field(min_length=1)
    scenarios: list[GoldenPathScenario] = Field(default_factory=list)
    fixture_packs: list[GoldenPathFixturePack] = Field(default_factory=list)
    started_at: datetime
    completed_at: datetime | None = None
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    skipped_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    step_results: list[GoldenPathStepResult] = Field(default_factory=list)
    assertion_results: list[GoldenPathAssertionResult] = Field(default_factory=list)
    report_id: str | None = None
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("warnings", "failures")
    @classmethod
    def list_payloads_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reject unsafe warning/failure payloads."""
        _reject_payload(value)
        return value

    @field_validator("result", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject unsafe payloads."""
        _reject_payload(value)
        return value


class GoldenPathReport(BaseModel):
    """Release-facing golden path report."""

    model_config = ConfigDict(extra="forbid")

    golden_path_report_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: GoldenPathReportStatus
    owner_scope: list[str] = Field(min_length=1)
    golden_path_run_id: str | None = None
    scenario_count: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    readiness_score: float = Field(ge=0.0, le=1.0)
    release_candidate_ready: bool
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("findings")
    @classmethod
    def findings_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reject unsafe findings."""
        _reject_payload(value)
        return value

    @field_validator("recommendations")
    @classmethod
    def recommendations_must_be_safe(cls, value: list[str]) -> list[str]:
        """Reject unsafe recommendations."""
        _reject_payload(value)
        return value

    @field_validator("report", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject unsafe payloads."""
        _reject_payload(value)
        return value

    @model_validator(mode="after")
    def critical_failures_block_release_candidate(self) -> GoldenPathReport:
        """Force release candidate readiness false when critical findings exist."""
        if any(
            str(item.get("severity", "")).lower() == "critical"
            and str(item.get("status", "failed")).lower() == "failed"
            for item in self.findings
        ):
            self.release_candidate_ready = False
        return self


class GoldenPathQuery(BaseModel):
    """Query golden path records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    status: str | None = None
    scenario_type: str | None = None
    trace_id: str | None = None
    limit: int = Field(default=50, ge=1, le=500)


def _safe_key(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    if not _DOTTED_LOWERCASE.fullmatch(cleaned):
        raise ValueError(f"{field_name} must be dotted lowercase text")
    _reject_domain_terms(cleaned)
    _reject_external_service(cleaned)
    return cleaned


def _safe_text(value: str, field_name: str) -> None:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    reject_hidden_or_secret_text(cleaned, field_name)
    _reject_domain_terms(cleaned)


def _reject_payload(value: object) -> None:
    reject_secret_like_payload(value)
    if _contains_hidden_reasoning(value):
        raise ValueError("golden path payload must not contain hidden reasoning")
    if _contains_domain_term(value):
        raise ValueError("golden path payload must not contain domain-specific logic")
    if _contains_external_service(value):
        raise ValueError("golden path payload must not reference external services")


def _reject_domain_terms(value: object) -> None:
    if _contains_domain_term(value):
        raise ValueError("golden path must not contain domain-specific terms")


def _reject_external_service(value: object) -> None:
    if _contains_external_service(value):
        raise ValueError("golden path must not reference external services")


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


def _contains_external_service(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_external_service(key) or _contains_external_service(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_external_service(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(term in lowered for term in _EXTERNAL_SERVICE_TERMS)
    return False


def _contains_hidden_reasoning(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_hidden_reasoning(key) or _contains_hidden_reasoning(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_hidden_reasoning(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(
            marker in lowered
            for marker in (
                "chain_of_thought",
                "chain-of-thought",
                "hidden_reasoning",
            )
        )
    return False


__all__ = [
    "GoldenPathAssertionResult",
    "GoldenPathAssertionStatus",
    "GoldenPathAssertionType",
    "GoldenPathFixturePack",
    "GoldenPathQuery",
    "GoldenPathReport",
    "GoldenPathReportStatus",
    "GoldenPathResultStatus",
    "GoldenPathRun",
    "GoldenPathRunMode",
    "GoldenPathRunRequest",
    "GoldenPathRunStatus",
    "GoldenPathScenario",
    "GoldenPathScenarioStatus",
    "GoldenPathScenarioType",
    "GoldenPathSeverity",
    "GoldenPathStepResult",
]
