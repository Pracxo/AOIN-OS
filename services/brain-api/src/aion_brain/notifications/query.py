"""Notification query facade."""

from __future__ import annotations

from aion_brain.contracts.notifications import NotificationQuery, NotificationRecord
from aion_brain.contracts.scopes import ActorContext


class NotificationQueryService:
    """Read notifications through the router boundary."""

    def __init__(
        self, notification_router: object, *, actor_context: ActorContext | None = None
    ) -> None:
        self._notification_router = notification_router
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> NotificationQueryService:
        router_scope = getattr(self._notification_router, "with_actor_context", None)
        router = (
            router_scope(actor_context) if callable(router_scope) else self._notification_router
        )
        return NotificationQueryService(router, actor_context=actor_context)

    def query(self, query: NotificationQuery) -> list[NotificationRecord]:
        query_call = getattr(self._notification_router, "query", None)
        if not callable(query_call):
            return []
        result = query_call(query)
        return [item for item in result if isinstance(item, NotificationRecord)]

    def list_notifications(
        self, scope: list[str], status: str | None = None, limit: int = 100
    ) -> list[NotificationRecord]:
        return self.query(NotificationQuery(scope=scope, status=status, limit=limit))


__all__ = ["NotificationQueryService"]
