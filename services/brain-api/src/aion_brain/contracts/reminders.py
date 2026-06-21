"""Reminder queue contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

ReminderType = Literal[
    "operator",
    "actor",
    "workspace",
    "schedule",
    "approval",
    "run_supervision",
    "backup",
    "release",
    "freeze",
    "security",
    "generic",
]
ReminderStatus = Literal[
    "pending",
    "due",
    "acknowledged",
    "snoozed",
    "dismissed",
    "deleted",
]


class ReminderRecord(BaseModel):
    """A local reminder record. It never delivers through external systems."""

    model_config = ConfigDict(extra="forbid")

    reminder_id: str = Field(min_length=1)
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    schedule_id: str | None = None
    due_item_id: str | None = None
    reminder_type: ReminderType
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    due_at: datetime
    status: ReminderStatus
    owner_scope: list[str] = Field(min_length=1)
    refs: list[str] = Field(default_factory=list)
    snooze_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    acknowledged_at: datetime | None = None
    snoozed_until: datetime | None = None
    dismissed_at: datetime | None = None
    deleted_at: datetime | None = None

    @field_validator("title", "message")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "reminder text")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value

    @model_validator(mode="after")
    def snoozed_reminder_requires_until(self) -> ReminderRecord:
        if self.status == "snoozed" and self.snoozed_until is None:
            raise ValueError("snoozed reminder requires snoozed_until")
        return self


class ReminderCreateRequest(BaseModel):
    """Request to create a local reminder."""

    model_config = ConfigDict(extra="forbid")

    reminder_id: str | None = None
    trace_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    schedule_id: str | None = None
    due_item_id: str | None = None
    reminder_type: ReminderType = "generic"
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    due_at: datetime
    owner_scope: list[str] = Field(min_length=1)
    refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None

    @field_validator("title", "message")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "reminder text")
        return value.strip()

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_payload(value)
        return value


__all__ = [
    "ReminderCreateRequest",
    "ReminderRecord",
    "ReminderStatus",
    "ReminderType",
]
