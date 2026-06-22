"""Planner tests."""

from datetime import UTC, datetime

from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.reasoning import ReasoningResult
from aion_brain.planning.planner import Planner


def make_context(intent_type: str) -> ContextPacket:
    """Create a context packet with intent metadata."""
    return ContextPacket(
        context_id="context-1",
        intent_id="intent-1",
        goal="generic goal",
        known_context=[{"source": "intent", "intent_type": intent_type}],
        retrieved_memory_ids=[],
        available_capability_ids=[],
        constraints=[],
        open_questions=[],
        execution_limits={"no_model_calls": True},
    )


def test_planner_creates_question_answer_steps() -> None:
    """Question answering plans use generic response steps."""
    plan = Planner().create_plan(make_context("question.answer"))

    assert [step.step_id for step in plan.steps] == [
        "retrieve_context",
        "draft_response",
        "evaluate_response",
    ]
    assert [step.action_type for step in plan.steps] == [
        "memory.retrieve",
        "response.draft",
        "evaluation.score",
    ]
    assert plan.risk_level == "low"


def test_planner_creates_steps_for_supported_intents() -> None:
    """Every deterministic intent maps to the expected generic step IDs."""
    expectations = {
        "goal.plan": [
            "retrieve_context",
            "identify_capabilities",
            "create_plan",
            "policy_check",
        ],
        "action.execute": [
            "retrieve_context",
            "identify_capabilities",
            "create_plan",
            "policy_check",
            "wait_for_execution_layer",
        ],
        "memory.remember": ["validate_memory_candidate", "policy_check", "store_memory"],
        "memory.retrieve": ["policy_check", "retrieve_memory"],
        "capability.discover": ["policy_check", "list_capabilities"],
        "unknown": ["ask_clarifying_question"],
    }

    for intent_type, step_ids in expectations.items():
        plan = Planner().create_plan(make_context(intent_type))

        assert [step.step_id for step in plan.steps] == step_ids
        assert all(step.status == "pending" for step in plan.steps)
        assert all(step.capability_required is not None for step in plan.steps)


def test_planner_uses_unknown_when_context_has_no_intent_type() -> None:
    """Missing intent metadata becomes a clarification plan."""
    context = make_context("question.answer").model_copy(update={"known_context": []})

    plan = Planner().create_plan(context)

    assert [step.step_id for step in plan.steps] == ["ask_clarifying_question"]
    assert plan.steps[0].action_type == "clarification.ask"


def test_planner_uses_clarification_step_from_reasoning() -> None:
    """Clarifying reasoning adds a generic clarification plan step."""
    plan = Planner().create_plan(make_context("question.answer"), make_reasoning())

    assert [step.step_id for step in plan.steps] == [
        "retrieve_context",
        "draft_response",
        "evaluate_response",
        "ask_clarifying_question",
    ]
    assert plan.metadata == {
        "reasoning_suggested_next_actions": ["ask_clarifying_question"],
    }


def make_reasoning() -> ReasoningResult:
    """Create a clarifying reasoning result."""
    return ReasoningResult.model_validate(
        {
            "reasoning_id": "reasoning-1",
            "trace_id": "trace-1",
            "context_id": "context-1",
            "mode": "plan_assist",
            "summary": "summary",
            "interpretation": "interpretation",
            "suggested_next_actions": ["ask_clarifying_question"],
            "constraints": [],
            "confidence": 0.6,
            "requires_clarification": True,
            "clarification_questions": ["What is the goal?"],
            "route_decision": {
                "route_id": "route-1",
                "trace_id": "trace-1",
                "reasoning_id": "reasoning-1",
                "selected_provider": "aion-local",
                "selected_model": "deterministic-reasoner-v0",
                "mode": "plan_assist",
                "reason": "v0.1 uses deterministic local reasoning only",
                "fallback_providers": [],
                "privacy_level": "local",
                "risk_level": "low",
                "estimated_cost": 0.0,
                "estimated_latency_ms": 0,
                "created_at": datetime.now(UTC).isoformat(),
            },
            "prompt_packet": {
                "prompt_id": "prompt-1",
                "trace_id": "trace-1",
                "intent_id": "intent-1",
                "context_id": "context-1",
                "goal": "generic goal",
                "system_instructions": [],
                "context_items": [],
                "constraints": [],
                "requested_output_schema": {},
                "token_budget_hint": None,
                "created_at": datetime.now(UTC).isoformat(),
            },
            "metadata": {},
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
