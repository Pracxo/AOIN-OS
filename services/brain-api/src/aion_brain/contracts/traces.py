"""Trace contracts owned by AION Brain."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DecisionTrace(BaseModel):
    """Audit-ready record of a Brain loop decision."""

    model_config = ConfigDict(extra="forbid")

    trace_id: str
    event_id: str
    intent_id: str | None
    context_id: str | None
    plan_id: str | None
    memory_refs: list[str]
    capability_refs: list[str]
    reasoning_refs: list[str] = Field(default_factory=list)
    execution_refs: list[str] = Field(default_factory=list)
    policy_decisions: list[str]
    outcome: dict[str, Any]
    created_at: datetime
