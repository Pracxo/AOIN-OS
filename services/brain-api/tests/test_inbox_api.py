"""Inbox API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.inbox import get_inbox_service
from aion_brain.contracts.inbox import InboxMessage, InboxReceiveResult
from aion_brain.main import app


class FakeInboxService:
    """Inbox fake."""

    def __init__(self) -> None:
        self.message = message()

    def receive(self, request):  # type: ignore[no-untyped-def]
        return InboxReceiveResult(
            accepted=True,
            duplicate=False,
            inbox=self.message,
            reason=None,
        )

    def list_messages(self, status=None, source=None, limit=50):  # type: ignore[no-untyped-def]
        return [self.message]

    def mark_processed(self, inbox_id, processed_by, result):  # type: ignore[no-untyped-def]
        return self.message.model_copy(update={"status": "processed", "processed_by": processed_by})

    def mark_failed(self, inbox_id, processed_by, error):  # type: ignore[no-untyped-def]
        return self.message.model_copy(update={"status": "failed", "processed_by": processed_by})


def test_inbox_api_works() -> None:
    """Inbox API can receive and list messages."""
    fake = FakeInboxService()
    app.dependency_overrides[get_inbox_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(
            "/brain/inbox/receive",
            json={
                "source": "nats",
                "external_message_id": "message-1",
                "message_type": "event",
                "payload": {},
            },
        )
        assert response.status_code == 200
        assert response.json()["accepted"] is True

        list_response = client.get("/brain/inbox")
        assert list_response.status_code == 200
        assert list_response.json()[0]["inbox_id"] == "inbox-1"
    finally:
        app.dependency_overrides.clear()


def message() -> InboxMessage:
    return InboxMessage(
        inbox_id="inbox-1",
        source="nats",
        external_message_id="message-1",
        message_type="event",
        payload_hash="hash",
        status="received",
        received_at=datetime.now(UTC),
    )
