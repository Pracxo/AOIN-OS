"""Event publisher boundaries."""

import asyncio
from typing import Protocol

from nats.aio.client import Client as NATSClient

from aion_brain.contracts.events import AIONEvent


class EventPublisher(Protocol):
    """Interface for publishing accepted AION events."""

    def publish(self, event: AIONEvent) -> bool:
        """Publish an event and return whether publishing succeeded."""
        ...


class NoopEventPublisher:
    """Test publisher that avoids external NATS calls."""

    def __init__(self, *, published: bool = True) -> None:
        self.published = published
        self.events: list[AIONEvent] = []

    def publish(self, event: AIONEvent) -> bool:
        """Record the event and return a configured publication result."""
        self.events.append(event)
        return self.published


class NatsEventPublisher:
    """NATS implementation of the event publisher boundary."""

    def __init__(self, nats_url: str, *, timeout_seconds: float = 1.0) -> None:
        self._nats_url = nats_url
        self._timeout_seconds = timeout_seconds

    def publish(self, event: AIONEvent) -> bool:
        """Publish an event to the AION NATS subject."""
        try:
            return asyncio.run(self._publish_async(event))
        except Exception:
            return False

    async def _publish_async(self, event: AIONEvent) -> bool:
        client = NATSClient()
        try:
            await client.connect(
                servers=[self._nats_url],
                connect_timeout=max(1, int(self._timeout_seconds)),
                max_reconnect_attempts=0,
            )
            await client.publish(subject_for_event(event), event.model_dump_json().encode("utf-8"))
            await client.flush(timeout=max(1, int(self._timeout_seconds)))
            return True
        except Exception:
            return False
        finally:
            if client.is_connected:
                await client.close()


def subject_for_event(event: AIONEvent) -> str:
    """Return the NATS subject for an AION event."""
    return f"aion.events.{event.event_type}"
