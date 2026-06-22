"""Deterministic reasoning adapter tests."""

import sys
from datetime import UTC, datetime

import pytest

from aion_brain.contracts.reasoning import ModelRouteDecision, PromptPacket
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter
from aion_brain.reasoning.litellm_adapter import LiteLLMAdapter


def test_deterministic_adapter_returns_stable_local_output() -> None:
    """Same prompt and route produce the same deterministic response payload."""
    prompt = make_prompt()
    route = make_route()
    adapter = DeterministicReasoningAdapter()

    first = adapter.complete(prompt, route)
    second = adapter.complete(prompt, route)

    assert first.provider == "deterministic"
    assert first.model == "deterministic-reasoner-v0"
    assert first.status == "completed"
    assert first.response == second.response
    assert first.response["suggested_next_actions"] == [
        "review_available_capabilities",
        "use_retrieved_memory",
    ]


def test_deterministic_adapter_does_not_import_external_providers() -> None:
    """The local adapter does not load external model provider packages."""
    DeterministicReasoningAdapter().complete(make_prompt(), make_route())

    assert "openai" not in sys.modules
    assert "anthropic" not in sys.modules
    assert "litellm" not in sys.modules


def test_litellm_adapter_is_placeholder_boundary() -> None:
    """LiteLLM adapter is a placeholder and does not import LiteLLM."""
    with pytest.raises(NotImplementedError):
        LiteLLMAdapter().complete(make_prompt(), make_route())

    assert "AION contracts must remain independent" in (LiteLLMAdapter.__doc__ or "")
    assert "litellm" not in sys.modules


def make_prompt() -> PromptPacket:
    """Create a prompt packet."""
    return PromptPacket(
        prompt_id="prompt-1",
        trace_id="trace-1",
        intent_id="intent-1",
        context_id="context-1",
        goal="answer a generic question",
        system_instructions=["Use AION contracts."],
        context_items=[
            {"type": "known_context", "value": [{"source": "intent"}]},
            {"type": "retrieved_memory_ids", "value": ["memory-1"]},
            {"type": "available_capability_ids", "value": ["capability-1"]},
            {"type": "open_questions", "value": []},
        ],
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
        selected_provider="deterministic",
        selected_model="deterministic-reasoner-v0",
        mode="analyze",
        reason="v0.1 uses deterministic local reasoning only",
        fallback_providers=[],
        privacy_level="local",
        risk_level="low",
        estimated_cost=0.0,
        estimated_latency_ms=0,
        created_at=datetime.now(UTC),
    )
