"""Retrieval contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.retrieval import RetrievalRequest, RetrievedContextItem


def test_retrieval_request_validates_scope() -> None:
    """RetrievalRequest requires at least one scope."""
    with pytest.raises(ValidationError):
        RetrievalRequest(
            retrieval_id="retrieval-1",
            trace_id=None,
            intent_id=None,
            query="alpha",
            scope=[],
            requested_sources=["lexical_memory"],
        )


def test_retrieval_request_rejects_unknown_requested_sources() -> None:
    """RetrievalRequest rejects source values outside AION vocabulary."""
    with pytest.raises(ValidationError):
        RetrievalRequest(
            retrieval_id="retrieval-1",
            trace_id=None,
            intent_id=None,
            query="alpha",
            scope=["workspace:main"],
            requested_sources=["unknown_source"],
        )


def test_retrieved_context_item_validates_score_and_confidence() -> None:
    """RetrievedContextItem keeps score and confidence normalized."""
    with pytest.raises(ValidationError):
        make_item(score=1.2)
    with pytest.raises(ValidationError):
        make_item(confidence=-0.1)


def make_item(score: float = 0.5, confidence: float = 0.5) -> RetrievedContextItem:
    """Create a retrieval item."""
    return RetrievedContextItem(
        item_id="item-1",
        source="lexical_memory",
        source_id="memory-1",
        title=None,
        content="alpha",
        score=score,
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
