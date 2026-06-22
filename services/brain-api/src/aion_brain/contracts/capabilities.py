"""Capability contracts owned by AION Brain."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class CapabilityManifest(BaseModel):
    """Declared capabilities for future modules."""

    model_config = ConfigDict(extra="forbid")

    module_id: str
    version: str
    capabilities: list[dict[str, Any]]
    permissions_required: list[str]
    memory_read_scopes: list[str]
    memory_write_scopes: list[str]
    events_subscribed: list[str]
    events_published: list[str]
    execution_mode: str
