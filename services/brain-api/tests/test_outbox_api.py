"""Outbox API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.outbox import get_outbox_service
from aion_brain.contracts.outbox import OutboxMessage, OutboxProcessResult
from aion_brain.main import app


class FakeOutboxService:
    """Outbox fake."""

    def __init__(self) -> None:
        self.message = message()

    def enqueue(self, request):  # type: ignore[no-untyped-def]
        self.message = self.message.model_copy(update={"destination": request.destination})
        return self.message

    def get(self, outbox_id):  # type: ignore[no-untyped-def]
        return self.message if outbox_id == self.message.outbox_id else None

    def list_messages(self, status=None, destination=None, limit=50):  # type: ignore[no-untyped-def]
        return [self.message]

    def process_once(self, request):  # type: ignore[no-untyped-def]
        return OutboxProcessResult(
            processed=1,
            sent=0,
            failed=0,
            skipped=1,
            dry_run=request.dry_run,
            messages=[self.message],
        )

    def cancel(self, outbox_id, reason=None):  # type: ignore[no-untyped-def]
        return self.message.model_copy(update={"status": "cancelled"})


def test_outbox_api_works() -> None:
    """Outbox API can enqueue, list, and process dry-run."""
    fake = FakeOutboxService()
    app.dependency_overrides[get_outbox_service] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(
            "/brain/outbox",
            json={"message_type": "event.publish", "destination": "noop", "payload": {}},
        )
        assert response.status_code == 200
        assert response.json()["outbox_id"] == "outbox-1"

        process_response = client.post("/brain/outbox/process-once", json={"dry_run": True})
        assert process_response.status_code == 200
        assert process_response.json()["skipped"] == 1
    finally:
        app.dependency_overrides.clear()


def message() -> OutboxMessage:
    return OutboxMessage(
        outbox_id="outbox-1",
        message_type="event.publish",
        destination="noop",
        payload={},
        headers={},
        status="pending",
        attempt_count=0,
        max_attempts=3,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
