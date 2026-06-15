"""Semantic memory contract tests."""

from datetime import UTC, datetime

from aion_brain.contracts.memory import (
    MemoryRecord,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
)


def make_memory() -> MemoryRecord:
    """Create a memory record."""
    return MemoryRecord(
        memory_id="memory-1",
        memory_type="semantic",
        owner_scope=["workspace:main"],
        source_event_id=None,
        content_ref="content://memory-1",
        summary="alpha beta",
        confidence=0.9,
        sensitivity="low",
        created_at=datetime.now(UTC),
        expires_at=None,
        metadata={},
    )


def test_semantic_query_defaults() -> None:
    """Semantic queries have safe defaults."""
    query = SemanticMemoryQuery(query="alpha", scope=["workspace:main"])

    assert query.limit == 10
    assert query.memory_types == []
    assert query.min_score is None


def test_semantic_result_serializes() -> None:
    """Semantic results preserve AION contract fields."""
    result = SemanticMemoryResult(
        memory=make_memory(),
        score=0.8,
        retrieval_source="semantic",
        adapter_name="in-memory",
        matched_terms=["alpha"],
        metadata={"test": True},
    )

    dumped = result.model_dump(mode="json")

    assert dumped["memory"]["memory_id"] == "memory-1"
    assert dumped["score"] == 0.8
    assert dumped["adapter_name"] == "in-memory"


def test_semantic_index_response_serializes() -> None:
    """Semantic index responses are public AION JSON."""
    response = SemanticIndexResponse(
        indexed=True,
        memory_id="memory-1",
        adapter_name="pgvector",
        embedding_id="pgvector-memory-1",
        reason=None,
    )

    assert response.model_dump(mode="json")["indexed"] is True
