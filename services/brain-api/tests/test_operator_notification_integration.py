"""Operator integration tests for notifications and alerts."""

from __future__ import annotations

from aion_brain.contracts.alerts import AlertCreateRequest
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.repository import OperatorRepository
from tests.kernel_fakes import AllowPolicy
from tests.notification_fakes import service_graph


def test_operator_surfaces_notifications_alerts_escalations_and_digests() -> None:
    (
        _repo,
        _topics,
        _subscriptions,
        router,
        alerts,
        escalations,
        digests,
        query,
        _policy,
        _telemetry,
    ) = service_graph()
    router.publish(
        NotificationPublishRequest(
            topic_key="generic.info",
            severity="medium",
            title="Notification",
            message="Local operator notification.",
            source_type="generic",
            owner_scope=["workspace:main"],
        )
    )
    alerts.create_alert(
        AlertCreateRequest(
            alert_type="generic",
            severity="critical",
            title="Critical alert",
            description="Critical local alert.",
            source_type="generic",
            owner_scope=["workspace:main"],
        )
    )
    digests.create_digest(["workspace:main"], "operator")

    repository = OperatorRepository(database_url="sqlite+pysqlite:///:memory:")
    action_center = ActionCenterService(
        repository,
        AllowPolicy(),
        notification_query_service=query,
        alert_service=alerts,
        escalation_service=escalations,
        notification_digest_service=digests,
    )
    queues = QueueSummaryBuilder(
        notification_query_service=query,
        alert_service=alerts,
        escalation_service=escalations,
        notification_digest_service=digests,
    )

    items = action_center.build_action_items(["workspace:main"])
    summaries = queues.build_queues(["workspace:main"])
    titles = {summary.title for summary in summaries}

    assert any(item.recommended_action == "review_alert" for item in items)
    assert "Unread Notifications" in titles
    assert "Open Alerts" in titles
    assert "Escalation Records" in titles
    assert "Notification Digests" in titles
