"""Resource reference and link integrity contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aion_brain.contracts.model_outputs import reject_secret_like_payload

RelationType = Literal[
    "references",
    "depends_on",
    "produced",
    "produced_by",
    "caused",
    "caused_by",
    "grounded_by",
    "cites",
    "explains",
    "blocks",
    "blocked_by",
    "supersedes",
    "superseded_by",
    "derived_from",
    "related_to",
    "owns",
    "belongs_to",
    "generic",
]
ResourceLinkStatus = Literal["active", "verified", "broken", "stale", "deleted"]
BrokenReferenceIssueType = Literal[
    "missing_target",
    "missing_source",
    "stale_target",
    "deleted_target",
    "type_mismatch",
    "scope_mismatch",
    "invalid_uri",
    "forbidden_reference",
    "unresolved_reference",
    "generic",
]
BrokenReferenceStatus = Literal["open", "resolved", "dismissed", "archived"]
OrphanedResourceIssueType = Literal[
    "no_inbound_refs",
    "no_outbound_refs",
    "missing_provenance",
    "missing_audit",
    "stale_index",
    "generic",
]
Severity = Literal["info", "low", "medium", "high", "critical"]


def _must_be_aion_uri(value: str) -> str:
    if not value.startswith("aion://"):
        raise ValueError("resource URI must start with aion://")
    return value


class ResourceReferenceLink(BaseModel):
    """Directed link between two AION resource URIs."""

    model_config = ConfigDict(extra="forbid")

    resource_link_id: str = Field(min_length=1)
    trace_id: str | None = None
    source_resource_uri: str
    target_resource_uri: str
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    relation_type: RelationType = "references"
    status: ResourceLinkStatus = "active"
    confidence: float = Field(ge=0.0, le=1.0)
    discovered_by: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    verified_at: datetime | None = None
    broken_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("source_resource_uri", "target_resource_uri")
    @classmethod
    def uri_must_be_aion_uri(cls, value: str) -> str:
        return _must_be_aion_uri(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ResourceReferenceCreateRequest(BaseModel):
    """Request to create a registry-owned reference link."""

    model_config = ConfigDict(extra="forbid")

    resource_link_id: str | None = None
    trace_id: str | None = None
    source_resource_uri: str
    target_resource_uri: str
    relation_type: RelationType = "references"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    discovered_by: str = Field(default="manual", min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("source_resource_uri", "target_resource_uri")
    @classmethod
    def uri_must_be_aion_uri(cls, value: str) -> str:
        return _must_be_aion_uri(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class BrokenReference(BaseModel):
    """Detected broken or stale reference. It does not repair source data."""

    model_config = ConfigDict(extra="forbid")

    broken_reference_id: str = Field(min_length=1)
    trace_id: str | None = None
    source_resource_uri: str
    target_resource_uri: str
    source_type: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    issue_type: BrokenReferenceIssueType
    severity: Severity
    status: BrokenReferenceStatus = "open"
    reason: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    validation_run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("source_resource_uri", "target_resource_uri")
    @classmethod
    def uri_must_be_aion_uri(cls, value: str) -> str:
        return _must_be_aion_uri(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class OrphanedResource(BaseModel):
    """Detected resource with weak registry connectivity."""

    model_config = ConfigDict(extra="forbid")

    orphaned_resource_id: str = Field(min_length=1)
    trace_id: str | None = None
    resource_uri: str
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    issue_type: OrphanedResourceIssueType
    severity: Severity
    status: BrokenReferenceStatus = "open"
    reason: str = Field(min_length=1)
    inbound_ref_count: int = Field(ge=0)
    outbound_ref_count: int = Field(ge=0)
    validation_run_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    @field_validator("resource_uri")
    @classmethod
    def uri_must_be_aion_uri(cls, value: str) -> str:
        return _must_be_aion_uri(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "BrokenReference",
    "BrokenReferenceIssueType",
    "BrokenReferenceStatus",
    "OrphanedResource",
    "OrphanedResourceIssueType",
    "RelationType",
    "ResourceLinkStatus",
    "ResourceReferenceCreateRequest",
    "ResourceReferenceLink",
    "Severity",
]
