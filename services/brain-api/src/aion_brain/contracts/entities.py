"""Entity resolver and canonical reference contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.concepts import reject_secret_like_keys

EntityType = Literal[
    "generic",
    "actor_ref",
    "organization_ref",
    "place_ref",
    "object_ref",
    "event_ref",
    "document_ref",
    "system_ref",
    "capability_ref",
    "concept_ref",
    "unknown",
]
EntityStatus = Literal["proposed", "active", "merged", "archived", "rejected"]
EntitySensitivity = Literal["public", "internal", "confidential", "restricted"]
EntityAliasType = Literal[
    "exact",
    "shorthand",
    "alternate",
    "normalized",
    "user_supplied",
    "system_generated",
]
EntityMentionType = Literal[
    "explicit",
    "inferred_from_text",
    "system_reference",
    "unresolved",
    "alias",
]
EntityMentionSourceType = Literal[
    "dialogue_message",
    "response",
    "evidence",
    "evidence_chunk",
    "memory",
    "belief_claim",
    "graph_node",
    "graph_edge",
    "trace",
    "command",
    "workflow",
    "task",
    "audit_entry",
    "system",
    "generic",
]
ReferenceEndpointType = Literal[
    "dialogue_message",
    "response",
    "evidence",
    "evidence_chunk",
    "memory",
    "belief_claim",
    "graph_node",
    "graph_edge",
    "trace",
    "reasoning",
    "plan",
    "execution",
    "workflow",
    "task",
    "command",
    "audit_entry",
    "entity",
    "concept",
    "system",
]
ReferenceRelationType = Literal[
    "refers_to",
    "alias_of",
    "same_as",
    "related_to",
    "grounded_by",
    "mentioned_in",
    "derived_from",
    "superseded_by",
    "produced_by",
    "unresolved_reference",
]
EntityResolutionStatus = Literal["completed", "dry_run", "failed", "blocked_by_policy"]
EntityProposalStatus = Literal["proposed", "approved", "rejected", "completed", "cancelled"]

_HIDDEN_MARKERS = {
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "hidden reasoning",
    "raw_prompt",
    "raw prompt",
}
_SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "ghp_", "-----begin private key-----")
_SENSITIVE_IDENTITY_KEYS = {
    "age",
    "biometric",
    "date_of_birth",
    "disability",
    "ethnicity",
    "gender_identity",
    "health",
    "nationality",
    "political_view",
    "race",
    "religion",
    "sexual_orientation",
}


class EntityRecord(BaseModel):
    """One canonical reference record."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1)
    trace_id: str | None = None
    canonical_name: str = Field(min_length=1)
    normalized_name: str = Field(min_length=1)
    entity_type: EntityType
    status: EntityStatus
    owner_scope: list[str] = Field(min_length=1)
    concept_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    graph_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    sensitivity: EntitySensitivity
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    merged_into_entity_id: str | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("canonical_name", "normalized_name")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class EntityCreateRequest(BaseModel):
    """Request to create one canonical entity reference."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str | None = None
    trace_id: str | None = None
    canonical_name: str = Field(min_length=1)
    entity_type: EntityType = "generic"
    owner_scope: list[str] = Field(min_length=1)
    concept_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    graph_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    sensitivity: EntitySensitivity = "internal"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("canonical_name")
    @classmethod
    def canonical_name_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class EntityAlias(BaseModel):
    """Alias that may resolve to an entity."""

    model_config = ConfigDict(extra="forbid")

    alias_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    alias: str = Field(min_length=1)
    normalized_alias: str = Field(min_length=1)
    alias_type: EntityAliasType
    confidence: float = Field(ge=0.0, le=1.0)
    source_type: str | None = None
    source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("alias", "normalized_alias")
    @classmethod
    def alias_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class EntityAliasCreateRequest(BaseModel):
    """Request to add an entity alias."""

    model_config = ConfigDict(extra="forbid")

    alias_id: str | None = None
    entity_id: str = Field(min_length=1)
    alias: str = Field(min_length=1)
    alias_type: EntityAliasType = "alternate"
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    source_type: str | None = None
    source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("alias")
    @classmethod
    def alias_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class EntityMention(BaseModel):
    """Raw mention extracted from an AION-owned source."""

    model_config = ConfigDict(extra="forbid")

    mention_id: str = Field(min_length=1)
    trace_id: str | None = None
    entity_id: str | None = None
    source_type: EntityMentionSourceType
    source_id: str = Field(min_length=1)
    mention_text: str = Field(min_length=1)
    normalized_mention: str = Field(min_length=1)
    mention_type: EntityMentionType
    start_char: int | None = None
    end_char: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    resolved: bool
    resolution_score: float | None = Field(default=None, ge=0.0, le=1.0)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("mention_text", "normalized_mention")
    @classmethod
    def mention_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class EntityMentionCreateRequest(BaseModel):
    """Request to create one mention."""

    model_config = ConfigDict(extra="forbid")

    mention_id: str | None = None
    trace_id: str | None = None
    entity_id: str | None = None
    source_type: EntityMentionSourceType
    source_id: str = Field(min_length=1)
    mention_text: str = Field(min_length=1)
    mention_type: EntityMentionType = "explicit"
    start_char: int | None = None
    end_char: int | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("mention_text")
    @classmethod
    def mention_must_be_safe(cls, value: str) -> str:
        _reject_unsafe_text(value)
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class ReferenceLink(BaseModel):
    """A canonical reference relation across AION-owned records."""

    model_config = ConfigDict(extra="forbid")

    reference_link_id: str = Field(min_length=1)
    trace_id: str | None = None
    source_type: ReferenceEndpointType
    source_id: str = Field(min_length=1)
    target_type: ReferenceEndpointType
    target_id: str = Field(min_length=1)
    relation_type: ReferenceRelationType
    entity_id: str | None = None
    concept_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class ReferenceLinkCreateRequest(BaseModel):
    """Request to create a canonical reference link."""

    model_config = ConfigDict(extra="forbid")

    reference_link_id: str | None = None
    trace_id: str | None = None
    source_type: ReferenceEndpointType
    source_id: str = Field(min_length=1)
    target_type: ReferenceEndpointType
    target_id: str = Field(min_length=1)
    relation_type: ReferenceRelationType = "refers_to"
    entity_id: str | None = None
    concept_id: str | None = None
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class EntityResolutionRequest(BaseModel):
    """Request to resolve mentions to canonical entity references."""

    model_config = ConfigDict(extra="forbid")

    resolution_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    source_type: EntityMentionSourceType | None = None
    source_id: str | None = None
    text: str | None = None
    mentions: list[EntityMentionCreateRequest] = Field(default_factory=list)
    create_missing_entities: bool = False
    auto_link: bool = True
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @model_validator(mode="after")
    def source_or_mentions_must_exist(self) -> EntityResolutionRequest:
        if not self.text and not self.source_id and not self.mentions:
            raise ValueError("text or source_id or mentions must be present")
        return self

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_entity_metadata(value)
        return value


class EntityResolutionCandidate(BaseModel):
    """One possible entity match for a mention."""

    model_config = ConfigDict(extra="forbid")

    entity: EntityRecord
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str]
    matched_aliases: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class EntityResolutionResult(BaseModel):
    """Result of one deterministic entity resolution run."""

    model_config = ConfigDict(extra="forbid")

    resolution_run_id: str
    status: EntityResolutionStatus
    owner_scope: list[str] = Field(min_length=1)
    source_type: str | None
    source_id: str | None
    mentions_seen: int = Field(ge=0)
    mentions_resolved: int = Field(ge=0)
    mentions_unresolved: int = Field(ge=0)
    entities_created: int = Field(ge=0)
    reference_links_created: int = Field(ge=0)
    candidates: dict[str, list[EntityResolutionCandidate]]
    created_mentions: list[EntityMention]
    created_entities: list[EntityRecord]
    created_links: list[ReferenceLink]
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None


class EntityQuery(BaseModel):
    """Query canonical entity references."""

    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    scope: list[str] = Field(min_length=1)
    entity_types: list[EntityType] = Field(default_factory=list)
    statuses: list[EntityStatus] = Field(default_factory=list)
    concept_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    belief_refs: list[str] = Field(default_factory=list)
    include_merged: bool = False
    include_deleted: bool = False
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    limit: int = Field(default=50, ge=1, le=500)


class EntityQueryResult(BaseModel):
    """Entity query result with related records."""

    model_config = ConfigDict(extra="forbid")

    entities: list[EntityRecord]
    aliases: list[EntityAlias]
    mentions: list[EntityMention]
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityMergeProposal(BaseModel):
    """Proposal to merge duplicate canonical entity references."""

    model_config = ConfigDict(extra="forbid")

    merge_proposal_id: str = Field(min_length=1)
    trace_id: str | None = None
    primary_entity_id: str = Field(min_length=1)
    duplicate_entity_id: str = Field(min_length=1)
    status: EntityProposalStatus
    score: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    approval_request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @model_validator(mode="after")
    def entities_must_differ(self) -> EntityMergeProposal:
        if self.primary_entity_id == self.duplicate_entity_id:
            raise ValueError("primary_entity_id cannot equal duplicate_entity_id")
        return self


class EntitySplitProposal(BaseModel):
    """Proposal to split one overloaded canonical reference."""

    model_config = ConfigDict(extra="forbid")

    split_proposal_id: str = Field(min_length=1)
    trace_id: str | None = None
    entity_id: str = Field(min_length=1)
    status: EntityProposalStatus
    reason: str = Field(min_length=1)
    proposed_entities: list[dict[str, Any]]
    evidence_refs: list[str] = Field(default_factory=list)
    approval_request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None


class EntityDeleteRequest(BaseModel):
    """Request to archive or soft-delete an entity."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class EntityExtractMentionsRequest(BaseModel):
    """API request for deterministic mention extraction."""

    model_config = ConfigDict(extra="forbid")

    source_type: EntityMentionSourceType
    source_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    trace_id: str | None = None
    max_mentions: int = Field(default=50, ge=1, le=100)


