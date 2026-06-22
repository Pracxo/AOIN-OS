"""Event reaction matcher tests."""

from datetime import UTC, datetime

from aion_brain.contracts.event_reactions import EventSubscription, EventTriggerRule
from aion_brain.contracts.events import AIONEvent
from aion_brain.event_reactions.matcher import EventTriggerMatcher


def test_matcher_supports_exact_and_wildcard_event_patterns() -> None:
    """Subscriptions match exact event types and simple wildcard suffixes."""
    matcher = EventTriggerMatcher()

    assert matcher.matches_subscription(
        event(event_type="generic.received"),
        subscription("generic.*"),
    )
    assert matcher.matches_subscription(
        event(event_type="generic.received"),
        subscription("generic.received"),
    )
    assert not matcher.matches_subscription(
        event(event_type="other.received"),
        subscription("generic.*"),
    )


def test_matcher_applies_source_filters() -> None:
    """Source filters must match exactly when present."""
    sub = subscription("generic.*", source_filters=["trusted-source"])

    assert EventTriggerMatcher().matches_subscription(event(source="trusted-source"), sub)
    assert not EventTriggerMatcher().matches_subscription(event(source="other-source"), sub)


def test_matcher_applies_required_and_optional_rules() -> None:
    """Required rules gate matches while optional rule misses do not block."""
    sub = subscription(
        "generic.*",
        rules=[
            EventTriggerRule(
                rule_id="payload-message",
                rule_type="payload_key_exists",
                field_path="message",
                operator="exists",
                required=True,
            ),
            EventTriggerRule(
                rule_id="optional",
                rule_type="payload_value_equals",
                field_path="missing",
                operator="equals",
                value="x",
                required=False,
            ),
        ],
    )

    assert EventTriggerMatcher().matches_subscription(event(payload={"message": "hello"}), sub)
    assert not EventTriggerMatcher().matches_subscription(event(payload={}), sub)


def test_matcher_supports_payload_value_and_scope_rules() -> None:
    """Payload and security scope rules are deterministic and generic."""
    sub = subscription(
        "generic.*",
        rules=[
            EventTriggerRule(
                rule_id="intent",
                rule_type="payload_value_in",
                field_path="intent",
                operator="in",
                values=["remember", "retrieve"],
            ),
            EventTriggerRule(
                rule_id="scope",
                rule_type="security_scope_contains",
                operator="contains",
                value="workspace:main",
            ),
        ],
    )

    assert EventTriggerMatcher().matches_subscription(event(payload={"intent": "remember"}), sub)
    assert not EventTriggerMatcher().matches_subscription(event(payload={"intent": "execute"}), sub)


def test_matcher_supports_trace_and_correlation_presence() -> None:
    """Trace and correlation presence rules use normalized event metadata."""
    sub = subscription(
        "generic.*",
        rules=[
            EventTriggerRule(
                rule_id="trace",
                rule_type="trace_present",
                operator="exists",
            ),
            EventTriggerRule(
                rule_id="correlation",
                rule_type="correlation_present",
                operator="exists",
            ),
        ],
    )

    assert EventTriggerMatcher().matches_subscription(
        event(trace_id="trace-1", correlation_id="corr-1"),
        sub,
    )
    assert not EventTriggerMatcher().matches_subscription(event(trace_id=None), sub)


def test_matcher_returns_all_matching_subscriptions() -> None:
    """The matcher returns matching subscriptions in input order."""
    subscriptions = [subscription("generic.*", "sub-1"), subscription("other.*", "sub-2")]

    matches = EventTriggerMatcher().match_subscriptions(event(), subscriptions)

    assert [item.subscription_id for item in matches] == ["sub-1"]


def event(
    *,
    event_type: str = "generic.received",
    source: str = "trusted-source",
    payload: dict[str, object] | None = None,
    trace_id: str | None = "trace-1",
    correlation_id: str | None = "corr-1",
) -> AIONEvent:
    """Create a normalized event for matcher tests."""
    return AIONEvent(
        event_id="event-1",
        source=source,
        event_type=event_type,
        payload_type="generic.payload",
        payload=payload if payload is not None else {"message": "hello", "intent": "remember"},
        timestamp=datetime.now(UTC),
        correlation_id=correlation_id,
        trace_id=trace_id,
        security_scope=["workspace:main"],
    )


def subscription(
    pattern: str,
    subscription_id: str = "sub-1",
    *,
    source_filters: list[str] | None = None,
    rules: list[EventTriggerRule] | None = None,
) -> EventSubscription:
    """Create a subscription for matcher tests."""
    return EventSubscription(
        subscription_id=subscription_id,
        name="Generic subscription",
        description="React to generic events.",
        owner_scope=["workspace:main"],
        source_filters=source_filters or [],
        event_type_patterns=[pattern],
        trigger_rules=rules or [],
        target_type="noop",
    )
