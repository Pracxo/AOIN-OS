"""Notification digest service."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.alerts import AlertRecord
from aion_brain.contracts.notifications import (
    NotificationDigest,
    NotificationRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class NotificationDigestService:
    """Create deterministic local notification digests."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        notification_router: object | None = None,
        alert_service: object | None = None,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._notification_router = notification_router
        self._alert_service = alert_service
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> NotificationDigestService:
        return NotificationDigestService(
            self._repository,
            self._policy_adapter,
            notification_router=self._notification_router,
            alert_service=self._alert_service,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_digest(
        self,
        scope: list[str],
        digest_type: str,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        created_by: str | None = None,
    ) -> NotificationDigest:
        authorize(
            self._policy_adapter,
            action_type="notification.digest.create",
            resource_type="notification_digest",
            resource_id=None,
            scope=scope,
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=workspace_id or self._actor_context.workspace_id,
            risk_level="low",
        )
        notifications = _query_notifications(self._repository, scope)
        alerts = _query_alerts(self._repository, scope)
        severity_counts = Counter(item.severity for item in notifications)
        topic_counts = Counter(item.topic_key for item in notifications)
        open_alert_count = sum(1 for alert in alerts if alert.status == "open")
        recommendations = ["acknowledge_notifications"]
        if any(item.severity == "critical" for item in notifications) or any(
            item.severity == "critical" for item in alerts
        ):
            recommendations.insert(0, "review_critical_alerts")
        if open_alert_count:
            recommendations.append("run_operator_readiness")
        digest = NotificationDigest(
            digest_id=f"notification-digest-{uuid4().hex}",
            actor_id=actor_id or self._actor_context.actor_id,
            workspace_id=workspace_id or self._actor_context.workspace_id,
            digest_type=digest_type,  # type: ignore[arg-type]
            status="created",
            owner_scope=scope,
            title=f"{digest_type.title()} notification digest",
            summary=f"{len(notifications)} notifications and {open_alert_count} open alerts.",
            notification_ids=[item.notification_id for item in notifications],
            alert_ids=[item.alert_id for item in alerts],
            counts={
                "by_severity": dict(severity_counts),
                "by_topic": dict(topic_counts),
                "open_alerts": open_alert_count,
            },
            recommendations=recommendations,
            metadata={"local_only": True},
            created_by=created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_digest(self._repository, digest)
        emit_telemetry(
            self._telemetry_service,
            event_type="notification_digest_created",
            node_type="digest",
            node_id=stored.digest_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"digest_type": stored.digest_type},
        )
        return stored

    def list_digests(
        self, scope: list[str], digest_type: str | None = None, limit: int = 50
    ) -> list[NotificationDigest]:
        authorize(
            self._policy_adapter,
            action_type="notification.digest.read",
            resource_type="notification_digest",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_digests = getattr(self._repository, "list_digests", None)
        if not callable(list_digests):
            return []
        result = list_digests(scope=scope, digest_type=digest_type, limit=limit)
        return [item for item in result if isinstance(item, NotificationDigest)]


def _query_notifications(repository: object, scope: list[str]) -> list[NotificationRecord]:
    list_notifications = getattr(repository, "list_notifications", None)
    if not callable(list_notifications):
        return []
    result = list_notifications(scope=scope, limit=500)
    return [item for item in result if isinstance(item, NotificationRecord)]


def _query_alerts(repository: object, scope: list[str]) -> list[AlertRecord]:
    list_alerts = getattr(repository, "list_alerts", None)
    if not callable(list_alerts):
        return []
    result = list_alerts(scope=scope, limit=500)
    return [item for item in result if isinstance(item, AlertRecord)]


def _save_digest(repository: object, digest: NotificationDigest) -> NotificationDigest:
    save = getattr(repository, "save_digest", None)
    stored = save(digest) if callable(save) else digest
    return stored if isinstance(stored, NotificationDigest) else digest


__all__ = ["NotificationDigestService"]
