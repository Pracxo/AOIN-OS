"""Scope and actor-context contracts owned by AION Brain."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScopeResolutionRequest(BaseModel):
    """Request to resolve actor scopes and permissions."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    workspace_id: str | None = None
    requested_scopes: list[str] = Field(min_length=1)
    action_type: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScopeResolution(BaseModel):
    """Resolved scopes and permissions for an actor action."""

    model_config = ConfigDict(extra="forbid")

    scope_resolution_id: str
    actor_id: str | None
    workspace_id: str | None
    requested_scopes: list[str]
    resolved_scopes: list[str]
    permissions: list[str]
    allow: bool
    constraints: list[str]
    created_at: datetime | None = None


class ActorContext(BaseModel):
    """Current request actor context."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    actor_type: str | None = None
    workspace_id: str | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    security_scope: list[str] = Field(default_factory=list)
    correlation_id: str | None = None
    trace_id: str | None = None
    dev_mode: bool = False
