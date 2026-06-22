"""Retrieval scoring tests."""

from datetime import UTC, datetime

from aion_brain.contracts.retrieval import RetrievedContextItem
from aion_brain.retrieval.scoring import rank_items, score_candidate


def test_scoring_clamps_scores_to_bounds() -> None:
    """Scoring clamps normalized features to 0..1."""
    score = score_candidate(
        source="semantic_memory",
        base_relevance=3.0,
        confidence=2.0,
        lexical_overlap=2.0,
        recency_score=2.0,
    )

    assert 0.0 <= score <= 1.0


def test_scoring_ranks_higher_confidence_and_overlap_higher() -> None:
    """Ranking rewards confidence and exact query term overlap."""
    lower = make_item("low", "delta", confidence=0.2)
    higher = make_item("high", "alpha beta", confidence=0.9)

    ranked = rank_items("alpha", [lower, higher])

    assert [item.source_id for item in ranked] == ["high", "low"]


def make_item(source_id: str, content: str, *, confidence: float) -> RetrievedContextItem:
    """Create a retrieval item."""
    return RetrievedContextItem(
        item_id=f"item-{source_id}",
        source="lexical_memory",
        source_id=source_id,
        title=None,
        content=content,
        score=0.5,
        confidence=confidence,
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
