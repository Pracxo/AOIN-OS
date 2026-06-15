"""Optional Graphiti temporal knowledge graph adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

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
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.memory.graphiti_compat import GraphitiCompat
from aion_brain.memory.graphiti_repository import GraphitiRepository


class GraphitiGraphMemoryAdapter:
    """Optional Graphiti adapter behind AION's GraphMemoryAdapter boundary."""

    adapter_name = "graphiti"

    def __init__(
        self,
        *,
        graphiti_repository: GraphitiRepository | None = None,
        postgres_graph_adapter: object | None = None,
        telemetry_service: object | None = None,
        compat: GraphitiCompat | None = None,
        enabled: bool = False,
        config_name: str = "default",
        backend_type: str = "unknown",
        endpoint_ref: str | None = None,
        fail_open_to_postgres_graph: bool = True,
        model_gateway_enabled: bool = False,
    ) -> None:
        self._repository = graphiti_repository
        self._canonical = postgres_graph_adapter
        self._telemetry_service = telemetry_service
        self._compat = compat or GraphitiCompat()
        self._enabled = enabled
        self._config_name = _safe_config_name(config_name)
        self._backend_type = backend_type
        self._endpoint_ref = endpoint_ref or None
        self._fail_open = fail_open_to_postgres_graph
        self._model_gateway_enabled = model_gateway_enabled
        self._clients: dict[str, Any] = {}

    def upsert_node(self, node: GraphNode) -> GraphUpsertResponse:
        """Store a node canonically, then optionally index it in Graphiti."""
        canonical_response = _canonical_call(self._canonical, "upsert_node", node)
        status = self.status(self._config_name)
        if not status.available:
            self._emit_unavailable(status)
            return _upsert_or_unavailable(canonical_response, "node", node.node_id, status.reason)
        response = self._compat.upsert_node(self._client(status), node)
        self._record_sync(
            status,
            "node",
            node.node_id,
            "graphiti_node",
            response.object_id,
            node.owner_scope,
        )
        self._emit(
            "graph_node_indexed",
            "graph",
            node.node_id,
            0.6,
            {"config_name": status.config_name},
        )
        if isinstance(canonical_response, GraphUpsertResponse):
            return canonical_response
        return response

    def upsert_edge(self, edge: GraphEdge) -> GraphUpsertResponse:
        """Store an edge canonically, then optionally index it in Graphiti."""
        canonical_response = _canonical_call(self._canonical, "upsert_edge", edge)
        status = self.status(self._config_name)
        if not status.available:
            self._emit_unavailable(status)
            return _upsert_or_unavailable(canonical_response, "edge", edge.edge_id, status.reason)
        response = self._compat.upsert_edge(self._client(status), edge)
        self._record_sync(
            status,
            "edge",
            edge.edge_id,
            "graphiti_edge",
            response.object_id,
            edge.owner_scope,
        )
        self._emit(
            "graph_edge_indexed",
            "graph",
            edge.edge_id,
            0.6,
            {"config_name": status.config_name},
        )
        if isinstance(canonical_response, GraphUpsertResponse):
            return canonical_response
        return response

    def get_node(self, node_id: str, scope: list[str]) -> GraphNode | None:
        """Return a canonical graph node visible to scope."""
        return cast(GraphNode | None, _canonical_call(self._canonical, "get_node", node_id, scope))

    def get_edge(self, edge_id: str, scope: list[str]) -> GraphEdge | None:
        """Return a canonical graph edge visible to scope."""
        return cast(GraphEdge | None, _canonical_call(self._canonical, "get_edge", edge_id, scope))

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        """Query Graphiti when available, otherwise use configured fallback."""
        status = self.status(self._config_name)
        if not status.available:
            return self._fallback_result("query_graph", status, query)
        try:
            result = self._compat.query(self._client(status), query)
        except RuntimeError as exc:
            return self._fallback_result(
                "query_graph",
                status.model_copy(update={"available": False, "reason": str(exc)}),
                query,
            )
        return _graphiti_result(result, fallback=False, fallback_reason=None)

    def neighbors(
        self,
        node_id: str,
        scope: list[str],
        max_depth: int = 1,
        limit: int = 25,
    ) -> GraphQueryResult:
        """Return neighbors through Graphiti query or canonical fallback."""
        query = GraphQuery(scope=scope, start_node_id=node_id, max_depth=max_depth, limit=limit)
        status = self.status(self._config_name)
        if not status.available:
            return self._fallback_result("neighbors", status, query)
        try:
            result = self._compat.query(self._client(status), query)
        except RuntimeError as exc:
            return self._fallback_result(
                "neighbors",
                status.model_copy(update={"available": False, "reason": str(exc)}),
                query,
            )
        return _graphiti_result(result, fallback=False, fallback_reason=None)

    def soft_delete_node(self, node_id: str, scope: list[str]) -> bool:
        """Soft-delete canonical node and sync metadata."""
        deleted = bool(_canonical_call(self._canonical, "soft_delete_node", node_id, scope))
        status = self.status(self._config_name)
        if self._repository is not None:
            self._repository.soft_delete_sync_record(status.graphiti_config_id, "node", node_id)
        return deleted

    def soft_delete_edge(self, edge_id: str, scope: list[str]) -> bool:
        """Soft-delete canonical edge and sync metadata."""
        deleted = bool(_canonical_call(self._canonical, "soft_delete_edge", edge_id, scope))
        status = self.status(self._config_name)
        if self._repository is not None:
            self._repository.soft_delete_sync_record(status.graphiti_config_id, "edge", edge_id)
        return deleted

    def list_nodes(self, scope: list[str], *, limit: int = 10000) -> list[GraphNode]:
        """List canonical nodes visible to scope."""
        return _canonical_call(self._canonical, "list_nodes", scope, limit=limit) or []

    def list_edges(self, scope: list[str], *, limit: int = 10000) -> list[GraphEdge]:
        """List canonical edges visible to scope."""
        return _canonical_call(self._canonical, "list_edges", scope, limit=limit) or []

    def add_episode(self, request: GraphitiEpisodeRequest) -> GraphitiEpisodeResponse:
        """Add a temporal episode when Graphiti is available."""
        status = self.status(request.metadata.get("config_name", self._config_name))
        episode_id = request.episode_id or f"episode-{uuid4().hex}"
        if not status.available:
            self._emit_unavailable(status)
            return GraphitiEpisodeResponse(
                added=False,
                episode_id=episode_id,
                status=status.status,
                reason=status.reason,
                metadata={"adapter_name": self.adapter_name},
            )
        response = self._compat.add_episode(
            self._client(status),
            request.model_copy(update={"episode_id": episode_id}),
        )
        if self._repository is not None:
            self._repository.record_sync(
                status.graphiti_config_id,
                request.source_type,
                request.source_id,
                "graphiti_episode",
                response.episode_id,
                request.scope,
                "synced" if response.added else "failed",
                {"trace_id": request.trace_id},
            )
        self._emit(
            "graph_episode_added",
            "episode",
            response.episode_id,
            0.6,
            {"source_type": request.source_type},
        )
        return response

    def sync(self, request: GraphitiSyncRequest) -> GraphitiSyncResponse:
        """Sync canonical graph records into Graphiti."""
        status = self.status(request.config_name)
        nodes = self._eligible_nodes(request)
        edges = self._eligible_edges(request)
        if request.dry_run:
            return _sync_response(
                request,
                status,
                synced=False,
                indexed_nodes=len(nodes),
                indexed_edges=len(edges),
                skipped=0,
                failed=0,
                reason=status.reason if not status.available else None,
            )
        if not status.available:
            self._emit_unavailable(status)
            return _sync_response(
                request,
                status,
                synced=False,
                indexed_nodes=0,
                indexed_edges=0,
                skipped=len(nodes) + len(edges),
                failed=0,
                reason=status.reason,
            )
        indexed_nodes = 0
        indexed_edges = 0
        failed = 0
        for node in nodes:
            try:
                self._compat.upsert_node(self._client(status), node)
                self._record_sync(
                    status,
                    "node",
                    node.node_id,
                    "graphiti_node",
                    node.node_id,
                    node.owner_scope,
                )
                indexed_nodes += 1
            except Exception:
                failed += 1
        for edge in edges:
            try:
                self._compat.upsert_edge(self._client(status), edge)
                self._record_sync(
                    status,
                    "edge",
                    edge.edge_id,
                    "graphiti_edge",
                    edge.edge_id,
                    edge.owner_scope,
                )
                indexed_edges += 1
            except Exception:
                failed += 1
        self._emit(
            "graphiti_synced",
            "index",
            request.config_name,
            0.8,
            {"indexed_nodes": indexed_nodes, "indexed_edges": indexed_edges, "failed": failed},
        )
        return _sync_response(
            request,
            status,
            synced=failed == 0,
            indexed_nodes=indexed_nodes,
            indexed_edges=indexed_edges,
            skipped=0,
            failed=failed,
            reason=None if failed == 0 else "graphiti_sync_partial_failure",
        )

    def status(self, config_name: str = "default") -> GraphitiConfigStatus:
        """Return Graphiti availability and config metadata."""
        safe_name = _safe_config_name(config_name)
        base = _status(
            config_name=safe_name,
            backend_type=self._backend_type,
            endpoint_ref=self._endpoint_ref,
            status="active",
            available=True,
            reason=None,
        )
        if not self._enabled:
            return base.model_copy(
                update={"status": "disabled", "available": False, "reason": "graphiti_disabled"}
            )
        if not self._compat.is_available():
            return base.model_copy(
                update={
                    "status": "unavailable",
                    "available": False,
                    "reason": self._compat.availability_reason() or "graphiti_package_unavailable",
                }
            )
        if self._compat.requires_llm() and not self._model_gateway_enabled:
            return base.model_copy(
                update={
                    "status": "unavailable",
                    "available": False,
                    "reason": "graphiti_llm_disabled",
                }
            )
        if self._repository is None:
            return base.model_copy(
                update={
                    "status": "unavailable",
                    "available": False,
                    "reason": "graphiti_repository_missing",
                }
            )
        try:
            return self._repository.create_or_get_config(
                safe_name,
                self._backend_type,
                self._endpoint_ref,
            )
        except RuntimeError as exc:
            return base.model_copy(
                update={"status": "failed", "available": False, "reason": str(exc)}
            )

    def _fallback_result(
        self,
        operation: str,
        status: GraphitiConfigStatus,
        query: GraphQuery,
    ) -> GraphQueryResult:
        self._emit_unavailable(status)
        if self._fail_open and self._canonical is not None:
            self._emit(
                "graph_adapter_fallback",
                "adapter",
                "postgres_graph",
                0.8,
                {"reason": status.reason, "operation": operation},
            )
            result = _canonical_call(
                self._canonical,
                "neighbors" if operation == "neighbors" else "query_graph",
                query.start_node_id,
                query.scope,
                max_depth=query.max_depth,
                limit=query.limit,
            ) if operation == "neighbors" and query.start_node_id else _canonical_call(
                self._canonical,
                "query_graph",
                query,
            )
            if isinstance(result, GraphQueryResult):
                return _graphiti_result(result, fallback=True, fallback_reason=status.reason)
        return GraphQueryResult(
            nodes=[],
            edges=[],
            score=0.0,
            retrieval_source="graph",
            adapter_name=self.adapter_name,
            metadata={
                "adapter_name": self.adapter_name,
                "fallback": False,
                "fallback_reason": status.reason,
                "unavailable": True,
            },
        )

    def _eligible_nodes(self, request: GraphitiSyncRequest) -> list[GraphNode]:
        if request.source_types and not {"node", "graph_node"}.intersection(request.source_types):
            return []
        return self.list_nodes(request.scope, limit=request.limit)

    def _eligible_edges(self, request: GraphitiSyncRequest) -> list[GraphEdge]:
        if request.source_types and not {"edge", "graph_edge"}.intersection(request.source_types):
            return []
        remaining = max(request.limit - len(self._eligible_nodes(request)), 0)
        return self.list_edges(request.scope, limit=remaining or request.limit)

    def _client(self, status: GraphitiConfigStatus) -> Any:
        client = self._clients.get(status.config_name)
        if client is not None:
            return client
        client = self._compat.create_client(status)
        self._clients[status.config_name] = client
        return client

    def _record_sync(
        self,
        status: GraphitiConfigStatus,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        owner_scope: list[str],
    ) -> None:
        if self._repository is None:
            return
        self._repository.record_sync(
            status.graphiti_config_id,
            source_type,
            source_id,
            target_type,
            target_id,
            owner_scope,
            "synced",
            {"adapter_name": self.adapter_name},
        )

    def _emit_unavailable(self, status: GraphitiConfigStatus) -> None:
        self._emit(
            "graphiti_unavailable",
            "adapter",
            self.adapter_name,
            0.7,
            {"reason": status.reason, "config_name": status.config_name},
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-graphiti-{event_type}-{node_id}",
            trace_id=f"graphiti-{node_id}",
            event_type=cast(Any, event_type),
            node_type=cast(Any, node_type),
            node_id=node_id,
            edge_from=None,
            edge_to=None,
            intensity=max(0.0, min(1.0, intensity)),
            payload=payload,
            created_at=datetime.now(UTC),
        )
        emit = getattr(self._telemetry_service, "emit", None)
        save = getattr(self._telemetry_service, "save_visual_telemetry", None)
        try:
            if callable(emit):
                emit(event)
            elif callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _graphiti_result(
    result: GraphQueryResult,
    *,
    fallback: bool,
    fallback_reason: str | None,
) -> GraphQueryResult:
    return result.model_copy(
        update={
            "adapter_name": "graphiti",
            "metadata": {
                **result.metadata,
                "adapter_name": "graphiti",
                "fallback": fallback,
                "fallback_reason": fallback_reason,
            },
        }
    )


