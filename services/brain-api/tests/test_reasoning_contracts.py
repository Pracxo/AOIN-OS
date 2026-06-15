"""Reasoning contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.reasoning import (
    ModelRouteDecision,
    PromptPacket,
    ReasoningRequest,
    ReasoningResult,
)


def test_reasoning_request_validates_mode() -> None:
    """ReasoningRequest accepts only the generic mode vocabulary."""
    with pytest.raises(ValidationError):
        ReasoningRequest(
            reasoning_id="reasoning-1",
            trace_id="trace-1",
            intent=make_intent(),
            context=make_context(),
            mode="invalid",
            risk_level="low",
            metadata={},
        )


def test_reasoning_result_validates_confidence_bounds() -> None:
    """ReasoningResult confidence stays bounded."""
    with pytest.raises(ValidationError):
        ReasoningResult(
            reasoning_id="reasoning-1",
            trace_id="trace-1",
            context_id="context-1",
            mode="analyze",
            summary="summary",
            interpretation="interpretation",
            suggested_next_actions=[],
            constraints=[],
            confidence=1.2,
            requires_clarification=False,
            clarification_questions=[],
            route_decision=make_route(),
            prompt_packet=make_prompt(),
            metadata={},
            created_at=datetime.now(UTC),
        )


def make_intent() -> IntentFrame:
    """Create an intent frame."""
    return IntentFrame(
        intent_id="intent-1",
        event_id="event-1",
        intent_type="question.answer",
        goal="answer a generic question",
        urgency="normal",
        risk_level="low",
        requires_memory=True,
        requires_capability=False,
        requires_approval=False,
        confidence=0.9,
    )


def make_context() -> ContextPacket:
    """Create a context packet."""
    return ContextPacket(
        context_id="context-1",
        intent_id="intent-1",
        goal="answer a generic question",
        known_context=[{"source": "intent", "intent_type": "question.answer"}],
        retrieved_memory_ids=["memory-1"],
        available_capability_ids=["capability-1"],
        constraints=["stay_generic"],
        open_questions=[],
        execution_limits={"no_external_calls": True},
    )


def make_prompt() -> PromptPacket:
    """Create a prompt packet."""
    return PromptPacket(
        prompt_id="prompt-1",
        trace_id="trace-1",
        intent_id="intent-1",
        context_id="context-1",
        goal="answer a generic question",
        system_instructions=["Use AION contracts."],
        context_items=[],
        constraints=[],
        requested_output_schema={},
        token_budget_hint=None,
        created_at=datetime.now(UTC),
    )


def make_route() -> ModelRouteDecision:
    """Create a route decision."""
    return ModelRouteDecision(
        route_id="route-1",
        trace_id="trace-1",
        reasoning_id="reasoning-1",
        selected_provider="aion-local",
        selected_model="deterministic-reasoner-v0",
        mode="analyze",
        reason="test",
        fallback_providers=[],
        privacy_level="local",
        risk_level="low",
        estimated_cost=0.0,
        estimated_latency_ms=0,
        created_at=datetime.now(UTC),
    )
