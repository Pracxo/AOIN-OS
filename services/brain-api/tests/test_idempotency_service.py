"""Idempotency service tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.idempotency import IdempotencyCheckRequest
from aion_brain.idempotency.repository import IdempotencyRepository
from aion_brain.idempotency.service import IdempotencyService


def test_idempotency_service_starts_new_record() -> None:
    """A new key can be started."""
    service = make_service()
    record = service.start(request())

    assert record.status == "started"
    assert record.request_hash


def test_idempotency_service_returns_duplicate_for_same_key_and_hash() -> None:
    """A completed matching record is returned as duplicate."""
    service = make_service()
    service.start(request())
    service.complete("idem-1", {"status": "accepted"})

    result = service.check(request())

    assert result.duplicate is True
    assert result.conflict is False
    assert result.record is not None
    assert result.record.response == {"status": "accepted"}


def test_idempotency_service_returns_conflict_for_same_key_different_hash() -> None:
    """Same key with different request payload conflicts."""
    service = make_service()
    service.start(request())

    result = service.check(request(payload={"value": 2}))

    assert result.duplicate is True
    assert result.conflict is True
    assert result.reason == "idempotency_conflict"


def test_idempotency_service_completes_record_with_response_hash() -> None:
    """Completed records store a response hash."""
    service = make_service()
    service.start(request())

    record = service.complete("idem-1", {"ok": True})

    assert record.status == "completed"
    assert record.response_hash


def make_service() -> IdempotencyService:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return IdempotencyService(IdempotencyRepository(engine=engine))


def request(payload: dict[str, object] | None = None) -> IdempotencyCheckRequest:
    return IdempotencyCheckRequest(
        idempotency_key="idem-1",
        route="/brain/events",
        request_payload=payload or {"value": 1},
    )
