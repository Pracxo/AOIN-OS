"""Deterministic local reasoning adapter."""

from datetime import UTC, datetime
from typing import Any

from aion_brain.contracts.reasoning import ModelCallRecord, ModelRouteDecision, PromptPacket
from aion_brain.reasoning.router import LOCAL_MODEL, LOCAL_PROVIDER


class DeterministicReasoningAdapter:
    """Local provider-free reasoning adapter for AION v0.1."""

    def complete(self, prompt: PromptPacket, route: ModelRouteDecision) -> ModelCallRecord:
        """Produce a stable model call record without external calls."""
        response = _response_from_prompt(prompt)
        return ModelCallRecord(
            model_call_id=f"model-call-{prompt.prompt_id}",
            trace_id=prompt.trace_id,
            reasoning_id=route.reasoning_id,
            provider=LOCAL_PROVIDER,
            model=LOCAL_MODEL,
            mode=route.mode,
            request={
                "prompt_packet": prompt.model_dump(mode="json"),
                "route_decision": route.model_dump(mode="json"),
            },
            response=response,
            status="completed",
            latency_ms=0,
            cost_estimate=0.0,
            created_at=datetime.now(UTC),
        )


def _response_from_prompt(prompt: PromptPacket) -> dict[str, Any]:
    goal = prompt.goal.strip()
    open_questions = _list_context_value(prompt, "open_questions")
    memory_ids = _list_context_value(prompt, "retrieved_memory_ids")
    capability_ids = _list_context_value(prompt, "available_capability_ids")
    known_context = _list_context_value(prompt, "known_context")

    suggested_actions: list[str] = []
    if capability_ids:
        suggested_actions.append("review_available_capabilities")
    if memory_ids:
        suggested_actions.append("use_retrieved_memory")
    if not goal or open_questions or not known_context:
        suggested_actions.append("ask_clarifying_question")

    clarification_questions = [str(question) for question in open_questions]
    if not goal and not clarification_questions:
        clarification_questions.append("What goal should AION reason about?")

    requires_clarification = not goal or bool(clarification_questions)
    confidence = 0.6 if requires_clarification else 0.85
    return {
        "summary": _summary(goal, memory_ids, capability_ids),
        "interpretation": _interpretation(goal, known_context),
        "suggested_next_actions": suggested_actions,
        "requires_clarification": requires_clarification,
        "clarification_questions": clarification_questions,
        "confidence": confidence,
    }


def _list_context_value(prompt: PromptPacket, item_type: str) -> list[Any]:
    for item in prompt.context_items:
        if item.get("type") == item_type:
            value = item.get("value")
            if isinstance(value, list):
                return value
            return []
    return []


def _summary(goal: str, memory_ids: list[Any], capability_ids: list[Any]) -> str:
    if not goal:
        return "AION needs a clearer goal before reasoning can continue."
    parts = [f"AION reviewed the provided context for goal: {goal}."]
    if memory_ids:
        parts.append("Relevant memory references are available.")
    if capability_ids:
        parts.append("Relevant capability references are available.")
    return " ".join(parts)


def _interpretation(goal: str, known_context: list[Any]) -> str:
    if not goal:
        return "The context packet does not provide a usable goal."
    if not known_context:
        return "The goal is present, but supporting context is limited."
    return "The goal can be handled with deterministic planning over the supplied context."
