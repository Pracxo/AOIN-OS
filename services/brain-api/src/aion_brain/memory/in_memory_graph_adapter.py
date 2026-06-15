"""In-memory temporal graph adapter for tests."""

import json
import re
from collections import deque
from datetime import UTC, datetime

from pydantic import ValidationError

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


class InMemoryGraphAdapter:
    """Dictionary-backed GraphMemoryAdapter for unit tests."""

    adapter_name = "in_memory"

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}

    def upsert_node(self, node: GraphNode) -> GraphUpsertResponse:
        """Store or update a graph node."""
        now = datetime.now(UTC)
        existing = self._nodes.get(node.node_id)
        self._nodes[node.node_id] = node.model_copy(
            update={
                "created_at": node.created_at or (existing.created_at if existing else now),
                "updated_at": now,
                "deleted_at": None,
            }
        )
        return GraphUpsertResponse(
            upserted=True,
            object_type="node",
            object_id=node.node_id,
            reason=None,
        )

    def upsert_edge(self, edge: GraphEdge) -> GraphUpsertResponse:
        """Store or update a graph edge."""
        now = datetime.now(UTC)
        existing = self._edges.get(edge.edge_id)
        self._edges[edge.edge_id] = edge.model_copy(
            update={
                "created_at": edge.created_at or (existing.created_at if existing else now),
                "updated_at": now,
                "deleted_at": None,
            }
        )
        return GraphUpsertResponse(
            upserted=True,
            object_type="edge",
            object_id=edge.edge_id,
            reason=None,
        )

    def get_node(self, node_id: str, scope: list[str]) -> GraphNode | None:
        """Return an active node visible to scope."""
        node = self._nodes.get(node_id)
        if node is None or not _visible_node(node, scope, include_expired=True):
            return None
        return node

    def get_edge(self, edge_id: str, scope: list[str]) -> GraphEdge | None:
        """Return an active edge visible to scope."""
        edge = self._edges.get(edge_id)
        if edge is None or not _visible_edge(edge, scope, include_expired=True):
            return None
        return edge

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        """Query graph memory with deterministic filters."""
        if query.start_node_id:
            return self._neighbors_from_query(query)

        node_types = set(query.node_types)
        edge_types = set(query.edge_types)
        nodes = [
            node
            for node in self._nodes.values()
            if _visible_node(
                node,
                query.scope,
                include_expired=query.include_expired,
                as_of=query.as_of,
            )
            and (not node_types or node.node_type in node_types)
            and _text_matches(query.query, node.label, node.properties)
        ]
        nodes = sorted(nodes, key=lambda node: (node.observed_at, node.node_id), reverse=True)[
            : query.limit
        ]
        node_ids = {node.node_id for node in nodes}
        edges = [
            edge
            for edge in self._edges.values()
            if _visible_edge(
                edge,
                query.scope,
                include_expired=query.include_expired,
                as_of=query.as_of,
            )
            and (not edge_types or edge.edge_type in edge_types)
            and (
                edge.from_node_id in node_ids
                or edge.to_node_id in node_ids
                or _text_matches(query.query, edge.edge_type, edge.properties)
            )
        ][: query.limit]
        return _result(
            nodes=nodes,
            edges=edges,
            adapter_name=self.adapter_name,
            metadata={"query": query.query, "limit": query.limit},
        )

    def neighbors(
        self,
        node_id: str,
        scope: list[str],
        max_depth: int = 1,
        limit: int = 25,
    ) -> GraphQueryResult:
        """Return neighboring nodes and connecting edges."""
        query = GraphQuery(
            scope=scope,
            start_node_id=node_id,
            max_depth=max_depth,
            limit=limit,
        )
        return self._neighbors_from_query(query)

    def soft_delete_node(self, node_id: str, scope: list[str]) -> bool:
        """Soft-delete a node visible to scope."""
        node = self.get_node(node_id, scope)
        if node is None:
            return False
        self._nodes[node_id] = node.model_copy(update={"deleted_at": datetime.now(UTC)})
        return True

    def soft_delete_edge(self, edge_id: str, scope: list[str]) -> bool:
        """Soft-delete an edge visible to scope."""
        edge = self.get_edge(edge_id, scope)
        if edge is None:
            return False
        self._edges[edge_id] = edge.model_copy(update={"deleted_at": datetime.now(UTC)})
        return True

    def list_nodes(self, scope: list[str], *, limit: int = 10000) -> list[GraphNode]:
        """List active nodes visible to scope."""
        return [
            node
            for node in self._nodes.values()
            if _visible_node(node, scope, include_expired=False)
        ][:limit]

    def list_edges(self, scope: list[str], *, limit: int = 10000) -> list[GraphEdge]:
        """List active edges visible to scope."""
        return [
            edge
            for edge in self._edges.values()
            if _visible_edge(edge, scope, include_expired=False)
        ][:limit]

    def status(self, config_name: str = "default") -> GraphitiConfigStatus | None:
        """In-memory graph memory has no Graphiti status."""
        return None

    def sync(self, request: GraphitiSyncRequest) -> GraphitiSyncResponse:
        """In-memory graph memory does not sync Graphiti indexes."""
        raise RuntimeError("graphiti_not_selected")

    def add_episode(self, request: GraphitiEpisodeRequest) -> GraphitiEpisodeResponse:
        """In-memory graph memory does not add Graphiti episodes."""
        raise RuntimeError("graphiti_not_selected")

    def _neighbors_from_query(self, query: GraphQuery) -> GraphQueryResult:
        if query.start_node_id is None:
            raise ValidationError.from_exception_data("GraphQuery", [])
        start = self.get_node(query.start_node_id, query.scope)
        if start is None:
            return _result(
                nodes=[],
                edges=[],
                adapter_name=self.adapter_name,
                metadata={"start_node_id": query.start_node_id},
            )

        visited = {start.node_id}
        result_nodes: dict[str, GraphNode] = {start.node_id: start}
        result_edges: dict[str, GraphEdge] = {}
        queue: deque[tuple[str, int]] = deque([(start.node_id, 0)])

        while queue and len(result_nodes) < query.limit:
            current_id, depth = queue.popleft()
            if depth >= query.max_depth:
                continue
            for edge in self._active_edges_for_scope(query.scope):
                if edge.edge_id in result_edges:
                    continue
                next_id = _next_neighbor(edge, current_id)
                if next_id is None:
                    continue
                next_node = self.get_node(next_id, query.scope)
                if next_node is None:
                    continue
                result_edges[edge.edge_id] = edge
                if next_id not in visited:
                    visited.add(next_id)
                    result_nodes[next_id] = next_node
                    queue.append((next_id, depth + 1))
                if len(result_nodes) >= query.limit:
                    break

        return _result(
            nodes=list(result_nodes.values())[: query.limit],
            edges=list(result_edges.values())[: query.limit],
            adapter_name=self.adapter_name,
            metadata={"start_node_id": query.start_node_id, "max_depth": query.max_depth},
        )

    def _active_edges_for_scope(self, scope: list[str]) -> list[GraphEdge]:
        return [
            edge
            for edge in self._edges.values()
            if _visible_edge(edge, scope, include_expired=False)
        ]


