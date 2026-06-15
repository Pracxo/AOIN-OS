"""Deterministic intent engine."""

import re

from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame

INTENT_RISK_LEVELS = {
    "question.answer": "low",
    "memory.retrieve": "low",
    "context.compile": "low",
    "capability.discover": "low",
    "memory.remember": "medium",
    "goal.plan": "medium",
    "action.execute": "high",
    "unknown": "medium",
}

MEMORY_INTENTS = {"question.answer", "memory.retrieve", "context.compile"}
CAPABILITY_INTENTS = {"goal.plan", "action.execute", "capability.discover"}


class IntentEngine:
    """Convert normalized events into generic intent frames."""

    def from_event(self, event: AIONEvent) -> IntentFrame:
        """Classify an event using deterministic generic rules."""
        intent_type, confidence = self._classify(event)
        return IntentFrame(
            intent_id=f"intent-{event.event_id}",
            event_id=event.event_id,
            intent_type=intent_type,
            goal=_extract_goal(event),
            urgency="normal",
            risk_level=INTENT_RISK_LEVELS[intent_type],
            requires_memory=intent_type in MEMORY_INTENTS,
            requires_capability=intent_type in CAPABILITY_INTENTS,
            requires_approval=intent_type == "action.execute",
            confidence=confidence,
        )

    def _classify(self, event: AIONEvent) -> tuple[str, float]:
        event_type_match = _classify_text(event.event_type)
        if event.event_type in INTENT_RISK_LEVELS:
            return event.event_type, 0.9
        if event_type_match != "unknown":
            return event_type_match, 0.75

        explicit_intent = _explicit_payload_intent(event)
        if explicit_intent is not None:
            return explicit_intent, 0.75

        keyword_match = _classify_text(_payload_text(event))
        if keyword_match != "unknown":
            return keyword_match, 0.6

        return "unknown", 0.2


def _explicit_payload_intent(event: AIONEvent) -> str | None:
    for key in ("intent_type", "intent"):
        value = event.payload.get(key)
        if isinstance(value, str) and value in INTENT_RISK_LEVELS:
            return value
    return None


def _classify_text(value: str) -> str:
    tokens = set(re.findall(r"[a-z0-9]+", value.lower()))
    if tokens.intersection({"what", "how", "why", "question", "answer", "ask"}):
        return "question.answer"
    if "remember" in tokens:
        return "memory.remember"
    if "retrieve" in tokens:
        return "memory.retrieve"
    if "plan" in tokens or "goal" in tokens:
        return "goal.plan"
    if "execute" in tokens or "action" in tokens:
        return "action.execute"
    if "context" in tokens and "compile" in tokens:
        return "context.compile"
    if "capability" in tokens and ("discover" in tokens or "list" in tokens):
        return "capability.discover"
    return "unknown"


def _extract_goal(event: AIONEvent) -> str:
    for key in ("goal", "query", "question", "message", "text", "command"):
        value = event.payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown"


def _payload_text(event: AIONEvent) -> str:
    parts: list[str] = []
    for value in event.payload.values():
        if isinstance(value, str):
            parts.append(value)
    return " ".join(parts)
