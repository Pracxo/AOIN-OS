"""Shared fakes for notification center tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.notifications.alerts import AlertService
from aion_brain.notifications.digests import NotificationDigestService
from aion_brain.notifications.escalations import EscalationService
from aion_brain.notifications.query import NotificationQueryService
from aion_brain.notifications.repository import NotificationRepository
from aion_brain.notifications.router import NotificationRouter
from aion_brain.notifications.subscriptions import NotificationSubscriptionService
from aion_brain.notifications.topics import NotificationTopicService


class AllowPolicy:
    """Always-allow policy fake."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy(AllowPolicy):
    """Deny one policy action."""

    def __init__(self, action_type: str) -> None:
        super().__init__()
        self._action_type = action_type

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self._action_type
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=not allow,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["denied"],
            audit_level="standard" if allow else "high",
        )


class FakeTelemetry:
    """Collect emitted visual telemetry events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeSettings:
    """Notification settings fake."""

    notifications_enabled = True
    alert_router_enabled = True
    notification_subscriptions_enabled = True
    escalation_queue_enabled = True
    notification_digests_enabled = True
    external_notifications_enabled = False
    notification_local_delivery_only = True
    notification_auto_create_operator_items = True


def repository() -> NotificationRepository:
    """Return an in-memory notification repository."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return NotificationRepository(engine=engine)


def service_graph(
    *,
    policy: AllowPolicy | None = None,
    telemetry: FakeTelemetry | None = None,
) -> tuple[
    NotificationRepository,
    NotificationTopicService,
    NotificationSubscriptionService,
    NotificationRouter,
    AlertService,
    EscalationService,
    NotificationDigestService,
    NotificationQueryService,
    AllowPolicy,
    FakeTelemetry,
]:
    """Return local notification services over one repository."""

    repo = repository()
    selected_policy = policy or AllowPolicy()
    selected_telemetry = telemetry or FakeTelemetry()
    alert_service = AlertService(
        repo,
        selected_policy,
        telemetry_service=selected_telemetry,
    )
    router = NotificationRouter(
        repo,
        selected_policy,
        alert_service=alert_service,
        telemetry_service=selected_telemetry,
        settings=FakeSettings(),
    )
    topics = NotificationTopicService(
        repo,
        selected_policy,
        telemetry_service=selected_telemetry,
    )
    subscriptions = NotificationSubscriptionService(
        repo,
        selected_policy,
        telemetry_service=selected_telemetry,
    )
    escalations = EscalationService(
        repo,
        selected_policy,
        telemetry_service=selected_telemetry,
        settings=FakeSettings(),
    )
    digests = NotificationDigestService(
        repo,
        selected_policy,
        notification_router=router,
        alert_service=alert_service,
        telemetry_service=selected_telemetry,
    )
    query = NotificationQueryService(router)
    return (
        repo,
        topics,
        subscriptions,
        router,
        alert_service,
        escalations,
        digests,
        query,
        selected_policy,
        selected_telemetry,
    )
