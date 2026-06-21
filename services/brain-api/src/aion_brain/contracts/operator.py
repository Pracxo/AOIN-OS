"""Operator Control Tower contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

OperatorCategory = Literal[
    "kernel",
    "health",
    "readiness",
    "security",
    "resilience",
    "runtime_config",
    "policy",
    "autonomy",
    "approvals",
    "commands",
    "events",
    "memory",
    "audit",
    "performance",
    "backups",
    "release",
    "workflows",
    "tasks",
    "scheduler",
    "incidents",
    "cycles",
    "visual",
    "registry",
    "lifecycle",
    "learning",
    "self_model",
    "sdk",
    "operator",
]
OperatorCardStatus = Literal[
    "healthy",
    "ready",
    "passed",
    "warning",
    "degraded",
    "blocked",
    "failed",
    "unknown",
]
OperatorSeverity = Literal["low", "medium", "high", "critical"]
OperatorQueueType = Literal[
    "approvals",
    "commands",
    "outbox",
    "inbox",
    "workflows",
    "tasks",
    "scheduler",
    "event_reactions",
    "dead_letters",
    "backups",
    "release_packages",
    "incidents",
    "root_causes",
    "recovery_reviews",
    "broken_references",
    "orphaned_resources",
    "registry_rebuilds",
    "drift_findings",
    "migration_notes",
    "compatibility_scans",
    "extension_packages",
    "extension_reviews",
    "extension_compatibility",
    "extension_install_plans",
    "module_slots",
    "capability_bindings",
    "binding_validations",
    "binding_conflicts",
    "module_mount_plans",
    "route_binding_previews",
    "archive_candidates",
    "redaction_candidates",
    "purge_previews",
    "lifecycle_reviews",
    "audit_verifications",
    "resilience_tests",
    "security_scans",
    "scenarios",
    "learning_patterns",
    "skill_suggestions",
    "regression_suggestions",
    "generic",
]
OperatorActionStatus = Literal["open", "acknowledged", "resolved", "dismissed"]
OperatorActionSourceType = Literal[
    "kernel",
    "health",
    "resilience",
    "security",
    "runtime_config",
    "approval",
    "command",
    "outbox",
    "inbox",
    "workflow",
    "task",
    "schedule",
    "due_item",
    "reminder",
    "scheduler_tick",
    "event_router",
    "memory_governance",
    "audit",
    "backup",
    "release",
    "freeze",
    "performance",
    "scenario",
    "visual",
    "alert",
    "incident",
    "incident_signal",
    "registry",
    "broken_reference",
    "orphaned_resource",
    "interface_drift",
    "migration_note",
    "compatibility_scan",
    "extension_package",
    "extension_review",
    "extension_compatibility",
    "extension_install_plan",
    "extension_capability_declaration",
    "module_slot",
    "capability_binding",
    "binding_validation",
    "binding_conflict",
    "module_mount_plan",
    "route_binding_preview",
    "lifecycle",
    "archive_candidate",
    "redaction_candidate",
    "purge_preview",
    "lifecycle_review",
    "root_cause",
    "recovery_review",
    "outcome",
    "effect_verification",
    "outcome_feedback",
    "learning_pattern",
    "skill_suggestion",
    "regression_suggestion",
    "learning_synthesis",
    "self_model",
    "limitation",
    "self_assessment",
    "capability_awareness",
    "confidence_calibration",
    "generic",
]
OperatorOverallStatus = Literal[
    "ready",
    "healthy",
    "warning",
    "degraded",
    "blocked",
    "failed",
    "unknown",
]
OperatorSnapshotType = Literal[
    "manual",
    "boot",
    "pre_release",
    "post_release",
    "incident_review",
    "local_ops",
]
OperatorSnapshotStatus = Literal["created", "failed"]

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}


class OperatorStatusCard(BaseModel):
    """One summarized status tile for a generic AION subsystem."""

    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: OperatorCategory
    status: OperatorCardStatus
    severity: OperatorSeverity
    summary: str = Field(min_length=1)
    metric: dict[str, Any] = Field(default_factory=dict)
    source_type: str = Field(min_length=1)
    source_id: str | None = None
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "summary")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("metadata", "metric")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class OperatorQueueSummary(BaseModel):
    """Queue count summary for local operator visibility."""

    model_config = ConfigDict(extra="forbid")

    queue_id: str = Field(min_length=1)
    queue_type: OperatorQueueType
    title: str = Field(min_length=1)
    pending_count: int = Field(ge=0)
    running_count: int = Field(ge=0)
    blocked_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    oldest_item_at: datetime | None = None
    newest_item_at: datetime | None = None
    status: OperatorCardStatus
    severity: OperatorSeverity
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class OperatorActionItem(BaseModel):
    """Read-mostly operator action recommendation."""

    model_config = ConfigDict(extra="forbid")

    action_item_id: str = Field(min_length=1)
    trace_id: str | None = None
    source_type: OperatorActionSourceType
    source_id: str | None = None
    category: OperatorCategory
    severity: OperatorSeverity
    status: OperatorActionStatus
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    recommended_action: str = Field(min_length=1)
    runbook_ref: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("title", "description", "recommended_action")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class OperatorOverviewRequest(BaseModel):
    """Request one read-mostly operator overview."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    include_cards: bool = True
    include_queues: bool = True
    include_actions: bool = True
    include_readiness: bool = True
    include_runbooks: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class OperatorOverview(BaseModel):
    """Aggregated local operator view."""

    model_config = ConfigDict(extra="forbid")

    overview_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    overall_status: OperatorOverallStatus
    cards: list[OperatorStatusCard] = Field(default_factory=list)
    queues: list[OperatorQueueSummary] = Field(default_factory=list)
    actions: list[OperatorActionItem] = Field(default_factory=list)
    readiness: dict[str, Any] = Field(default_factory=dict)
    runbooks: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime


