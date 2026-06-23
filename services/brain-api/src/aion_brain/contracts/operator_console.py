"""Read-only Operator Console contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text

ConsoleView = Literal[
    "overview",
    "readiness",
    "release_candidate",
    "freeze_release",
    "golden_path",
    "module_lifecycle",
    "module_activation",
    "module_mock_runtime",
    "model_provider_hardening",
    "notifications",
    "incidents",
    "registry_integrity",
    "lifecycle_review",
    "audit_provenance",
    "settings_safety",
    "generic",
]
ConsoleActionType = Literal[
    "read",
    "dry_run",
    "acknowledge",
    "dismiss_with_reason",
    "review_record",
    "forbidden",
    "generic",
]
ConsoleSectionStatus = Literal["ready", "warning", "blocked", "unavailable", "empty", "unknown"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}
_SECRET_VALUE_MARKERS = (
    "sk-",
    "xoxb-",
    "ghp_",
    "-----begin private key-----",
    "hidden reasoning",
    "hidden_reasoning",
    "chain-of-thought",
    "chain_of_thought",
    "raw prompt",
    "raw_prompt",
)


class ConsoleDataSource(BaseModel):
    """A read-only source that can feed a future console view."""

    model_config = ConfigDict(extra="forbid")

    data_source_id: str = Field(min_length=1)
    source_key: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    service_name: str = Field(min_length=1)
    endpoint_hint: str | None = None
    cli_hint: str | None = None
    status: str = Field(min_length=1)
    available: bool
    read_only: bool
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console data source metadata")
        return value

    @model_validator(mode="after")
    def data_source_must_be_read_only(self) -> ConsoleDataSource:
        if not self.read_only:
            raise ValueError("console data sources must be read-only")
        return self


class ConsoleActionDescriptor(BaseModel):
    """Descriptive operator action metadata. It never executes."""

    model_config = ConfigDict(extra="forbid")

    action_key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    action_type: ConsoleActionType
    status: str = Field(min_length=1)
    dry_run_only: bool
    forbidden: bool
    requires_policy: bool
    requires_approval: bool
    endpoint_hint: str | None = None
    cli_hint: str | None = None
    reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("label", "reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        if value:
            reject_hidden_or_secret_text(value, "console action text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console action metadata")
        return value

    @model_validator(mode="after")
    def forbidden_action_requires_reason(self) -> ConsoleActionDescriptor:
        if self.forbidden and not self.reason.strip():
            raise ValueError("forbidden console actions must include reason")
        return self


class ConsoleViewSection(BaseModel):
    """One redacted section in a console view model."""

    model_config = ConfigDict(extra="forbid")

    section_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: ConsoleSectionStatus
    severity: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    items: list[dict[str, Any]] = Field(default_factory=list)
    data_sources: list[ConsoleDataSource] = Field(default_factory=list)
    allowed_actions: list[ConsoleActionDescriptor] = Field(default_factory=list)
    forbidden_actions: list[ConsoleActionDescriptor] = Field(default_factory=list)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "console section summary")
        return value

    @field_validator("items", "blockers", "warnings")
    @classmethod
    def list_payloads_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_payload(value, "console section payload")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console section metadata")
        return value


class ConsoleViewModelRequest(BaseModel):
    """Request a read-only console view model."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    view: ConsoleView = "overview"
    owner_scope: list[str] = Field(min_length=1)
    include_actions: bool = True
    include_forbidden_actions: bool = True
    include_refs: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console view request metadata")
        return value


class ConsoleViewModel(BaseModel):
    """Read-only, redacted console view model."""

    model_config = ConfigDict(extra="forbid")

    console_view_model_id: str
    trace_id: str | None = None
    view: ConsoleView
    status: str
    read_only: bool
    owner_scope: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sections: list[ConsoleViewSection]
    global_actions: list[ConsoleActionDescriptor] = Field(default_factory=list)
    forbidden_actions: list[ConsoleActionDescriptor] = Field(default_factory=list)
    data_sources: list[ConsoleDataSource] = Field(default_factory=list)
    generated_at: datetime
    redaction_applied: bool
    safety_findings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "console view summary")
        return value

    @field_validator("safety_findings")
    @classmethod
    def safety_findings_must_be_safe(
        cls, value: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        reject_secret_like_payload(value, "console safety findings")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console view metadata")
        return value

    @model_validator(mode="after")
    def view_model_must_be_safe(self) -> ConsoleViewModel:
        if not self.read_only:
            raise ValueError("console view models must be read-only")
        if not self.redaction_applied:
            raise ValueError("console view models must apply redaction")
        return self


class ConsoleAuditRequest(BaseModel):
    """Request a local console contract audit."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    views: list[ConsoleView] = Field(default_factory=list)
    include_examples: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console audit request metadata")
        return value


class ConsoleAuditResult(BaseModel):
    """Result of a local read-only console contract audit."""

    model_config = ConfigDict(extra="forbid")

    console_audit_id: str
    trace_id: str | None = None
    status: str
    owner_scope: list[str] = Field(min_length=1)
    views_checked: list[ConsoleView]
    findings: list[dict[str, Any]] = Field(default_factory=list)
    redaction_passed: bool
    forbidden_action_passed: bool
    data_source_passed: bool
    frontend_absent: bool
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("findings")
    @classmethod
    def findings_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_payload(value, "console audit findings")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console audit metadata")
        return value

    @model_validator(mode="after")
    def frontend_must_be_absent(self) -> ConsoleAuditResult:
        if not self.frontend_absent:
            raise ValueError("frontend_absent must be true in AION-088")
        return self


class ConsoleWorkflowStep(BaseModel):
    """One future console workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    view: ConsoleView
    source_key: str = Field(min_length=1)
    cli_hint: str | None = None
    endpoint_hint: str | None = None
    expected_status: str = Field(min_length=1)
    allowed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console workflow metadata")
        return value


class ConsoleWorkflowMap(BaseModel):
    """Read-only workflow map for a future console."""

    model_config = ConfigDict(extra="forbid")

    workflow_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    steps: list[ConsoleWorkflowStep]
    no_go_conditions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("description")
    @classmethod
    def description_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "console workflow description")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value, "console workflow metadata")
        return value


def reject_secret_like_payload(value: object, field_name: str) -> None:
    """Reject raw secret, prompt, or hidden-reasoning markers in arbitrary payloads."""
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered_key = str(key).lower().replace("-", "_")
            if any(part in lowered_key for part in _SECRET_KEY_PARTS):
                raise ValueError(f"{field_name} must not contain secret-like key {key}")
            reject_secret_like_payload(nested, field_name)
    elif isinstance(value, list):
        for item in value:
            reject_secret_like_payload(item, field_name)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
            raise ValueError(f"{field_name} must not contain unsafe text")


def utc_now() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(UTC)


__all__ = [
    "ConsoleActionDescriptor",
    "ConsoleActionType",
    "ConsoleAuditRequest",
    "ConsoleAuditResult",
    "ConsoleDataSource",
    "ConsoleSectionStatus",
    "ConsoleView",
    "ConsoleViewModel",
    "ConsoleViewModelRequest",
    "ConsoleViewSection",
    "ConsoleWorkflowMap",
    "ConsoleWorkflowStep",
    "reject_secret_like_payload",
]
