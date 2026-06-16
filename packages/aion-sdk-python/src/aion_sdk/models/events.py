"""Event models."""

from datetime import datetime
from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class AIONEventModel(AIONSDKModel):
    event_id: str
    source: str
    event_type: str
    payload_type: str
    payload: dict[str, Any]
    timestamp: datetime
    security_scope: list[str]
    actor_id: str | None = None
    workspace_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None


class EventAcceptanceModel(AIONSDKModel):
    status: str
    event_id: str
    trace_id: str
    correlation_id: str
    persisted: bool
    published: bool = Field(default=False)
