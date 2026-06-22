"""Scenario harness contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ScenarioStepType = Literal[
    "health_check",
    "kernel_status",
    "kernel_self_test",
    "create_event",
    "create_evidence",
    "create_memory",
    "retrieve_memory",
    "semantic_retrieve",
    "create_attention_signal",
    "compile_context",
    "reason",
    "plan",
    "think",
    "command_noop",
    "event_dispatch_dry_run",
    "workflow_dry_run",
    "cycle_dry_run",
    "autonomy_decide",
    "risk_assess",
    "approval_create",
    "module_scaffold",
    "module_certify",
    "sandbox_validate",
    "visual_map",
    "replay_dry_run",
    "regression_dry_run",
    "contract_export",
    "policy_simulate",
    "api_error_check",
    "sdk_smoke",
    "cli_smoke",
    "noop",
]
ScenarioStatus = Literal["active", "disabled"]
ScenarioType = Literal[
    "golden_path",
    "smoke",
    "api_contract",
    "memory",
    "policy",
    "autonomy",
    "workflow",
    "module",
    "sandbox",
    "visual",
    "replay",
    "release_baseline",
]
ScenarioRunMode = Literal["dry_run", "controlled"]
ScenarioRunStatus = Literal["passed", "failed", "warning", "skipped"]
ScenarioStepRunStatus = Literal["passed", "failed", "skipped", "warning"]
DemoFixtureStatus = Literal["active", "disabled"]
DemoFixtureType = Literal[
    "event",
    "evidence",
    "memory",
    "graph",
    "skill",
    "policy",
    "autonomy",
    "module_package",
    "sandbox_profile",
    "scenario",
]

ALLOWED_STEP_TYPES: set[str] = set(ScenarioStepType.__args__)  # type: ignore[attr-defined]
ALLOWED_SCENARIO_TYPES: set[str] = set(ScenarioType.__args__)  # type: ignore[attr-defined]

SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}

BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payment",
    "payments",
    "procurement",
}


class ScenarioStep(BaseModel):
    """One deterministic step in an AION scenario."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1)
    step_type: ScenarioStepType
    description: str = Field(min_length=1)
    request: dict[str, Any] = Field(default_factory=dict)
    expected: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    timeout_seconds: int | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("request", "expected", "metadata")
    @classmethod
    def dictionaries_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in step dictionaries."""
        reject_secret_like_keys(value)
        return value


class ScenarioDefinition(BaseModel):
    """A versionable deterministic Brain validation scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ScenarioStatus
    scenario_type: ScenarioType
    owner_scope: list[str] = Field(min_length=1)
    steps: list[ScenarioStep] = Field(min_length=1)
    expected: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank display text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("tags")
    @classmethod
    def tags_must_be_generic(cls, value: list[str]) -> list[str]:
        """Reject domain-specific scenario tags."""
        reject_domain_terms(value)
        return value

    @field_validator("expected", "metadata")
    @classmethod
    def dictionaries_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in scenario dictionaries."""
        reject_secret_like_keys(value)
        return value


class ScenarioCreateRequest(BaseModel):
    """Request to create a scenario definition."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    scenario_type: ScenarioType
    owner_scope: list[str] = Field(default_factory=list)
    steps: list[ScenarioStep] = Field(min_length=1)
    expected: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    activate: bool = True

    @field_validator("tags")
    @classmethod
    def tags_must_be_generic(cls, value: list[str]) -> list[str]:
        """Reject domain-specific scenario tags."""
        reject_domain_terms(value)
        return value

    @field_validator("expected", "metadata")
    @classmethod
    def dictionaries_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in request dictionaries."""
        reject_secret_like_keys(value)
        return value


class ScenarioRunRequest(BaseModel):
    """Request to run a scenario in a side-effect-safe mode."""

    model_config = ConfigDict(extra="forbid")

    scenario_run_id: str | None = None
    scenario_id: str | None = None
    scenario: ScenarioDefinition | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: ScenarioRunMode = "dry_run"
    owner_scope: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    fail_fast: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @model_validator(mode="after")
    def require_scenario_reference(self) -> "ScenarioRunRequest":
        """Require either an existing scenario id or inline scenario definition."""
        if self.scenario_id is None and self.scenario is None:
            raise ValueError("scenario_id or scenario must be present")
        return self

    @field_validator("tags")
    @classmethod
    def tags_must_be_generic(cls, value: list[str]) -> list[str]:
        """Reject domain-specific scenario tags."""
        reject_domain_terms(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        reject_secret_like_keys(value)
        return value


class ScenarioStepRun(BaseModel):
    """Result of one scenario step execution."""

    model_config = ConfigDict(extra="forbid")

    scenario_step_run_id: str = Field(min_length=1)
    scenario_run_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    step_type: ScenarioStepType
    status: ScenarioStepRunStatus
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    expected: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int | None = Field(default=None, ge=0)
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ScenarioRun(BaseModel):
    """Complete persisted result for a scenario execution."""

    model_config = ConfigDict(extra="forbid")

    scenario_run_id: str = Field(min_length=1)
    scenario_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: ScenarioRunStatus
    mode: ScenarioRunMode
    owner_scope: list[str] = Field(default_factory=list)
    step_count: int = Field(ge=0)
    passed_steps: int = Field(ge=0)
    failed_steps: int = Field(ge=0)
    skipped_steps: int = Field(ge=0)
    steps: list[ScenarioStepRun] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    comparison: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class DemoFixture(BaseModel):
    """Generic demo fixture record for safe local validation."""

    model_config = ConfigDict(extra="forbid")

    fixture_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: DemoFixtureStatus
    fixture_type: DemoFixtureType
    owner_scope: list[str] = Field(min_length=1)
    content: dict[str, Any] = Field(default_factory=dict)
    loaded: bool = False
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    loaded_at: datetime | None = None

    @field_validator("content", "result")
    @classmethod
    def dictionaries_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like fixture dictionaries."""
        reject_secret_like_keys(value)
        return value


