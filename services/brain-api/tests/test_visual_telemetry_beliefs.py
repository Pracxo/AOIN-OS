from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainVisualNode
from tests.belief_helpers import belief_bundle, create_claim


def test_visual_telemetry_accepts_belief_event_and_node_types() -> None:
    event = VisualTelemetryEvent(
        telemetry_id="telemetry-belief-1",
        trace_id="trace-1",
        event_type="belief_claim_created",
        node_id="claim-1",
        node_type="claim",
        edge_from=None,
        edge_to=None,
        intensity=0.7,
        payload={"status": "supported"},
        created_at=datetime.now(UTC),
    )
    node = BrainVisualNode(
        node_id="belief-1",
        node_type="belief",
        label="Belief",
        status="active",
        intensity=0.7,
        owner_scope=["workspace:main"],
        trace_refs=["trace-1"],
        source_refs=[],
        metadata={},
        first_seen_at=None,
        last_seen_at=None,
    )

    assert event.event_type == "belief_claim_created"
    assert node.node_type == "belief"


def test_belief_service_emits_visual_telemetry_event() -> None:
    bundle = belief_bundle()

    claim = create_claim(bundle, "Belief telemetry can be emitted.")

    assert claim.claim_id
    assert any(
        getattr(event, "event_type", "") == "belief_claim_created"
        for event in bundle.telemetry.events
    )
