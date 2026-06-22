"""Graphiti graph adapter tests."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.graph import (
    GraphEdge,
    GraphitiEpisodeRequest,
    GraphitiEpisodeResponse,
    GraphitiSyncRequest,
    GraphNode,
    GraphQuery,
    GraphQueryResult,
    GraphUpsertResponse,
)
from aion_brain.memory.graphiti_adapter import GraphitiGraphMemoryAdapter
from aion_brain.memory.graphiti_repository import GraphitiRepository
from aion_brain.memory.in_memory_graph_adapter import InMemoryGraphAdapter


def test_graphiti_disabled_by_default_reports_public_status() -> None:
    """Graphiti starts disabled and returns an AION-owned status contract."""
    adapter = GraphitiGraphMemoryAdapter()

    status = adapter.status()

    assert status.adapter_name == "graphiti"
    assert status.available is False
    assert status.status == "disabled"
    assert status.reason == "graphiti_disabled"


def test_graphiti_unavailable_fails_open_to_canonical_graph() -> None:
    """Unavailable Graphiti must not break canonical graph writes or reads."""
    canonical = InMemoryGraphAdapter()
    adapter = GraphitiGraphMemoryAdapter(
        postgres_graph_adapter=canonical,
        compat=FakeGraphitiCompat(available=False),
        enabled=True,
        fail_open_to_postgres_graph=True,
    )

    response = adapter.upsert_node(make_node("node-1"))
    result = adapter.query_graph(GraphQuery(query="node", scope=["workspace:main"]))

    assert response.upserted is True
    assert canonical.get_node("node-1", ["workspace:main"]) is not None
    assert result.nodes[0].node_id == "node-1"
    assert result.adapter_name == "graphiti"
    assert result.metadata["fallback"] is True
    assert result.metadata["fallback_reason"] == "graphiti_package_unavailable"


def test_graphiti_sync_dry_run_counts_canonical_records() -> None:
    """Dry-run sync counts eligible canonical graph records without indexing."""
    canonical = InMemoryGraphAdapter()
    canonical.upsert_node(make_node("node-1"))
    canonical.upsert_node(make_node("node-2"))
    canonical.upsert_edge(make_edge("edge-1", "node-1", "node-2"))
    compat = FakeGraphitiCompat()
    adapter = GraphitiGraphMemoryAdapter(
        graphiti_repository=graphiti_repository(),
        postgres_graph_adapter=canonical,
        compat=compat,
        enabled=True,
    )

    response = adapter.sync(
        GraphitiSyncRequest(
            config_name="default",
            scope=["workspace:main"],
            dry_run=True,
            limit=10,
        )
    )

    assert response.synced is False
    assert response.indexed_nodes == 2
    assert response.indexed_edges == 1
    assert compat.upserted_nodes == []
    assert compat.upserted_edges == []


def test_graphiti_sync_records_successful_indexing() -> None:
    """A real sync uses the compat boundary and records public metadata."""
    canonical = InMemoryGraphAdapter()
    canonical.upsert_node(make_node("node-1"))
    repository = graphiti_repository()
    compat = FakeGraphitiCompat()
    adapter = GraphitiGraphMemoryAdapter(
        graphiti_repository=repository,
        postgres_graph_adapter=canonical,
        compat=compat,
        enabled=True,
    )

    response = adapter.sync(
        GraphitiSyncRequest(config_name="default", scope=["workspace:main"], limit=10)
    )
    records = repository.list_sync_records(
        response.status.graphiti_config_id,
        ["workspace:main"],
    )

    assert response.synced is True
    assert response.indexed_nodes == 1
    assert compat.upserted_nodes == ["node-1"]
    assert records[0]["source_id"] == "node-1"


def test_graphiti_episode_unavailable_returns_public_contract() -> None:
    """Episode writes fail closed to an explicit public response."""
    adapter = GraphitiGraphMemoryAdapter(
        compat=FakeGraphitiCompat(available=False),
        enabled=True,
    )

    response = adapter.add_episode(make_episode_request())

    assert response.added is False
    assert response.status == "unavailable"
    assert response.reason == "graphiti_package_unavailable"


def test_graphiti_llm_requirement_blocks_without_model_gateway() -> None:
    """Graphiti APIs that require LLM access are blocked until explicitly enabled."""
    compat = FakeGraphitiCompat(requires_llm=True)
    adapter = GraphitiGraphMemoryAdapter(
        graphiti_repository=graphiti_repository(),
        compat=compat,
        enabled=True,
        model_gateway_enabled=False,
    )

    status = adapter.status()

    assert status.available is False
    assert status.reason == "graphiti_llm_disabled"
    assert compat.created_clients == 0


def test_graphiti_query_returns_only_aion_graph_contracts() -> None:
    """Graphiti query results are coerced to AION graph contracts."""
    adapter = GraphitiGraphMemoryAdapter(
        graphiti_repository=graphiti_repository(),
        compat=FakeGraphitiCompat(),
        enabled=True,
    )

    result = adapter.query_graph(GraphQuery(query="node", scope=["workspace:main"]))

    assert isinstance(result, GraphQueryResult)
    assert result.adapter_name == "graphiti"
    assert result.nodes[0].node_id == "graphiti-node"


def graphiti_repository() -> GraphitiRepository:
    """Create an isolated SQLite Graphiti metadata repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return GraphitiRepository(engine=engine)


