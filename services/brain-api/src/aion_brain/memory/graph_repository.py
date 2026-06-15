"""Postgres temporal graph repository."""

import json
import re
from collections import deque
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool

from aion_brain.contracts.graph import (
    GraphEdge,
    GraphNode,
    GraphQuery,
    GraphQueryResult,
    GraphUpsertResponse,
)

graph_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_graph_nodes = Table(
    "aion_graph_nodes",
    graph_metadata,
    Column("node_id", Text, primary_key=True),
    Column("node_type", Text, nullable=False),
    Column("label", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("properties", json_payload_type, nullable=False),
    Column("source_event_id", Text, nullable=True),
    Column("confidence", Float, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("valid_from", DateTime(timezone=True), nullable=True),
    Column("valid_to", DateTime(timezone=True), nullable=True),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_graph_nodes_node_type", "node_type"),
    Index("ix_aion_graph_nodes_label", "label"),
    Index("ix_aion_graph_nodes_observed_at", "observed_at"),
    Index("ix_aion_graph_nodes_source_event_id", "source_event_id"),
    Index("ix_aion_graph_nodes_deleted_at", "deleted_at"),
)

aion_graph_edges = Table(
    "aion_graph_edges",
    graph_metadata,
    Column("edge_id", Text, primary_key=True),
    Column("edge_type", Text, nullable=False),
    Column("from_node_id", Text, ForeignKey("aion_graph_nodes.node_id"), nullable=False),
    Column("to_node_id", Text, ForeignKey("aion_graph_nodes.node_id"), nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("properties", json_payload_type, nullable=False),
    Column("source_event_id", Text, nullable=True),
    Column("confidence", Float, nullable=False),
    Column("sensitivity", Text, nullable=False),
    Column("valid_from", DateTime(timezone=True), nullable=True),
    Column("valid_to", DateTime(timezone=True), nullable=True),
    Column("observed_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_graph_edges_edge_type", "edge_type"),
    Index("ix_aion_graph_edges_from_node_id", "from_node_id"),
    Index("ix_aion_graph_edges_to_node_id", "to_node_id"),
    Index("ix_aion_graph_edges_observed_at", "observed_at"),
    Index("ix_aion_graph_edges_source_event_id", "source_event_id"),
    Index("ix_aion_graph_edges_deleted_at", "deleted_at"),
)


class GraphRepository:
    """Repository for local temporal graph memory."""

    adapter_name = "postgres"

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        if engine is None:
            if database_url is None:
                raise ValueError("database_url or engine is required")
            self._engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_pre_ping=True,
            )
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False
        self._schema_lock = Lock()

    def upsert_node(self, node: GraphNode) -> GraphUpsertResponse:
        """Store or update a graph node."""
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_graph_nodes).where(aion_graph_nodes.c.node_id == node.node_id)
            ).mappings().first()
            values = _node_values(
                node,
                created_at=_created_at(existing, node.created_at, now),
                updated_at=now,
                deleted_at=None,
            )
            if existing is None:
                connection.execute(insert(aion_graph_nodes).values(**values))
            else:
                connection.execute(
                    update(aion_graph_nodes)
                    .where(aion_graph_nodes.c.node_id == node.node_id)
                    .values(**values)
                )
        return GraphUpsertResponse(
            upserted=True,
            object_type="node",
            object_id=node.node_id,
            reason=None,
        )

    def upsert_edge(self, edge: GraphEdge) -> GraphUpsertResponse:
        """Store or update a graph edge."""
        self._ensure_schema()
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_graph_edges).where(aion_graph_edges.c.edge_id == edge.edge_id)
            ).mappings().first()
            values = _edge_values(
                edge,
                created_at=_created_at(existing, edge.created_at, now),
                updated_at=now,
                deleted_at=None,
            )
            if existing is None:
                connection.execute(insert(aion_graph_edges).values(**values))
            else:
                connection.execute(
                    update(aion_graph_edges)
                    .where(aion_graph_edges.c.edge_id == edge.edge_id)
                    .values(**values)
                )
        return GraphUpsertResponse(
            upserted=True,
            object_type="edge",
            object_id=edge.edge_id,
            reason=None,
        )

    def get_node(self, node_id: str, scope: list[str]) -> GraphNode | None:
        """Return an active node visible to scope."""
        self._ensure_schema()
        statement = select(aion_graph_nodes).where(
            aion_graph_nodes.c.node_id == node_id,
            aion_graph_nodes.c.deleted_at.is_(None),
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        node = _row_to_node(row)
        if not _scope_matches(node.owner_scope, scope):
            return None
        return node

    def get_edge(self, edge_id: str, scope: list[str]) -> GraphEdge | None:
        """Return an active edge visible to scope."""
        self._ensure_schema()
        statement = select(aion_graph_edges).where(
            aion_graph_edges.c.edge_id == edge_id,
            aion_graph_edges.c.deleted_at.is_(None),
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        edge = _row_to_edge(row)
        if not _scope_matches(edge.owner_scope, scope):
            return None
        return edge

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        """Query graph memory with deterministic filters."""
        if query.start_node_id:
            return self.neighbors(
                query.start_node_id,
                query.scope,
                max_depth=query.max_depth,
                limit=query.limit,
            )
        nodes = _filter_nodes(_all_nodes(self._engine, self._ensure_schema), query)
        node_ids = {node.node_id for node in nodes}
        edges = _filter_edges(
            _all_edges(self._engine, self._ensure_schema),
            query,
            node_ids=node_ids,
        )
        return _result(
            nodes=nodes[: query.limit],
            edges=edges[: query.limit],
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
        query = GraphQuery(scope=scope, start_node_id=node_id, max_depth=max_depth, limit=limit)
        start = self.get_node(node_id, scope)
        if start is None:
            return _result(
                nodes=[],
                edges=[],
                metadata={"start_node_id": node_id, "max_depth": max_depth},
            )

        active_nodes = {
            node.node_id: node
            for node in _filter_nodes(_all_nodes(self._engine, self._ensure_schema), query)
        }
        active_edges = _filter_edges(_all_edges(self._engine, self._ensure_schema), query)
        visited = {node_id}
        result_nodes: dict[str, GraphNode] = {node_id: start}
        result_edges: dict[str, GraphEdge] = {}
        queue: deque[tuple[str, int]] = deque([(node_id, 0)])

        while queue and len(result_nodes) < limit:
            current_id, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for edge in active_edges:
                if edge.edge_id in result_edges:
                    continue
                next_id = _next_neighbor(edge, current_id)
                if next_id is None or next_id not in active_nodes:
                    continue
                result_edges[edge.edge_id] = edge
                if next_id not in visited:
                    visited.add(next_id)
                    result_nodes[next_id] = active_nodes[next_id]
                    queue.append((next_id, depth + 1))
                if len(result_nodes) >= limit:
                    break

        return _result(
            nodes=list(result_nodes.values())[:limit],
            edges=list(result_edges.values())[:limit],
            metadata={"start_node_id": node_id, "max_depth": max_depth},
        )

    def list_nodes(self, scope: list[str], *, limit: int = 10000) -> list[GraphNode]:
        """List active graph nodes visible to scope."""
        query = GraphQuery(scope=scope, limit=min(limit, 100))
        nodes = _filter_nodes(_all_nodes(self._engine, self._ensure_schema), query)
        return nodes[:limit]

    def list_edges(self, scope: list[str], *, limit: int = 10000) -> list[GraphEdge]:
        """List active graph edges visible to scope."""
        query = GraphQuery(scope=scope, limit=min(limit, 100))
        edges = _filter_edges(_all_edges(self._engine, self._ensure_schema), query)
        return edges[:limit]

    def soft_delete_node(self, node_id: str, scope: list[str]) -> bool:
        """Soft-delete a node visible to scope."""
        if self.get_node(node_id, scope) is None:
            return False
        statement = (
            update(aion_graph_nodes)
            .where(aion_graph_nodes.c.node_id == node_id)
            .values(deleted_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        )
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        return result.rowcount == 1

    def soft_delete_edge(self, edge_id: str, scope: list[str]) -> bool:
        """Soft-delete an edge visible to scope."""
        if self.get_edge(edge_id, scope) is None:
            return False
        statement = (
            update(aion_graph_edges)
            .where(aion_graph_edges.c.edge_id == edge_id)
            .values(deleted_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        )
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        return result.rowcount == 1

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        with self._schema_lock:
            if self._schema_ready or not self._auto_create:
                return
            graph_metadata.create_all(self._engine)
            self._schema_ready = True


def _all_nodes(engine: Engine, ensure_schema: Any) -> list[GraphNode]:
    ensure_schema()
    with engine.connect() as connection:
        rows = connection.execute(select(aion_graph_nodes)).mappings().all()
    return [_row_to_node(row) for row in rows]


def _all_edges(engine: Engine, ensure_schema: Any) -> list[GraphEdge]:
    ensure_schema()
    with engine.connect() as connection:
        rows = connection.execute(select(aion_graph_edges)).mappings().all()
    return [_row_to_edge(row) for row in rows]


def _filter_nodes(nodes: list[GraphNode], query: GraphQuery) -> list[GraphNode]:
    node_types = set(query.node_types)
    filtered = [
        node
        for node in nodes
        if _scope_matches(node.owner_scope, query.scope)
        and node.deleted_at is None
        and _temporal_active(node.valid_from, node.valid_to, query.include_expired, query.as_of)
        and (not node_types or node.node_type in node_types)
        and _text_matches(query.query, node.label, node.properties)
    ]
    return sorted(filtered, key=lambda node: (node.observed_at, node.node_id), reverse=True)


def _filter_edges(
    edges: list[GraphEdge],
    query: GraphQuery,
    *,
    node_ids: set[str] | None = None,
) -> list[GraphEdge]:
    edge_types = set(query.edge_types)
    filtered = [
        edge
        for edge in edges
        if _scope_matches(edge.owner_scope, query.scope)
        and edge.deleted_at is None
        and _temporal_active(edge.valid_from, edge.valid_to, query.include_expired, query.as_of)
        and (not edge_types or edge.edge_type in edge_types)
        and _edge_matches(edge, query.query, node_ids)
    ]
    return sorted(filtered, key=lambda edge: (edge.observed_at, edge.edge_id), reverse=True)


def _edge_matches(edge: GraphEdge, query: str | None, node_ids: set[str] | None) -> bool:
    if node_ids and (edge.from_node_id in node_ids or edge.to_node_id in node_ids):
        return True
    return _text_matches(query, edge.edge_type, edge.properties)


def _result(
    *,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    metadata: dict[str, object],
) -> GraphQueryResult:
    return GraphQueryResult(
        nodes=nodes,
        edges=edges,
        score=1.0 if nodes or edges else 0.0,
        retrieval_source="graph",
        adapter_name=GraphRepository.adapter_name,
        metadata=metadata,
    )


def _node_values(
    node: GraphNode,
    *,
    created_at: datetime,
    updated_at: datetime,
    deleted_at: datetime | None,
) -> dict[str, Any]:
    values = node.model_dump(mode="python")
    values["created_at"] = created_at
    values["updated_at"] = updated_at
    values["deleted_at"] = deleted_at
    return values


def _edge_values(
    edge: GraphEdge,
    *,
    created_at: datetime,
    updated_at: datetime,
    deleted_at: datetime | None,
) -> dict[str, Any]:
    values = edge.model_dump(mode="python")
    values["created_at"] = created_at
    values["updated_at"] = updated_at
    values["deleted_at"] = deleted_at
    return values


def _created_at(row: RowMapping | None, value: datetime | None, now: datetime) -> datetime:
    if value is not None:
        return value
    if row is not None:
        return _coerce_datetime(row["created_at"])
    return now


def _row_to_node(row: RowMapping) -> GraphNode:
    return GraphNode(
        node_id=str(row["node_id"]),
        node_type=str(row["node_type"]),
        label=str(row["label"]),
        owner_scope=list(row["owner_scope"]),
        properties=dict(row["properties"]),
        source_event_id=_optional_str(row["source_event_id"]),
        confidence=float(row["confidence"]),
        sensitivity=str(row["sensitivity"]),
        valid_from=_optional_datetime(row["valid_from"]),
        valid_to=_optional_datetime(row["valid_to"]),
        observed_at=_coerce_datetime(row["observed_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
    )


def _row_to_edge(row: RowMapping) -> GraphEdge:
    return GraphEdge(
        edge_id=str(row["edge_id"]),
        edge_type=str(row["edge_type"]),
        from_node_id=str(row["from_node_id"]),
        to_node_id=str(row["to_node_id"]),
        owner_scope=list(row["owner_scope"]),
        properties=dict(row["properties"]),
        source_event_id=_optional_str(row["source_event_id"]),
        confidence=float(row["confidence"]),
        sensitivity=str(row["sensitivity"]),
        valid_from=_optional_datetime(row["valid_from"]),
        valid_to=_optional_datetime(row["valid_to"]),
        observed_at=_coerce_datetime(row["observed_at"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        deleted_at=_optional_datetime(row["deleted_at"]),
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


def _text_matches(query: str | None, label: str, properties: dict[str, Any]) -> bool:
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


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    return _coerce_datetime(value)


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
