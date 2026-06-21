"""Run supervision contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

RunTargetSystem = Literal[
    "command_bus",
    "workflow_engine",
    "execution_orchestrator",
    "capability_runtime",
    "mcp_adapter",
    "cognitive_cycle",
    "sandbox",
    "action_proposal",
    "noop",
]
RunSupervisionSourceType = Literal[
    "execution_handoff",
    "action_proposal",
    "command",
    "workflow",
    "execution",
    "capability",
    "mcp",
    "sandbox",
    "cycle",
    "operator",
    "system",
    "generic",
]
RunSupervisionStatus = Literal[
    "active",
    "completed",
    "failed",
    "stalled",
    "timed_out",
    "cancelled",
    "blocked",
    "archived",
]
RunType = Literal[
    "command", "workflow", "execution", "capability", "mcp_tool", "cycle", "sandbox", "generic"
]
ObservedRunStatus = Literal[
    "pending",
    "running",
    "waiting_for_approval",
    "paused",
    "completed",
    "failed",
    "cancelled",
    "blocked",
    "unknown",
]
TimeoutPolicyStatus = Literal["active", "disabled"]
TimeoutPolicySeverity = Literal["low", "medium", "high", "critical"]
TimeoutAction = Literal[
    "report_only",
    "create_action_item",
    "request_cancellation",
    "request_compensation",
    "block_future_handoffs",
]
SupervisionReportStatus = Literal["passed", "warning", "failed"]


class RunTargetRef(BaseModel):
    """Provider-neutral reference to a supervised target run."""

    model_config = ConfigDict(extra="forbid")

    target_system: RunTargetSystem
    target_run_id: str | None = None
    target_request_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None

    @field_validator("target_run_id", "target_request_id", "target_type", "target_id")
    @classmethod
    def identifiers_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "run target identifier")
        return value


class RunSupervisionRecord(BaseModel):
    """Canonical local record for observing a governed run."""

    model_config = ConfigDict(extra="forbid")

    run_supervision_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: RunSupervisionSourceType
    source_id: str = Field(min_length=1)
    target_system: RunTargetSystem
    target_run_id: str | None = None
    status: RunSupervisionStatus
    run_type: RunType
    owner_scope: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    current_status: ObservedRunStatus
    previous_status: ObservedRunStatus | None = None
    timeout_policy_id: str | None = None
    deadline_at: datetime | None = None
    last_sample_id: str | None = None
    last_seen_at: datetime | None = None
    stalled: bool = False
    cancellable: bool = False
    pausable: bool = False
    resumable: bool = False
    compensation_available: bool = False
    outcome_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("source_id", "title", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "run supervision text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RunSupervisionCreateRequest(BaseModel):
    """Request to register a run for supervision."""

    model_config = ConfigDict(extra="forbid")

    run_supervision_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: RunSupervisionSourceType
    source_id: str = Field(min_length=1)
    target_system: RunTargetSystem
    target_run_id: str | None = None
    run_type: RunType = "generic"
    owner_scope: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    timeout_policy_id: str | None = None
    deadline_at: datetime | None = None
    cancellable: bool = False
    pausable: bool = False
    resumable: bool = False
    compensation_available: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RunStatusSample(BaseModel):
    """One deterministic status sample from the target subsystem."""

    model_config = ConfigDict(extra="forbid")

    run_status_sample_id: str = Field(min_length=1)
    run_supervision_id: str = Field(min_length=1)
    trace_id: str | None = None
    target_system: RunTargetSystem
    target_run_id: str | None = None
    observed_status: ObservedRunStatus
    raw_status: dict[str, Any] = Field(default_factory=dict)
    progress: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime | None = None

    @field_validator("raw_status", "progress", "error", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RunTimeoutPolicy(BaseModel):
    """Metadata-only timeout policy. It does not execute control actions."""

    model_config = ConfigDict(extra="forbid")

    timeout_policy_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: TimeoutPolicyStatus
    target_system: RunTargetSystem
    run_type: RunType
    timeout_seconds: int = Field(ge=1, le=86400)
    stall_after_seconds: int = Field(ge=1, le=86400)
    max_status_age_seconds: int = Field(ge=1, le=86400)
    severity: TimeoutPolicySeverity
    action_on_timeout: TimeoutAction
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "timeout policy text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def policy_must_not_auto_execute(self) -> RunTimeoutPolicy:
        if self.metadata.get("auto_execute") is True:
            raise ValueError("timeout policy must not auto-execute")
        return self


class RunSupervisionReport(BaseModel):
    """Read-only report over supervised run state."""

    model_config = ConfigDict(extra="forbid")

    supervision_report_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: SupervisionReportStatus
    owner_scope: list[str] = Field(min_length=1)
    target_systems: list[str] = Field(default_factory=list)
    run_count: int = Field(ge=0)
    active_count: int = Field(ge=0)
    completed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    stalled_count: int = Field(ge=0)
    timeout_count: int = Field(ge=0)
    control_request_count: int = Field(ge=0)
    compensation_plan_count: int = Field(ge=0)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("findings", mode="after")
    @classmethod
    def findings_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_payload(item)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class RunSupervisionReportRequest(BaseModel):
    """Request to generate a supervision report."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    target_systems: list[str] = Field(default_factory=list)
    include_archived: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "ObservedRunStatus",
    "RunStatusSample",
    "RunSupervisionCreateRequest",
    "RunSupervisionRecord",
    "RunSupervisionReport",
    "RunSupervisionReportRequest",
    "RunTargetRef",
    "RunTargetSystem",
    "RunTimeoutPolicy",
]
