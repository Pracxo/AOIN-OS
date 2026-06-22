"""Escalation queue and digest tests."""

from __future__ import annotations

from aion_brain.contracts.alerts import AlertCreateRequest
from aion_brain.contracts.notifications import EscalationPolicy, NotificationPublishRequest
from tests.notification_fakes import service_graph


def test_escalation_evaluate_creates_local_record_and_honors_repeat_limit() -> None:
    (
        _repo,
        _topics,
        _subscriptions,
        _router,
        alerts,
        escalations,
        _digests,
        _query,
        _policy,
        telemetry,
    ) = service_graph()
    alert = alerts.create_alert(
        AlertCreateRequest(
            alert_type="generic",
            severity="critical",
            title="Critical alert",
            description="Critical local alert.",
            source_type="generic",
            owner_scope=["workspace:main"],
        )
    )
    escalations.create_policy(
        EscalationPolicy(
            escalation_policy_id="policy-1",
            name="Critical operator policy",
            description="Local operator escalation.",
            status="active",
            alert_type="generic",
            severity_threshold="high",
            delay_seconds=0,
            repeat_limit=1,
            escalation_channel="operator_inbox",
            escalation_target="operator",
            owner_scope=["workspace:main"],
        )
    )

    first = escalations.evaluate(alert_id=alert.alert_id, scope=["workspace:main"])
    second = escalations.evaluate(alert_id=alert.alert_id, scope=["workspace:main"])

    assert len(first) == 1
    assert first[0].local_only is True
    assert first[0].result["external_delivery"] is False
    assert second == []
    assert any(
        getattr(event, "event_type", None) == "escalation_record_created"
        for event in telemetry.events
    )


def test_notification_digest_summarizes_notifications_and_alerts() -> None:
    (
        _repo,
        _topics,
        _subscriptions,
        router,
        _alerts,
        _escalations,
        digests,
        _query,
        _policy,
        telemetry,
    ) = service_graph()
    router.publish(
        NotificationPublishRequest(
            topic_key="generic.info",
            severity="critical",
            title="Critical local item",
            message="Review the local item.",
            source_type="generic",
            owner_scope=["workspace:main"],
        )
    )

    digest = digests.create_digest(["workspace:main"], "operator")
    listed = digests.list_digests(["workspace:main"])

    assert digest.notification_ids
    assert digest.alert_ids
    assert digest.counts["open_alerts"] == 1
    assert digest.recommendations[0] == "review_critical_alerts"
    assert listed[0].digest_id == digest.digest_id
    assert any(
        getattr(event, "event_type", None) == "notification_digest_created"
        for event in telemetry.events
    )
