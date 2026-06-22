"""Compensation planning contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

CompensationPlanStatus = Literal[
    "proposed",
    "approved",
    "rejected",
    "archived",
    "converted_to_action_proposals",
]
CompensationPlanType = Literal[
    "rollback",
    "retry",
    "manual_review",
    "cleanup",
    "notify_operator",
    "no_op",
    "generic",
]
CompensationStepType = Literal[
    "rollback",
    "retry",
    "cancel",
    "inspect",
    "cleanup",
    "verify_outcome",
    "notify_operator",
    "create_action_proposal",
    "no_op",
    "generic",
]
CompensationStepStatus = Literal["proposed", "converted", "rejected", "archived"]
CompensationRiskLevel = Literal["low", "medium", "high", "critical"]


class CompensationStep(BaseModel):
    """One non-executing step in a compensation plan."""

    model_config = ConfigDict(extra="forbid")

    compensation_step_id: str = Field(min_length=1)
    compensation_plan_id: str = Field(min_length=1)
    step_order: int = Field(ge=1)
    step_type: CompensationStepType
    status: CompensationStepStatus
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    proposed_action_type: str | None = None
    proposed_target_system: str | None = None
    proposed_payload: dict[str, Any] = Field(default_factory=dict)
    expected_effects: list[dict[str, Any]] = Field(default_factory=list)
    risk_level: CompensationRiskLevel
    requires_approval: bool = False
    action_proposal_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("title", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "compensation step text")
        return value

    @field_validator("proposed_payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @field_validator("expected_effects")
    @classmethod
    def expected_effects_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_payload(item)
        return value

    @model_validator(mode="after")
    def step_must_not_execute_itself(self) -> CompensationStep:
        if (
            self.proposed_payload.get("execute") is True
            or self.metadata.get("auto_execute") is True
        ):
            raise ValueError("compensation step must not execute itself")
        return self


class CompensationPlan(BaseModel):
    """Metadata-only compensation plan. It does not execute itself."""

    model_config = ConfigDict(extra="forbid")

    compensation_plan_id: str = Field(min_length=1)
    trace_id: str | None = None
    run_supervision_id: str | None = None
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    status: CompensationPlanStatus
    plan_type: CompensationPlanType
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    trigger_reason: str = Field(min_length=1)
    target_refs: list[str] = Field(default_factory=list)
    steps: list[CompensationStep] = Field(default_factory=list)
    risk_level: CompensationRiskLevel
    approval_request_id: str | None = None
    policy_decision_id: str | None = None
    autonomy_decision_id: str | None = None
    executable: bool = False
    execution_allowed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    approved_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("title", "description", "trigger_reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "compensation plan text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def plan_must_not_execute_itself(self) -> CompensationPlan:
        if self.execution_allowed or self.metadata.get("auto_execute") is True:
            raise ValueError("compensation plan must not execute itself")
        return self


class CompensationPlanCreateRequest(BaseModel):
    """Request to create a non-executing compensation plan."""

    model_config = ConfigDict(extra="forbid")

    compensation_plan_id: str | None = None
    trace_id: str | None = None
    run_supervision_id: str | None = None
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    plan_type: CompensationPlanType = "generic"
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    trigger_reason: str = Field(min_length=1)
    target_refs: list[str] = Field(default_factory=list)
    risk_level: CompensationRiskLevel = "medium"
    executable: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = ["CompensationPlan", "CompensationPlanCreateRequest", "CompensationStep"]
