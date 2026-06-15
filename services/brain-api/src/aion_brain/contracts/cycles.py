"""Cognitive cycle contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CycleStepType = Literal[
    "attention_review",
    "working_memory_sweep",
    "memory_decay",
    "memory_conflict_scan",
    "memory_compaction",
    "reflection_create",
    "skill_candidate_create",
    "regression_check",
    "replay_check",
    "visual_snapshot",
    "observability_summary",
    "approval_expiry",
    "workflow_heartbeat_review",
    "kernel_self_test",
    "noop",
]
CycleRiskLevel = Literal["low", "medium", "high", "critical"]
CycleType = Literal["wake", "active", "review", "sleep_consolidation", "maintenance", "shutdown"]
CycleTemplateStatus = Literal["active", "disabled"]
CycleMode = Literal["dry_run", "controlled"]
CycleStepRunStatus = Literal[
    "pending",
    "running",
    "completed",
    "skipped",
    "failed",
    "blocked_by_policy",
    "waiting_for_approval",
]
CycleRunStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "blocked_by_policy",
    "waiting_for_approval",
    "cancelled",
]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
    "authorization",
}
_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "hr",
    "procurement",
}


class CognitiveCycleStep(BaseModel):
    """One generic step in a cognitive cycle template."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1)
    step_type: CycleStepType
    description: str = Field(min_length=1)
    enabled: bool = True
    required: bool = False
    risk_level: CycleRiskLevel = "low"
    input_template: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("step_id", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank step IDs and descriptions."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        _reject_domain_terms([value])
        return value

    @field_validator("input_template", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like payloads."""
        _reject_secret_like_keys(value)
        return value


class CognitiveCycleTemplate(BaseModel):
    """Persistent template for one cognitive operating rhythm."""

    model_config = ConfigDict(extra="forbid")

    cycle_template_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    cycle_type: CycleType
    status: CycleTemplateStatus
    owner_scope: list[str] = Field(min_length=1)
    steps: list[CognitiveCycleStep] = Field(min_length=1)
    risk_level: CycleRiskLevel
    requires_approval: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_cannot_be_blank(cls, value: str) -> str:
        """Reject blank text."""
        if not value.strip():
            raise ValueError("value cannot be empty")
        _reject_domain_terms([value])
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata."""
        _reject_secret_like_keys(value)
        return value


class CognitiveCycleRunRequest(BaseModel):
    """Request to run one manual cognitive cycle."""

    model_config = ConfigDict(extra="forbid")

    cycle_run_id: str | None = None
    cycle_template_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    cycle_type: CycleType
    mode: CycleMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("input", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like payloads."""
        _reject_secret_like_keys(value)
        return value


class CognitiveCycleStepRun(BaseModel):
    """Persistent state for one cycle step execution."""

    model_config = ConfigDict(extra="forbid")

    cycle_step_run_id: str = Field(min_length=1)
    cycle_run_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    step_type: CycleStepType
    status: CycleStepRunStatus
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CognitiveCycleRun(BaseModel):
    """Persistent cognitive cycle run."""

    model_config = ConfigDict(extra="forbid")

    cycle_run_id: str = Field(min_length=1)
    cycle_template_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    cycle_type: CycleType
    status: CycleRunStatus
    mode: CycleMode
    owner_scope: list[str] = Field(min_length=1)
    steps: list[CognitiveCycleStepRun] = Field(default_factory=list)
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    autonomy_decision_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SleepConsolidationRecord(BaseModel):
    """Result of one sleep consolidation cycle."""

    model_config = ConfigDict(extra="forbid")

    consolidation_id: str = Field(min_length=1)
    cycle_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    working_memory_slots_reviewed: int = Field(ge=0)
    memories_decayed: int = Field(ge=0)
    conflicts_detected: int = Field(ge=0)
    compaction_runs: int = Field(ge=0)
    reflections_created: int = Field(ge=0)
    skill_candidates_created: int = Field(ge=0)
    regression_cases_checked: int = Field(ge=0)
    visual_snapshots_created: int = Field(ge=0)
    summary: str = Field(min_length=1)
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("summary")
    @classmethod
    def summary_cannot_be_blank(cls, value: str) -> str:
        """Reject blank summaries."""
        if not value.strip():
            raise ValueError("summary cannot be empty")
        return value

    @field_validator("result")
    @classmethod
    def result_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like result payloads."""
        _reject_secret_like_keys(value)
        return value


class CycleStatus(BaseModel):
    """Summary status for one cycle type."""

    model_config = ConfigDict(extra="forbid")

    cycle_type: CycleType
    latest_run: CognitiveCycleRun | None = None
    active_run_count: int = Field(ge=0)
    completed_run_count: int = Field(ge=0)
    failed_run_count: int = Field(ge=0)
    generated_at: datetime


class SleepConsolidationRequest(BaseModel):
    """Convenience API body for sleep consolidation."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    mode: CycleMode = "dry_run"
    actor_id: str | None = None
    workspace_id: str | None = None
    approval_present: bool = False
    input: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def input_must_be_safe(self) -> "SleepConsolidationRequest":
        """Reject secret-like input."""
        _reject_secret_like_keys(self.input)
        return self


def _reject_secret_like_keys(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise ValueError("payload must not contain secret-like keys")
            _reject_secret_like_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_secret_like_keys(nested)


def _reject_domain_terms(values: list[str]) -> None:
    for value in values:
        lowered = value.lower()
        if any(term in lowered for term in _BANNED_DOMAIN_TERMS):
            raise ValueError("cycle contracts must stay domain-neutral")
