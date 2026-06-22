"""Memory contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MemoryType = Literal[
    "working",
    "episodic",
    "semantic",
    "procedural",
    "preference",
    "graph",
    "audit",
]
TurboVecIndexState = Literal["active", "disabled", "unavailable", "rebuilding", "failed"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
    "authorization",
}


class MemoryRecord(BaseModel):
    """Policy-aware memory metadata and summary."""

    model_config = ConfigDict(extra="forbid")

    memory_id: str
    memory_type: MemoryType
    owner_scope: list[str]
    source_event_id: str | None
    content_ref: str | None
    summary: str
    confidence: float
    sensitivity: str
    created_at: datetime
    expires_at: datetime | None
    metadata: dict[str, Any]


class MemoryRetrievalRequest(BaseModel):
    """Request contract for deterministic memory retrieval."""

    model_config = ConfigDict(extra="forbid")

    query: str
    scope: list[str]
    limit: int = Field(default=10, ge=1, le=100)
    memory_types: list[MemoryType] = Field(default_factory=list)


class SemanticMemoryQuery(BaseModel):
    """Request contract for semantic memory recall."""

    model_config = ConfigDict(extra="forbid")

    query: str
    scope: list[str]
    limit: int = Field(default=10, ge=1, le=100)
    memory_types: list[MemoryType] = Field(default_factory=list)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)


class SemanticMemoryResult(BaseModel):
    """Semantic recall result grounded in a MemoryRecord."""

    model_config = ConfigDict(extra="forbid")

    memory: MemoryRecord
    score: float = Field(ge=0.0, le=1.0)
    retrieval_source: str
    adapter_name: str
    matched_terms: list[str]
    metadata: dict[str, Any]


class SemanticIndexRequest(BaseModel):
    """Semantic index request."""

    model_config = ConfigDict(extra="forbid")

    memory_id: str
    force_reindex: bool = False


class SemanticIndexResponse(BaseModel):
    """Semantic index response."""

    model_config = ConfigDict(extra="forbid")

    indexed: bool
    memory_id: str
    adapter_name: str
    embedding_id: str | None
    reason: str | None


class MemoryDeleteResponse(BaseModel):
    """Response contract for soft deletion."""

    model_config = ConfigDict(extra="forbid")

    deleted: bool
    memory_id: str


class TurboVecIndexStatus(BaseModel):
    """Status of an AION-managed TurboVec recall index."""

    model_config = ConfigDict(extra="forbid")

    index_id: str = Field(min_length=1)
    index_name: str = Field(min_length=1)
    adapter_name: str = Field(min_length=1)
    dimensions: int = Field(gt=0)
    bit_width: int
    index_path: str = Field(min_length=1)
    status: TurboVecIndexState
    entry_count: int = Field(ge=0)
    available: bool
    reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None
    updated_at: datetime | None
    rebuilt_at: datetime | None

    @field_validator("bit_width")
    @classmethod
    def bit_width_must_be_supported(cls, value: int) -> int:
        """Validate supported compressed vector bit widths."""
        if value not in {2, 3, 4, 8}:
            raise ValueError("bit_width must be one of 2, 3, 4, or 8")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in public metadata."""
        _reject_secret_like_keys(value)
        return value


class TurboVecRebuildRequest(BaseModel):
    """Request to rebuild a TurboVec recall index from canonical memory."""

    model_config = ConfigDict(extra="forbid")

    index_name: str = "default"
    scope: list[str] = Field(min_length=1)
    memory_types: list[MemoryType] = Field(default_factory=list)
    limit: int = Field(default=10000, ge=1, le=1_000_000)
    force: bool = False
    dry_run: bool = False

    @field_validator("index_name")
    @classmethod
    def index_name_must_be_safe(cls, value: str) -> str:
        """Reject path traversal and nested index names."""
        if not value or "/" in value or "\\" in value or ".." in value:
            raise ValueError("index_name cannot be empty or contain path traversal")
        return value


class TurboVecRebuildResponse(BaseModel):
    """Response for a TurboVec index rebuild."""

    model_config = ConfigDict(extra="forbid")

    rebuilt: bool
    dry_run: bool
    index_name: str
    indexed: int = Field(ge=0)
    skipped: int = Field(ge=0)
    failed: int = Field(ge=0)
    status: TurboVecIndexStatus
    reason: str | None


class SemanticAdapterStatus(BaseModel):
    """Status summary for one semantic memory adapter."""

    model_config = ConfigDict(extra="forbid")

    adapter_name: str = Field(min_length=1)
    active: bool
    available: bool
    default: bool
    reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def adapter_metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in adapter metadata."""
        _reject_secret_like_keys(value)
        return value


class TurboVecReindexRequest(BaseModel):
    """Request to reindex one memory record through TurboVec."""

    model_config = ConfigDict(extra="forbid")

    index_name: str = "default"
    force: bool = False

    @field_validator("index_name")
    @classmethod
    def index_name_must_be_safe(cls, value: str) -> str:
        """Reject path traversal and nested index names."""
        return TurboVecRebuildRequest.index_name_must_be_safe(value)


class SemanticRetrieveResponse(BaseModel):
    """Semantic retrieval response with adapter fallback metadata."""

    model_config = ConfigDict(extra="forbid")

    results: list[SemanticMemoryResult]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def metadata_must_not_contain_secrets(self) -> "SemanticRetrieveResponse":
        """Reject secret-like keys in response metadata."""
        _reject_secret_like_keys(self.metadata)
        return self


def _reject_secret_like_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(secret in normalized for secret in _SECRET_KEY_PARTS):
                raise ValueError("metadata must not contain secret-like keys")
            _reject_secret_like_keys(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_like_keys(item)
