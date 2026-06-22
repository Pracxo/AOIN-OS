"""ModelRouter tests."""

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.reasoning import ReasoningRequest
from aion_brain.reasoning.router import LOCAL_MODEL, LOCAL_PROVIDER, ModelRouter


def test_model_router_selects_local_deterministic_model() -> None:
    """v0.1 routes only to the local deterministic model boundary."""
    route = ModelRouter().route(
        ReasoningRequest(
            reasoning_id="reasoning-1",
            trace_id="trace-1",
            intent=None,
            context=make_context(),
            mode="analyze",
            risk_level="low",
            metadata={},
        )
    )

    assert route.selected_provider == LOCAL_PROVIDER
    assert route.selected_model == LOCAL_MODEL
    assert route.privacy_level == "local"
    assert route.estimated_cost == 0.0
    assert route.estimated_latency_ms == 0


def make_context() -> ContextPacket:
    """Create a context packet."""
    return ContextPacket(
        context_id="context-1",
        intent_id="intent-1",
        goal="answer",
        known_context=[],
        retrieved_memory_ids=[],
        available_capability_ids=[],
        constraints=[],
        open_questions=[],
        execution_limits={},
    )
