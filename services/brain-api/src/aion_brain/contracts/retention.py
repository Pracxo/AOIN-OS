"""Retention policy contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)


def _requires_hard_delete(value: Any) -> bool:
    """Detect affirmative hard-delete requirements while allowing disabled flags."""

    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if lowered in {"hard_delete", "hard_delete_allowed", "hard_delete_enabled"}:
                if nested is True:
                    return True
                if isinstance(nested, str) and nested.strip().lower() in {"true", "yes", "enabled"}:
                    return True
                continue
            if _requires_hard_delete(nested):
                return True
        return False
    if isinstance(value, list):
        return any(_requires_hard_delete(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return "hard_delete" in lowered or "hard delete" in lowered
    return False


RetentionClass = Literal[
    "transient",
    "operational",
    "audit",
    "evidence",
    "memory",
    "registry",
    "release",
    "backup",
    "telemetry",
    "learning",
    "configuration",
    "unknown",
]
LifecyclePolicyStatus = Literal["active", "disabled"]
LifecyclePolicyType = Literal[
    "retention",
    "archive",
    "redaction",
    "review",
    "purge_preview",
    "classification",
    "generic",
]
LifecyclePolicyAction = Literal[
    "classify",
    "review",
    "create_archive_candidate",
    "create_redaction_candidate",
    "create_purge_preview",
    "report_only",
]
RetentionClassificationStatus = Literal[
    "active",
    "stale",
    "review_required",
    "archived",
    "deleted",
    "unknown",
]
LifecycleState = Literal[
    "current",
    "review_due",
    "archive_candidate",
    "redaction_candidate",
    "purge_preview",
    "retained",
    "archived",
    "stale",
    "unknown",
]
LifecycleSensitivity = Literal["public", "internal", "confidential", "restricted"]


class LifecyclePolicy(BaseModel):
    """Generic local retention policy."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_policy_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: LifecyclePolicyStatus
    policy_type: LifecyclePolicyType
    resource_types: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    retention_class: RetentionClass
    retention_days: int = Field(ge=0)
    review_after_days: int | None = Field(default=None, ge=0)
    archive_after_days: int | None = Field(default=None, ge=0)
    purge_after_days: int | None = Field(default=None, ge=0)
    action_on_match: LifecyclePolicyAction
    requires_backup: bool
    requires_approval: bool
    owner_scope: list[str] = Field(min_length=1)
    rule: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "lifecycle policy text")
        return value.strip()

    @field_validator("rule", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def policy_must_not_hard_delete(self) -> LifecyclePolicy:
        if _requires_hard_delete(self.rule) or _requires_hard_delete(self.metadata):
            raise ValueError("lifecycle policy must not require hard delete")
        return self


class LifecyclePolicyCreateRequest(BaseModel):
    """Request to create one lifecycle policy."""

    model_config = ConfigDict(extra="forbid")

    lifecycle_policy_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    policy_type: LifecyclePolicyType = "generic"
    resource_types: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    retention_class: RetentionClass = "unknown"
    retention_days: int = Field(default=365, ge=0)
    review_after_days: int | None = Field(default=None, ge=0)
    archive_after_days: int | None = Field(default=None, ge=0)
    purge_after_days: int | None = Field(default=None, ge=0)
    action_on_match: LifecyclePolicyAction = "report_only"
    requires_backup: bool = True
    requires_approval: bool = True
    owner_scope: list[str] = Field(min_length=1)
    rule: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "lifecycle policy text")
        return value.strip()

    @field_validator("rule", "metadata")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def policy_must_not_hard_delete(self) -> LifecyclePolicyCreateRequest:
        if _requires_hard_delete(self.rule) or _requires_hard_delete(self.metadata):
            raise ValueError("lifecycle policy must not require hard delete")
        return self


class RetentionClassification(BaseModel):
    """Lifecycle classification for one registry resource."""

    model_config = ConfigDict(extra="forbid")

    classification_id: str = Field(min_length=1)
    trace_id: str | None = None
    resource_uri: str
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    status: RetentionClassificationStatus
    retention_class: RetentionClass
    lifecycle_state: LifecycleState
    sensitivity: LifecycleSensitivity
    policy_refs: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    retention_until: datetime | None = None
    review_after: datetime | None = None
    archive_after: datetime | None = None
    purge_after: datetime | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("resource_uri")
    @classmethod
    def uri_must_be_aion_uri(cls, value: str) -> str:
        if not value.startswith("aion://"):
            raise ValueError("resource_uri must start with aion://")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "LifecyclePolicy",
    "LifecyclePolicyAction",
    "LifecyclePolicyCreateRequest",
    "LifecyclePolicyStatus",
    "LifecyclePolicyType",
    "LifecycleSensitivity",
    "LifecycleState",
    "RetentionClass",
    "RetentionClassification",
    "RetentionClassificationStatus",
]
