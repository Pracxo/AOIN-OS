"""Event reaction outbox integration tests."""

from datetime import UTC, datetime

from aion_brain.contracts.event_reactions import EventReactionAction, EventSubscription
from aion_brain.contracts.events import AIONEvent
from aion_brain.event_reactions.actions import EventReactionActionRunner


class FakeOutbox:
    """Outbox fake."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def enqueue(self, request: object) -> object:
        self.requests.append(request)
        return object()


def test_event_reaction_action_enqueues_lifecycle_outbox_message() -> None:
    """Event reactions enqueue lifecycle notifications through outbox."""
    outbox = FakeOutbox()
    runner = EventReactionActionRunner(outbox_service=outbox)

    runner.dry_run(action=action(), event=event(), subscription=subscription())

    assert outbox.requests


def action() -> EventReactionAction:
    return EventReactionAction(
        reaction_action_id="reaction-action-1",
        dispatch_id="dispatch-1",
        subscription_id="subscription-1",
        event_id="event-1",
        target_type="noop",
        action_type="event.reaction.noop",
        mode="dry_run",
        status="pending",
        input={},
        output={},
        error={},
    )


def event() -> AIONEvent:
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="generic.created",
        payload_type="json",
        payload={},
        timestamp=datetime.now(UTC),
        trace_id="trace-1",
        correlation_id="corr-1",
        security_scope=["workspace:main"],
    )


def subscription() -> EventSubscription:
    return EventSubscription(
        subscription_id="subscription-1",
        name="Test",
        description="Test subscription",
        owner_scope=["workspace:main"],
        event_type_patterns=["generic.*"],
        target_type="noop",
        reaction_mode="dry_run",
        risk_level="low",
    )