def _result(
    *,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    adapter_name: str,
    metadata: dict[str, object],
) -> GraphQueryResult:
    return GraphQueryResult(
        nodes=nodes,
        edges=edges,
        score=1.0 if nodes or edges else 0.0,
        retrieval_source="graph",
        adapter_name=adapter_name,
        metadata=metadata,
    )


def _visible_node(
    node: GraphNode,
    scope: list[str],
    *,
    include_expired: bool,
    as_of: datetime | None = None,
) -> bool:
    return (
        node.deleted_at is None
        and _scope_matches(node.owner_scope, scope)
        and _temporal_active(node.valid_from, node.valid_to, include_expired, as_of)
    )


def _visible_edge(
    edge: GraphEdge,
    scope: list[str],
    *,
    include_expired: bool,
    as_of: datetime | None = None,
) -> bool:
    return (
        edge.deleted_at is None
        and _scope_matches(edge.owner_scope, scope)
        and _temporal_active(edge.valid_from, edge.valid_to, include_expired, as_of)
    )


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(requested_scope))


def _temporal_active(
    valid_from: datetime | None,
    valid_to: datetime | None,
    include_expired: bool,
    as_of: datetime | None,
) -> bool:
    if include_expired:
        return True
    reference = as_of or datetime.now(UTC)
    if valid_from is not None and valid_from > reference:
        return False
    if valid_to is not None and valid_to <= reference:
        return False
    return True


def _text_matches(query: str | None, label: str, properties: dict[str, object]) -> bool:
    if not query:
        return True
    haystack = f"{label} {json.dumps(properties, sort_keys=True)}"
    return bool(_tokens(query).intersection(_tokens(haystack)))


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _next_neighbor(edge: GraphEdge, current_id: str) -> str | None:
    if edge.from_node_id == current_id:
        return edge.to_node_id
    if edge.to_node_id == current_id:
        return edge.from_node_id
    return None
