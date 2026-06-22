from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aion_sdk.models import AIONEventModel, HealthModel, MemoryRetrieveRequestModel
from aion_sdk.pagination import decode_cursor, encode_cursor


def test_cursor_round_trip() -> None:
    cursor = encode_cursor({"created_at": "2026-06-12T00:00:00Z", "id": "item-1"})

    assert decode_cursor(cursor) == {"created_at": "2026-06-12T00:00:00Z", "id": "item-1"}


def test_invalid_cursor_raises() -> None:
    with pytest.raises((ValueError, UnicodeDecodeError)):
        decode_cursor("not-json")


def test_models_are_forward_compatible() -> None:
    health = HealthModel(status="ok", service="aion-brain-api", version="0.1.0", extra="kept")
    event = AIONEventModel(
        event_id="event-1",
        source="test",
        event_type="test.received",
        payload_type="test.payload",
        payload={"message": "hello"},
        timestamp=datetime.now(UTC),
        security_scope=["workspace:main"],
    )
    request = MemoryRetrieveRequestModel(query="remember", scope=["workspace:main"])

    assert health.model_dump()["extra"] == "kept"
    assert event.event_id == "event-1"
    assert request.limit == 10
