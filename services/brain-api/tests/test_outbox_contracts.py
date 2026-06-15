"""Outbox contract tests."""

import pytest

from aion_brain.contracts.outbox import OutboxMessage


def test_outbox_message_validates_destination() -> None:
    """Outbox destination is constrained."""
    with pytest.raises(ValueError):
        OutboxMessage(
            outbox_id="outbox-1",
            message_type="event.publish",
            destination="external",  # type: ignore[arg-type]
            payload={},
            headers={},
            status="pending",
            attempt_count=0,
            max_attempts=3,
        )


def test_outbox_message_rejects_secret_like_headers() -> None:
    """Outbox headers must not contain secrets."""
    with pytest.raises(ValueError):
        OutboxMessage(
            outbox_id="outbox-1",
            message_type="event.publish",
            destination="noop",
            payload={},
            headers={"authorization": "secret"},
            status="pending",
            attempt_count=0,
            max_attempts=3,
        )
