from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_notifications_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.notifications.create_topic({"topic_id": "topic-1"})
    client.notifications.list_topics(["workspace:main"])
    client.notifications.seed_default_topics(["workspace:main"])
    client.notifications.create_subscription({"subscription_id": "sub-1"})
    client.notifications.list_subscriptions(["workspace:main"])
    client.notifications.publish({"topic_key": "generic.info"})
    client.notifications.query({"scope": ["workspace:main"]})
    client.notifications.mark_read("notification-1", "read")
    client.notifications.acknowledge("notification-1", "ack")
    client.notifications.resolve("notification-1", "done")
    client.notifications.create_alert({"alert_type": "generic"})
    client.notifications.query_alerts({"scope": ["workspace:main"]})
    client.notifications.acknowledge_alert("alert-1", "ack")
    client.notifications.resolve_alert("alert-1", "done")
    client.notifications.create_escalation_policy({"escalation_policy_id": "policy-1"})
    client.notifications.list_escalation_policies(["workspace:main"])
    client.notifications.evaluate_escalations(["workspace:main"], alert_id="alert-1")
    client.notifications.list_escalations(["workspace:main"])
    client.notifications.create_digest(["workspace:main"])
    client.notifications.list_digests(["workspace:main"])

    assert seen == [
        ("POST", "/brain/notifications/topics"),
        ("GET", "/brain/notifications/topics"),
        ("POST", "/brain/notifications/topics/seed-defaults"),
        ("POST", "/brain/notifications/subscriptions"),
        ("GET", "/brain/notifications/subscriptions"),
        ("POST", "/brain/notifications/publish"),
        ("POST", "/brain/notifications/query"),
        ("POST", "/brain/notifications/notification-1/read"),
        ("POST", "/brain/notifications/notification-1/acknowledge"),
        ("POST", "/brain/notifications/notification-1/resolve"),
        ("POST", "/brain/alerts"),
        ("POST", "/brain/alerts/query"),
        ("POST", "/brain/alerts/alert-1/acknowledge"),
        ("POST", "/brain/alerts/alert-1/resolve"),
        ("POST", "/brain/escalations/policies"),
        ("GET", "/brain/escalations/policies"),
        ("POST", "/brain/escalations/evaluate"),
        ("GET", "/brain/escalations"),
        ("POST", "/brain/notifications/digests"),
        ("GET", "/brain/notifications/digests"),
    ]


def test_notifications_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.notifications as resource

    assert "aion_brain" not in resource.__dict__