class EntityMergeProposalCreateRequest(BaseModel):
    """Request to propose an entity merge."""

    model_config = ConfigDict(extra="forbid")

    primary_entity_id: str = Field(min_length=1)
    duplicate_entity_id: str = Field(min_length=1)
    trace_id: str | None = None
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    created_by: str | None = None


class EntityProposalDecisionRequest(BaseModel):
    """Request to approve or reject a merge/split proposal."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    approval_present: bool = True
    reason: str = Field(min_length=1)


class EntitySplitProposalCreateRequest(BaseModel):
    """Request to propose an entity split."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    proposed_entities: list[dict[str, Any]] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    created_by: str | None = None


def reject_entity_metadata(value: Any, path: str = "") -> None:
    """Reject secrets and sensitive inferred identity metadata keys."""
    reject_secret_like_keys(value, path)
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if lowered in _SENSITIVE_IDENTITY_KEYS or any(
                lowered.endswith(f"_{part}") for part in _SENSITIVE_IDENTITY_KEYS
            ):
                raise ValueError(f"metadata contains sensitive identity key: {path}{key}")
            reject_entity_metadata(item, f"{path}{key}.")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_entity_metadata(item, f"{path}{index}.")


def text_has_hidden_markers(value: str) -> bool:
    """Return true when text contains hidden reasoning markers."""
    lowered = value.lower()
    return any(marker in lowered for marker in _HIDDEN_MARKERS)


