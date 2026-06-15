"""Inbox contract tests."""

import pytest

from aion_brain.contracts.inbox import InboxReceiveRequest


def test_inbox_receive_request_validates_external_message_id() -> None:
    """Inbox receive requires an external message ID."""
    with pytest.raises(ValueError):
        InboxReceiveRequest(
            source="nats",
            external_message_id="",
            message_type="event",
            payload={},
        )
