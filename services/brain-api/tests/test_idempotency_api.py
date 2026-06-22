"""Idempotency API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.idempotency import get_idempotency_service
from aion_brain.contracts.idempotency import IdempotencyRecord
from aion_brain.main import app


class FakeIdempotencyService:
    """Idempotency fake."""

    def get(self, idempotency_key: str) -> IdempotencyRecord | None:
        return IdempotencyRecord(
            idempotency_key=idempotency_key,
            route="/brain/events",
            request_hash="hash",
            status="completed",
            response={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def expire_old(self, limit: int = 100):  # type: ignore[no-untyped-def]
        return 3


def test_idempotency_api_works() -> None:
    """Idempotency API can read and expire records."""
    app.dependency_overrides[get_idempotency_service] = lambda: FakeIdempotencyService()
    try:
        client = TestClient(app)
        response = client.get("/brain/idempotency/idem-1")
        assert response.status_code == 200
        assert response.json()["idempotency_key"] == "idem-1"

        expire_response = client.post("/brain/idempotency/expire-old", json={"limit": 10})
        assert expire_response.status_code == 200
        assert expire_response.json()["expired"] == 3
    finally:
        app.dependency_overrides.clear()