def text_has_secret_markers(value: str) -> bool:
    """Return true when text contains raw secret markers."""
    lowered = value.lower()
    return any(marker in lowered for marker in _SECRET_VALUE_MARKERS)


def _reject_unsafe_text(value: str) -> None:
    if not value.strip():
        raise ValueError("value cannot be empty")
    if text_has_hidden_markers(value):
        raise ValueError("value must not contain hidden reasoning")
    if text_has_secret_markers(value):
        raise ValueError("value must not contain raw secrets")


__all__ = [
    "EntityAlias",
    "EntityAliasCreateRequest",
    "EntityCreateRequest",
    "EntityDeleteRequest",
    "EntityExtractMentionsRequest",
    "EntityMention",
    "EntityMentionCreateRequest",
    "EntityMergeProposal",
    "EntityMergeProposalCreateRequest",
    "EntityProposalDecisionRequest",
    "EntityQuery",
    "EntityQueryResult",
    "EntityRecord",
    "EntityResolutionCandidate",
    "EntityResolutionRequest",
    "EntityResolutionResult",
    "EntitySplitProposal",
    "EntitySplitProposalCreateRequest",
    "ReferenceLink",
    "ReferenceLinkCreateRequest",
    "reject_entity_metadata",
    "text_has_hidden_markers",
    "text_has_secret_markers",
]
