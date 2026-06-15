"""Event reaction repository tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.event_reactions import (
    EventDeadLetterRecord,
    EventDispatchRecord,
    EventReactionAction,
    EventSubscription,
    EventTriggerRule,
)
from aion_brain.event_reactions.repository import EventReactionRepository


def test_repository_persists_subscriptions() -> None:
    """Subscriptions round-trip through the repository."""
    repository = repository_fixture()
    subscription = EventSubscription(
        subscription_id="sub-1",
        name="Generic subscription",
        description="React to generic events.",
        owner_scope=["workspace:main"],
        event_type_patterns=["generic.*"],
        trigger_rules=[
            EventTriggerRule(
                rule_id="message",
                rule_type="payload_key_exists",
                field_path="message",
                operator="exists",
            )
        ],
        target_type="noop",
    )

    saved = repository.save_subscription(subscription)
    fetched = repository.get_subscription(saved.subscription_id)
    listed = repository.list_subscriptions(scope=["workspace:main"], status="active")

    assert fetched is not None
    assert fetched.subscription_id == "sub-1"
    assert fetched.trigger_rules[0].rule_id == "message"
    assert [item.subscription_id for item in listed] == ["sub-1"]


def test_repository_persists_dispatches_and_actions() -> None:
    """Dispatch records and action records round-trip through the repository."""
    repository = repository_fixture()
    action = action_record(status="dry_run")
    dispatch = EventDispatchRecord(
        dispatch_id="dispatch-1",
        event_id="event-1",
        trace_id="trace-1",
        status="dry_run",
        mode="dry_run",
        matched_subscription_ids=["sub-1"],
        actions=[action],
        action_count=1,
        completed_action_count=1,
        failed_action_count=0,
        blocked_action_count=0,
        result={"owner_scope": ["workspace:main"]},
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )

    repository.save_dispatch(dispatch)
    repository.save_action(action)

    fetched = repository.get_dispatch("dispatch-1")
    dispatches = repository.list_dispatches(scope=["workspace:main"])
    actions = repository.list_actions("dispatch-1")

    assert fetched is not None
    assert fetched.actions[0].status == "dry_run"
    assert dispatches[0].dispatch_id == "dispatch-1"
    assert actions[0].reaction_action_id == "action-1"


def test_repository_persists_dead_letters() -> None:
    """Dead-letter records round-trip through the repository."""
    repository = repository_fixture()
    record = EventDeadLetterRecord(
        dead_letter_id="dead-1",
        dispatch_id="dispatch-1",
        reaction_action_id="action-1",
        event_id="event-1",
        subscription_id="sub-1",
        trace_id="trace-1",
        reason="failed",
        error={"owner_scope": ["workspace:main"]},
        status="open",
        replay_count=0,
        created_at=datetime.now(UTC),
    )

    repository.save_dead_letter(record)
    fetched = repository.get_dead_letter("dead-1")
    listed = repository.list_dead_letters(scope=["workspace:main"], status="open")

    assert fetched is not None
    assert fetched.reason == "failed"
    assert listed[0].dead_letter_id == "dead-1"


def repository_fixture() -> EventReactionRepository:
    """Create an in-memory repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return EventReactionRepository(engine=engine)


def action_record(status: str = "running") -> EventReactionAction:
    """Create an action record."""
    return EventReactionAction(
        reaction_action_id="action-1",
        dispatch_id="dispatch-1",
        subscription_id="sub-1",
        event_id="event-1",
        trace_id="trace-1",
        target_type="noop",
        action_type="event.reaction.noop",
        mode="dry_run",
        status=status,  # type: ignore[arg-type]
        input={},
        output={},
        error={},
        created_at=datetime.now(UTC),
    )
