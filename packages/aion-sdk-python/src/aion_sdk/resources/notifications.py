"""Notification center SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class NotificationsResource:
    """Client helpers for local notification, alert, escalation, and digest APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_topic(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/notifications/topics", json=payload)

    def list_topics(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        return self._client.get("/brain/notifications/topics", params=params)

    def seed_default_topics(self, scope: Sequence[str], *, dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/notifications/topics/seed-defaults",
            json={"scope": list(scope), "dry_run": dry_run},
        )

    def create_subscription(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/notifications/subscriptions", json=payload)

    def list_subscriptions(
        self,
        scope: Sequence[str],
        *,
        topic_key: str | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if topic_key is not None:
            params["topic_key"] = topic_key
        if actor_id is not None:
            params["actor_id"] = actor_id
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/notifications/subscriptions", params=params)

    def publish(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/notifications/publish", json=payload)

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/notifications/query", json=payload)

    def mark_read(
        self, notification_id: str, reason: str, actor_id: str | None = None
    ) -> JSONValue:
        return self._notification_update(notification_id, "read", reason, actor_id)

    def acknowledge(
        self, notification_id: str, reason: str, actor_id: str | None = None
    ) -> JSONValue:
        return self._notification_update(notification_id, "acknowledge", reason, actor_id)

    def resolve(self, notification_id: str, reason: str, actor_id: str | None = None) -> JSONValue:
        return self._notification_update(notification_id, "resolve", reason, actor_id)

    def create_alert(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/alerts", json=payload)

    def query_alerts(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/alerts/query", json=payload)

    def acknowledge_alert(
        self, alert_id: str, reason: str, actor_id: str | None = None
    ) -> JSONValue:
        return self._alert_update(alert_id, "acknowledge", reason, actor_id)

    def resolve_alert(self, alert_id: str, reason: str, actor_id: str | None = None) -> JSONValue:
        return self._alert_update(alert_id, "resolve", reason, actor_id)

    def create_escalation_policy(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/escalations/policies", json=payload)

    def list_escalation_policies(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        topic_key: str | None = None,
        alert_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if topic_key is not None:
            params["topic_key"] = topic_key
        if alert_type is not None:
            params["alert_type"] = alert_type
        return self._client.get("/brain/escalations/policies", params=params)

    def evaluate_escalations(
        self,
        scope: Sequence[str],
        *,
        alert_id: str | None = None,
        notification_id: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"scope": list(scope)}
        if alert_id is not None:
            payload["alert_id"] = alert_id
        if notification_id is not None:
            payload["notification_id"] = notification_id
        return self._client.post("/brain/escalations/evaluate", json=payload)

    def list_escalations(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        return self._client.get("/brain/escalations", params=params)

    def create_digest(
        self,
        scope: Sequence[str],
        *,
        digest_type: str = "operator",
        actor_id: str | None = None,
        workspace_id: str | None = None,
        created_by: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"scope": list(scope), "digest_type": digest_type}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        if workspace_id is not None:
            payload["workspace_id"] = workspace_id
        if created_by is not None:
            payload["created_by"] = created_by
        return self._client.post("/brain/notifications/digests", json=payload)

    def list_digests(
        self,
        scope: Sequence[str],
        *,
        digest_type: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if digest_type is not None:
            params["digest_type"] = digest_type
        return self._client.get("/brain/notifications/digests", params=params)

    def _notification_update(
        self, notification_id: str, action: str, reason: str, actor_id: str | None
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(
            f"/brain/notifications/{notification_id}/{action}",
            json=payload,
        )

    def _alert_update(
        self, alert_id: str, action: str, reason: str, actor_id: str | None
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(f"/brain/alerts/{alert_id}/{action}", json=payload)


__all__ = ["NotificationsResource"]
