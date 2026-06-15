"""Postgres temporal graph memory adapter."""

from sqlalchemy.engine import Engine

from aion_brain.contracts.graph import (
    GraphEdge,
    GraphitiConfigStatus,
    GraphitiEpisodeRequest,
    GraphitiEpisodeResponse,
    GraphitiSyncRequest,
    GraphitiSyncResponse,
    GraphNode,
    GraphQuery,
    GraphQueryResult,
    GraphUpsertResponse,
)
from aion_brain.memory.graph_repository import GraphRepository


class PostgresGraphAdapter:
    """Postgres-backed GraphMemoryAdapter baseline."""

    adapter_name = "postgres_graph"

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        self._repository = GraphRepository(
            database_url=database_url,
            engine=engine,
            auto_create=auto_create,
        )

    def upsert_node(self, node: GraphNode) -> GraphUpsertResponse:
        """Store or update a graph node."""
        return self._repository.upsert_node(node)

    def upsert_edge(self, edge: GraphEdge) -> GraphUpsertResponse:
        """Store or update a graph edge."""
        return self._repository.upsert_edge(edge)

    def get_node(self, node_id: str, scope: list[str]) -> GraphNode | None:
        """Return a node visible to scope."""
        return self._repository.get_node(node_id, scope)

    def get_edge(self, edge_id: str, scope: list[str]) -> GraphEdge | None:
        """Return an edge visible to scope."""
        return self._repository.get_edge(edge_id, scope)

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        """Query graph memory."""
        return self._repository.query_graph(query)

    def neighbors(
        self,
        node_id: str,
        scope: list[str],
        max_depth: int = 1,
        limit: int = 25,
    ) -> GraphQueryResult:
        """Return neighboring graph memory."""
        return self._repository.neighbors(node_id, scope, max_depth=max_depth, limit=limit)

    def list_nodes(self, scope: list[str], *, limit: int = 10000) -> list[GraphNode]:
        """List active graph nodes visible to scope."""
        return self._repository.list_nodes(scope, limit=limit)

    def list_edges(self, scope: list[str], *, limit: int = 10000) -> list[GraphEdge]:
        """List active graph edges visible to scope."""
        return self._repository.list_edges(scope, limit=limit)

    def soft_delete_node(self, node_id: str, scope: list[str]) -> bool:
        """Soft-delete a graph node."""
        return self._repository.soft_delete_node(node_id, scope)

    def soft_delete_edge(self, edge_id: str, scope: list[str]) -> bool:
        """Soft-delete a graph edge."""
        return self._repository.soft_delete_edge(edge_id, scope)

    def status(self, config_name: str = "default") -> GraphitiConfigStatus | None:
        """Postgres graph memory has no Graphiti status."""
        return None

    def sync(self, request: GraphitiSyncRequest) -> GraphitiSyncResponse:
        """Postgres graph memory does not sync Graphiti indexes."""
        raise RuntimeError("graphiti_not_selected")

    def add_episode(self, request: GraphitiEpisodeRequest) -> GraphitiEpisodeResponse:
        """Postgres graph memory does not add Graphiti episodes."""
        raise RuntimeError("graphiti_not_selected")
