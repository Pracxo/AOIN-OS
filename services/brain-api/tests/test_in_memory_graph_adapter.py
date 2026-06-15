"""In-memory graph adapter tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.contracts.graph import GraphEdge, GraphNode, GraphQuery
from aion_brain.memory.in_memory_graph_adapter import InMemoryGraphAdapter


def make_node(
    node_id: str,
    *,
    scope: list[str] | None = None,
    label: str | None = None,
    valid_to: datetime | None = None,
) -> GraphNode:
    """Create a generic graph node."""
    return GraphNode(
        node_id=node_id,
        node_type="concept",
        label=label or node_id,
        owner_scope=scope or ["workspace:main"],
        properties={"note": label or node_id},
        source_event_id=None,
        confidence=0.8,
        sensitivity="low",
        valid_from=None,
        valid_to=valid_to,
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


def test_in_memory_graph_adapter_upserts_and_retrieves_node() -> None:
    """Nodes are retrievable after upsert."""
    adapter = InMemoryGraphAdapter()

    response = adapter.upsert_node(make_node("node-1"))

    assert response.upserted is True
    assert adapter.get_node("node-1", ["workspace:main"]) is not None


def test_in_memory_graph_adapter_upserts_and_retrieves_edge() -> None:
    """Edges are retrievable after upsert."""
    adapter = InMemoryGraphAdapter()
    adapter.upsert_node(make_node("node-1"))
    adapter.upsert_node(make_node("node-2"))

    response = adapter.upsert_edge(make_edge("edge-1", "node-1", "node-2"))

    assert response.object_id == "edge-1"
    assert adapter.get_edge("edge-1", ["workspace:main"]) is not None


def test_in_memory_graph_adapter_respects_scope_filtering() -> None:
    """Scope filtering hides records outside the requested scope."""
    adapter = InMemoryGraphAdapter()
    adapter.upsert_node(make_node("node-main", scope=["workspace:main"]))
    adapter.upsert_node(make_node("node-other", scope=["workspace:other"]))

    result = adapter.query_graph(GraphQuery(scope=["workspace:main"]))

    assert [node.node_id for node in result.nodes] == ["node-main"]


def test_in_memory_graph_adapter_excludes_deleted_nodes() -> None:
    """Soft-deleted nodes are excluded from graph retrieval."""
    adapter = InMemoryGraphAdapter()
    adapter.upsert_node(make_node("node-1"))

    deleted = adapter.soft_delete_node("node-1", ["workspace:main"])
    result = adapter.query_graph(GraphQuery(scope=["workspace:main"]))

    assert deleted is True
    assert result.nodes == []


def test_in_memory_graph_adapter_supports_neighbors_traversal() -> None:
    """Neighbor traversal follows generic edges up to depth."""
    adapter = InMemoryGraphAdapter()
    adapter.upsert_node(make_node("node-1"))
    adapter.upsert_node(make_node("node-2"))
    adapter.upsert_node(make_node("node-3"))
    adapter.upsert_edge(make_edge("edge-1", "node-1", "node-2"))
    adapter.upsert_edge(make_edge("edge-2", "node-2", "node-3"))

    result = adapter.neighbors("node-1", ["workspace:main"], max_depth=2)

    assert {node.node_id for node in result.nodes} == {"node-1", "node-2", "node-3"}
    assert {edge.edge_id for edge in result.edges} == {"edge-1", "edge-2"}


def test_in_memory_graph_adapter_respects_include_expired_false() -> None:
    """Expired graph objects are excluded unless explicitly requested."""
    adapter = InMemoryGraphAdapter()
    adapter.upsert_node(
        make_node("node-expired", valid_to=datetime.now(UTC) - timedelta(seconds=1))
    )

    current = adapter.query_graph(GraphQuery(scope=["workspace:main"]))
    historical = adapter.query_graph(GraphQuery(scope=["workspace:main"], include_expired=True))

    assert current.nodes == []
    assert [node.node_id for node in historical.nodes] == ["node-expired"]
