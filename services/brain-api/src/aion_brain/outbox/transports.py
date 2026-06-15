"""Outbox delivery transport boundaries."""

from dataclasses import dataclass
from typing import Protocol

from aion_brain.contracts.outbox import OutboxMessage


@dataclass(frozen=True)
class OutboxDeliveryResult:
    """Transport delivery result."""

    sent: bool
    skipped: bool = False
    error: dict[str, object] | None = None
    latency_ms: int | None = None


class OutboxTransport(Protocol):
    """Transport boundary for manual outbox processing."""

    def send(self, message: OutboxMessage) -> OutboxDeliveryResult:
        """Deliver one message."""
        ...


class InternalOutboxTransport:
    """Local internal transport with no external side effects."""

    def send(self, message: OutboxMessage) -> OutboxDeliveryResult:
        """Mark internal messages as delivered locally."""
        return OutboxDeliveryResult(sent=True)


class NoopOutboxTransport:
    """No-op transport for tests and dry internal notifications."""

    def send(self, message: OutboxMessage) -> OutboxDeliveryResult:
        """Mark noop messages as delivered locally."""
        return OutboxDeliveryResult(sent=True)


class WebhookPlaceholderTransport:
    """Placeholder transport that never performs network calls in v0.1."""

    def send(self, message: OutboxMessage) -> OutboxDeliveryResult:
        """Return a disabled result instead of performing network calls."""
        return OutboxDeliveryResult(
            sent=False,
            skipped=True,
            error={"reason": "webhook_placeholder_disabled"},
        )


class UnconfiguredNatsTransport:
    """NATS outbox transport placeholder used until explicit wiring is enabled."""

    def send(self, message: OutboxMessage) -> OutboxDeliveryResult:
        """Return an unconfigured result without opening a network connection."""
        return OutboxDeliveryResult(
            sent=False,
            skipped=True,
            error={"reason": "nats_transport_unconfigured"},
        )
