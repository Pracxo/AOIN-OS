"""Grounding Manager contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

GroundingSourceType = Literal[
    "evidence",
    "evidence_chunk",
    "memory",
    "belief_claim",
    "entity",
    "concept",
    "situation",
    "state_atom",
    "audit_entry",
    "provenance_link",
    "explanation",
    "outcome",
    "decision",
    "response",
    "operator",
    "system",
    "generic",
]
GroundingSensitivity = Literal["public", "internal", "confidential", "restricted"]
GroundingTrustLevel = Literal[
    "primary",
    "derived",
    "memory_recall",
    "belief_supported",
    "belief_uncertain",
    "unverified",
    "system_state",
    "unknown",
]
GroundingVerificationTargetType = Literal[
    "response",
    "explanation",
    "trace_narrative",
    "decision",
    "outcome",
    "belief",
    "operator",
    "generic",
]
GroundingVerificationStatus = Literal[
    "passed",
    "warning",
    "failed",
    "insufficient_sources",
    "blocked_by_policy",
]
SourceCoverageStatus = Literal["passed", "warning", "failed"]

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
    "chain_of_thought",
    "chain-of-thought",
    "chain of thought",
    "hidden_reasoning",
    "hidden reasoning",
    "private reasoning",
    "raw_prompt",
    "raw prompt",
    "system prompt",
    "developer prompt",
)


class GroundingSource(BaseModel):
    """Normalized source record used for response-level grounding."""

    model_config = ConfigDict(extra="forbid")

    grounding_source_id: str = Field(min_length=1)
    trace_id: str | None = None
    source_type: GroundingSourceType
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    sensitivity: GroundingSensitivity
    trust_level: GroundingTrustLevel
    evidence_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    entity_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "summary")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def memory_recall_must_not_be_primary(self) -> GroundingSource:
        if self.source_type == "memory" and self.trust_level == "primary":
            raise ValueError("memory recall cannot be primary evidence")
        if self.trust_level == "memory_recall" and self.source_type != "memory":
            raise ValueError("memory_recall trust level is only valid for memory sources")
        return self


class GroundingSourceCreateRequest(BaseModel):
    """Request to create or normalize a grounding source."""

    model_config = ConfigDict(extra="forbid")

    grounding_source_id: str | None = None
    trace_id: str | None = None
    source_type: GroundingSourceType
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    content_hash: str | None = None
    sensitivity: GroundingSensitivity = "internal"
    trust_level: GroundingTrustLevel = "unknown"
    evidence_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    entity_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "summary")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class GroundingVerificationRequest(BaseModel):
    """Request to verify whether a target is sufficiently grounded."""

    model_config = ConfigDict(extra="forbid")

    grounding_verification_id: str | None = None
    trace_id: str | None = None
    response_id: str | None = None
    explanation_id: str | None = None
    target_type: GroundingVerificationTargetType
    target_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    text: str | None = None
    required_source_types: list[GroundingSourceType] = Field(default_factory=list)
    require_evidence: bool = False
    require_belief_support: bool = False
    allow_memory_only: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("text")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "text")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def target_or_text_required(self) -> GroundingVerificationRequest:
        if not (self.response_id or self.explanation_id or self.target_id or self.text):
            raise ValueError("response_id, explanation_id, target_id, or text is required")
        return self


class GroundingVerificationRun(BaseModel):
    """Persisted result of one grounding verification."""

    model_config = ConfigDict(extra="forbid")

    grounding_verification_id: str = Field(min_length=1)
    trace_id: str | None = None
    response_id: str | None = None
    explanation_id: str | None = None
    target_type: GroundingVerificationTargetType
    target_id: str | None = None
    status: GroundingVerificationStatus
    owner_scope: list[str] = Field(min_length=1)
    grounded: bool
    checked_statement_count: int = Field(ge=0)
    supported_statement_count: int = Field(ge=0)
    unsupported_statement_count: int = Field(ge=0)
    citation_count: int = Field(ge=0)
    coverage_score: float = Field(ge=0.0, le=1.0)
    issues: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("issues", "result")
    @classmethod
    def payload_must_be_safe(cls, value: Any) -> Any:
        reject_secret_like_payload(value)
        return value


class SourceCoverageReport(BaseModel):
    """Source coverage summary for a response or explanation."""

    model_config = ConfigDict(extra="forbid")

    source_coverage_id: str = Field(min_length=1)
    trace_id: str | None = None
    response_id: str | None = None
    explanation_id: str | None = None
    status: SourceCoverageStatus
    owner_scope: list[str] = Field(min_length=1)
    source_counts: dict[str, int] = Field(default_factory=dict)
    required_source_types: list[GroundingSourceType] = Field(default_factory=list)
    missing_source_types: list[GroundingSourceType] = Field(default_factory=list)
    weak_source_refs: list[str] = Field(default_factory=list)
    strong_source_refs: list[str] = Field(default_factory=list)
    coverage_score: float = Field(ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class GroundingQuery(BaseModel):
    """Query grounding and citation records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    trace_id: str | None = None
    response_id: str | None = None
    explanation_id: str | None = None
    source_type: GroundingSourceType | None = None
    trust_level: GroundingTrustLevel | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)


def reject_hidden_or_secret_text(value: str, field_name: str) -> None:
    """Reject hidden reasoning, raw prompts, and obvious raw secret values."""

    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    lowered = value.lower()
    if any(marker in lowered for marker in _HIDDEN_MARKERS):
        raise ValueError(f"{field_name} must not contain hidden reasoning or raw prompts")
    if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
        raise ValueError(f"{field_name} must not contain raw secrets")


def reject_secret_like_payload(value: Any, path: str = "") -> None:
    """Reject recursive secret-like metadata keys and obvious secret values."""

    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                raise ValueError(f"payload contains secret-like key: {path}{key}")
            reject_secret_like_payload(item, f"{path}{key}.")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_secret_like_payload(item, f"{path}{index}.")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _SECRET_VALUE_MARKERS):
            raise ValueError(f"payload contains secret-like value at {path.rstrip('.')}")


__all__ = [
    "GroundingQuery",
    "GroundingSensitivity",
    "GroundingSource",
    "GroundingSourceCreateRequest",
    "GroundingSourceType",
    "GroundingTrustLevel",
    "GroundingVerificationRequest",
    "GroundingVerificationRun",
    "GroundingVerificationStatus",
    "SourceCoverageReport",
    "SourceCoverageStatus",
    "reject_hidden_or_secret_text",
    "reject_secret_like_payload",
]