class OperatorReadinessReport(BaseModel):
    """Release and local-ops readiness report for operators."""

    model_config = ConfigDict(extra="forbid")

    readiness_id: str
    overall_status: OperatorOverallStatus
    checks: list[dict[str, Any]] = Field(default_factory=list)
    blockers: list[OperatorActionItem] = Field(default_factory=list)
    warnings: list[OperatorActionItem] = Field(default_factory=list)
    release_ready: bool
    local_ops_ready: bool
    generated_at: datetime


class OperatorSnapshotRequest(BaseModel):
    """Create a local operator snapshot record."""

    model_config = ConfigDict(extra="forbid")

    operator_snapshot_id: str | None = None
    snapshot_type: OperatorSnapshotType = "manual"
    owner_scope: list[str] = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    include_actions: bool = True
    include_readiness: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
    generated_by: str | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class OperatorSnapshot(BaseModel):
    """Persisted local operator snapshot."""

    model_config = ConfigDict(extra="forbid")

    operator_snapshot_id: str
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    snapshot_type: OperatorSnapshotType
    status: OperatorSnapshotStatus
    owner_scope: list[str] = Field(min_length=1)
    overview: OperatorOverview
    action_items: list[OperatorActionItem] = Field(default_factory=list)
    queue_summaries: list[OperatorQueueSummary] = Field(default_factory=list)
    readiness: OperatorReadinessReport | None = None
    generated_by: str | None = None
    created_at: datetime | None = None


class OperatorAcknowledgementRequest(BaseModel):
    """Record that an operator acknowledged one local item."""

    model_config = ConfigDict(extra="forbid")

    acknowledgement_id: str | None = None
    action_item_id: str | None = None
    source_type: OperatorActionSourceType
    source_id: str = Field(min_length=1)
    actor_id: str | None = None
    workspace_id: str | None = None
    reason: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("reason cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_like_keys(value)
        return value


class OperatorAcknowledgement(BaseModel):
    """Persisted local acknowledgement."""

    model_config = ConfigDict(extra="forbid")

    acknowledgement_id: str
    action_item_id: str | None = None
    source_type: OperatorActionSourceType
    source_id: str
    actor_id: str | None = None
    workspace_id: str | None = None
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class OperatorRunbookLink(BaseModel):
    """Static local runbook link for operators."""

    model_config = ConfigDict(extra="forbid")

    runbook_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: OperatorCategory
    path: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)


def _reject_secret_like_keys(value: object) -> None:
    if _has_secret_like_key(value):
        raise ValueError("metadata must not contain secret-like keys")


def _has_secret_like_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in _SECRET_KEY_PARTS):
                return True
            if _has_secret_like_key(nested):
                return True
    if isinstance(value, list):
        return any(_has_secret_like_key(item) for item in value)
    return False
