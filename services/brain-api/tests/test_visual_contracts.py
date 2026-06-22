"""Visual projection contract tests."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from aion_brain.contracts.visual import (
    BrainMapRequest,
    BrainPulse,
    BrainVisualEdge,
    BrainVisualNode,
)


def test_brain_visual_node_validates_intensity_and_scope() -> None:
    """Nodes enforce intensity bounds and a non-empty owner scope."""
    with pytest.raises(ValidationError):
        make_node(intensity=1.1)
    with pytest.raises(ValidationError):
        make_node(owner_scope=[])


def test_brain_visual_edge_validates_weight_and_rejects_self_edge() -> None:
    """Edges enforce weight bounds and reject self-relations."""
    with pytest.raises(ValidationError):
        make_edge(weight=-0.1)
    with pytest.raises(ValidationError):
        make_edge(to_node_id="node-1")


def test_brain_pulse_requires_node_or_edge_target() -> None:
    """Pulses require a target."""
    with pytest.raises(ValidationError):
        BrainPulse(
            pulse_id="pulse-1",
            trace_id="trace-1",
            event_type="event_created",
            node_id=None,
            edge_id=None,
            intensity=0.5,
            duration_ms=500,
            payload={},
            created_at=datetime.now(UTC),
        )


def test_brain_map_request_validates_limit_and_time_range() -> None:
    """Map requests enforce limit bounds and chronological windows."""
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        BrainMapRequest(scope=["workspace:main"], limit=5001)
    with pytest.raises(ValidationError):
        BrainMapRequest(scope=["workspace:main"], since=now, until=now - timedelta(seconds=1))


def make_node(**updates: object) -> BrainVisualNode:
    values = {
        "node_id": "node-1",
        "node_type": "event",
        "label": "Node",
        "status": "active",
        "intensity": 0.5,
        "owner_scope": ["workspace:main"],
        "trace_refs": [],
        "source_refs": [],
        "metadata": {},
        "first_seen_at": None,
        "last_seen_at": None,
        **updates,
    }
    return BrainVisualNode.model_validate(values)


def make_edge(**updates: object) -> BrainVisualEdge:
    values = {
        "edge_id": "edge-1",
        "edge_type": "triggered",
        "from_node_id": "node-1",
        "to_node_id": "node-2",
        "weight": 0.5,
        "status": "active",
        "trace_refs": [],
        "metadata": {},
        "first_seen_at": None,
        "last_seen_at": None,
        **updates,
    }
    return BrainVisualEdge.model_validate(values)