def _sync_response(
    request: GraphitiSyncRequest,
    status: GraphitiConfigStatus,
    *,
    synced: bool,
    indexed_nodes: int,
    indexed_edges: int,
    skipped: int,
    failed: int,
    reason: str | None,
) -> GraphitiSyncResponse:
    return GraphitiSyncResponse(
        synced=synced,
        dry_run=request.dry_run,
        config_name=request.config_name,
        indexed_nodes=indexed_nodes,
        indexed_edges=indexed_edges,
        skipped=skipped,
        failed=failed,
        status=status,
        reason=reason,
    )


def _upsert_or_unavailable(
    response: object,
    object_type: str,
    object_id: str,
    reason: str | None,
) -> GraphUpsertResponse:
    if isinstance(response, GraphUpsertResponse):
        return response
    return GraphUpsertResponse(
        upserted=False,
        object_type=object_type,
        object_id=object_id,
        reason=reason,
    )


def _canonical_call(target: object | None, method_name: str, *args: Any, **kwargs: Any) -> Any:
    method = getattr(target, method_name, None)
    if not callable(method):
        return None
    return method(*args, **kwargs)


def _status(
    *,
    config_name: str,
    backend_type: str,
    endpoint_ref: str | None,
    status: str,
    available: bool,
    reason: str | None,
) -> GraphitiConfigStatus:
    now = datetime.now(UTC)
    return GraphitiConfigStatus(
        graphiti_config_id=f"graphiti-{config_name}",
        config_name=config_name,
        adapter_name="graphiti",
        status=cast(Any, status),
        backend_type=cast(Any, backend_type),
        endpoint_ref=endpoint_ref,
        available=available,
        reason=reason,
        metadata={},
        created_at=now,
        updated_at=now,
        last_health_check_at=None,
    )


def _safe_config_name(value: str) -> str:
    if not value or "/" in value or "\\" in value or ".." in value:
        raise ValueError("config_name cannot be empty or contain path traversal")
    return value
