"""Notification and escalation contracts owned by AION Brain."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

NotificationSeverity = Literal["info", "low", "medium", "high", "critical"]
NotificationTopicStatus = Literal["active", "disabled"]
NotificationCategory = Literal[
    "kernel",
    "operator",
    "approval",
    "action",
    "run_supervision",
    "security",
    "resilience",
    "audit",
    "grounding",
    "prompt",
    "model_output",
    "outcome",
    "learning",
    "backup",
    "release",
    "freeze",
    "performance",
    "runtime_config",
    "explanation",
    "generic",
]
NotificationSubscriberType = Literal[
    "actor", "workspace", "operator", "service", "auditor", "generic"
]
NotificationChannel = Literal[
    "operator_inbox",
    "actor_inbox",
    "workspace_feed",
    "audit_feed",
    "visual_feed",
    "local_digest",
]
NotificationSubscriptionStatus = Literal["active", "disabled"]
NotificationStatus = Literal[
    "new", "delivered", "read", "acknowledged", "resolved", "archived", "deleted"
]
NotificationSourceType = Literal[
    "operator",
    "approval",
    "action_proposal",
    "run_supervision",
    "command",
    "workflow",
    "execution",
    "capability",
    "mcp",
    "sandbox",
    "security_scan",
    "hardening_gate",
    "resilience",
    "audit",
    "grounding",
    "prompt",
    "model_output",
    "outcome",
    "learning",
    "backup",
    "release",
    "freeze",
    "performance",
    "runtime_config",
    "explanation",
    "system",
    "generic",
]
EscalationPolicyStatus = Literal["active", "disabled"]
EscalationStatus = Literal[
    "created", "delivered_local", "acknowledged", "resolved", "blocked", "failed"
]
DigestType = Literal["operator", "workspace", "actor", "daily", "release", "readiness", "generic"]
DigestStatus = Literal["created", "archived"]

_TOPIC_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


def _validate_topic_key(value: str) -> str:
    if not _TOPIC_KEY_RE.match(value):
        raise ValueError("topic_key must be dotted lowercase text")
    return value


def _validate_scope(value: list[str]) -> list[str]:
    if not value:
        raise ValueError("owner_scope cannot be empty")
    return value


def _validate_safe_text(value: str, field_name: str) -> str:
    reject_hidden_or_secret_text(value, field_name)
    return value


class NotificationTopic(BaseModel):
    """Local notification topic definition."""

    model_config = ConfigDict(extra="forbid")

    topic_id: str = Field(min_length=1)
    topic_key: str
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: NotificationTopicStatus
    category: NotificationCategory
    severity_default: NotificationSeverity
    owner_scope: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("topic_key")
    @classmethod
    def topic_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _validate_topic_key(value)

    @field_validator("owner_scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class NotificationSubscription(BaseModel):
    """Local-only subscription to notification topics."""

    model_config = ConfigDict(extra="forbid")

    subscription_id: str = Field(min_length=1)
    topic_key: str
    actor_id: str | None = None
    workspace_id: str | None = None
    subscriber_type: NotificationSubscriberType
    subscriber_ref: str = Field(min_length=1)
    channel: NotificationChannel
    status: NotificationSubscriptionStatus
    severity_threshold: NotificationSeverity
    filters: dict[str, Any] = Field(default_factory=dict)
    owner_scope: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("topic_key")
    @classmethod
    def topic_key_must_not_be_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("topic_key cannot be empty")
        return value

    @field_validator("owner_scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)

    @field_validator("filters", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class NotificationRecord(BaseModel):
    """Stored local notification record."""

    model_config = ConfigDict(extra="forbid")

    notification_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    topic_key: str = Field(min_length=1)
    status: NotificationStatus
    severity: NotificationSeverity
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    source_type: NotificationSourceType
    source_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    owner_scope: list[str]
    refs: list[str] = Field(default_factory=list)
    delivery_channels: list[NotificationChannel] = Field(default_factory=list)
    delivered_to: list[str] = Field(default_factory=list)
    read_by: list[str] = Field(default_factory=list)
    acknowledged_by: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    read_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("title", "message")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return _validate_safe_text(value, "notification text")

    @field_validator("owner_scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class NotificationPublishRequest(BaseModel):
    """Request to publish a local notification."""

    model_config = ConfigDict(extra="forbid")

    notification_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    topic_key: str
    severity: NotificationSeverity | None = None
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    source_type: NotificationSourceType
    source_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    owner_scope: list[str]
    refs: list[str] = Field(default_factory=list)
    delivery_channels: list[NotificationChannel] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("topic_key")
    @classmethod
    def topic_key_must_be_dotted_lowercase(cls, value: str) -> str:
        return _validate_topic_key(value)

    @field_validator("owner_scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)


class EscalationPolicy(BaseModel):
    """Local-only escalation policy metadata."""

    model_config = ConfigDict(extra="forbid")

    escalation_policy_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: EscalationPolicyStatus
    topic_key: str | None = None
    alert_type: str | None = None
    severity_threshold: NotificationSeverity
    delay_seconds: int = Field(ge=0)
    repeat_limit: int = Field(ge=0, le=100)
    escalation_channel: NotificationChannel
    escalation_target: str = Field(min_length=1)
    owner_scope: list[str]
    conditions: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("owner_scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)

    @field_validator("conditions", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class EscalationRecord(BaseModel):
    """Local-only escalation record."""

    model_config = ConfigDict(extra="forbid")

    escalation_record_id: str = Field(min_length=1)
    trace_id: str | None = None
    alert_id: str | None = None
    notification_id: str | None = None
    escalation_policy_id: str | None = None
    status: EscalationStatus
    severity: NotificationSeverity
    escalation_channel: NotificationChannel
    escalation_target: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    local_only: bool
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    @model_validator(mode="after")
    def must_remain_local(self) -> EscalationRecord:
        if not self.local_only:
            raise ValueError("escalation record must be local-only")
        return self

    @field_validator("result", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class NotificationDigest(BaseModel):
    """Deterministic local notification digest."""

    model_config = ConfigDict(extra="forbid")

    digest_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    digest_type: DigestType
    status: DigestStatus
    owner_scope: list[str]
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    notification_ids: list[str] = Field(default_factory=list)
    alert_ids: list[str] = Field(default_factory=list)
    counts: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None

    @field_validator("summary")
    @classmethod
    def summary_must_be_safe(cls, value: str) -> str:
        return _validate_safe_text(value, "notification digest summary")

    @field_validator("owner_scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class NotificationQuery(BaseModel):
    """Notification query contract."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str]
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    topic_key: str | None = None
    status: str | None = None
    severity: str | None = None
    source_type: str | None = None
    source_id: str | None = None
    include_deleted: bool = False
    limit: int = Field(default=50, ge=1, le=500)

    @field_validator("scope")
    @classmethod
    def scope_must_not_be_empty(cls, value: list[str]) -> list[str]:
        return _validate_scope(value)


__all__ = [
    "DigestType",
    "EscalationPolicy",
    "EscalationRecord",
    "NotificationChannel",
    "NotificationDigest",
    "NotificationPublishRequest",
    "NotificationQuery",
    "NotificationRecord",
    "NotificationSeverity",
    "NotificationSubscription",
    "NotificationTopic",
]
