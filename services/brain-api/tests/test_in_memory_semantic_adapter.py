"""In-memory semantic adapter tests."""

from datetime import UTC, datetime, timedelta
from typing import cast

from aion_brain.contracts.memory import MemoryRecord, MemoryType, SemanticMemoryQuery
from aion_brain.memory.in_memory_semantic_adapter import InMemorySemanticMemoryAdapter


def make_record(
    memory_id: str,
    summary: str,
    *,
    scope: list[str] | None = None,
    memory_type: str = "semantic",
) -> MemoryRecord:
    """Create a memory record."""
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=cast(MemoryType, memory_type),
        owner_scope=scope or ["workspace:main"],
        source_event_id=None,
        content_ref=None,
        summary=summary,
        confidence=0.9,
        sensitivity="low",
        created_at=datetime.now(UTC) + timedelta(seconds=len(memory_id)),
        expires_at=None,
        metadata={},
    )


def test_in_memory_semantic_adapter_retrieves_related_records() -> None:
    """Semantic adapter ranks related token-overlap records first."""
    adapter = InMemorySemanticMemoryAdapter()
    adapter.remember(make_record("memory-1", "alpha beta"))
    adapter.remember(make_record("memory-2", "gamma delta"))

    results = adapter.retrieve(SemanticMemoryQuery(query="alpha", scope=["workspace:main"]))

    assert results[0].memory.memory_id == "memory-1"
    assert results[0].retrieval_source == "semantic"


def test_in_memory_semantic_adapter_respects_scope_filtering() -> None:
    """Semantic recall filters by requested scope."""
    adapter = InMemorySemanticMemoryAdapter()
    adapter.remember(make_record("memory-main", "alpha", scope=["workspace:main"]))
    adapter.remember(make_record("memory-other", "alpha", scope=["workspace:other"]))

    results = adapter.retrieve(SemanticMemoryQuery(query="alpha", scope=["workspace:main"]))

    assert [result.memory.memory_id for result in results] == ["memory-main"]


def test_in_memory_semantic_adapter_respects_memory_type_filtering() -> None:
    """Semantic recall filters by memory type."""
    adapter = InMemorySemanticMemoryAdapter()
    adapter.remember(make_record("memory-semantic", "alpha", memory_type="semantic"))
    adapter.remember(make_record("memory-working", "alpha", memory_type="working"))

    results = adapter.retrieve(
        SemanticMemoryQuery(
            query="alpha",
            scope=["workspace:main"],
            memory_types=["working"],
        )
    )

    assert [result.memory.memory_id for result in results] == ["memory-working"]


def test_in_memory_semantic_adapter_respects_limit() -> None:
    """Semantic recall respects request limit."""
    adapter = InMemorySemanticMemoryAdapter()
    adapter.remember(make_record("memory-1", "alpha"))
    adapter.remember(make_record("memory-2", "alpha"))

    results = adapter.retrieve(
        SemanticMemoryQuery(query="alpha", scope=["workspace:main"], limit=1)
    )

    assert len(results) == 1
