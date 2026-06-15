"""Cognitive replay and Brain snapshot contracts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SnapshotType = Literal[
    "full_trace",
    "event_only",
    "context_only",
    "reasoning_only",
    "plan_only",
    "execution_only",
    "evaluation_only",
    "learning_only",
    "visual_only",
    "regression_input",
    "regression_expected",
    "replay_output",
]
ReplayMode = Literal["dry_run", "deterministic"]
ReplayStatus = Literal["pending", "running", "completed", "failed", "blocked_by_policy"]


class BrainSnapshot(BaseModel):
    """Immutable, content-addressed Brain state."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1)
    trace_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    snapshot_type: SnapshotType
    state: dict[str, Any] = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    created_by: str | None = None
    created_at: datetime | None = None


class SnapshotCreateRequest(BaseModel):
    """Request to create a content-addressed Brain snapshot."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str | None = None
    trace_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    snapshot_type: SnapshotType
    state: dict[str, Any] = Field(min_length=1)
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReplayRequest(BaseModel):
    """Request to replay a completed Brain trace locally."""

    model_config = ConfigDict(extra="forbid")

    replay_id: str | None = None
    source_trace_id: str = Field(min_length=1)
    mode: ReplayMode = "dry_run"
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    use_original_event: bool = True
    compare_to_source: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReplayRun(BaseModel):
    """Persisted outcome of a deterministic replay."""

    model_config = ConfigDict(extra="forbid")

    replay_id: str
    source_trace_id: str
    replay_trace_id: str | None
    mode: ReplayMode
    status: ReplayStatus
    input_snapshot_id: str | None
    output_snapshot_id: str | None
    comparison: dict[str, Any]
    drift_detected: bool
    created_by: str | None
    created_at: datetime | None
    completed_at: datetime | None


class TraceComparison(BaseModel):
    """Deterministic semantic comparison between two Brain snapshots."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str
    source_trace_id: str
    replay_trace_id: str | None
    source_snapshot_id: str | None
    replay_snapshot_id: str | None
    matched: bool
    drift_detected: bool
    score: float = Field(ge=0.0, le=1.0)
    differences: list[dict[str, Any]]
    ignored_fields: list[str]
    created_at: datetime
