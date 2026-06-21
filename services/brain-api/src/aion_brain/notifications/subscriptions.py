"""Notification subscription service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.notifications import NotificationSubscription
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class NotificationSubscriptionService:
    """Manage local-only notification subscriptions."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> NotificationSubscriptionService:
        return NotificationSubscriptionService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def create_subscription(
        self, subscription: NotificationSubscription
    ) -> NotificationSubscription:
        authorize(
            self._policy_adapter,
            action_type="notification.subscription.create",
            resource_type="notification_subscription",
            resource_id=subscription.subscription_id,
            scope=subscription.owner_scope,
            actor_id=subscription.actor_id or self._actor_context.actor_id,
            workspace_id=subscription.workspace_id or self._actor_context.workspace_id,
            risk_level="medium",
        )
        stored = _save_subscription(self._repository, subscription)
        emit_telemetry(
            self._telemetry_service,
            event_type="notification_subscription_created",
            node_type="notification_subscription",
            node_id=stored.subscription_id,
            intensity=0.3,
            trace_id=None,
            payload={"topic_key": stored.topic_key, "channel": stored.channel},
        )
        return stored

    def list_subscriptions(
        self,
        scope: list[str],
        topic_key: str | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[NotificationSubscription]:
        authorize(
            self._policy_adapter,
            action_type="notification.subscription.read",
            resource_type="notification_subscription",
            resource_id=None,
            scope=scope,
            risk_level="low",
        )
        list_subscriptions = getattr(self._repository, "list_subscriptions", None)
        if not callable(list_subscriptions):
            return []
        result = list_subscriptions(
            scope=scope,
            topic_key=topic_key,
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
            limit=limit,
        )
        return [item for item in result if isinstance(item, NotificationSubscription)]

    def disable_subscription(
        self, subscription_id: str, actor_id: str | None, reason: str
    ) -> NotificationSubscription:
        get = getattr(self._repository, "get_subscription", None)
        subscription = get(subscription_id) if callable(get) else None
        if not isinstance(subscription, NotificationSubscription):
            raise ValueError("notification_subscription_not_found")
        authorize(
            self._policy_adapter,
            action_type="notification.subscription.update",
            resource_type="notification_subscription",
            resource_id=subscription_id,
            scope=subscription.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level="medium",
            context={"reason": reason},
        )
        return _save_subscription(
            self._repository,
            subscription.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                    "metadata": {**subscription.metadata, "disable_reason": reason},
                }
            ),
        )


def _save_subscription(
    repository: object, subscription: NotificationSubscription
) -> NotificationSubscription:
    save = getattr(repository, "save_subscription", None)
    stored = save(subscription) if callable(save) else subscription
    return stored if isinstance(stored, NotificationSubscription) else subscription


__all__ = ["NotificationSubscriptionService"]
