"""Task lifecycle event publisher boundaries."""

import asyncio
import logging
from typing import Protocol

from nats.aio.client import Client as NATSClient

from aion_brain.contracts.tasks import TaskLifecycleEvent

logger = logging.getLogger(__name__)


class TaskLifecyclePublisher(Protocol):
    """Lifecycle event publisher interface."""

    def publish(self, event: TaskLifecycleEvent) -> bool:
        """Publish a lifecycle event."""
        ...


class NoopTaskLifecyclePublisher:
    """Publisher fake that avoids external NATS calls."""

    def __init__(self, *, published: bool = True) -> None:
        self.published = published
        self.events: list[TaskLifecycleEvent] = []

    def publish(self, event: TaskLifecycleEvent) -> bool:
        """Record the event and return a configured outcome."""
        self.events.append(event)
        return self.published


class NatsTaskLifecyclePublisher:
    """NATS publisher for lifecycle events."""

    def __init__(self, nats_url: str, *, timeout_seconds: float = 1.0) -> None:
        self._nats_url = nats_url
        self._timeout_seconds = timeout_seconds

    def publish(self, event: TaskLifecycleEvent) -> bool:
        """Publish lifecycle event without letting failures escape."""
        try:
            return asyncio.run(self._publish_async(event))
        except Exception as exc:
            logger.warning("lifecycle_publish_failed", extra={"error": str(exc)})
            return False

    async def _publish_async(self, event: TaskLifecycleEvent) -> bool:
        client = NATSClient()
        try:
            await client.connect(
                servers=[self._nats_url],
                connect_timeout=max(1, int(self._timeout_seconds)),
                max_reconnect_attempts=0,
            )
            await client.publish(_subject(event), event.model_dump_json().encode("utf-8"))
            await client.flush(timeout=max(1, int(self._timeout_seconds)))
            return True
        except Exception as exc:
            logger.warning("lifecycle_publish_failed", extra={"error": str(exc)})
            return False
        finally:
            if client.is_connected:
                await client.close()


def _subject(event: TaskLifecycleEvent) -> str:
    if event.event_type.startswith("goal_"):
        return "aion.lifecycle.goals"
    if event.event_type.startswith("schedule_"):
        return "aion.lifecycle.schedules"
    return "aion.lifecycle.tasks"
