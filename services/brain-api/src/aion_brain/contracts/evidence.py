"""Evidence Vault contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EvidenceSourceType = Literal[
    "text",
    "event",
    "memory",
    "graph",
    "trace",
    "model_call",
    "execution_output",
    "module_output",
    "task_output",
    "user_input",
    "system_note",
    "url_metadata",
    "file_metadata",
]

EvidenceSensitivity = Literal["public", "internal", "confidential", "restricted"]

EvidenceTargetType = Literal[
    "event",
    "memory",
    "graph_node",
    "graph_edge",
    "trace",
    "reasoning",
    "model_call",
    "plan",
    "execution",
    "task",
    "goal",
    "reflection",
    "skill",
    "capability",
    "module",
    "policy",
    "evaluation",
    "learning",
]

EvidenceRelationType = Literal[
    "supports",
    "cites",
    "derived_from",
    "contradicts",
    "references",
    "produced_by",
    "explains",
    "source_for",
]

GroundingVerificationStatus = Literal[
    "supported",
    "contradicted",
    "insufficient_evidence",
    "unverified",
]

SECRET_METADATA_KEYS = {"password", "secret", "token", "api_key", "private_key"}


class EvidenceRecord(BaseModel):
    """Canonical source evidence metadata."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    trace_id: str | None
    source_type: EvidenceSourceType
    source_ref: str | None
    owner_scope: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str
    content_hash: str = Field(min_length=1)
    content_ref: str | None
    media_type: str = Field(min_length=1)
    sensitivity: EvidenceSensitivity
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None
    updated_at: datetime | None
    deleted_at: datetime | None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_metadata(value)
        return value


class EvidenceChunk(BaseModel):
    """Deterministic text chunk for evidence retrieval."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1)
    text_hash: str = Field(min_length=1)
    token_count_hint: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None
    deleted_at: datetime | None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_metadata(value)
        return value


class EvidenceIngestRequest(BaseModel):
    """Request to ingest text evidence or metadata-only content references."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str | None = None
    trace_id: str | None = None
    source_type: EvidenceSourceType
    source_ref: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    title: str = Field(min_length=1)
    content_text: str | None = None
    summary: str | None = None
    content_ref: str | None = None
    media_type: str = "text/plain"
    sensitivity: EvidenceSensitivity = "internal"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_size_chars: int = Field(default=2000, ge=500, le=10000)
    chunk_overlap_chars: int = Field(default=200, ge=0, le=1000)

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_metadata(value)
        return value

    @model_validator(mode="after")
    def content_must_be_present(self) -> "EvidenceIngestRequest":
        """Require text or a content reference, and valid chunk overlap."""
        if not self.content_text and not self.content_ref:
            raise ValueError("content_text or content_ref is required")
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise ValueError("chunk_overlap_chars must be smaller than chunk_size_chars")
        return self


class EvidenceIngestResponse(BaseModel):
    """Evidence ingestion response."""

    model_config = ConfigDict(extra="forbid")

    ingested: bool
    evidence: EvidenceRecord
    chunk_count: int
    reason: str | None


class EvidenceSearchRequest(BaseModel):
    """Policy-gated evidence search request."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    scope: list[str] = Field(min_length=1)
    source_types: list[EvidenceSourceType] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)


class EvidenceSearchResult(BaseModel):
    """Ranked evidence search result."""

    model_config = ConfigDict(extra="forbid")

    evidence: EvidenceRecord
    chunk: EvidenceChunk | None
    score: float = Field(ge=0.0, le=1.0)
    matched_terms: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceLink(BaseModel):
    """Typed relation between evidence and a Brain-owned target."""

    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    target_type: EvidenceTargetType
    target_id: str = Field(min_length=1)
    relation_type: EvidenceRelationType
    trace_id: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None
    deleted_at: datetime | None

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_metadata(value)
        return value


class GroundingStatement(BaseModel):
    """Statement to check against evidence."""

    model_config = ConfigDict(extra="forbid")

    statement_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_metadata(value)
        return value


class GroundingRequest(BaseModel):
    """Request to deterministically ground statements in evidence."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None
    statements: list[GroundingStatement] = Field(min_length=1)
    scope: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    limit_per_statement: int = Field(default=5, ge=1, le=10)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)


class GroundingClaim(BaseModel):
    """Deterministic source-grounding claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    trace_id: str | None
    statement: str = Field(min_length=1)
    evidence_refs: list[str]
    chunk_refs: list[str]
    score: float = Field(ge=0.0, le=1.0)
    verification_status: GroundingVerificationStatus
    rationale: str
    created_at: datetime | None


class GroundingResponse(BaseModel):
    """Grounding response for one or more statements."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None
    claims: list[GroundingClaim]
    created_at: datetime


class ObjectRef(BaseModel):
    """AION-owned object reference contract."""

    model_config = ConfigDict(extra="forbid")

    content_ref: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like metadata keys."""
        reject_secret_metadata(value)
        return value


def reject_secret_metadata(value: dict[str, Any]) -> None:
    """Reject recursive secret-like metadata keys."""
    for key, item in value.items():
        if key.lower() in SECRET_METADATA_KEYS:
            raise ValueError(f"metadata must not contain secret-like key: {key}")
        if isinstance(item, dict):
            reject_secret_metadata(item)
