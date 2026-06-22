"""Graph memory adapter boundary."""

from typing import Protocol

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


class GraphMemoryAdapter(Protocol):
    """AION-owned graph memory adapter interface."""

    def upsert_node(self, node: GraphNode) -> GraphUpsertResponse:
        """Store or update a graph node."""
        ...

    def upsert_edge(self, edge: GraphEdge) -> GraphUpsertResponse:
        """Store or update a graph edge."""
        ...

    def get_node(self, node_id: str, scope: list[str]) -> GraphNode | None:
        """Return a graph node visible to the requested scope."""
        ...

    def get_edge(self, edge_id: str, scope: list[str]) -> GraphEdge | None:
        """Return a graph edge visible to the requested scope."""
        ...

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        """Query graph memory."""
        ...

    def neighbors(
        self,
        node_id: str,
        scope: list[str],
        max_depth: int = 1,
        limit: int = 25,
    ) -> GraphQueryResult:
        """Return neighboring graph nodes and edges."""
        ...

    def soft_delete_node(self, node_id: str, scope: list[str]) -> bool:
        """Soft-delete a graph node."""
        ...

    def soft_delete_edge(self, edge_id: str, scope: list[str]) -> bool:
        """Soft-delete a graph edge."""
        ...

    def list_nodes(self, scope: list[str], *, limit: int = 10000) -> list[GraphNode]:
        """List graph nodes visible to scope."""
        ...

    def list_edges(self, scope: list[str], *, limit: int = 10000) -> list[GraphEdge]:
        """List graph edges visible to scope."""
        ...

    def status(self, config_name: str = "default") -> GraphitiConfigStatus | None:
        """Return Graphiti config status when supported."""
        ...

    def sync(self, request: GraphitiSyncRequest) -> GraphitiSyncResponse:
        """Sync graph records into Graphiti when supported."""
        ...

    def add_episode(self, request: GraphitiEpisodeRequest) -> GraphitiEpisodeResponse:
        """Add a Graphiti episode when supported."""
        ...
