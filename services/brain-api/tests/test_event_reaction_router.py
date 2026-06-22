"""Event reaction router tests."""

from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.event_reactions import (
    EventDispatchRequest,
    EventSubscriptionCreateRequest,
)
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.event_reactions.actions import EventReactionActionRunner
from aion_brain.event_reactions.dead_letters import EventDeadLetterService
from aion_brain.event_reactions.matcher import EventTriggerMatcher
from aion_brain.event_reactions.repository import EventReactionRepository
from aion_brain.event_reactions.router import EventReactionRouter
from aion_brain.events.repository import EventRepository


class FakePolicy:
    """Policy fake."""

    def __init__(self, deny_action: str | None = None) -> None:
        self.deny_action = deny_action
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self.deny_action
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeAutonomy:
    """Autonomy fake."""

    def __init__(self, allow: bool = True) -> None:
        self.allow = allow

    def decide(self, request: object) -> SimpleNamespace:
        return SimpleNamespace(
            autonomy_decision_id="autonomy-1",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "autonomy_denied",
        )


class FakeRisk:
    """Risk fake."""

    def __init__(self, decision: str = "allow") -> None:
        self.decision = decision

    def assess(self, request: object) -> SimpleNamespace:
        return SimpleNamespace(
            risk_assessment_id="risk-1",
            decision=self.decision,
        )


class FakeApproval:
    """Approval fake."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def create_request(self, request: object) -> SimpleNamespace:
        self.requests.append(request)
        return SimpleNamespace(approval_request_id="approval-1")


class FailingActionRunner(EventReactionActionRunner):
    """Action runner that fails controlled actions."""

    def run(self, *, action, event, subscription):  # type: ignore[no-untyped-def]
        return action.model_copy(
            update={
                "status": "failed",
                "error": {"reason": "target_failed"},
                "completed_at": datetime.now(UTC),
            }
        )


def test_router_registers_subscription_and_dispatches_dry_run() -> None:
    """Router can register a subscription and dispatch in dry-run mode."""
    router, events, _reactions = make_router()
    events.save(event())
    subscription = router.create_subscription(subscription_request())

    dispatch = router.dispatch(
        EventDispatchRequest(
            event_id="event-1",
            owner_scope=["workspace:main"],
            mode="dry_run",
        )
    )

    assert subscription.subscription_id.startswith("event-subscription-")
    assert dispatch.status == "dry_run"
    assert dispatch.action_count == 1
    assert dispatch.actions[0].status == "dry_run"
    assert dispatch.matched_subscription_ids == [subscription.subscription_id]


def test_router_policy_deny_blocks_dispatch() -> None:
    """Policy denial blocks dispatch before matching or action side effects."""
    router, events, _reactions = make_router(policy=FakePolicy(deny_action="event.dispatch"))
    events.save(event())

    dispatch = router.dispatch(
        EventDispatchRequest(
            event_id="event-1",
            owner_scope=["workspace:main"],
            mode="dry_run",
        )
    )

    assert dispatch.status == "blocked_by_policy"
    assert dispatch.action_count == 0


def test_router_autonomy_deny_blocks_dispatch() -> None:
    """Autonomy denial blocks the whole dispatch."""
    router, events, _reactions = make_router(autonomy=FakeAutonomy(allow=False))
    events.save(event())

    dispatch = router.dispatch(
        EventDispatchRequest(
            event_id="event-1",
            owner_scope=["workspace:main"],
            mode="dry_run",
        )
    )

    assert dispatch.status == "blocked_by_autonomy"


def test_router_risk_approval_waits_for_approval() -> None:
    """Risk approval requirements create a waiting action."""
    approval = FakeApproval()
    router, events, _reactions = make_router(
        risk=FakeRisk(decision="require_approval"),
        approval=approval,
    )
    events.save(event())
    router.create_subscription(subscription_request(reaction_mode="controlled"))

    dispatch = router.dispatch(
        EventDispatchRequest(
            event_id="event-1",
            owner_scope=["workspace:main"],
            mode="controlled",
        )
    )

    assert dispatch.status == "blocked_by_policy"
    assert dispatch.actions[0].status == "waiting_for_approval"
    assert dispatch.actions[0].approval_request_id == "approval-1"
    assert len(approval.requests) == 1


def test_router_failed_action_creates_dead_letter() -> None:
    """Controlled action failure creates an open dead-letter record."""
    router, events, reactions = make_router(action_runner=FailingActionRunner())
    events.save(event())
    router.create_subscription(subscription_request(reaction_mode="controlled"))

    dispatch = router.dispatch(
        EventDispatchRequest(
            event_id="event-1",
            owner_scope=["workspace:main"],
            mode="controlled",
            approval_present=True,
        )
    )
    dead_letters = reactions.list_dead_letters(scope=["workspace:main"], status="open")

    assert dispatch.status == "failed"
    assert dispatch.actions[0].status == "failed"
    assert dead_letters[0].reason == "target_failed"


def make_router(
    *,
    policy: FakePolicy | None = None,
    autonomy: FakeAutonomy | None = None,
    risk: FakeRisk | None = None,
    approval: FakeApproval | None = None,
    action_runner: EventReactionActionRunner | None = None,
) -> tuple[EventReactionRouter, EventRepository, EventReactionRepository]:
    """Create a router with in-memory persistence."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    policy_adapter = policy or FakePolicy()
    event_repository = EventRepository(engine=engine)
    reaction_repository = EventReactionRepository(engine=engine)
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_EVENT_REACTION_MAX_ACTIONS_DEFAULT=25,
    )
    dead_letters = EventDeadLetterService(
        repository=reaction_repository,
        event_repository=event_repository,
        policy_adapter=policy_adapter,
        settings=settings,
    )
    router = EventReactionRouter(
        repository=reaction_repository,
        event_repository=event_repository,
        matcher=EventTriggerMatcher(),
        action_runner=action_runner or EventReactionActionRunner(),
        dead_letter_service=dead_letters,
        policy_adapter=policy_adapter,
        settings=settings,
        autonomy_governor=autonomy or FakeAutonomy(),
        risk_engine=risk or FakeRisk(),
        approval_service=approval,
    )
    dead_letters.set_router(router)
    return router, event_repository, reaction_repository


def subscription_request(reaction_mode: str = "dry_run") -> EventSubscriptionCreateRequest:
    """Create a generic subscription request."""
    return EventSubscriptionCreateRequest(
        name="Generic subscription",
        description="React to generic events.",
        owner_scope=["workspace:main"],
        event_type_patterns=["generic.*"],
        target_type="noop",
        reaction_mode=reaction_mode,  # type: ignore[arg-type]
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
