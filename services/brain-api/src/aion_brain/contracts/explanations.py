"""Grounded explanation contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.concepts import reject_secret_like_keys, text_has_secret_markers
from aion_brain.contracts.trace_narratives import TraceNarrative, TraceNarrativeRequest

ExplanationStepType = Literal[
    "event",
    "intent",
    "attention",
    "retrieval",
    "context",
    "memory",
    "evidence",
    "belief",
    "entity",
    "situation",
    "policy",
    "risk",
    "approval",
    "autonomy",
    "decision",
    "plan",
    "command",
    "execution",
    "workflow",
    "outcome",
    "response",
    "capability",
    "limitation",
    "error",
    "generic",
]
ExplanationType = Literal[
    "why",
    "why_not",
    "trace",
    "decision",
    "policy",
    "risk",
    "approval",
    "autonomy",
    "retrieval",
    "response",
    "outcome",
    "capability",
    "error",
    "operator",
    "generic",
]
ExplanationTargetType = Literal[
    "trace",
    "event",
    "message",
    "response",
    "command",
    "workflow",
    "task",
    "decision",
    "outcome",
    "memory",
    "evidence",
    "belief",
    "entity",
    "situation",
    "policy",
    "risk",
    "approval",
    "autonomy",
    "capability",
    "module",
    "mcp",
    "sandbox",
    "operator",
    "api_error",
    "generic",
]
ExplanationStatus = Literal[
    "completed",
    "partial",
    "failed",
    "blocked_by_policy",
    "insufficient_evidence",
]
ExplanationVerificationStatus = Literal["passed", "warning", "failed"]
ExplanationFeedbackType = Literal[
    "helpful",
    "unhelpful",
    "incomplete",
    "unclear",
    "incorrect",
    "generic",
]

_HIDDEN_REASONING_MARKERS = (
    "chain_of_thought",
    "chain-of-thought",
    "chain of thought",
    "hidden_reasoning",
    "hidden reasoning",
    "private reasoning",
    "show your reasoning",
    "step-by-step reasoning",
)
_RAW_PROMPT_MARKERS = (
    "raw_prompt",
    "raw prompt",
    "system prompt",
    "developer prompt",
    "provider payload",
)


class ExplanationStep(BaseModel):
    """One public, observable step in an explanation."""

    model_config = ConfigDict(extra="forbid")

    explanation_step_id: str = Field(min_length=1)
    explanation_id: str = Field(min_length=1)
    step_order: int = Field(ge=1)
    step_type: ExplanationStepType
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    source_type: str | None = None
    source_id: str | None = None
    refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("title", "description")
    @classmethod
    def text_must_be_public_safe(cls, value: str) -> str:
        reject_hidden_reasoning_text(value)
        reject_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_public_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_hidden_reasoning_payload(value)
        return value


class ExplanationRecord(BaseModel):
    """A grounded public explanation of observable AION records."""

    model_config = ConfigDict(extra="forbid")

    explanation_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    explanation_type: ExplanationType
    target_type: ExplanationTargetType
    target_id: str | None = None
    status: ExplanationStatus
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    grounded: bool
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    decision_refs: list[str] = Field(default_factory=list)
    outcome_refs: list[str] = Field(default_factory=list)
    audit_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    policy_decision_id: str | None = None
    autonomy_decision_id: str | None = None
    risk_assessment_id: str | None = None
    approval_request_id: str | None = None
    steps: list[ExplanationStep] = Field(default_factory=list)
    redaction_metadata: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("title", "summary")
    @classmethod
    def text_must_be_public_safe(cls, value: str) -> str:
        reject_hidden_reasoning_text(value)
        reject_secret_text(value)
        return value

    @field_validator("metadata", "redaction_metadata")
    @classmethod
    def metadata_must_be_public_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_hidden_reasoning_payload(value)
        return value


class ExplanationRequest(BaseModel):
    """Request to build a grounded explanation."""

    model_config = ConfigDict(extra="forbid")

    explanation_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    explanation_type: ExplanationType = "generic"
    target_type: ExplanationTargetType
    target_id: str | None = None
    question: str | None = None
    include_steps: bool = True
    include_evidence: bool = True
    include_audit: bool = True
    include_policy: bool = True
    include_confidence: bool = True
    require_grounding: bool = False
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("question")
    @classmethod
    def question_must_be_public_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_reasoning_text(value)
            reject_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_public_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_hidden_reasoning_payload(value)
        return value


class WhyNotRequest(BaseModel):
    """Request a deterministic why-not answer."""

    model_config = ConfigDict(extra="forbid")

    why_not_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    question: str = Field(min_length=1)
    target_type: ExplanationTargetType
    target_id: str | None = None
    requested_action: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("question")
    @classmethod
    def question_must_be_public_safe(cls, value: str) -> str:
        reject_hidden_reasoning_text(value)
        reject_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_public_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_hidden_reasoning_payload(value)
        return value


class WhyNotAnswer(BaseModel):
    """Deterministic why-not answer grounded in local records."""

    model_config = ConfigDict(extra="forbid")

    why_not_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    question: str = Field(min_length=1)
    target_type: ExplanationTargetType
    target_id: str | None = None
    requested_action: str | None = None
    answer: str = Field(min_length=1)
    blockers: list[dict[str, Any]] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    next_possible_steps: list[str] = Field(default_factory=list)
    refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("question", "answer")
    @classmethod
    def text_must_be_public_safe(cls, value: str) -> str:
        reject_hidden_reasoning_text(value)
        reject_secret_text(value)
        return value

    @field_validator("blockers", "metadata")
    @classmethod
    def payload_must_be_public_safe(cls, value: Any) -> Any:
        reject_secret_like_keys(value)
        reject_hidden_reasoning_payload(value)
        return value


class ExplanationVerification(BaseModel):
    """Deterministic safety and grounding verification for an explanation."""

    model_config = ConfigDict(extra="forbid")

    verification_id: str = Field(min_length=1)
    explanation_id: str | None = None
    trace_narrative_id: str | None = None
    status: ExplanationVerificationStatus
    grounded: bool
    no_hidden_reasoning: bool
    no_secrets: bool
    no_raw_prompts: bool
    issues: list[dict[str, Any]] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    created_at: datetime

    @field_validator("issues")
    @classmethod
    def issues_must_be_public_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reject_secret_like_keys(value)
        reject_hidden_reasoning_payload(value)
        return value


class ExplanationFeedback(BaseModel):
    """Feedback on an explanation, narrative, or why-not answer."""

    model_config = ConfigDict(extra="forbid")

    explanation_feedback_id: str = Field(min_length=1)
    explanation_id: str | None = None
    trace_narrative_id: str | None = None
    why_not_id: str | None = None
    actor_id: str | None = None
    feedback_type: ExplanationFeedbackType
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("comment")
    @classmethod
    def comment_must_be_public_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_reasoning_text(value)
            reject_secret_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_public_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        reject_hidden_reasoning_payload(value)
        return value

    @model_validator(mode="after")
    def require_feedback_target(self) -> "ExplanationFeedback":
        if not any((self.explanation_id, self.trace_narrative_id, self.why_not_id)):
            raise ValueError("feedback must target an explanation, trace narrative, or why-not")
        return self


def contains_hidden_reasoning_marker(value: str) -> bool:
    """Return true when text asks for or includes hidden reasoning."""

    lowered = value.lower()
    return any(marker in lowered for marker in _HIDDEN_REASONING_MARKERS)


def contains_raw_prompt_marker(value: str) -> bool:
    """Return true when text references raw prompts or provider payloads."""

    lowered = value.lower()
    return any(marker in lowered for marker in _RAW_PROMPT_MARKERS)


def reject_hidden_reasoning_text(value: str) -> None:
    """Reject hidden reasoning and raw prompt markers in public explanation text."""

    if contains_hidden_reasoning_marker(value) or contains_raw_prompt_marker(value):
        raise ValueError("explanations must not expose chain-of-thought or raw prompts")


def reject_secret_text(value: str) -> None:
    """Reject obvious raw secret markers in public explanation text."""

    if text_has_secret_markers(value):
        raise ValueError("explanations must not expose raw secrets")


def reject_hidden_reasoning_payload(value: Any) -> None:
    """Reject hidden reasoning markers anywhere in nested explanation payloads."""

    if isinstance(value, dict):
        for item in value.values():
            reject_hidden_reasoning_payload(item)
    elif isinstance(value, list):
        for item in value:
            reject_hidden_reasoning_payload(item)
    elif isinstance(value, str):
        reject_hidden_reasoning_text(value)
        reject_secret_text(value)


__all__ = [
    "ExplanationFeedback",
    "ExplanationFeedbackType",
    "ExplanationRecord",
    "ExplanationRequest",
    "ExplanationStatus",
    "ExplanationStep",
    "ExplanationStepType",
    "ExplanationTargetType",
    "ExplanationType",
    "ExplanationVerification",
    "ExplanationVerificationStatus",
    "TraceNarrative",
    "TraceNarrativeRequest",
    "WhyNotAnswer",
    "WhyNotRequest",
    "contains_hidden_reasoning_marker",
    "contains_raw_prompt_marker",
    "reject_hidden_reasoning_payload",
    "reject_hidden_reasoning_text",
    "reject_secret_text",
]
