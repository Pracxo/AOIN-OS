"""Notification API route tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_notification_api_routes_work() -> None:
    client = TestClient(create_app(kernel_container()))

    topic = client.post(
        "/brain/notifications/topics",
        json={
            "topic_id": "topic-generic-info",
            "topic_key": "generic.info",
            "name": "Generic info",
            "description": "Generic local notification.",
            "status": "active",
            "category": "generic",
            "severity_default": "info",
            "owner_scope": ["workspace:main"],
        },
    )
    assert topic.status_code == 200
    assert (
        client.get(
            "/brain/notifications/topics",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    seed = client.post(
        "/brain/notifications/topics/seed-defaults",
        json={"scope": ["workspace:main"], "dry_run": True},
    )
    assert seed.status_code == 200
    assert seed.json()["dry_run"] is True

    subscription = client.post(
        "/brain/notifications/subscriptions",
        json={
            "subscription_id": "sub-operator",
            "topic_key": "generic.info",
            "subscriber_type": "operator",
            "subscriber_ref": "operator",
            "channel": "operator_inbox",
            "status": "active",
            "severity_threshold": "info",
            "owner_scope": ["workspace:main"],
        },
    )
    assert subscription.status_code == 200
    assert (
        client.get(
            "/brain/notifications/subscriptions",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )

    published = client.post(
        "/brain/notifications/publish",
        json={
            "topic_key": "generic.info",
            "severity": "high",
            "title": "Local notification",
            "message": "Local notification only.",
            "source_type": "generic",
            "owner_scope": ["workspace:main"],
        },
    )
    assert published.status_code == 200
    notification_id = published.json()["notification_id"]
    assert (
        client.post("/brain/notifications/query", json={"scope": ["workspace:main"]}).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/notifications/{notification_id}/read",
            json={"reason": "read"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/notifications/{notification_id}/acknowledge",
            json={"reason": "acknowledged"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/notifications/{notification_id}/resolve",
            json={"reason": "resolved"},
        ).status_code
        == 200
    )

    alert = client.post(
        "/brain/alerts",
        json={
            "alert_type": "generic",
            "severity": "critical",
            "title": "Critical alert",
            "description": "Critical local alert.",
            "source_type": "generic",
            "owner_scope": ["workspace:main"],
        },
    )
    assert alert.status_code == 200
    alert_id = alert.json()["alert_id"]
    assert client.post("/brain/alerts/query", json={"scope": ["workspace:main"]}).status_code == 200
    assert (
        client.post(
            f"/brain/alerts/{alert_id}/acknowledge",
            json={"reason": "acknowledged"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/brain/alerts/{alert_id}/resolve",
            json={"reason": "resolved"},
        ).status_code
        == 200
    )

    policy = client.post(
        "/brain/escalations/policies",
        json={
            "escalation_policy_id": "policy-generic",
            "name": "Generic policy",
            "description": "Local escalation policy.",
            "status": "active",
            "alert_type": "generic",
            "severity_threshold": "high",
            "delay_seconds": 0,
            "repeat_limit": 2,
            "escalation_channel": "operator_inbox",
            "escalation_target": "operator",
            "owner_scope": ["workspace:main"],
        },
    )
    assert policy.status_code == 200
    assert (
        client.get(
            "/brain/escalations/policies",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
    evaluated = client.post(
        "/brain/escalations/evaluate",
        json={"alert_id": alert_id, "scope": ["workspace:main"]},
    )
    assert evaluated.status_code == 200
    assert client.get("/brain/escalations", params={"scope": "workspace:main"}).status_code == 200

    digest = client.post(
        "/brain/notifications/digests",
        json={"scope": ["workspace:main"], "digest_type": "operator"},
    )
    assert digest.status_code == 200
    assert (
        client.get(
            "/brain/notifications/digests",
            params={"scope": "workspace:main"},
        ).status_code
        == 200
    )
