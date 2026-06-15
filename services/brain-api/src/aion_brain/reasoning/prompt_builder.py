"""Provider-neutral prompt packet builder."""

from datetime import UTC, datetime
from typing import Any

from aion_brain.contracts.reasoning import PromptPacket, ReasoningRequest

SYSTEM_INSTRUCTIONS = [
    "You are AION Brain reasoning over a domain-neutral context packet.",
    "Do not introduce domain-specific assumptions.",
    "Use only provided context, constraints, and contracts.",
    "Ground claims in available evidence references when evidence is provided.",
]

REQUESTED_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "summary",
        "interpretation",
        "suggested_next_actions",
        "requires_clarification",
        "clarification_questions",
        "confidence",
    ],
    "properties": {
        "summary": {"type": "string"},
        "interpretation": {"type": "string"},
        "suggested_next_actions": {"type": "array", "items": {"type": "string"}},
        "requires_clarification": {"type": "boolean"},
        "clarification_questions": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}


class PromptBuilder:
    """Build prompt packets from AION context contracts."""

    def build(self, request: ReasoningRequest) -> PromptPacket:
        """Build a provider-neutral prompt packet."""
        context = request.context
        return PromptPacket(
            prompt_id=f"prompt-{request.reasoning_id}",
            trace_id=request.trace_id,
            intent_id=request.intent.intent_id if request.intent else context.intent_id,
            context_id=context.context_id,
            goal=context.goal,
            system_instructions=list(SYSTEM_INSTRUCTIONS),
            context_items=[
                {"type": "goal", "value": context.goal},
                {"type": "known_context", "value": context.known_context},
                {"type": "retrieved_memory_ids", "value": context.retrieved_memory_ids},
                {"type": "evidence_refs", "value": _evidence_refs(context.known_context)},
                {"type": "available_capability_ids", "value": context.available_capability_ids},
                {"type": "constraints", "value": context.constraints},
                {"type": "open_questions", "value": context.open_questions},
                {"type": "execution_limits", "value": context.execution_limits},
            ],
            constraints=list(context.constraints),
            requested_output_schema=dict(REQUESTED_OUTPUT_SCHEMA),
            token_budget_hint=_token_budget_hint(context.execution_limits),
            created_at=datetime.now(UTC),
        )


def _token_budget_hint(execution_limits: dict[str, Any]) -> int | None:
    value = execution_limits.get("token_budget_hint")
    if isinstance(value, int) and value > 0:
        return value
    return None


def _evidence_refs(known_context: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for item in known_context:
        value = item.get("evidence_ref")
        values = item.get("evidence_refs")
        candidates = values if isinstance(values, list) else [value]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate and candidate not in seen:
                seen.add(candidate)
                refs.append(candidate)
    return refs
