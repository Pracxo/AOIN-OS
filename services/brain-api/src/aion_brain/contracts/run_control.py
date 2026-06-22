"""Run control request contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.run_supervision import RunTargetSystem

RunControlType = Literal[
    "cancel",
    "pause",
    "resume",
    "mark_failed",
    "mark_completed",
    "request_status",
    "request_compensation",
    "generic",
]
RunControlStatus = Literal[
    "requested",
    "approved",
    "blocked",
    "handed_off",
    "completed",
    "failed",
    "waiting_for_approval",
    "unsupported",
]
RunControlMode = Literal["dry_run", "controlled"]


class RunControlRequest(BaseModel):
    """Manual run control request. It never executes itself."""

    model_config = ConfigDict(extra="forbid")

    run_control_request_id: str = Field(min_length=1)
    run_supervision_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    control_type: RunControlType
    status: RunControlStatus
    reason: str = Field(min_length=1)
    requested_mode: RunControlMode = "dry_run"
    target_system: RunTargetSystem
    target_run_id: str | None = None
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

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "run control reason")
        return value

    @field_validator("result", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def request_must_not_execute_itself(self) -> RunControlRequest:
        if self.result.get("executed") is True or self.metadata.get("auto_execute") is True:
            raise ValueError("run control request must not execute itself")
        return self


class RunControlRequestCreateRequest(BaseModel):
    """Request to create a manual run control request."""

    model_config = ConfigDict(extra="forbid")

    run_control_request_id: str | None = None
    run_supervision_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    control_type: RunControlType
    reason: str = Field(min_length=1)
    requested_mode: RunControlMode = "dry_run"
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "run control reason")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = ["RunControlRequest", "RunControlRequestCreateRequest"]
