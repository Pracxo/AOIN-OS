"""Action proposal broker contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.execution_handoffs import ExecutionHandoff
from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

ActionProposalSourceType = Literal[
    "user_request",
    "dialogue",
    "model_output",
    "tool_intent",
    "decision",
    "plan",
    "workflow",
    "operator",
    "scheduler",
    "command",
    "system",
    "generic",
]
ActionProposalStatus = Literal[
    "proposed",
    "under_review",
    "approved_for_handoff",
    "blocked",
    "rejected",
    "handed_off",
    "completed",
    "archived",
]
ActionProposalType = Literal[
    "command",
    "workflow",
    "execution",
    "capability",
    "mcp_tool",
    "cycle",
    "sandbox_run",
    "memory_governance",
    "generic",
]
ActionRiskLevel = Literal["low", "medium", "high", "critical"]
ActionBlockerType = Literal[
    "policy_denied",
    "autonomy_denied",
    "approval_required",
    "risk_too_high",
    "capability_unavailable",
    "sandbox_required",
    "sandbox_blocked",
    "runtime_config_disabled",
    "tool_execution_disabled",
    "external_action_blocked",
    "missing_permission",
    "missing_grounding",
    "prompt_boundary_failed",
    "model_output_blocked",
    "unsupported_target",
    "generic",
]
ActionBlockerSeverity = Literal["low", "medium", "high", "critical"]
ActionBlockerStatus = Literal["open", "resolved", "dismissed"]
ActionReviewStatus = Literal["completed", "failed"]
ActionReviewDecision = Literal[
    "approve_for_handoff",
    "reject",
    "block",
    "request_approval",
    "request_clarification",
    "dry_run_only",
]
ToolIntentReviewStatus = Literal["completed", "failed"]
ToolIntentReviewDecision = Literal[
    "create_proposal",
    "reject",
    "block",
    "needs_clarification",
    "unsupported",
]


class ActionProposal(BaseModel):
    """Reviewed action candidate that does not execute itself."""

    model_config = ConfigDict(extra="forbid")

    action_proposal_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: ActionProposalSourceType
    source_id: str = Field(min_length=1)
    status: ActionProposalStatus
    proposal_type: ActionProposalType
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    proposed_payload: dict[str, Any] = Field(default_factory=dict)
    required_permissions: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    risk_level: ActionRiskLevel
    autonomy_mode_required: str | None = None
    sandbox_profile_id: str | None = None
    capability_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    model_output_refs: list[str] = Field(default_factory=list)
    tool_intent_refs: list[str] = Field(default_factory=list)
    blocker_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    reviewed_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("title", "description", "action_type", "target_type")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "action proposal text")
        return value

    @field_validator("proposed_payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def proposal_must_not_execute_itself(self) -> ActionProposal:
        if (
            self.proposed_payload.get("execute") is True
            or self.metadata.get("auto_execute") is True
        ):
            raise ValueError("action proposal must not execute itself")
        return self


class ActionProposalCreateRequest(BaseModel):
    """Request to create an action proposal."""

    model_config = ConfigDict(extra="forbid")

    action_proposal_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_type: ActionProposalSourceType
    source_id: str = Field(min_length=1)
    proposal_type: ActionProposalType
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    proposed_payload: dict[str, Any] = Field(default_factory=dict)
    required_permissions: list[str] = Field(default_factory=list)
    required_approvals: list[str] = Field(default_factory=list)
    risk_level: ActionRiskLevel = "medium"
    autonomy_mode_required: str | None = None
    sandbox_profile_id: str | None = None
    capability_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    model_output_refs: list[str] = Field(default_factory=list)
    tool_intent_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("proposed_payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ActionBlocker(BaseModel):
    """Metadata-only blocker for an action proposal."""

    model_config = ConfigDict(extra="forbid")

    action_blocker_id: str = Field(min_length=1)
    action_proposal_id: str | None = None
    trace_id: str | None = None
    blocker_type: ActionBlockerType
    severity: ActionBlockerSeverity
    status: ActionBlockerStatus
    reason: str = Field(min_length=1)
    missing_requirement: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("reason")
    @classmethod
    def reason_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "reason")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ActionProposalReview(BaseModel):
    """Completed review record for a proposal."""

    model_config = ConfigDict(extra="forbid")

    action_review_id: str = Field(min_length=1)
    action_proposal_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: ActionReviewStatus
    decision: ActionReviewDecision
    reviewer_id: str | None = None
    reason: str = Field(min_length=1)
    policy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    autonomy_decision_id: str | None = None
    approval_request_id: str | None = None
    blocker_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ActionProposalReviewRequest(BaseModel):
    """Request to review an action proposal."""

    model_config = ConfigDict(extra="forbid")

    action_proposal_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    decision: ActionReviewDecision
    reason: str = Field(min_length=1)
    approval_present: bool = False
    reviewer_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ToolIntentReview(BaseModel):
    """Review record for a captured tool intent."""

    model_config = ConfigDict(extra="forbid")

    tool_intent_review_id: str = Field(min_length=1)
    tool_intent_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: ToolIntentReviewStatus
    decision: ToolIntentReviewDecision
    action_proposal_id: str | None = None
    blocker_refs: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ToolIntentReviewRequest(BaseModel):
    """Request to review a captured tool intent."""

    model_config = ConfigDict(extra="forbid")

    tool_intent_id: str = Field(min_length=1)
    decision: ToolIntentReviewDecision = "create_proposal"
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    approval_present: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ActionProposalQuery(BaseModel):
    """Query action proposal broker records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    trace_id: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    status: str | None = None
    proposal_type: str | None = None
    risk_level: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)


class ActionProposalQueryResult(BaseModel):
    """Action proposal query result."""

    model_config = ConfigDict(extra="forbid")

    proposals: list[ActionProposal] = Field(default_factory=list)
    reviews: list[ActionProposalReview] = Field(default_factory=list)
    blockers: list[ActionBlocker] = Field(default_factory=list)
    handoffs: list[ExecutionHandoff] = Field(default_factory=list)
    tool_intent_reviews: list[ToolIntentReview] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "ActionBlocker",
    "ActionProposal",
    "ActionProposalCreateRequest",
    "ActionProposalQuery",
    "ActionProposalQueryResult",
    "ActionProposalReview",
    "ActionProposalReviewRequest",
    "ToolIntentReview",
    "ToolIntentReviewRequest",
]
