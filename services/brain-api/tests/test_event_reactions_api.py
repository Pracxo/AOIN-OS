"""Event reaction API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.event_reactions import get_event_reaction_router
from aion_brain.contracts.event_reactions import (
    EventDeadLetterRecord,
    EventDispatchRecord,
    EventDispatchRequest,
    EventRouterStatus,
    EventSubscription,
    EventSubscriptionCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeDeadLetterService:
    """Dead-letter fake."""

    def list_dead_letters(self, scope, status=None, limit=100):  # type: ignore[no-untyped-def]
        return [dead_letter()]

    def mark_resolved(self, dead_letter_id, actor_id, reason):  # type: ignore[no-untyped-def]
        return dead_letter(dead_letter_id=dead_letter_id, status="resolved")

    def replay(self, dead_letter_id, approval_present=False):  # type: ignore[no-untyped-def]
        return dispatch_record(dispatch_id="replay-dispatch-1")


class FakeEventReactionRouter:
    """Router fake for API tests."""

    def __init__(self) -> None:
        self._dead_letter_service = FakeDeadLetterService()
        self.subscription = subscription()
        self.record = dispatch_record()

    def create_subscription(self, request: EventSubscriptionCreateRequest) -> EventSubscription:
        self.subscription = self.subscription.model_copy(
            update={
                "name": request.name,
                "description": request.description,
                "owner_scope": request.owner_scope,
            }
        )
        return self.subscription

    def list_subscriptions(self, scope, status=None):  # type: ignore[no-untyped-def]
        return [self.subscription]

    def get_subscription(self, subscription_id: str, scope: list[str]) -> EventSubscription | None:
        return self.subscription if subscription_id == self.subscription.subscription_id else None

    def disable_subscription(
        self,
        subscription_id: str,
        *,
        actor_id: str | None,
        reason: str,
    ) -> EventSubscription:
        return self.subscription.model_copy(update={"status": "disabled"})

    def dispatch(self, request: EventDispatchRequest) -> EventDispatchRecord:
        return self.record.model_copy(update={"mode": request.mode})

    def get_dispatch(self, dispatch_id: str, scope: list[str]) -> EventDispatchRecord | None:
        return self.record if dispatch_id == self.record.dispatch_id else None

    def list_dispatches(self, scope, status=None, limit=100):  # type: ignore[no-untyped-def]
        return [self.record]

    def list_dead_letters(self, scope, status=None, limit=100):  # type: ignore[no-untyped-def]
        return self._dead_letter_service.list_dead_letters(scope, status, limit)

    def resolve_dead_letter(self, dead_letter_id, actor_id=None, reason="resolved"):  # type: ignore[no-untyped-def]
        return self._dead_letter_service.mark_resolved(dead_letter_id, actor_id, reason)

    def replay_dead_letter(self, dead_letter_id, approval_present=False):  # type: ignore[no-untyped-def]
        return self._dead_letter_service.replay(dead_letter_id, approval_present)

    def status(self, scope: list[str] | None = None) -> EventRouterStatus:
        return EventRouterStatus(
            enabled=True,
            auto_dispatch_enabled=False,
            subscription_count=1,
            active_subscription_count=1,
            pending_dead_letter_count=1,
            latest_dispatch_id=self.record.dispatch_id,
            generated_at=datetime.now(UTC),
        )


def test_event_reaction_api_routes_work() -> None:
    """Event reaction API exposes subscription, dispatch, dead-letter, and status routes."""
    fake = FakeEventReactionRouter()
    app.dependency_overrides[get_event_reaction_router] = lambda: fake
    app.dependency_overrides[get_actor_context] = actor_context
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/event-router/subscriptions",
            json={
                "name": "Generic subscription",
                "description": "React to generic events.",
                "event_type_patterns": ["generic.*"],
                "target_type": "noop",
            },
        )
        listed = client.get(
            "/brain/event-router/subscriptions",
            params={"scope": "workspace:main"},
        )
        fetched = client.get(
            "/brain/event-router/subscriptions/sub-1",
            params={"scope": "workspace:main"},
        )
        disabled = client.post(
            "/brain/event-router/subscriptions/sub-1/disable",
            json={"reason": "not needed"},
        )
        dispatched = client.post(
            "/brain/event-router/dispatch",
            json={"event_id": "event-1", "owner_scope": ["workspace:main"]},
        )
        dispatch_get = client.get(
            "/brain/event-router/dispatches/dispatch-1",
            params={"scope": "workspace:main"},
        )
        dispatches = client.get(
            "/brain/event-router/dispatches",
            params={"scope": "workspace:main"},
        )
        dead_letters = client.get(
            "/brain/event-router/dead-letters",
            params={"scope": "workspace:main"},
        )
        resolved = client.post(
            "/brain/event-router/dead-letters/dead-1/resolve",
            json={"reason": "fixed"},
        )
        replayed = client.post(
            "/brain/event-router/dead-letters/dead-1/replay",
            json={"approval_present": False},
        )
        status = client.get(
            "/brain/event-router/status",
            params={"scope": "workspace:main"},
        )
    finally:
        app.dependency_overrides.clear()

    for response in (
        created,
        listed,
        fetched,
        disabled,
        dispatched,
        dispatch_get,
        dispatches,
        dead_letters,
        resolved,
        replayed,
        status,
    ):
        assert response.status_code == 200
    assert disabled.json()["status"] == "disabled"
    assert replayed.json()["dispatch_id"] == "replay-dispatch-1"
    assert status.json()["auto_dispatch_enabled"] is False


def actor_context() -> ActorContext:
    """Return a fake actor context."""
    return ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        security_scope=["workspace:main"],
        trace_id="trace-1",
        dev_mode=True,
    )


def subscription() -> EventSubscription:
    """Create a subscription contract."""
    return EventSubscription(
        subscription_id="sub-1",
        name="Generic subscription",
        description="React to generic events.",
        owner_scope=["workspace:main"],
        event_type_patterns=["generic.*"],
        target_type="noop",
    )


def dispatch_record(dispatch_id: str = "dispatch-1") -> EventDispatchRecord:
    """Create a dispatch record."""
    return EventDispatchRecord(
        dispatch_id=dispatch_id,
        event_id="event-1",
        trace_id="trace-1",
        status="dry_run",
        mode="dry_run",
        matched_subscription_ids=["sub-1"],
        actions=[],
        action_count=0,
        completed_action_count=0,
        failed_action_count=0,
        blocked_action_count=0,
        result={"owner_scope": ["workspace:main"]},
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def dead_letter(
    dead_letter_id: str = "dead-1",
    status: str = "open",
) -> EventDeadLetterRecord:
    """Create a dead-letter contract."""
    return EventDeadLetterRecord(
        dead_letter_id=dead_letter_id,
        dispatch_id="dispatch-1",
        reaction_action_id="action-1",
        event_id="event-1",
        subscription_id="sub-1",
        trace_id="trace-1",
        reason="failed",
        error={"owner_scope": ["workspace:main"]},
        status=status,  # type: ignore[arg-type]
        replay_count=0,
        created_at=datetime.now(UTC),
    )
