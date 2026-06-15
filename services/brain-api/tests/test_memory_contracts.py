"""Memory contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.memory import MemoryRecord, MemoryRetrievalRequest


def test_memory_record_accepts_generic_memory_types() -> None:
    """MemoryRecord supports the generic Brain memory classes."""
    now = datetime.now(UTC)

    for memory_type in [
        "working",
        "episodic",
        "semantic",
        "procedural",
        "preference",
        "graph",
        "audit",
    ]:
        record = MemoryRecord(
            memory_id=f"memory-{memory_type}",
            memory_type=memory_type,
            owner_scope=["workspace:main"],
            source_event_id=None,
            content_ref=None,
            summary=f"{memory_type} summary",
            confidence=0.9,
            sensitivity="low",
            created_at=now,
            expires_at=None,
            metadata={},
        )

        assert record.memory_type == memory_type


def test_memory_record_rejects_unknown_memory_type() -> None:
    """MemoryRecord rejects domain-specific memory classes."""
    with pytest.raises(ValidationError):
        MemoryRecord(
            memory_id="memory-invalid",
            memory_type="custom",
            owner_scope=["workspace:main"],
            source_event_id=None,
            content_ref=None,
            summary="Invalid memory",
            confidence=0.9,
            sensitivity="low",
            created_at=datetime.now(UTC),
            expires_at=None,
            metadata={},
        )


def test_memory_retrieval_request_defaults() -> None:
    """MemoryRetrievalRequest has stable retrieval defaults."""
    request = MemoryRetrievalRequest(query="alpha", scope=["workspace:main"])

    assert request.limit == 10
    assert request.memory_types == []
