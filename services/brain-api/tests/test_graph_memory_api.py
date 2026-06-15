"""Graph memory API tests."""

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient

from aion_brain.api.graph_memory import (
    get_graph_memory_service,
    get_graph_telemetry_repository,
)
from aion_brain.contracts.graph import (
    GraphEdge,
    GraphNode,
    GraphQuery,
    GraphQueryResult,
    GraphUpsertResponse,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.main import app
from aion_brain.memory.graph_service import GraphMemoryService
from aion_brain.memory.graphiti_adapter import GraphitiGraphMemoryAdapter
from aion_brain.memory.in_memory_graph_adapter import InMemoryGraphAdapter


class FakePolicyAdapter:
    """Policy fake for graph API tests."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class FakeTelemetryRepository:
    """Telemetry fake for graph API tests."""

    def __init__(self) -> None:
        self.saved: list[object] = []

    def save_visual_telemetry(self, trace_id: str, events: list[object]) -> list[object]:
        self.saved.extend(events)
        return events


def test_graph_query_api_returns_graph_query_result() -> None:
    """Graph query endpoint returns a GraphQueryResult."""
    service = GraphMemoryService(
        adapter=InMemoryGraphAdapter(),
        policy_adapter=FakePolicyAdapter(),
    )
    service.upsert_node(make_node("node-1"))
    telemetry = FakeTelemetryRepository()
    app.dependency_overrides[get_graph_memory_service] = lambda: service
    app.dependency_overrides[get_graph_telemetry_repository] = lambda: telemetry
    try:
        response = TestClient(app).post(
            "/brain/memory/graph/query",
            json={"query": "node", "scope": ["workspace:main"], "limit": 10},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["retrieval_source"] == "graph"
    assert response.json()["nodes"][0]["node_id"] == "node-1"


def test_graph_upsert_api_emits_visual_telemetry() -> None:
    """Graph node upsert emits activation telemetry."""
    service = GraphMemoryService(
        adapter=InMemoryGraphAdapter(),
        policy_adapter=FakePolicyAdapter(),
    )
    telemetry = FakeTelemetryRepository()
    app.dependency_overrides[get_graph_memory_service] = lambda: service
    app.dependency_overrides[get_graph_telemetry_repository] = lambda: telemetry
    try:
        response = TestClient(app).post("/brain/memory/graph/nodes", json=node_payload("node-1"))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "upserted": True,
        "object_type": "node",
        "object_id": "node-1",
        "reason": None,
    }
    assert telemetry.saved[0].event_type == "memory_node_activated"
    assert telemetry.saved[0].node_id == "node-1"


def test_graph_memory_api_get_and_delete_support_comma_scope() -> None:
    """Graph get/delete endpoints support comma-separated scope query values."""
    service = GraphMemoryService(
        adapter=InMemoryGraphAdapter(),
        policy_adapter=FakePolicyAdapter(),
    )
    service.upsert_node(make_node("node-1"))
    telemetry = FakeTelemetryRepository()
    app.dependency_overrides[get_graph_memory_service] = lambda: service
    app.dependency_overrides[get_graph_telemetry_repository] = lambda: telemetry
    try:
        get_response = TestClient(app).get(
            "/brain/memory/graph/nodes/node-1?scope=workspace:main,workspace:other"
        )
        delete_response = TestClient(app).delete(
            "/brain/memory/graph/nodes/node-1?scope=workspace:main"
        )
    finally:
        app.dependency_overrides.clear()

    assert get_response.status_code == 200
    assert delete_response.json() == {"deleted": True, "node_id": "node-1"}


def test_graphiti_api_endpoints_return_public_contracts() -> None:
    """Graphiti status, sync, episode, and adapter endpoints stay contract-owned."""
    canonical = InMemoryGraphAdapter()
    canonical.upsert_node(make_node("node-1"))
    graphiti = GraphitiGraphMemoryAdapter(
        postgres_graph_adapter=canonical,
        enabled=False,
    )
    service = GraphMemoryService(
        adapter=canonical,
        policy_adapter=FakePolicyAdapter(),
        configured_adapter="graphiti",
        fallback_reason="graphiti_disabled",
        graphiti_adapter=graphiti,
    )
    app.dependency_overrides[get_graph_memory_service] = lambda: service
    try:
        client = TestClient(app)
        adapters_response = client.get("/brain/memory/graph/adapters")
        status_response = client.get("/brain/memory/graph/graphiti/status")
        sync_response = client.post(
            "/brain/memory/graph/graphiti/sync",
            json={
                "config_name": "default",
                "scope": ["workspace:main"],
                "source_types": [],
                "limit": 10,
                "dry_run": True,
                "force": False,
            },
        )
        episode_response = client.post(
            "/brain/memory/graph/graphiti/episodes",
            json={
                "episode_id": None,
                "trace_id": "trace-1",
                "source_type": "event",
                "source_id": "event-1",
                "content": "A generic episode.",
                "scope": ["workspace:main"],
                "observed_at": datetime.now(UTC).isoformat(),
                "metadata": {},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert adapters_response.status_code == 200
    assert any(item["adapter_name"] == "graphiti" for item in adapters_response.json())
    assert status_response.json()["reason"] == "graphiti_disabled"
    assert sync_response.json()["dry_run"] is True
    assert sync_response.json()["indexed_nodes"] == 1
    assert episode_response.json()["added"] is False
    assert episode_response.json()["metadata"]["adapter_name"] == "graphiti"


def node_payload(node_id: str) -> dict[str, Any]:
    """Create a graph node API payload."""
    return {
        "node_id": node_id,
        "node_type": "concept",
        "label": node_id,
        "owner_scope": ["workspace:main"],
        "properties": {},
        "source_event_id": None,
        "confidence": 0.8,
        "sensitivity": "low",
        "valid_from": None,
        "valid_to": None,
        "observed_at": datetime.now(UTC).isoformat(),
        "created_at": None,
        "updated_at": None,
        "deleted_at": None,
    }


def make_node(node_id: str) -> GraphNode:
    """Create a generic graph node."""
    return GraphNode(**node_payload(node_id))


def make_edge(edge_id: str) -> GraphEdge:
    """Create a generic graph edge."""
    return GraphEdge(
        edge_id=edge_id,
        edge_type="related_to",
        from_node_id="node-1",
        to_node_id="node-2",
        owner_scope=["workspace:main"],
        properties={},
        source_event_id=None,
        confidence=0.7,
        sensitivity="low",
        valid_from=None,
        valid_to=None,
        observed_at=datetime.now(UTC),
    )


class FakeGraphService:
    """Protocol shape check fake retained for type imports."""

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        return GraphQueryResult(
            nodes=[],
            edges=[],
            score=0.0,
            retrieval_source="graph",
            adapter_name="fake",
            metadata={"query": query.query},
        )

    def upsert_edge(self, edge: GraphEdge) -> GraphUpsertResponse:
        return GraphUpsertResponse(
            upserted=True,
            object_type="edge",
            object_id=edge.edge_id,
            reason=None,
        )
