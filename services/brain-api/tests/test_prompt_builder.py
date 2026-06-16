"""PromptBuilder tests."""

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.reasoning import ReasoningRequest
from aion_brain.reasoning.prompt_builder import SYSTEM_INSTRUCTIONS, PromptBuilder


def test_prompt_builder_includes_context_parts() -> None:
    """Prompt packets include goal, constraints, memory refs, and capability refs."""
    request = ReasoningRequest(
        reasoning_id="reasoning-1",
        trace_id="trace-1",
        intent=None,
        context=ContextPacket(
            context_id="context-1",
            intent_id="intent-1",
            goal="answer a generic question",
            known_context=[{"source": "intent"}],
            retrieved_memory_ids=["memory-1"],
            available_capability_ids=["capability-1"],
            constraints=["stay_generic"],
            open_questions=["clarify scope"],
            execution_limits={"token_budget_hint": 500},
        ),
        mode="analyze",
        risk_level="low",
        metadata={},
    )

    prompt = PromptBuilder().build(request)

    items = {item["type"]: item["value"] for item in prompt.context_items}
    assert prompt.goal == "answer a generic question"
    assert prompt.system_instructions == SYSTEM_INSTRUCTIONS
    assert items["retrieved_memory_ids"] == ["memory-1"]
    assert items["available_capability_ids"] == ["capability-1"]
    assert prompt.constraints == ["stay_generic"]
    assert prompt.token_budget_hint == 500


def test_prompt_builder_includes_belief_status_metadata() -> None:
    request = ReasoningRequest(
        reasoning_id="reasoning-1",
        trace_id="trace-1",
        intent=None,
        context=ContextPacket(
            context_id="context-1",
            intent_id="intent-1",
            goal="answer a generic question",
            known_context=[
                {
                    "source": "belief_state",
                    "source_id": "claim-1",
                    "metadata": {"status": "contradicted", "claim_type": "generic"},
                }
            ],
            retrieved_memory_ids=[],
            available_capability_ids=[],
            constraints=["belief_contradicted:generic"],
            open_questions=[],
            execution_limits={},
        ),
        mode="analyze",
        risk_level="low",
        metadata={},
    )

    prompt = PromptBuilder().build(request)
    items = {item["type"]: item["value"] for item in prompt.context_items}

    assert items["belief_status_metadata"] == [
        {
            "source_id": "claim-1",
            "status": "contradicted",
            "claim_type": "generic",
            "not_absolute_truth": True,
        }
    ]
