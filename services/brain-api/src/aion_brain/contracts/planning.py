"""Planning contracts owned by AION Brain."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlanStep(BaseModel):
    """A deterministic, policy-checkable plan step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    action_type: str
    capability_required: str | None
    risk_level: str
    status: str


class PlanGraph(BaseModel):
    """A policy-checkable plan graph."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    intent_id: str
    goal: str
    steps: list[PlanStep]
    dependencies: list[dict[str, Any]]
    risk_level: str
    approval_required: bool
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
