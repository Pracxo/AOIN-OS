"""Memory service tests."""

from datetime import UTC, datetime, timedelta

import pytest

from aion_brain.contracts.memory import MemoryRecord, MemoryRetrievalRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.memory.in_memory_adapter import InMemorySemanticMemoryAdapter
from aion_brain.memory.service import MemoryPolicyDenied, PostgresMemoryService


class FakePolicyAdapter:
    """Fake policy adapter for memory service tests."""

    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard",
        )


def make_service(
    *,
    allow: bool = True,
) -> tuple[PostgresMemoryService, InMemorySemanticMemoryAdapter]:
    """Create a service with in-memory storage and fake policy."""
    adapter = InMemorySemanticMemoryAdapter()
    service = PostgresMemoryService(adapter, FakePolicyAdapter(allow=allow))
    return service, adapter


def make_record(
    memory_id: str,
    summary: str,
    *,
    scope: list[str] | None = None,
    created_at: datetime | None = None,
    confidence: float = 0.8,
) -> MemoryRecord:
    """Create a memory record."""
    return MemoryRecord(
        memory_id=memory_id,
        memory_type="semantic",
        owner_scope=scope or ["workspace:main"],
        source_event_id=None,
        content_ref=None,
        summary=summary,
        confidence=confidence,
        sensitivity="low",
        created_at=created_at or datetime.now(UTC),
        expires_at=None,
        metadata={"test": True},
    )


def test_memory_create() -> None:
    """The service creates memory when policy allows."""
    service, adapter = make_service()
    record = make_record("memory-1", "alpha beta")

    saved = service.create(record)

    assert saved.memory_id == "memory-1"
    assert adapter.get("memory-1") == record


def test_memory_retrieve_by_lexical_match() -> None:
    """Retrieval ranks exact token overlap first."""
    service, _adapter = make_service()
    now = datetime.now(UTC)
    service.create(make_record("memory-1", "alpha beta", created_at=now))
    service.create(
        make_record("memory-2", "alpha beta gamma", created_at=now - timedelta(seconds=5))
    )
    service.create(make_record("memory-3", "delta epsilon", created_at=now + timedelta(seconds=10)))

    results = service.retrieve(
        MemoryRetrievalRequest(query="alpha gamma", scope=["workspace:main"], limit=10)
    )

    assert [record.memory_id for record in results][:2] == ["memory-2", "memory-1"]


def test_memory_retrieve_filters_scope() -> None:
    """Retrieval only returns records within requested scope."""
    service, _adapter = make_service()
    service.create(make_record("memory-main", "alpha", scope=["workspace:main"]))
    service.create(make_record("memory-other", "alpha", scope=["workspace:other"]))

    results = service.retrieve(
        MemoryRetrievalRequest(query="alpha", scope=["workspace:main"], limit=10)
    )

    assert [record.memory_id for record in results] == ["memory-main"]


def test_soft_delete_excludes_deleted_records() -> None:
    """Soft-deleted memory is excluded from get and retrieval."""
    service, _adapter = make_service()
    service.create(make_record("memory-1", "alpha"))

    deleted = service.delete("memory-1")
    results = service.retrieve(
        MemoryRetrievalRequest(query="alpha", scope=["workspace:main"], limit=10)
    )

    assert deleted is True
    assert service.get("memory-1") is None
    assert results == []


def test_policy_deny_blocks_memory_write() -> None:
    """Policy denial blocks memory writes."""
    service, _adapter = make_service(allow=False)

    with pytest.raises(MemoryPolicyDenied):
        service.create(make_record("memory-1", "alpha"))
