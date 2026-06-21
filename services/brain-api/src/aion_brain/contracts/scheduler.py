"""Temporal scheduler contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)
from aion_brain.contracts.reminders import ReminderRecord

RecurrenceFrequency = Literal["once", "hourly", "daily", "weekly", "monthly", "manual"]
ScheduleStatus = Literal["active", "paused", "disabled", "completed", "deleted"]
ScheduleType = Literal[
    "reminder",
    "notification",
    "operator_check",
    "run_supervision_check",
    "backup_check",
    "security_check",
    "resilience_check",
    "audit_check",
    "release_check",
    "freeze_check",
    "performance_check",
    "digest",
    "action_proposal",
    "generic",
]
ScheduleTargetType = Literal[
    "notification",
    "reminder",
    "operator_action",
    "action_proposal",
    "run_supervision",
    "backup",
    "security_scan",
    "resilience_test",
    "audit_verification",
    "release_package",
    "freeze_gate",
    "performance_benchmark",
    "digest",
    "noop",
    "generic",
]
ScheduleActionMode = Literal[
    "notify_only",
    "propose_only",
    "operator_item_only",
    "dry_run",
    "manual",
]
DueItemStatus = Literal["due", "processed", "missed", "failed", "skipped"]
SchedulerTickMode = Literal["dry_run", "controlled"]
SchedulerTickStatus = Literal[
    "completed",
    "dry_run",
    "warning",
    "failed",
    "blocked_by_policy",
    "blocked_by_autonomy",
]
SchedulePolicyType = Literal[
    "max_frequency",
    "missed_schedule",
    "overdue_reminder",
    "action_proposal_limit",
    "notification_limit",
    "manual_review",
    "generic",
]
SchedulePolicyAction = Literal[
    "report_only",
    "create_notification",
    "create_operator_item",
    "block_schedule",
    "pause_schedule",
]
SchedulePolicyStatus = Literal["active", "disabled"]
SchedulerReportStatus = Literal["passed", "warning", "failed"]


class RecurrenceRule(BaseModel):
    """Deterministic recurrence rule evaluated locally in UTC."""

    model_config = ConfigDict(extra="forbid")

    frequency: RecurrenceFrequency
    interval: int = Field(default=1, ge=1, le=1000)
    days_of_week: list[int] = Field(default_factory=list)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    months: list[int] = Field(default_factory=list)
    count: int | None = Field(default=None, ge=1)
    until: datetime | None = None

    @field_validator("days_of_week")
    @classmethod
    def days_must_be_weekday_indexes(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("days_of_week values must be between 0 and 6")
        return sorted(set(value))

    @field_validator("months")
    @classmethod
    def months_must_be_calendar_indexes(cls, value: list[int]) -> list[int]:
        if any(month < 1 or month > 12 for month in value):
            raise ValueError("months values must be between 1 and 12")
        return sorted(set(value))


class ScheduleRecord(BaseModel):
    """Persistent local schedule. It creates records, not target execution."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schedule_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    schedule_type: ScheduleType
    target_type: ScheduleTargetType
    action_mode: ScheduleActionMode
    recurrence: RecurrenceRule = Field(
        validation_alias=AliasChoices("recurrence", "recurrence_rule")
    )
    start_at: datetime
    end_at: datetime | None = None
    timezone: str = Field(default="UTC", min_length=1)
    status: ScheduleStatus
    next_due_at: datetime | None = None
    last_due_at: datetime | None = None
    last_tick_run_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    target_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    paused_at: datetime | None = None
    disabled_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("name", "description", "timezone")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "schedule text")
        return value.strip()

    @field_validator("target_payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def schedule_must_not_execute_target(self) -> ScheduleRecord:
        if self.end_at is not None and self.end_at < self.start_at:
            raise ValueError("end_at must not be before start_at")
        if self.target_payload.get("execute") is True or self.metadata.get("auto_execute") is True:
            raise ValueError("schedule cannot directly execute target action")
        return self


class ScheduleCreateRequest(BaseModel):
    """Request to create a local schedule."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schedule_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    schedule_type: ScheduleType = "generic"
    target_type: ScheduleTargetType = "generic"
    action_mode: ScheduleActionMode = "notify_only"
    recurrence: RecurrenceRule = Field(
        validation_alias=AliasChoices("recurrence", "recurrence_rule")
    )
    start_at: datetime
    end_at: datetime | None = None
    timezone: str = Field(default="UTC", min_length=1)
    owner_scope: list[str] = Field(min_length=1)
    target_payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("name", "description", "timezone")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "schedule text")
        return value.strip()

    @field_validator("target_payload", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def schedule_must_not_execute_target(self) -> ScheduleCreateRequest:
        if self.end_at is not None and self.end_at < self.start_at:
            raise ValueError("end_at must not be before start_at")
        if self.target_payload.get("execute") is True or self.metadata.get("auto_execute") is True:
            raise ValueError("schedule cannot directly execute target action")
        return self


class ScheduleDueItem(BaseModel):
    """A due schedule occurrence materialized by a local tick."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    due_item_id: str = Field(min_length=1)
    schedule_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    due_at: datetime
    status: DueItemStatus
    target_type: ScheduleTargetType
    action_mode: ScheduleActionMode
    target_payload: dict[str, Any] = Field(default_factory=dict)
    owner_scope: list[str] = Field(min_length=1)
    created_from_tick_run_id: str | None = None
    processed_at: datetime | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("target_payload", "result", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class SchedulerTickRequest(BaseModel):
    """Request to run one explicit local scheduler tick."""

    model_config = ConfigDict(extra="forbid")

    tick_run_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    scope: list[str] = Field(
        min_length=1,
        validation_alias=AliasChoices("scope", "owner_scope"),
    )
    mode: SchedulerTickMode = "dry_run"
    tick_at: datetime | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    schedule_ids: list[str] = Field(default_factory=list)
    force_manual: bool = False
    create_notifications: bool | None = None
    create_action_proposals: bool | None = None
    create_operator_items: bool | None = None
    max_due_items: int | None = Field(default=None, ge=1, le=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def validate_tick_window(self) -> SchedulerTickRequest:
        if (
            self.window_start is not None
            and self.window_end is not None
            and self.window_start >= self.window_end
        ):
            raise ValueError("window_start must be before window_end")
        return self


class SchedulerTickRun(BaseModel):
    """Result of one explicit scheduler tick."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    tick_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    mode: SchedulerTickMode
    status: SchedulerTickStatus
    tick_at: datetime
    window_start: datetime
    window_end: datetime
    schedules_checked: int = Field(ge=0)
    due_items_created: int = Field(ge=0)
    reminders_created: int = Field(ge=0)
    notifications_created: int = Field(ge=0)
    action_proposals_created: int = Field(ge=0)
    operator_items_created: int = Field(ge=0)
    schedules_missed: int = Field(
        ge=0,
        validation_alias=AliasChoices("schedules_missed", "missed_detected"),
    )
    due_items: list[ScheduleDueItem] = Field(default_factory=list)
    reminders: list[ReminderRecord] = Field(default_factory=list)
    policy_decision_ids: list[str] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    completed_at: datetime | None = None


class SchedulePolicy(BaseModel):
    """Local policy-like scheduler guardrail metadata."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    policy_id: str = Field(
        min_length=1,
        validation_alias=AliasChoices("policy_id", "schedule_policy_id"),
    )
    policy_type: SchedulePolicyType
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: SchedulePolicyStatus = "active"
    owner_scope: list[str] = Field(min_length=1)
    conditions: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("conditions", "rule"),
    )
    action_on_violation: SchedulePolicyAction = "report_only"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("name", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "schedule policy text")
        return value.strip()

    @field_validator("conditions", "metadata")
    @classmethod
    def payloads_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


class SchedulerReport(BaseModel):
    """Read-only summary of local scheduler state."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(min_length=1)
    trace_id: str | None = None
    workspace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    status: SchedulerReportStatus
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    active_schedule_count: int = Field(ge=0)
    due_item_count: int = Field(ge=0)
    reminder_count: int = Field(ge=0)
    missed_schedule_count: int = Field(ge=0)
    failed_tick_count: int = Field(ge=0)
    findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @field_validator("title", "summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "scheduler report text")
        return value.strip()


__all__ = [
    "DueItemStatus",
    "RecurrenceFrequency",
    "RecurrenceRule",
    "ScheduleActionMode",
    "ScheduleCreateRequest",
    "ScheduleDueItem",
    "SchedulePolicy",
    "SchedulePolicyAction",
    "SchedulePolicyStatus",
    "SchedulePolicyType",
    "ScheduleRecord",
    "ScheduleStatus",
    "ScheduleTargetType",
    "ScheduleType",
    "SchedulerReport",
    "SchedulerReportStatus",
    "SchedulerTickMode",
    "SchedulerTickRequest",
    "SchedulerTickRun",
    "SchedulerTickStatus",
]
