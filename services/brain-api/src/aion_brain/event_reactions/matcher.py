"""Deterministic event subscription matcher."""

from typing import Any

from aion_brain.contracts.event_reactions import EventSubscription, EventTriggerRule
from aion_brain.contracts.events import AIONEvent


class EventTriggerMatcher:
    """Match normalized AION events to active subscriptions without eval or regex."""

    def matches_subscription(self, event: AIONEvent, subscription: EventSubscription) -> bool:
        """Return whether one event satisfies a subscription."""
        if subscription.status != "active":
            return False
        if subscription.source_filters and event.source not in subscription.source_filters:
            return False
        if not any(
            _pattern_matches(event.event_type, pattern)
            for pattern in subscription.event_type_patterns
        ):
            return False
        for rule in subscription.trigger_rules:
            matched = self.matches_rule(event, rule)
            if rule.required and not matched:
                return False
        return True

    def matches_rule(self, event: AIONEvent, rule: EventTriggerRule) -> bool:
        """Return whether one event satisfies one trigger rule."""
        if rule.rule_type == "event_type":
            return _compare(event.event_type, rule.operator, rule.value, rule.values)
        if rule.rule_type == "source":
            return _compare(event.source, rule.operator, rule.value, rule.values)
        if rule.rule_type == "actor":
            return _compare(event.actor_id, rule.operator, rule.value, rule.values)
        if rule.rule_type == "workspace":
            return _compare(event.workspace_id, rule.operator, rule.value, rule.values)
        if rule.rule_type == "payload_key_exists":
            return _value_at(event, rule.field_path, payload_default=True) is not _MISSING
        if rule.rule_type == "payload_value_equals":
            value = _value_at(event, rule.field_path, payload_default=True)
            return value is not _MISSING and _compare(value, "equals", rule.value, rule.values)
        if rule.rule_type == "payload_value_in":
            value = _value_at(event, rule.field_path, payload_default=True)
            return value is not _MISSING and _compare(value, "in", rule.value, rule.values)
        if rule.rule_type == "security_scope_contains":
            return _compare(event.security_scope, "contains", rule.value, rule.values)
        if rule.rule_type == "correlation_present":
            return event.correlation_id is not None and bool(event.correlation_id)
        if rule.rule_type == "trace_present":
            return event.trace_id is not None and bool(event.trace_id)
        if rule.rule_type == "risk_level_hint":
            value = event.payload.get("risk_level_hint", event.payload.get("risk_level"))
            return _compare(value, rule.operator, rule.value, rule.values)
        value = _value_at(event, rule.field_path, payload_default=False)
        return value is not _MISSING and _compare(value, rule.operator, rule.value, rule.values)

    def match_subscriptions(
        self,
        event: AIONEvent,
        subscriptions: list[EventSubscription],
    ) -> list[EventSubscription]:
        """Return all matching active subscriptions in their existing order."""
        return [
            subscription
            for subscription in subscriptions
            if self.matches_subscription(event, subscription)
        ]


def _pattern_matches(event_type: str, pattern: str) -> bool:
    if pattern == event_type:
        return True
    if pattern.endswith("*"):
        return event_type.startswith(pattern[:-1])
    return False


class _Missing:
    """Sentinel for absent values."""


_MISSING = _Missing()


def _value_at(event: AIONEvent, field_path: str | None, *, payload_default: bool) -> object:
    if field_path is None:
        return _MISSING
    path = field_path if not payload_default else _payload_path(field_path)
    if path in {"source", "event_type", "actor_id", "workspace_id", "trace_id", "correlation_id"}:
        return getattr(event, path)
    if path == "security_scope":
        return event.security_scope
    if not path.startswith("payload."):
        return _MISSING
    value: object = event.payload
    for segment in path.split(".")[1:]:
        if not isinstance(value, dict) or segment not in value:
            return _MISSING
        value = value[segment]
    return value


def _payload_path(field_path: str) -> str:
    if field_path.startswith("payload."):
        return field_path
    if field_path in {
        "source",
        "event_type",
        "actor_id",
        "workspace_id",
        "trace_id",
        "correlation_id",
    }:
        return field_path
    return f"payload.{field_path}"


def _compare(value: object, operator: str, expected: Any | None, values: list[Any]) -> bool:
    candidates = values or ([] if expected is None else [expected])
    if operator == "exists":
        return value is not None
    if operator == "equals":
        return value == expected
    if operator == "not_equals":
        return value != expected
    if operator == "in":
        return value in candidates
    if operator == "not_in":
        return value not in candidates
    if operator == "contains":
        return _contains(value, candidates)
    if operator == "starts_with":
        return isinstance(value, str) and isinstance(expected, str) and value.startswith(expected)
    if operator == "ends_with":
        return isinstance(value, str) and isinstance(expected, str) and value.endswith(expected)
    return False


def _contains(value: object, candidates: list[Any]) -> bool:
    if isinstance(value, list):
        return any(candidate in value for candidate in candidates)
    if isinstance(value, str):
        return any(isinstance(candidate, str) and candidate in value for candidate in candidates)
    if isinstance(value, dict):
        return any(candidate in value for candidate in candidates if isinstance(candidate, str))
    return False
