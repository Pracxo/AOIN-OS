"""Context Fusion Engine tests."""

from datetime import UTC, datetime

from aion_brain.contracts.retrieval import (
    ContextFusionRequest,
    RetrievalResult,
    RetrievedContextItem,
)
from aion_brain.retrieval.fusion import ContextFusionEngine


def test_context_fusion_deduplicates_duplicate_content() -> None:
    """Fusion removes duplicate content before producing a bundle."""
    result = make_result(
        [
            make_item("memory-1", "alpha beta", 0.9),
            make_item("memory-2", "alpha beta", 0.8),
        ]
    )

    bundle = ContextFusionEngine().fuse(ContextFusionRequest(retrieval_result=result, goal="alpha"))

    assert [item.source_id for item in bundle.items] == ["memory-1"]


def test_context_fusion_respects_max_items() -> None:
    """Fusion limits item count."""
    result = make_result([make_item("memory-1", "alpha", 0.9), make_item("memory-2", "beta", 0.8)])

    bundle = ContextFusionEngine().fuse(
        ContextFusionRequest(retrieval_result=result, goal="alpha", max_items=1)
    )

    assert len(bundle.items) == 1


def test_context_fusion_respects_max_chars() -> None:
    """Fusion truncates oversized first content and respects max_chars."""
    result = make_result([make_item("memory-1", "a" * 200, 0.9)])

    bundle = ContextFusionEngine().fuse(
        ContextFusionRequest(retrieval_result=result, goal="alpha", max_chars=100)
    )

    assert len(bundle.items[0].content) == 100


def make_result(items: list[RetrievedContextItem]) -> RetrievalResult:
    """Create a retrieval result."""
    return RetrievalResult(
        retrieval_id="retrieval-1",
        query="alpha",
        items=items,
        source_counts={"lexical_memory": len(items)},
        constraints=[],
        created_at=datetime.now(UTC),
    )


def make_item(source_id: str, content: str, score: float) -> RetrievedContextItem:
    """Create a retrieval item."""
    return RetrievedContextItem(
        item_id=f"item-{source_id}",
        source="lexical_memory",
        source_id=source_id,
        title=source_id,
        content=content,
        score=score,
        confidence=0.9,
        sensitivity="low",
        owner_scope=["workspace:main"],
        memory_type="semantic",
        capability_id=None,
        graph_node_ids=[],
        graph_edge_ids=[],
        trace_refs=[],
        evidence_ref=None,
        metadata={"created_at": datetime.now(UTC).isoformat()},
    )