class FakeGraphitiCompat:
    """Fake optional Graphiti compat boundary."""

    def __init__(self, *, available: bool = True, requires_llm: bool = False) -> None:
        self.available = available
        self.llm_required = requires_llm
        self.created_clients = 0
        self.upserted_nodes: list[str] = []
        self.upserted_edges: list[str] = []

    def is_available(self) -> bool:
        return self.available

    def availability_reason(self) -> str | None:
        return None if self.available else "graphiti_package_unavailable"

    def requires_llm(self) -> bool:
        return self.llm_required

    def create_client(self, config: object) -> object:
        self.created_clients += 1
        return {"config": config}

    def upsert_node(self, client: object, node: GraphNode) -> GraphUpsertResponse:
        self.upserted_nodes.append(node.node_id)
        return GraphUpsertResponse(
            upserted=True,
            object_type="node",
            object_id=node.node_id,
            reason=None,
        )

    def upsert_edge(self, client: object, edge: GraphEdge) -> GraphUpsertResponse:
        self.upserted_edges.append(edge.edge_id)
        return GraphUpsertResponse(
            upserted=True,
            object_type="edge",
            object_id=edge.edge_id,
            reason=None,
        )

    def query(self, client: object, query: GraphQuery) -> GraphQueryResult:
        return GraphQueryResult(
            nodes=[make_node("graphiti-node")],
            edges=[],
            score=0.9,
            retrieval_source="graph",
            adapter_name="graphiti",
            metadata={"query": query.query, "client_type": type(client).__name__},
        )

    def add_episode(
        self,
        client: object,
        episode: GraphitiEpisodeRequest,
    ) -> GraphitiEpisodeResponse:
        return GraphitiEpisodeResponse(
            added=True,
            episode_id=episode.episode_id or "episode-1",
            status="active",
            reason=None,
            metadata={"client_type": type(client).__name__},
        )


def make_node(node_id: str) -> GraphNode:
    """Create a generic graph node."""
    return GraphNode(
        node_id=node_id,
        node_type="concept",
        label=node_id,
        owner_scope=["workspace:main"],
        properties={"summary": node_id},
        source_event_id=None,
        confidence=0.8,
        sensitivity="low",
        valid_from=None,
        valid_to=None,
        observed_at=datetime.now(UTC),
    )


def make_edge(edge_id: str, from_node_id: str, to_node_id: str) -> GraphEdge:
    """Create a generic graph edge."""
    return GraphEdge(
        edge_id=edge_id,
        edge_type="related_to",
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        owner_scope=["workspace:main"],
        properties={},
        source_event_id=None,
        confidence=0.7,
        sensitivity="low",
        valid_from=None,
        valid_to=None,
        observed_at=datetime.now(UTC),
    )


def make_episode_request(metadata: dict[str, Any] | None = None) -> GraphitiEpisodeRequest:
    """Create a generic Graphiti episode request."""
    return GraphitiEpisodeRequest(
        episode_id=None,
        trace_id="trace-1",
        source_type="event",
        source_id="event-1",
        content="A generic memory episode.",
        scope=["workspace:main"],
        observed_at=datetime.now(UTC),
        metadata=metadata or {},
    )
