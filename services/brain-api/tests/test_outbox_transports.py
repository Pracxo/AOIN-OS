"""Outbox transport tests."""

from aion_brain.contracts.outbox import OutboxMessage
from aion_brain.outbox.transports import WebhookPlaceholderTransport


def test_webhook_placeholder_never_calls_network() -> None:
    """The webhook placeholder returns disabled without network access."""
    result = WebhookPlaceholderTransport().send(
        OutboxMessage(
            outbox_id="outbox-1",
            message_type="event.publish",
            destination="webhook_placeholder",
            payload={},
            headers={},
            status="pending",
            attempt_count=0,
            max_attempts=3,
        )
    )

    assert result.sent is False
    assert result.skipped is True
    assert result.error == {"reason": "webhook_placeholder_disabled"}
