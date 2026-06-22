"""Notification router tests."""

from __future__ import annotations

import pytest

from aion_brain.contracts.notifications import (
    NotificationPublishRequest,
    NotificationSubscription,
    NotificationTopic,
)
from tests.notification_fakes import DenyPolicy, service_graph


def test_notification_publish_delivers_locally_and_creates_alert() -> None:
    repo, topics, subscriptions, router, *_rest, telemetry = service_graph()
    topics.create_topic(
        NotificationTopic(
            topic_id="topic-run-timeout",
            topic_key="run.timeout",
            name="Run timeout",
            description="Run timed out.",
            status="active",
            category="run_supervision",
            severity_default="critical",
            owner_scope=["workspace:main"],
        )
    )
    subscriptions.create_subscription(
        NotificationSubscription(
            subscription_id="sub-operator",
            topic_key="run.timeout",
            subscriber_type="operator",
            subscriber_ref="operator",
            channel="operator_inbox",
            status="active",
            severity_threshold="high",
            owner_scope=["workspace:main"],
        )
    )

    stored = router.publish(
        NotificationPublishRequest(
            topic_key="run.timeout",
            title="Run timed out",
            message="A supervised run timed out.",
            source_type="run_supervision",
            source_id="run-1",
            owner_scope=["workspace:main"],
            metadata={"raw_prompt": "private", "safe": "value"},
        )
    )

    alerts = repo.list_alerts(scope=["workspace:main"])
    event_types = {getattr(event, "event_type", None) for event in telemetry.events}

    assert stored.status == "delivered"
    assert stored.delivery_channels == ["operator_inbox"]
    assert stored.delivered_to == ["operator"]
    assert "raw_prompt" not in stored.metadata
    assert "[redacted]" in stored.metadata.values()
    assert alerts[0].alert_type == "timeout"
    assert "notification_published" in event_types
    assert "notification_delivered_local" in event_types
    assert "alert_created" in event_types


def test_notification_publish_policy_deny_blocks_persistence() -> None:
    repo, _topics, _subscriptions, router, *_rest = service_graph(
        policy=DenyPolicy("notification.publish")
    )

    with pytest.raises(PermissionError):
        router.publish(
            NotificationPublishRequest(
                topic_key="generic.info",
                title="Denied",
                message="Denied notification.",
                source_type="generic",
                owner_scope=["workspace:main"],
            )
        )

    assert repo.list_notifications(scope=["workspace:main"]) == []
