"""Temporal graph memory contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

GraphitiConfigState = Literal["active", "disabled", "unavailable", "failed"]
GraphitiBackendType = Literal["neo4j", "falkordb", "in_memory_fake", "unknown"]
_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
}
_BANNED_SOURCE_TYPES = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "hr",
    "procurement",
    "it",
}


class GraphNode(BaseModel):
    """A generic temporal graph node."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1)
    node_type: str = Field(min_length=1)
    label: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    properties: dict[str, Any]
    source_event_id: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    sensitivity: str
    valid_from: datetime | None
    valid_to: datetime | None
    observed_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class GraphEdge(BaseModel):
    """A generic temporal graph relationship."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str = Field(min_length=1)
    edge_type: str = Field(min_length=1)
    from_node_id: str = Field(min_length=1)
    to_node_id: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    properties: dict[str, Any]
    source_event_id: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    sensitivity: str
    valid_from: datetime | None
    valid_to: datetime | None
    observed_at: datetime
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class GraphQuery(BaseModel):
    """Generic temporal graph retrieval request."""

    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    scope: list[str] = Field(min_length=1)
    node_types: list[str] = Field(default_factory=list)
    edge_types: list[str] = Field(default_factory=list)
    start_node_id: str | None = None
    max_depth: int = Field(default=2, ge=1, le=5)
    limit: int = Field(default=25, ge=1, le=100)
    include_expired: bool = False
    as_of: datetime | None = None


class GraphQueryResult(BaseModel):
    """Temporal graph retrieval result."""

    model_config = ConfigDict(extra="forbid")

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    score: float = Field(ge=0.0, le=1.0)
    retrieval_source: str
    adapter_name: str
    metadata: dict[str, Any]


class GraphUpsertResponse(BaseModel):
    """Graph upsert response."""

    model_config = ConfigDict(extra="forbid")

    upserted: bool
    object_type: str
    object_id: str
    reason: str | None


class GraphMemoryAdapterStatus(BaseModel):
    """Public status summary for one graph memory adapter."""

    model_config = ConfigDict(extra="forbid")

    adapter_name: str = Field(min_length=1)
    active: bool
    available: bool
    default: bool
    reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in public metadata."""
        _reject_secret_like_keys(value)
        return value


class GraphitiConfigStatus(BaseModel):
    """Public status for an AION-managed Graphiti configuration."""

    model_config = ConfigDict(extra="forbid")

    graphiti_config_id: str = Field(min_length=1)
    config_name: str = Field(min_length=1)
    adapter_name: str = Field(min_length=1)
    status: GraphitiConfigState
    backend_type: GraphitiBackendType
    endpoint_ref: str | None
    available: bool
    reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None
    updated_at: datetime | None
    last_health_check_at: datetime | None

    @field_validator("config_name")
    @classmethod
    def config_name_must_be_safe(cls, value: str) -> str:
        """Reject empty and path-like config names."""
        return _safe_config_name(value)

    @field_validator("endpoint_ref")
    @classmethod
    def endpoint_ref_must_not_contain_secrets(cls, value: str | None) -> str | None:
        """Reject secret-like endpoint references."""
        if value is not None:
            _reject_secret_like_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def config_metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in public metadata."""
        _reject_secret_like_keys(value)
        return value


class GraphitiSyncRequest(BaseModel):
    """Request to sync canonical graph records into optional Graphiti."""

    model_config = ConfigDict(extra="forbid")

    config_name: str = "default"
    scope: list[str] = Field(min_length=1)
    source_types: list[str] = Field(default_factory=list)
    limit: int = Field(default=10000, ge=1, le=1_000_000)
    dry_run: bool = False
    force: bool = False

    @field_validator("config_name")
    @classmethod
    def config_name_must_be_safe(cls, value: str) -> str:
        """Reject unsafe config names."""
        return _safe_config_name(value)


class GraphitiSyncResponse(BaseModel):
    """Response for a Graphiti graph sync request."""

    model_config = ConfigDict(extra="forbid")

    synced: bool
    dry_run: bool
    config_name: str
    indexed_nodes: int = Field(ge=0)
    indexed_edges: int = Field(ge=0)
    skipped: int = Field(ge=0)
    failed: int = Field(ge=0)
    status: GraphitiConfigStatus
    reason: str | None


class GraphitiEpisodeRequest(BaseModel):
    """Request to add temporal context as a Graphiti episode."""

    model_config = ConfigDict(extra="forbid")

    episode_id: str | None
    trace_id: str | None
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    scope: list[str] = Field(min_length=1)
    observed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_type")
    @classmethod
    def source_type_must_be_generic(cls, value: str) -> str:
        """Reject domain-specific source type vocabulary."""
        normalized = value.lower().replace("-", "_")
        if normalized in _BANNED_SOURCE_TYPES:
            raise ValueError("source_type must be generic")
        return value

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        """Reject blank episode content."""
        if not value.strip():
            raise ValueError("content cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def episode_metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in episode metadata."""
        _reject_secret_like_keys(value)
        return value


class GraphitiEpisodeResponse(BaseModel):
    """Response from adding a Graphiti episode."""

    model_config = ConfigDict(extra="forbid")

    added: bool
    episode_id: str
    status: str
    reason: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def response_metadata_must_not_contain_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Reject secret-like keys in response metadata."""
        _reject_secret_like_keys(value)
        return value


def _safe_config_name(value: str) -> str:
    if not value or "/" in value or "\\" in value or ".." in value:
        raise ValueError("config_name cannot be empty or contain path traversal")
    return value


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


def _reject_secret_like_text(value: str) -> None:
    normalized = value.lower().replace("-", "_")
    if any(secret in normalized for secret in _SECRET_KEY_PARTS):
        raise ValueError("endpoint_ref must not contain secret-like values")
