"""Visual Brain Projection models."""

from datetime import datetime
from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class VisualTelemetryEventModel(AIONSDKModel):
    telemetry_id: str
    event_type: str
    node_type: str
    node_id: str
    trace_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class BrainMapModel(AIONSDKModel):
    map_id: str
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    pulses: list[dict[str, Any]] = Field(default_factory=list)
    clusters: list[dict[str, Any]] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