class DemoFixtureLoadRequest(BaseModel):
    """Request to load one demo fixture."""

    model_config = ConfigDict(extra="forbid")

    fixture_id: str | None = None
    fixture: DemoFixture | None = None
    fixture_name: str | None = None
    owner_scope: list[str] = Field(default_factory=list)
    dry_run: bool = True
    created_by: str | None = None

    @model_validator(mode="after")
    def require_fixture_selector(self) -> "DemoFixtureLoadRequest":
        """Require one fixture selector."""
        if self.fixture_id is None and self.fixture is None and self.fixture_name is None:
            raise ValueError("fixture_id or fixture or fixture_name must be present")
        return self


class DemoFixtureLoadResult(BaseModel):
    """Result of a demo fixture load request."""

    model_config = ConfigDict(extra="forbid")

    fixture_id: str = Field(min_length=1)
    loaded: bool
    dry_run: bool
    result: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None
    created_at: datetime


def reject_secret_like_keys(value: dict[str, Any]) -> None:
    """Reject secret-like keys anywhere inside a dictionary."""
    for key, item in value.items():
        lowered = str(key).lower()
        if any(part in lowered for part in SECRET_KEY_PARTS):
            raise ValueError("payload must not contain secret-like keys")
        if isinstance(item, dict):
            reject_secret_like_keys(item)
        elif isinstance(item, list):
            for element in item:
                if isinstance(element, dict):
                    reject_secret_like_keys(element)


def reject_domain_terms(values: list[str]) -> None:
    """Reject vertical/domain-specific terms from public Brain scenario metadata."""
    for value in values:
        lowered = value.lower()
        if any(term in lowered for term in BANNED_DOMAIN_TERMS):
            raise ValueError("scenario metadata must remain domain-neutral")
