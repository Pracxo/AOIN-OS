"""Local performance benchmark and capacity contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.versioning import reject_secret_like_keys

PerformanceSampleStatus = Literal["passed", "failed", "warning", "skipped"]
BenchmarkOperationType = Literal[
    "health",
    "kernel_status",
    "kernel_self_test",
    "event_ingest",
    "memory_create",
    "memory_retrieve",
    "evidence_ingest",
    "evidence_search",
    "retrieval_query",
    "context_compile",
    "reasoning_deterministic",
    "planning",
    "brain_think",
    "command_noop",
    "event_dispatch_dry_run",
    "workflow_dry_run",
    "cycle_dry_run",
    "visual_map",
    "backup_dry_run",
    "release_baseline_dry_run",
    "api_request",
    "noop",
]
BenchmarkDefinitionStatus = Literal["active", "disabled"]
BenchmarkType = Literal[
    "smoke",
    "api_latency",
    "memory",
    "retrieval",
    "reasoning",
    "workflow",
    "visual",
    "release",
    "full_local",
]
BenchmarkRunMode = Literal["dry_run", "controlled"]
BenchmarkRunStatus = Literal["passed", "failed", "warning"]
CapacityBaselineStatus = Literal["active", "archived", "failed"]
ResourceBudgetProfileStatus = Literal["active", "disabled"]
BudgetEnforcementMode = Literal["report_only", "warn", "block"]
PerformanceRegressionStatus = Literal["passed", "warning", "failed"]

BUDGET_KEYS = {
    "max_request_duration_ms",
    "max_brain_think_duration_ms",
    "max_retrieval_duration_ms",
    "max_memory_retrieve_duration_ms",
    "max_visual_map_duration_ms",
    "max_benchmark_duration_ms",
    "max_records_per_operation",
    "max_context_items",
    "max_context_chars",
}


class PerformanceSample(BaseModel):
    """One local timing sample for a Brain operation."""

    model_config = ConfigDict(extra="forbid")

    performance_sample_id: str = Field(min_length=1)
    trace_id: str | None = None
    benchmark_run_id: str | None = None
    operation_type: BenchmarkOperationType
    component: str = Field(min_length=1)
    status: PerformanceSampleStatus
    duration_ms: int = Field(ge=0)
    input_size_bytes: int | None = Field(default=None, ge=0)
    output_size_bytes: int | None = Field(default=None, ge=0)
    item_count: int | None = Field(default=None, ge=0)
    error: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("error", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like performance payload keys."""
        reject_secret_like_keys(value)
        return value


class BenchmarkStep(BaseModel):
    """One deterministic benchmark operation."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1)
    operation_type: BenchmarkOperationType
    description: str = Field(min_length=1)
    repeat: int = Field(default=1, ge=1, le=100)
    timeout_ms: int | None = Field(default=None, gt=0)
    expected_status: PerformanceSampleStatus = "passed"
    threshold_ms: int | None = Field(default=None, gt=0)
    payload: dict[str, Any] = Field(default_factory=dict)
    required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like benchmark payload keys."""
        reject_secret_like_keys(value)
        return value


class BenchmarkDefinition(BaseModel):
    """Reusable local benchmark definition."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: BenchmarkDefinitionStatus = "active"
    benchmark_type: BenchmarkType
    owner_scope: list[str] = Field(min_length=1)
    steps: list[BenchmarkStep] = Field(min_length=1)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("thresholds", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like benchmark metadata."""
        reject_secret_like_keys(value)
        return value


class BenchmarkRunRequest(BaseModel):
    """Request to run a deterministic local benchmark."""

    model_config = ConfigDict(extra="forbid")

    benchmark_run_id: str | None = None
    benchmark_id: str | None = None
    benchmark: BenchmarkDefinition | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: BenchmarkRunMode = "dry_run"
    owner_scope: list[str] = Field(default_factory=list, min_length=1)
    repeat: int = Field(default=1, ge=1, le=20)
    compare_to_baseline_id: str | None = None
    fail_on_regression: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like run metadata."""
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def require_benchmark(self) -> BenchmarkRunRequest:
        """Require either an existing definition id or an inline definition."""
        if not self.benchmark_id and self.benchmark is None:
            raise ValueError("benchmark_id or benchmark is required")
        return self


class BenchmarkRun(BaseModel):
    """Completed local benchmark run."""

    model_config = ConfigDict(extra="forbid")

    benchmark_run_id: str = Field(min_length=1)
    benchmark_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: BenchmarkRunStatus
    mode: BenchmarkRunMode
    owner_scope: list[str] = Field(min_length=1)
    samples: list[PerformanceSample] = Field(default_factory=list)
    sample_count: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    summary: dict[str, Any] = Field(default_factory=dict)
    report: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("summary", "report")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like run payloads."""
        reject_secret_like_keys(value)
        return value


class CapacityBaseline(BaseModel):
    """Capacity baseline built from one or more benchmark runs."""

    model_config = ConfigDict(extra="forbid")

    capacity_baseline_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    baseline_name: str = Field(min_length=1)
    status: CapacityBaselineStatus
    environment: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    thresholds: dict[str, Any] = Field(default_factory=dict)
    benchmark_run_ids: list[str] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("environment", "metrics", "thresholds", "report")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like baseline payloads."""
        reject_secret_like_keys(value)
        return value


class ResourceBudgetProfile(BaseModel):
    """Report-only resource budget profile."""

    model_config = ConfigDict(extra="forbid")

    resource_budget_profile_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: ResourceBudgetProfileStatus = "active"
    owner_scope: list[str] = Field(min_length=1)
    budgets: dict[str, int | float | str] = Field(default_factory=dict)
    enforcement_mode: BudgetEnforcementMode = "report_only"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("budgets")
    @classmethod
    def budgets_must_be_known(
        cls,
        value: dict[str, int | float | str],
    ) -> dict[str, int | float | str]:
        """Allow only generic numeric or threshold budget keys."""
        unknown = sorted(set(value) - BUDGET_KEYS)
        if unknown:
            raise ValueError(f"unknown budget keys: {unknown}")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like budget metadata."""
        reject_secret_like_keys(value)
        return value


class PerformanceRegressionReport(BaseModel):
    """Comparison of a benchmark run against a capacity baseline."""

    model_config = ConfigDict(extra="forbid")

    regression_report_id: str = Field(min_length=1)
    baseline_id: str | None = None
    benchmark_run_id: str = Field(min_length=1)
    status: PerformanceRegressionStatus
    regressions: list[dict[str, Any]] = Field(default_factory=list)
    improvements: list[dict[str, Any]] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("regressions", "improvements")
    @classmethod
    def lists_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Reject secret-like comparison payloads."""
        for item in value:
            reject_secret_like_keys(item)
        return value

    @field_validator("report")
    @classmethod
    def report_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like comparison metadata."""
        reject_secret_like_keys(value)
        return value


class PerformanceSummary(BaseModel):
    """Aggregate timing summary over local performance samples."""

    model_config = ConfigDict(extra="forbid")

    window: str = Field(min_length=1)
    sample_count: int = Field(ge=0)
    p50_ms: float = Field(ge=0)
    p95_ms: float = Field(ge=0)
    p99_ms: float = Field(ge=0)
    max_ms: float = Field(ge=0)
    error_count: int = Field(ge=0)
    generated_at: datetime
