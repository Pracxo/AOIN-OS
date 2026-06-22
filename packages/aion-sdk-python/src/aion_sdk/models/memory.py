"""Memory models."""

from datetime import datetime
from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class MemoryRecordModel(AIONSDKModel):
    memory_id: str
    memory_type: str
    owner_scope: list[str]
    summary: str
    confidence: float
    sensitivity: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_event_id: str | None = None
    content_ref: str | None = None
    created_at: datetime | None = None
    expires_at: datetime | None = None
    deleted_at: datetime | None = None


class MemoryRetrieveRequestModel(AIONSDKModel):
    query: str
    scope: list[str]
    limit: int = 10
    memory_types: list[str] = Field(default_factory=list)
