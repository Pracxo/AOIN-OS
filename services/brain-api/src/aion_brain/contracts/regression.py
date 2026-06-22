"""Local deterministic regression harness contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aion_brain.contracts.replay import ReplayMode, TraceComparison

RegressionCaseStatus = Literal["active", "disabled", "archived"]
RegressionResultStatus = Literal["passed", "failed", "blocked_by_policy", "replay_failed"]
RegressionRunStatus = Literal["pending", "running", "completed", "failed", "blocked_by_policy"]
EvalAdapterName = Literal["promptfoo", "ragas", "local"]


class RegressionCase(BaseModel):
    """Golden trace regression case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_trace_id: str
    input_snapshot_id: str
    expected_snapshot_id: str
    owner_scope: list[str] = Field(min_length=1)
    status: RegressionCaseStatus
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RegressionCaseCreateRequest(BaseModel):
    """Request to promote a trace into a golden regression case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_trace_id: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegressionRunRequest(BaseModel):
    """Request to run selected local golden trace cases."""

    model_config = ConfigDict(extra="forbid")

    regression_run_id: str | None = None
    case_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    mode: ReplayMode = "dry_run"
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_selection(self) -> "RegressionRunRequest":
        """Require explicit cases, tags, or an intentional allow-all flag."""
        if not self.case_ids and not self.tags and self.metadata.get("allow_all") is not True:
            raise ValueError("case_ids or tags are required unless metadata.allow_all=true")
        return self


class RegressionRunResult(BaseModel):
    """Result for one golden trace case."""

    model_config = ConfigDict(extra="forbid")

    result_id: str
    regression_run_id: str
    case_id: str
    replay_id: str | None
    status: RegressionResultStatus
    drift_detected: bool
    comparison: TraceComparison
    created_at: datetime | None = None


class RegressionRun(BaseModel):
    """Persisted local regression run."""

    model_config = ConfigDict(extra="forbid")

    regression_run_id: str
    status: RegressionRunStatus
    case_count: int = Field(ge=0)
    passed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    drift_count: int = Field(ge=0)
    results: list[RegressionRunResult]
    report: dict[str, Any]
    created_by: str | None
    created_at: datetime | None
    completed_at: datetime | None


class EvalAdapterRunRequest(BaseModel):
    """Request to an evaluation adapter boundary."""

    model_config = ConfigDict(extra="forbid")

    adapter_name: EvalAdapterName
    regression_run_id: str | None = None
    dataset_ref: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)


class EvalAdapterRunResult(BaseModel):
    """Evaluation adapter result owned by AION."""

    model_config = ConfigDict(extra="forbid")

    adapter_name: EvalAdapterName
    status: str
    output: dict[str, Any]
    reason: str | None = None
