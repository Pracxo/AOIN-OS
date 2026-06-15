"""Event contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AIONEvent(BaseModel):
    """Normalized incoming activity for the Brain loop."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    source: str
    event_type: str
    actor_id: str | None = None
    workspace_id: str | None = None
    payload_type: str
    payload: dict[str, Any]
    timestamp: datetime
    correlation_id: str | None = None
    trace_id: str | None = None
    security_scope: list[str] = Field(default_factory=list)


class EventAcceptance(BaseModel):
    """Acceptance result for an ingested event."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["accepted"]
    event_id: str
    trace_id: str
    correlation_id: str
    persisted: bool
    published: bool
