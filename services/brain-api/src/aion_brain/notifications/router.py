"""Local notification router."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.alerts import AlertCreateRequest, AlertType
from aion_brain.contracts.notifications import (
    NotificationPublishRequest,
    NotificationQuery,
    NotificationRecord,
    NotificationSubscription,
    NotificationTopic,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.notifications.redaction import redact_payload, redact_text

_SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


class NotificationRouter:
    """Publish local notifications and route them to local subscribers."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        alert_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._alert_service = alert_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> NotificationRouter:
        return NotificationRouter(
            self._repository,
            self._policy_adapter,
            alert_service=self._alert_service,
            telemetry_service=self._telemetry_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def publish(self, request: NotificationPublishRequest) -> NotificationRecord:
        if self._settings is not None and not bool(
            getattr(self._settings, "notifications_enabled", True)
        ):
            raise RuntimeError("notifications_disabled")
        authorize(
            self._policy_adapter,
            action_type="notification.publish",
            resource_type="notification",
            resource_id=request.notification_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
        )
        topic = _get_topic(self._repository, request.topic_key)
        severity = request.severity or (topic.severity_default if topic else "info")
        subscriptions = _matching_subscriptions(
            _list_subscriptions(self._repository, request.owner_scope, request.topic_key),
            severity,
        )
        channels = request.delivery_channels or [item.channel for item in subscriptions]
        if not channels:
            channels = ["operator_inbox"]
        delivered_to = [item.subscriber_ref for item in subscriptions]
        if not delivered_to and "operator_inbox" in channels:
            delivered_to = ["operator"]
        notification = NotificationRecord(
            notification_id=request.notification_id or f"notification-{uuid4().hex}",
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            topic_key=request.topic_key,
            status="delivered",
            severity=severity,
            title=redact_text(request.title),
            message=redact_text(request.message),
            source_type=request.source_type,
            source_id=request.source_id,
            target_type=request.target_type,
            target_id=request.target_id,
            owner_scope=request.owner_scope,
            refs=request.refs,
            delivery_channels=channels,
            delivered_to=delivered_to,
            metadata=redact_payload({**request.metadata, "local_delivery_only": True}),
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_notification(self._repository, notification)
        emit_telemetry(
            self._telemetry_service,
            event_type="notification_published",
            node_type="notification",
            node_id=stored.notification_id,
            intensity=_notification_intensity(stored.severity),
            trace_id=stored.trace_id,
            payload={"topic_key": stored.topic_key, "severity": stored.severity},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="notification_delivered_local",
            node_type="notification",
            node_id=stored.notification_id,
            intensity=0.4,
            trace_id=stored.trace_id,
            payload={"delivery_channels": list(stored.delivery_channels)},
        )
        if (
            severity in {"high", "critical"}
            and bool(getattr(self._settings, "alert_router_enabled", True))
            and self._alert_service is not None
        ):
            create_alert = getattr(self._alert_service, "create_alert", None)
            if callable(create_alert):
                create_alert(
                    AlertCreateRequest(
                        trace_id=stored.trace_id,
                        actor_id=stored.actor_id,
                        workspace_id=stored.workspace_id,
                        alert_type=cast(
                            AlertType,
                            _alert_type_for_source(stored.source_type, stored.topic_key),
                        ),
                        severity=stored.severity,
                        title=stored.title,
                        description=stored.message,
                        source_type=stored.source_type,
                        source_id=stored.source_id,
                        owner_scope=stored.owner_scope,
                        metadata={"notification_id": stored.notification_id},
                    )
                )
        return stored

    def mark_read(
        self, notification_id: str, actor_id: str | None, reason: str | None = None
    ) -> NotificationRecord:
        return self._update(notification_id, actor_id, reason or "read", "read")

    def acknowledge(
        self, notification_id: str, actor_id: str | None, reason: str
    ) -> NotificationRecord:
        return self._update(notification_id, actor_id, reason, "acknowledged")

    def resolve(
        self, notification_id: str, actor_id: str | None, reason: str
    ) -> NotificationRecord:
        return self._update(notification_id, actor_id, reason, "resolved")

    def query(self, query: NotificationQuery) -> list[NotificationRecord]:
        authorize(
            self._policy_adapter,
            action_type="notification.read",
            resource_type="notification",
            resource_id=None,
            scope=query.scope,
            risk_level="low",
        )
        list_notifications = getattr(self._repository, "list_notifications", None)
        if not callable(list_notifications):
            return []
        result = list_notifications(**query.model_dump(mode="python"))
        return [item for item in result if isinstance(item, NotificationRecord)]

    def _update(
        self, notification_id: str, actor_id: str | None, reason: str, status: str
    ) -> NotificationRecord:
        notification = _require_notification(self._repository, notification_id)
        authorize(
            self._policy_adapter,
            action_type="notification.update",
            resource_type="notification",
            resource_id=notification_id,
            scope=notification.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="low",
            context={"reason": reason, "status": status},
        )
        now = datetime.now(UTC)
        update: dict[str, object] = {
            "status": status,
            "metadata": {**notification.metadata, f"{status}_reason": reason},
        }
        if status == "read":
            update["read_at"] = now
            update["read_by"] = sorted({*notification.read_by, actor_id or "actor"})
        if status == "acknowledged":
            update["acknowledged_at"] = now
            update["acknowledged_by"] = sorted({*notification.acknowledged_by, actor_id or "actor"})
        if status == "resolved":
            update["resolved_at"] = now
        stored = _save_notification(self._repository, notification.model_copy(update=update))
        if status == "acknowledged":
            emit_telemetry(
                self._telemetry_service,
                event_type="notification_acknowledged",
                node_type="notification",
                node_id=stored.notification_id,
                intensity=0.3,
                trace_id=stored.trace_id,
                payload={"status": stored.status},
            )
        return stored


def _save_notification(repository: object, notification: NotificationRecord) -> NotificationRecord:
    save = getattr(repository, "save_notification", None)
    stored = save(notification) if callable(save) else notification
    return stored if isinstance(stored, NotificationRecord) else notification


def _require_notification(repository: object, notification_id: str) -> NotificationRecord:
    get = getattr(repository, "get_notification", None)
    notification = get(notification_id) if callable(get) else None
    if not isinstance(notification, NotificationRecord):
        raise ValueError("notification_not_found")
    return notification


def _get_topic(repository: object, topic_key: str) -> NotificationTopic | None:
    get = getattr(repository, "get_topic", None)
    topic = get(topic_key) if callable(get) else None
    return topic if isinstance(topic, NotificationTopic) else None


def _list_subscriptions(
    repository: object, scope: list[str], topic_key: str
) -> list[NotificationSubscription]:
    list_subscriptions = getattr(repository, "list_subscriptions", None)
    if not callable(list_subscriptions):
        return []
    result = list_subscriptions(scope=scope, topic_key=topic_key, status="active", limit=100)
    return [item for item in result if isinstance(item, NotificationSubscription)]


def _matching_subscriptions(
    subscriptions: list[NotificationSubscription], severity: str
) -> list[NotificationSubscription]:
    severity_rank = _SEVERITY_RANK.get(severity, 0)
    return [
        item
        for item in subscriptions
        if _SEVERITY_RANK.get(item.severity_threshold, 0) <= severity_rank
    ]


def _notification_intensity(severity: str) -> float:
    if severity == "critical":
        return 1.0
    if severity == "high":
        return 0.8
    return 0.5


def _alert_type_for_source(source_type: str, topic_key: str) -> str:
    if topic_key == "run.stalled":
        return "stalled_run"
    if topic_key == "run.timeout":
        return "timeout"
    if source_type == "action_proposal":
        return "blocked_action"
    if source_type == "model_output":
        return "blocked_model_output"
    if source_type == "prompt":
        return "prompt_injection"
    if source_type == "grounding":
        return "failed_grounding"
    if source_type in {"security_scan", "hardening_gate"}:
        return "failed_security_check"
    if source_type == "audit":
        return "failed_audit_verification"
    if source_type == "backup":
        return "failed_backup"
    if source_type == "release":
        return "failed_release"
    if source_type == "freeze":
        return "failed_freeze"
    return "generic"


__all__ = ["NotificationRouter"]
