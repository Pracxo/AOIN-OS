"""Reasoning and model gateway contracts owned by AION Brain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.intent import IntentFrame

ReasoningMode = Literal[
    "route",
    "analyze",
    "plan_assist",
    "draft",
    "critique",
    "verify",
    "reflect",
]

ReasoningRiskLevel = Literal["low", "medium", "high", "critical"]


class PromptPacket(BaseModel):
    """Provider-neutral prompt packet for reasoning adapters."""

    model_config = ConfigDict(extra="forbid")

    prompt_id: str = Field(min_length=1)
    trace_id: str | None
    intent_id: str | None
    context_id: str
    goal: str
    system_instructions: list[str]
    context_items: list[dict[str, Any]]
    constraints: list[str]
    requested_output_schema: dict[str, Any]
    token_budget_hint: int | None = Field(default=None, ge=1)
    created_at: datetime


class ModelRouteDecision(BaseModel):
    """Provider-neutral model routing decision."""

    model_config = ConfigDict(extra="forbid")

    route_id: str = Field(min_length=1)
    trace_id: str | None
    reasoning_id: str | None
    selected_provider: str = Field(min_length=1)
    selected_model: str = Field(min_length=1)
    mode: ReasoningMode
    reason: str
    fallback_providers: list[str]
    privacy_level: str
    risk_level: ReasoningRiskLevel
    estimated_cost: float | None = Field(default=None, ge=0.0)
    estimated_latency_ms: int | None = Field(default=None, ge=0)
    created_at: datetime


class ReasoningRequest(BaseModel):
    """Request for generic AION reasoning."""

    model_config = ConfigDict(extra="forbid")

    reasoning_id: str = Field(min_length=1)
    trace_id: str | None
    intent: IntentFrame | None
    context: ContextPacket
    mode: ReasoningMode
    risk_level: ReasoningRiskLevel
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelCallRecord(BaseModel):
    """Provider-neutral model call ledger record."""

    model_config = ConfigDict(extra="forbid")

    model_call_id: str = Field(min_length=1)
    trace_id: str | None
    reasoning_id: str | None
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    mode: ReasoningMode
    request: dict[str, Any]
    response: dict[str, Any]
    status: str
    latency_ms: int | None = Field(default=None, ge=0)
    cost_estimate: float | None = Field(default=None, ge=0.0)
    created_at: datetime


class ReasoningResult(BaseModel):
    """Result of a generic reasoning pass."""

    model_config = ConfigDict(extra="forbid")

    reasoning_id: str = Field(min_length=1)
    trace_id: str | None
    context_id: str
    mode: ReasoningMode
    summary: str
    interpretation: str
    suggested_next_actions: list[str]
    constraints: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    requires_clarification: bool
    clarification_questions: list[str]
    route_decision: ModelRouteDecision
    prompt_packet: PromptPacket
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
