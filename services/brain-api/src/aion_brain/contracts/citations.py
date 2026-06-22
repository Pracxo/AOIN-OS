"""Citation and source-attribution contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.grounding import (
    GroundingQuery,
    GroundingSource,
    GroundingSourceType,
    SourceCoverageReport,
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

CitationType = Literal[
    "supports_statement",
    "grounds_response",
    "explains_decision",
    "supports_belief",
    "supports_outcome",
    "source_reference",
    "weak_reference",
    "disputed_reference",
    "generic",
]
ResponseCitationMapStatus = Literal["passed", "warning", "failed", "insufficient_sources"]
UnsupportedStatementSeverity = Literal["low", "medium", "high", "critical"]


class CitationRecord(BaseModel):
    """One deterministic citation to a grounding source."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str = Field(min_length=1)
    trace_id: str | None = None
    response_id: str | None = None
    explanation_id: str | None = None
    source_type: GroundingSourceType
    source_id: str = Field(min_length=1)
    grounding_source_id: str | None = None
    citation_type: CitationType
    label: str = Field(min_length=1)
    quote: str | None = None
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    verified: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("quote")
    @classmethod
    def quote_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "quote")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def char_bounds_must_be_ordered(self) -> CitationRecord:
        if self.start_char is not None and self.end_char is not None:
            if self.end_char < self.start_char:
                raise ValueError("end_char must be greater than or equal to start_char")
        return self


class CitationCreateRequest(BaseModel):
    """Request to create one citation record."""

    model_config = ConfigDict(extra="forbid")

    citation_id: str | None = None
    trace_id: str | None = None
    response_id: str | None = None
    explanation_id: str | None = None
    source_type: GroundingSourceType
    source_id: str = Field(min_length=1)
    grounding_source_id: str | None = None
    citation_type: CitationType = "source_reference"
    label: str = Field(min_length=1)
    quote: str | None = None
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    verified: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("quote")
    @classmethod
    def quote_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "quote")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class UnsupportedStatement(BaseModel):
    """Statement that lacks sufficient deterministic support."""

    model_config = ConfigDict(extra="forbid")

    unsupported_statement_id: str = Field(min_length=1)
    trace_id: str | None = None
    response_id: str | None = None
    explanation_id: str | None = None
    statement_text: str = Field(min_length=1)
    statement_hash: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    severity: UnsupportedStatementSeverity
    required_support: list[str] = Field(default_factory=list)
    candidate_source_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("statement_text")
    @classmethod
    def statement_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "statement_text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ResponseCitationMap(BaseModel):
    """Citation coverage map for a response-like target."""

    model_config = ConfigDict(extra="forbid")

    citation_map_id: str = Field(min_length=1)
    response_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: ResponseCitationMapStatus
    grounded: bool
    citation_ids: list[str] = Field(default_factory=list)
    unsupported_statement_ids: list[str] = Field(default_factory=list)
    coverage_score: float = Field(ge=0.0, le=1.0)
    required_source_types: list[GroundingSourceType] = Field(default_factory=list)
    missing_source_types: list[GroundingSourceType] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class GroundingQueryResult(BaseModel):
    """Combined source-attribution query result."""

    model_config = ConfigDict(extra="forbid")

    sources: list[GroundingSource]
    citations: list[CitationRecord]
    citation_maps: list[ResponseCitationMap]
    unsupported_statements: list[UnsupportedStatement]
    coverage_reports: list[SourceCoverageReport]
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "CitationCreateRequest",
    "CitationRecord",
    "CitationType",
    "GroundingQuery",
    "GroundingQueryResult",
    "ResponseCitationMap",
    "ResponseCitationMapStatus",
    "UnsupportedStatement",
    "UnsupportedStatementSeverity",
]
