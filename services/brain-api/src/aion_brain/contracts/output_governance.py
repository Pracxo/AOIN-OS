"""Output governance request and query contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.model_outputs import (
    ModelOutputRecord,
    ModelOutputSegment,
    ResponseCandidate,
    StructuredOutputValidation,
    ToolIntentCandidate,
    reject_secret_like_payload,
)

OutputGovernanceStatus = Literal["passed", "warning", "failed", "blocked"]


class OutputGovernanceRequest(BaseModel):
    """Request to run model output governance."""

    model_config = ConfigDict(extra="forbid")

    output_governance_id: str | None = None
    trace_id: str | None = None
    model_output_id: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    parse_segments: bool = True
    validate_structured: bool = True
    create_response_candidate: bool = True
    detect_tool_intents: bool = True
    verify_grounding: bool = True
    require_grounding: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class OutputGovernanceRun(BaseModel):
    """Persisted model output governance run."""

    model_config = ConfigDict(extra="forbid")

    output_governance_id: str = Field(min_length=1)
    trace_id: str | None = None
    model_output_id: str = Field(min_length=1)
    status: OutputGovernanceStatus
    owner_scope: list[str] = Field(min_length=1)
    parsed_segments: list[ModelOutputSegment] = Field(default_factory=list)
    response_candidates: list[ResponseCandidate] = Field(default_factory=list)
    tool_intents: list[ToolIntentCandidate] = Field(default_factory=list)
    structured_validations: list[StructuredOutputValidation] = Field(default_factory=list)
    blocked: bool
    issues: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("issues")
    @classmethod
    def issues_must_be_safe(cls, value: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in value:
            reject_secret_like_payload(item)
        return value

    @field_validator("result")
    @classmethod
    def result_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ModelOutputQuery(BaseModel):
    """Query model output governance records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    trace_id: str | None = None
    prompt_packet_id: str | None = None
    model_route: str | None = None
    status: str | None = None
    output_type: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)


class ModelOutputQueryResult(BaseModel):
    """Model output query result."""

    model_config = ConfigDict(extra="forbid")

    outputs: list[ModelOutputRecord] = Field(default_factory=list)
    segments: list[ModelOutputSegment] = Field(default_factory=list)
    response_candidates: list[ResponseCandidate] = Field(default_factory=list)
    tool_intents: list[ToolIntentCandidate] = Field(default_factory=list)
    governance_runs: list[OutputGovernanceRun] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "ModelOutputQuery",
    "ModelOutputQueryResult",
    "OutputGovernanceRequest",
    "OutputGovernanceRun",
]
