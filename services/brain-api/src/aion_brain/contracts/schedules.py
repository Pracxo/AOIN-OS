"""Schedule metadata contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ScheduleOwnerType = Literal["goal", "task", "workflow"]
ScheduleType = Literal["once", "interval", "cron"]
ScheduleStatus = Literal["active", "paused", "cancelled"]


class ScheduleRecord(BaseModel):
    """Persistent schedule metadata record."""

    model_config = ConfigDict(extra="forbid")

    schedule_id: str = Field(min_length=1)
    owner_type: ScheduleOwnerType
    owner_id: str = Field(min_length=1)
    schedule_type: ScheduleType
    schedule_expression: str = Field(min_length=1)
    timezone: str = Field(default="UTC", min_length=1)
    status: ScheduleStatus
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ScheduleCreateRequest(BaseModel):
    """Request to store schedule metadata."""

    model_config = ConfigDict(extra="forbid")

    schedule_id: str | None = None
    owner_type: ScheduleOwnerType
    owner_id: str = Field(min_length=1)
    schedule_type: ScheduleType
    schedule_expression: str = Field(min_length=1)
    timezone: str = Field(default="UTC", min_length=1)
    next_run_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
