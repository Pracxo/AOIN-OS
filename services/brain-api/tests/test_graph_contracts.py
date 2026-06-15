"""Graph memory contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.graph import GraphNode, GraphQuery


def test_graph_node_validates_confidence_bounds() -> None:
    """GraphNode confidence must stay in the normalized range."""
    with pytest.raises(ValidationError):
        GraphNode(
            node_id="node-1",
            node_type="concept",
            label="Concept",
            owner_scope=["workspace:main"],
            properties={},
            source_event_id=None,
            confidence=1.2,
            sensitivity="low",
            valid_from=None,
            valid_to=None,
            observed_at=datetime.now(UTC),
        )


def test_graph_query_validates_depth_and_limit() -> None:
    """GraphQuery bounds keep traversal predictable."""
    with pytest.raises(ValidationError):
        GraphQuery(scope=["workspace:main"], max_depth=6)
    with pytest.raises(ValidationError):
        GraphQuery(scope=["workspace:main"], limit=0)
