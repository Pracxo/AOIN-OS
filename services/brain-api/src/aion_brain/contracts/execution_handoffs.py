"""Execution handoff contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_secret_like_payload

ExecutionHandoffType = Literal[
    "command_dispatch",
    "workflow_run",
    "execution_run",
    "capability_invoke",
    "mcp_tool_invoke",
    "cycle_run",
    "sandbox_run",
    "dry_run",
    "generic",
]
ExecutionTargetSystem = Literal[
    "command_bus",
    "workflow_engine",
    "execution_orchestrator",
    "capability_runtime",
    "mcp_adapter",
    "cognitive_cycle",
    "sandbox",
    "noop",
]
ExecutionHandoffMode = Literal["dry_run", "controlled"]
ExecutionHandoffStatus = Literal[
    "dry_run",
    "handed_off",
    "blocked",
    "waiting_for_approval",
    "failed",
    "unsupported",
]


class ExecutionHandoffRequest(BaseModel):
    """Request to explicitly hand off an approved proposal."""

    model_config = ConfigDict(extra="forbid")

    execution_handoff_id: str | None = None
    action_proposal_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    handoff_type: ExecutionHandoffType
    target_system: ExecutionTargetSystem
    mode: ExecutionHandoffMode = "dry_run"
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def controlled_high_risk_requires_approval(self) -> ExecutionHandoffRequest:
        risk_level = str(self.metadata.get("risk_level", "")).lower()
        if (
            self.mode == "controlled"
            and risk_level in {"high", "critical"}
            and not self.approval_present
        ):
            raise ValueError("controlled high-risk handoff requires approval")
        return self


class ExecutionHandoff(BaseModel):
    """Persisted execution handoff record."""

    model_config = ConfigDict(extra="forbid")

    execution_handoff_id: str = Field(min_length=1)
    action_proposal_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: ExecutionHandoffStatus
    handoff_type: ExecutionHandoffType
    target_system: ExecutionTargetSystem
    target_request_id: str | None = None
    target_run_id: str | None = None
    handoff_payload: dict[str, Any] = Field(default_factory=dict)
    policy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    autonomy_decision_id: str | None = None
    approval_request_id: str | None = None
    blocker_refs: list[str] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("handoff_payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = ["ExecutionHandoff", "ExecutionHandoffRequest"]
