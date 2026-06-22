"""Event reaction dead-letter service tests."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.event_reactions import (
    EventDispatchRecord,
    EventDispatchRequest,
    EventReactionAction,
)
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.event_reactions.dead_letters import EventDeadLetterService
from aion_brain.event_reactions.repository import EventReactionRepository
from aion_brain.events.repository import EventRepository


class FakePolicy:
    """Policy fake."""

    def __init__(self, allow: bool = True) -> None:
        self.allow = allow

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeRouter:
    """Replay router fake."""

    def __init__(self) -> None:
        self.requests: list[EventDispatchRequest] = []

    def dispatch(self, request: EventDispatchRequest) -> EventDispatchRecord:
        self.requests.append(request)
        event_id = request.event.event_id if request.event else request.event_id or "event-1"
        return EventDispatchRecord(
            dispatch_id="replay-dispatch-1",
            event_id=event_id,
            trace_id=request.trace_id,
            status="dry_run",
            mode="dry_run",
            matched_subscription_ids=request.subscription_ids,
            actions=[],
            action_count=0,
            completed_action_count=0,
            failed_action_count=0,
            blocked_action_count=0,
            result={"owner_scope": request.owner_scope},
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )


def test_dead_letter_service_creates_and_resolves_record() -> None:
    """Dead letters can be created and marked resolved."""
    service, _events, _repository = make_service()
    record = service.create_dead_letter(
        dispatch_id="dispatch-1",
        action=action(),
        event=event(),
        reason="failed",
        error={"reason": "failed"},
    )

    resolved = service.mark_resolved(
        record.dead_letter_id,
        actor_id="actor-1",
        reason="fixed",
    )

    assert record.status == "open"
    assert resolved.status == "resolved"
    assert resolved.error["resolution_reason"] == "fixed"


def test_dead_letter_service_replays_original_event() -> None:
    """Replay loads the original event and dispatches dry-run."""
    router = FakeRouter()
    service, events, _repository = make_service(router=router)
    events.save(event())
    record = service.create_dead_letter(
        dispatch_id="dispatch-1",
        action=action(),
        event=event(),
        reason="failed",
        error={"reason": "failed"},
    )

    replay = service.replay(record.dead_letter_id)

    assert replay.dispatch_id == "replay-dispatch-1"
    assert router.requests[0].mode == "dry_run"
    assert router.requests[0].subscription_ids == ["sub-1"]


def test_dead_letter_service_policy_deny_blocks_replay() -> None:
    """Policy denial fails closed for replay."""
    router = FakeRouter()
    service, events, _repository = make_service(policy=FakePolicy(allow=False), router=router)
    events.save(event())
    record = service.create_dead_letter(
        dispatch_id="dispatch-1",
        action=action(),
        event=event(),
        reason="failed",
        error={"reason": "failed"},
    )

    with pytest.raises(PermissionError):
        service.replay(record.dead_letter_id)

    assert router.requests == []


def make_service(
    *,
    policy: FakePolicy | None = None,
    router: FakeRouter | None = None,
) -> tuple[EventDeadLetterService, EventRepository, EventReactionRepository]:
    """Create a dead-letter service with in-memory persistence."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    events = EventRepository(engine=engine)
    repository = EventReactionRepository(engine=engine)
    service = EventDeadLetterService(
        repository=repository,
        event_repository=events,
        policy_adapter=policy or FakePolicy(),
        settings=Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:"),
        router=router,
    )
    return service, events, repository


def action() -> EventReactionAction:
    """Create a failed reaction action."""
    return EventReactionAction(
        reaction_action_id="action-1",
        dispatch_id="dispatch-1",
        subscription_id="sub-1",
        event_id="event-1",
        trace_id="trace-1",
        target_type="noop",
        action_type="event.reaction.noop",
        mode="controlled",
        status="failed",
        error={"reason": "failed"},
    )


def event() -> AIONEvent:
    """Create a normalized event."""
    return AIONEvent(
        event_id="event-1",
        source="test-suite",
        event_type="generic.received",
        actor_id="actor-1",
        workspace_id="workspace-1",
        payload_type="generic.payload",
        payload={"message": "hello"},
        timestamp=datetime.now(UTC),
        trace_id="trace-1",
        correlation_id="corr-1",
        security_scope=["workspace:main"],
    )
