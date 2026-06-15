"""Event reaction contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.event_reactions import (
    EventDeadLetterRecord,
    EventDispatchRequest,
    EventReactionAction,
    EventSubscription,
    EventSubscriptionCreateRequest,
    EventTriggerRule,
)
from aion_brain.contracts.events import AIONEvent


def test_trigger_rule_rejects_code_like_field_path() -> None:
    """Trigger rules only accept static dotted paths."""
    with pytest.raises(ValidationError):
        EventTriggerRule(
            rule_id="rule-1",
            rule_type="generic",
            field_path="payload.items[0]",
            operator="exists",
        )


def test_subscription_requires_event_patterns_and_safe_metadata() -> None:
    """Subscriptions reject empty patterns and secret-like metadata."""
    with pytest.raises(ValidationError):
        EventSubscriptionCreateRequest(
            name="Generic subscription",
            description="React to generic events.",
            event_type_patterns=[],
            target_type="noop",
        )

    with pytest.raises(ValidationError):
        EventSubscriptionCreateRequest(
            name="Generic subscription",
            description="React to generic events.",
            event_type_patterns=["generic.*"],
            target_type="noop",
            metadata={"api_key": "secret"},
        )


def test_subscription_rejects_vertical_target_terms() -> None:
    """Subscriptions remain domain-neutral."""
    with pytest.raises(ValidationError):
        EventSubscriptionCreateRequest(
            name="Generic subscription",
            description="React to generic events.",
            event_type_patterns=["generic.*"],
            target_type="capability",
            target_id="finance.capability",
        )


def test_dispatch_request_requires_event_or_event_id() -> None:
    """Dispatch requests need an inline event or ledger reference."""
    with pytest.raises(ValidationError):
        EventDispatchRequest(owner_scope=["workspace:main"])


def test_dispatch_request_accepts_inline_event() -> None:
    """Dispatch requests can carry an inline normalized event."""
    request = EventDispatchRequest(
        event=event(),
        owner_scope=["workspace:main"],
    )

    assert request.event is not None
    assert request.event.event_id == "event-1"


def test_action_and_dead_letter_contracts_validate_payload_safety() -> None:
    """Action and dead-letter records reject secret-like payloads."""
    with pytest.raises(ValidationError):
        EventReactionAction(
            reaction_action_id="action-1",
            dispatch_id="dispatch-1",
            subscription_id="sub-1",
            event_id="event-1",
            target_type="noop",
            action_type="event.reaction.noop",
            mode="dry_run",
            status="pending",
            input={"token": "secret"},
        )

    with pytest.raises(ValidationError):
        EventDeadLetterRecord(
            dead_letter_id="dead-1",
            dispatch_id="dispatch-1",
            event_id="event-1",
            reason="failed",
            error={"password": "secret"},
        )


def test_event_subscription_contract_accepts_generic_targets() -> None:
    """A valid generic subscription contract can be created."""
    subscription = EventSubscription(
        subscription_id="sub-1",
        name="Generic subscription",
        description="React to a generic event.",
        owner_scope=["workspace:main"],
        event_type_patterns=["generic.*"],
        target_type="noop",
    )

    assert subscription.status == "active"
    assert subscription.reaction_mode == "dry_run"


def event() -> AIONEvent:
    """Return a valid normalized event."""
    return AIONEvent(
        event_id="event-1",
        source="test-suite",
        event_type="generic.received",
        payload_type="generic.payload",
        payload={"message": "remember this"},
        timestamp=datetime.now(UTC),
        security_scope=["workspace:main"],
    )
