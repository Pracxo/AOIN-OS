"""Global Resource Registry contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.resource_references import (
    BrokenReference,
    OrphanedResource,
    ResourceReferenceLink,
)

ResourceType = Literal[
    "audit_entry",
    "provenance_link",
    "evidence",
    "evidence_chunk",
    "memory",
    "belief_claim",
    "concept",
    "entity",
    "entity_mention",
    "situation",
    "state_atom",
    "decision_frame",
    "decision_option",
    "decision_record",
    "outcome",
    "expected_effect",
    "observed_effect",
    "explanation",
    "trace_narrative",
    "grounding_source",
    "citation",
    "prompt_packet",
    "model_output",
    "response_candidate",
    "action_proposal",
    "execution_handoff",
    "run_supervision",
    "notification",
    "alert",
    "schedule",
    "reminder",
    "incident",
    "root_cause_candidate",
    "recovery_review",
    "backup_job",
    "release_package",
    "freeze_gate",
    "contract_snapshot",
    "compatibility_scan",
    "interface_drift",
    "migration_note",
    "contract_report",
    "extension_package",
    "extension_compatibility",
    "extension_install_plan",
    "security_scan",
    "resilience_test",
    "operator_action",
    "workflow",
    "command",
    "task",
    "goal",
    "generic",
]
ResourceStatus = Literal["active", "archived", "deleted", "stale", "missing", "unknown"]
ResourceVisibility = Literal["internal", "operator", "audit", "hidden", "restricted"]
ResourceSensitivity = Literal["public", "internal", "confidential", "restricted"]
RegistryRunMode = Literal["dry_run", "controlled"]
RegistryRunStatus = Literal["completed", "dry_run", "warning", "failed", "blocked_by_policy"]
RegistrySnapshotType = Literal[
    "manual", "validation", "rebuild", "release", "freeze", "backup", "operator"
]


class ResourceDescriptor(BaseModel):
    """Safe descriptor for a source-system record."""

    model_config = ConfigDict(extra="forbid")

    resource_uri: str
    resource_type: ResourceType
    resource_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    source_system: str = Field(min_length=1)
    status: ResourceStatus = "active"
    visibility: ResourceVisibility = "internal"
    sensitivity: ResourceSensitivity = "internal"
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    deleted_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator("resource_uri")
    @classmethod
    def uri_must_be_aion_uri(cls, value: str) -> str:
        if not value.startswith("aion://"):
            raise ValueError("resource_uri must start with aion://")
        reject_hidden_or_secret_text(value, "resource_uri")
        return value

    @field_validator("title", "summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "resource descriptor text")
        return value.strip()

    @field_validator("refs")
    @classmethod
    def refs_must_be_safe(cls, value: list[str]) -> list[str]:
        for item in value:
            reject_hidden_or_secret_text(item, "resource ref")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ResourceIndexRecord(BaseModel):
    """Registry-owned index row for a resource descriptor."""

    model_config = ConfigDict(extra="forbid")

    resource_index_id: str = Field(min_length=1)
    descriptor: ResourceDescriptor
    created_at: datetime | None = None


class ResourceIndexUpsertRequest(BaseModel):
    """Request to upsert a resource descriptor into the registry index."""

    model_config = ConfigDict(extra="forbid")

    resource_index_id: str | None = None
    descriptor: ResourceDescriptor
    created_by: str | None = None


class ReferenceValidationRequest(BaseModel):
    """Request to validate indexed resource links."""

    model_config = ConfigDict(extra="forbid")

    validation_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: RegistryRunMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    resource_types: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    include_orphans: bool = True
    include_stale: bool = True
    create_notifications: bool = False
    create_incident_signals: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ReferenceValidationRun(BaseModel):
    """Result of a reference validation pass."""

    model_config = ConfigDict(extra="forbid")

    validation_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: RegistryRunStatus
    mode: RegistryRunMode
    owner_scope: list[str] = Field(min_length=1)
    resource_types: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    resources_checked: int = Field(ge=0)
    links_checked: int = Field(ge=0)
    broken_count: int = Field(ge=0)
    orphaned_count: int = Field(ge=0)
    stale_count: int = Field(ge=0)
    broken_references: list[BrokenReference] = Field(default_factory=list)
    orphaned_resources: list[OrphanedResource] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class RegistryRebuildRequest(BaseModel):
    """Request to rebuild registry-owned index records from source descriptors."""

    model_config = ConfigDict(extra="forbid")

    rebuild_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    mode: RegistryRunMode = "dry_run"
    owner_scope: list[str] = Field(min_length=1)
    resource_types: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    clear_missing: bool = False
    create_snapshot: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def clear_missing_must_not_delete_sources(self) -> RegistryRebuildRequest:
        if self.metadata.get("delete_source_records") is True:
            raise ValueError("registry rebuild must not delete source records")
        return self


class RegistryRebuildRun(BaseModel):
    """Result of a registry rebuild pass."""

    model_config = ConfigDict(extra="forbid")

    rebuild_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    status: RegistryRunStatus
    mode: RegistryRunMode
    owner_scope: list[str] = Field(min_length=1)
    resource_types: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    resources_seen: int = Field(ge=0)
    resources_indexed: int = Field(ge=0)
    links_indexed: int = Field(ge=0)
    skipped: int = Field(ge=0)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class RegistrySnapshot(BaseModel):
    """Deterministic snapshot of registry-owned index and link metadata."""

    model_config = ConfigDict(extra="forbid")

    registry_snapshot_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: ResourceStatus = "active"
    snapshot_type: RegistrySnapshotType
    owner_scope: list[str] = Field(min_length=1)
    resource_count: int = Field(ge=0)
    link_count: int = Field(ge=0)
    broken_count: int = Field(ge=0)
    orphaned_count: int = Field(ge=0)
    resource_type_counts: dict[str, int] = Field(default_factory=dict)
    source_system_counts: dict[str, int] = Field(default_factory=dict)
    root_hash: str = Field(min_length=1)
    report: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("report", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class ResourceRegistryQuery(BaseModel):
    """Query over registry-owned index and integrity records."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    query: str | None = None
    resource_type: str | None = None
    source_system: str | None = None
    status: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=1000)


class ResourceRegistryQueryResult(BaseModel):
    """Registry query response containing AION-owned contracts only."""

    model_config = ConfigDict(extra="forbid")

    resources: list[ResourceDescriptor] = Field(default_factory=list)
    links: list[ResourceReferenceLink] = Field(default_factory=list)
    broken_references: list[BrokenReference] = Field(default_factory=list)
    orphaned_resources: list[OrphanedResource] = Field(default_factory=list)
    total_count: int = Field(ge=0)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ReferenceValidationRequest",
    "ReferenceValidationRun",
    "RegistryRebuildRequest",
    "RegistryRebuildRun",
    "RegistryRunMode",
    "RegistryRunStatus",
    "RegistrySnapshot",
    "RegistrySnapshotType",
    "ResourceDescriptor",
    "ResourceIndexRecord",
    "ResourceIndexUpsertRequest",
    "ResourceRegistryQuery",
    "ResourceRegistryQueryResult",
    "ResourceSensitivity",
    "ResourceStatus",
    "ResourceType",
    "ResourceVisibility",
]
