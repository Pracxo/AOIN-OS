"""pgvector adapter unit tests."""

from datetime import UTC, datetime

from aion_brain.contracts.memory import MemoryRecord, SemanticMemoryResult
from aion_brain.memory.pgvector_adapter import result_from_memory_for_unit


def test_pgvector_adapter_builds_aion_contract_results() -> None:
    """pgvector adapter helper returns AION contracts, not vector-engine types."""
    record = MemoryRecord(
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

    result = result_from_memory_for_unit(record, score=0.8, query="alpha")

    assert isinstance(result, SemanticMemoryResult)
    assert result.memory.memory_id == "memory-1"
    assert result.adapter_name == "pgvector"
    assert "alpha" in result.matched_terms
