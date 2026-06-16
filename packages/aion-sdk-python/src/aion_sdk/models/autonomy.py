"""Autonomy models."""

from typing import Any

from pydantic import Field

from aion_sdk.models.base import AIONSDKModel


class AutonomyStatusModel(AIONSDKModel):
    status: str
    actor_id: str | None = None
    workspace_id: str | None = None
    active_run_level: dict[str, Any] | None = None


class AutonomyDecisionModel(AIONSDKModel):
    decision_id: str
    allow: bool
    reason: str
    constraints: dict[str, Any] = Field(default_factory=dict)
