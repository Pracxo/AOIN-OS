"""Model output governance contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ModelOutputStatus = Literal["received", "parsed", "governed", "blocked", "failed", "archived"]
ModelOutputType = Literal[
    "text", "json", "markdown", "structured", "tool_intent", "mixed", "empty", "generic"
]
OutputSegmentType = Literal[
    "answer_text",
    "bullet",
    "json_block",
    "code_block",
    "citation_hint",
    "claim_candidate",
    "tool_intent",
    "refusal",
    "uncertainty",
    "hidden_reasoning_removed",
    "unsafe_removed",
    "generic",
]
StructuredValidationStatus = Literal["passed", "warning", "failed"]
ResponseCandidateStatus = Literal[
    "proposed", "verified", "blocked", "promoted", "rejected", "archived"
]
ResponseCandidateType = Literal[
    "answer", "clarification", "refusal", "status", "explanation", "summary", "generic"
]
ToolIntentStatus = Literal["captured", "blocked", "rejected", "converted_to_request", "archived"]
ToolIntentType = Literal[
    "tool_call",
    "capability_invoke",
    "mcp_tool",
    "workflow_run",
    "command_dispatch",
    "memory_write",
    "external_request",
    "unknown",
]
OutputRiskLevel = Literal["low", "medium", "high", "critical"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "raw_prompt",
    "secret",
    "token",
}
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")
_HIDDEN_MARKERS = (
    "chain-of-thought",
    "chain_of_thought",
    "hidden reasoning",
    "hidden_reasoning",
    "private reasoning",
    "raw prompt",
    "raw_prompt",
    "system prompt:",
    "developer prompt:",
)


def reject_secret_like_payload(value: object) -> None:
    """Reject secret-like keys and values from public model-output contracts."""

    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise ValueError("payload must not contain secret-like keys")
            reject_secret_like_payload(nested)
    elif isinstance(value, list):
        for item in value:
            reject_secret_like_payload(item)
    elif isinstance(value, str):
        reject_hidden_or_secret_text(value, "payload")


def reject_hidden_or_secret_text(value: str, field_name: str) -> None:
    """Reject hidden reasoning, raw prompt echoes, and obvious secret values."""

    lowered = value.lower()
    if any(marker in lowered for marker in _HIDDEN_MARKERS):
        raise ValueError(f"{field_name} must not contain hidden reasoning or raw prompt markers")
    if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
        raise ValueError(f"{field_name} must not contain secret-like values")


class ModelOutputRecord(BaseModel):
    """Redacted and hashed provider-neutral model output record."""

    model_config = ConfigDict(extra="forbid")

    model_output_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    prompt_packet_id: str | None = None
    model_input_manifest_id: str | None = None
    model_route: str | None = None
    provider_type: str | None = None
    status: ModelOutputStatus
    output_type: ModelOutputType
    raw_output_hash: str = Field(min_length=1)
    redacted_output: str
    output_redacted: bool
    token_estimate: int = Field(ge=0)
    char_count: int = Field(ge=0)
    safety_findings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("redacted_output")
    @classmethod
    def redacted_output_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "redacted_output")
        return value

    @field_validator("safety_findings")
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


class ModelOutputCreateRequest(BaseModel):
    """Request to receive a model output through AION governance."""

    model_config = ConfigDict(extra="forbid")

    model_output_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    prompt_packet_id: str | None = None
    model_input_manifest_id: str | None = None
    model_route: str | None = None
    provider_type: str | None = None
    output_type: ModelOutputType = "text"
    raw_output: str
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @model_validator(mode="after")
    def empty_output_type_must_be_empty(self) -> ModelOutputCreateRequest:
        if self.output_type == "empty" and self.raw_output:
            raise ValueError("raw_output must be empty when output_type is empty")
        if self.output_type != "empty" and self.raw_output == "":
            raise ValueError("raw_output may only be empty when output_type is empty")
        return self

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ModelOutputSegment(BaseModel):
    """Parsed redacted model output segment."""

    model_config = ConfigDict(extra="forbid")

    output_segment_id: str = Field(min_length=1)
    model_output_id: str = Field(min_length=1)
    trace_id: str | None = None
    segment_order: int = Field(ge=1)
    segment_type: OutputSegmentType
    content: str
    content_hash: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    unsafe: bool
    findings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def content_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "content")
        return value

    @field_validator("findings")
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


class StructuredOutputValidation(BaseModel):
    """Deterministic structured output validation result."""

    model_config = ConfigDict(extra="forbid")

    structured_validation_id: str = Field(min_length=1)
    model_output_id: str = Field(min_length=1)
    trace_id: str | None = None
    schema_name: str | None = None
    status: StructuredValidationStatus
    valid: bool
    parsed_payload: dict[str, Any] = Field(default_factory=dict)
    schema_errors: list[dict[str, Any]] = Field(default_factory=list)
    safety_errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("parsed_payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ResponseCandidate(BaseModel):
    """Governed candidate that can later become a ResponseDraft."""

    model_config = ConfigDict(extra="forbid")

    response_candidate_id: str = Field(min_length=1)
    model_output_id: str | None = None
    trace_id: str | None = None
    dialogue_session_id: str | None = None
    prompt_packet_id: str | None = None
    status: ResponseCandidateStatus
    response_type: ResponseCandidateType
    content: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    grounded: bool
    citation_refs: list[str] = Field(default_factory=list)
    grounding_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    entity_refs: list[str] = Field(default_factory=list)
    unsupported_statement_refs: list[str] = Field(default_factory=list)
    verification_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=1.0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    promoted_response_id: str | None = None
    deleted_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def content_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "content")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ToolIntentCandidate(BaseModel):
    """Captured but non-executable tool intent candidate."""

    model_config = ConfigDict(extra="forbid")

    tool_intent_id: str = Field(min_length=1)
    model_output_id: str | None = None
    trace_id: str | None = None
    prompt_packet_id: str | None = None
    status: ToolIntentStatus
    intent_type: ToolIntentType
    tool_name: str | None = None
    action_type: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    arguments_redacted: dict[str, Any] = Field(default_factory=dict)
    raw_arguments_hash: str | None = None
    risk_level: OutputRiskLevel
    policy_decision_id: str | None = None
    autonomy_decision_id: str | None = None
    approval_request_id: str | None = None
    blocked_reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("arguments_redacted", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "ModelOutputCreateRequest",
    "ModelOutputRecord",
    "ModelOutputSegment",
    "ResponseCandidate",
    "StructuredOutputValidation",
    "ToolIntentCandidate",
    "reject_hidden_or_secret_text",
    "reject_secret_like_payload",
]
