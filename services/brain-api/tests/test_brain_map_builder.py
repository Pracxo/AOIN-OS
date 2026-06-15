"""Brain Map builder tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.config import Settings
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import BrainMapRequest, VisualTelemetryQuery
from aion_brain.visual.map_builder import BrainMapBuilder


class FakeTelemetryRepository:
    """Telemetry repository fake."""

    def __init__(self, events: list[VisualTelemetryEvent]) -> None:
        self.events = events

    def query_telemetry(self, query: VisualTelemetryQuery) -> list[VisualTelemetryEvent]:
        return self.events[: query.limit]


def test_brain_map_builder_deduplicates_nodes_and_builds_edges_clusters() -> None:
    """Projection aggregates nodes and builds timeline, explicit, and sequence edges."""
    now = datetime.now(UTC)
    events = [
        event("telemetry-1", "event-1", "event", "brain_loop_started", now, edge_to=None),
        event(
            "telemetry-2",
            "intent-1",
            "intent",
            "intent_classified",
            now + timedelta(seconds=1),
            edge_from="event-1",
            edge_to="intent-1",
        ),
        event(
            "telemetry-3",
            "intent-1",
            "intent",
            "intent_classified",
            now + timedelta(seconds=2),
        ),
    ]

    brain_map = BrainMapBuilder(FakeTelemetryRepository(events), Settings(_env_file=None)).build(
        BrainMapRequest(scope=["workspace:main"], decay=False)
    )

    assert len(brain_map.nodes) == 2
    assert {edge.edge_type for edge in brain_map.edges} >= {
        "triggered",
        "linked_to",
        "classified_as",
    }
    assert {cluster.cluster_type for cluster in brain_map.clusters} >= {"reasoning"}


def test_brain_map_builder_handles_missing_references_without_crash() -> None:
    """Missing explicit references do not break map projection."""
    item = event(
        "telemetry-1",
        "event-1",
        "event",
        "brain_loop_started",
        datetime.now(UTC),
        edge_from="missing-a",
        edge_to="missing-b",
    )

    brain_map = BrainMapBuilder(FakeTelemetryRepository([item]), Settings(_env_file=None)).build(
        BrainMapRequest(scope=["workspace:main"])
    )

    assert brain_map.nodes[0].node_id == "event-1"
    assert brain_map.edges[0].edge_type == "linked_to"


def event(
    telemetry_id: str,
    node_id: str,
    node_type: str,
    event_type: str,
    created_at: datetime,
    *,
    edge_from: str | None = None,
    edge_to: str | None = None,
) -> VisualTelemetryEvent:
    """Create valid visual telemetry."""
    return VisualTelemetryEvent.model_validate(
        {
            "telemetry_id": telemetry_id,
            "trace_id": "trace-1",
            "event_type": event_type,
            "node_type": node_type,
            "node_id": node_id,
            "edge_from": edge_from,
            "edge_to": edge_to,
            "intensity": 0.8,
            "payload": {"owner_scope": ["workspace:main"]},
            "created_at": created_at,
        }
    )
