"""Postgres graph adapter unit tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.graph import GraphEdge, GraphNode, GraphQuery
from aion_brain.memory.postgres_graph_adapter import PostgresGraphAdapter


def test_postgres_graph_adapter_uses_aion_contracts_with_sqlite_unit_engine() -> None:
    """The adapter persists and returns AION graph contracts only."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    adapter = PostgresGraphAdapter(engine=engine)
    adapter.upsert_node(make_node("node-1", "Seed node"))
    adapter.upsert_node(make_node("node-2", "Related node"))
    adapter.upsert_edge(make_edge("edge-1", "node-1", "node-2"))

    result = adapter.query_graph(GraphQuery(query="seed", scope=["workspace:main"]))

    assert result.adapter_name == "postgres"
    assert isinstance(result.nodes[0], GraphNode)
    assert adapter.get_edge("edge-1", ["workspace:main"]) is not None


def make_node(node_id: str, label: str) -> GraphNode:
    """Create a generic graph node."""
    return GraphNode(
        node_id=node_id,
        node_type="concept",
        label=label,
        owner_scope=["workspace:main"],
        properties={},
        source_event_id=None,
        confidence=0.9,
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
        confidence=0.8,
        sensitivity="low",
        valid_from=None,
        valid_to=None,
        observed_at=datetime.now(UTC),
    )
