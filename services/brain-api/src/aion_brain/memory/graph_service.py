"""Policy-gated graph memory service."""

from typing import cast

from aion_brain.contracts.graph import (
    GraphEdge,
    GraphitiConfigStatus,
    GraphitiEpisodeRequest,
    GraphitiEpisodeResponse,
    GraphitiSyncRequest,
    GraphitiSyncResponse,
    GraphMemoryAdapterStatus,
    GraphNode,
    GraphQuery,
    GraphQueryResult,
    GraphUpsertResponse,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.memory.graph_base import GraphMemoryAdapter
from aion_brain.policy.base import PolicyAdapter


class GraphMemoryPolicyDenied(Exception):
    """Raised when policy denies graph memory access."""

    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class GraphMemoryUnavailable(Exception):
    """Raised when the configured graph adapter is unavailable."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class GraphMemoryService:
    """Graph memory service with mandatory policy checks."""

    def __init__(
        self,
        *,
        adapter: GraphMemoryAdapter,
        policy_adapter: PolicyAdapter,
        configured_adapter: str | None = None,
        fallback_reason: str | None = None,
        graphiti_adapter: GraphMemoryAdapter | None = None,
        degraded_mode_service: object | None = None,
    ) -> None:
        self._adapter = adapter
        self._policy_adapter = policy_adapter
        self._configured_adapter = configured_adapter or getattr(
            adapter,
            "adapter_name",
            "unknown",
        )
        self._fallback_reason = fallback_reason
        self._graphiti_adapter = graphiti_adapter
        self._degraded_mode_service = degraded_mode_service

    def set_degraded_mode_service(self, degraded_mode_service: object | None) -> None:
        """Attach degraded mode service after kernel assembly."""
        self._degraded_mode_service = degraded_mode_service

    def upsert_node(self, node: GraphNode) -> GraphUpsertResponse:
        """Authorize and upsert a graph node."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_type="graph_node",
            resource_id=node.node_id,
            risk_level=_risk_from_sensitivity(node.sensitivity),
            scope=node.owner_scope,
            context={"node_type": node.node_type, "source_event_id": node.source_event_id},
        )
        return self._adapter.upsert_node(node)

    def upsert_edge(self, edge: GraphEdge) -> GraphUpsertResponse:
        """Authorize and upsert a graph edge."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_type="graph_edge",
            resource_id=edge.edge_id,
            risk_level=_risk_from_sensitivity(edge.sensitivity),
            scope=edge.owner_scope,
            context={
                "edge_type": edge.edge_type,
                "from_node_id": edge.from_node_id,
                "to_node_id": edge.to_node_id,
                "source_event_id": edge.source_event_id,
            },
        )
        return self._adapter.upsert_edge(edge)

    def get_node(self, node_id: str, scope: list[str]) -> GraphNode | None:
        """Authorize and return a graph node."""
        self._authorize_retrieve(
            resource_type="graph_node",
            resource_id=node_id,
            scope=scope,
            context={"operation": "get_node"},
        )
        return self._adapter.get_node(node_id, scope)

    def get_edge(self, edge_id: str, scope: list[str]) -> GraphEdge | None:
        """Authorize and return a graph edge."""
        self._authorize_retrieve(
            resource_type="graph_edge",
            resource_id=edge_id,
            scope=scope,
            context={"operation": "get_edge"},
        )
        return self._adapter.get_edge(edge_id, scope)

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        """Authorize and query graph memory."""
        self._authorize_retrieve(
            resource_type="graph",
            resource_id=query.start_node_id,
            scope=query.scope,
            context={
                "operation": "query_graph",
                "node_types": query.node_types,
                "edge_types": query.edge_types,
            },
        )
        try:
            result = self._adapter.query_graph(query)
        except RuntimeError as exc:
            self._enter_degraded("graph_memory", str(exc), query.scope)
            raise GraphMemoryUnavailable(str(exc)) from exc
        if self._fallback_reason:
            return result.model_copy(
                update={
                    "metadata": {
                        **result.metadata,
                        "adapter_fallback": True,
                        "fallback_reason": self._fallback_reason,
                    }
                }
            )
        return result

    def neighbors(
        self,
        node_id: str,
        scope: list[str],
        *,
        max_depth: int = 1,
        limit: int = 25,
    ) -> GraphQueryResult:
        """Authorize and retrieve graph neighbors."""
        self._authorize_retrieve(
            resource_type="graph",
            resource_id=node_id,
            scope=scope,
            context={"operation": "neighbors", "max_depth": max_depth, "limit": limit},
        )
        try:
            result = self._adapter.neighbors(node_id, scope, max_depth=max_depth, limit=limit)
        except RuntimeError as exc:
            self._enter_degraded("graph_memory", str(exc), scope)
            raise GraphMemoryUnavailable(str(exc)) from exc
        if self._fallback_reason:
            return result.model_copy(
                update={
                    "metadata": {
                        **result.metadata,
                        "adapter_fallback": True,
                        "fallback_reason": self._fallback_reason,
                    }
                }
            )
        return result

    def delete_node(self, node_id: str, scope: list[str]) -> bool:
        """Authorize and soft-delete a node."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_type="graph_node",
            resource_id=node_id,
            risk_level="low",
            scope=scope,
            context={"operation": "soft_delete_node"},
        )
        return self._adapter.soft_delete_node(node_id, scope)

    def delete_edge(self, edge_id: str, scope: list[str]) -> bool:
        """Authorize and soft-delete an edge."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_type="graph_edge",
            resource_id=edge_id,
            risk_level="low",
            scope=scope,
            context={"operation": "soft_delete_edge"},
        )
        return self._adapter.soft_delete_edge(edge_id, scope)

    def adapter_statuses(self, scope: list[str]) -> list[GraphMemoryAdapterStatus]:
        """Return public graph adapter status summaries."""
        self._authorize_retrieve(
            resource_type="graph_adapter",
            resource_id=None,
            scope=scope,
            context={"operation": "graph_adapter_status"},
        )
        active_name = _normalized_adapter_name(getattr(self._adapter, "adapter_name", "unknown"))
        default_name = _normalized_adapter_name(str(self._configured_adapter))
        graphiti_status = self.graphiti_status("default", scope, authorize=False)
        return [
            GraphMemoryAdapterStatus(
                adapter_name="in_memory",
                active=active_name in {"in_memory", "in-memory"},
                available=True,
                default=default_name in {"in_memory", "in-memory"},
                reason=None,
                metadata={},
            ),
            GraphMemoryAdapterStatus(
                adapter_name="postgres_graph",
                active=active_name in {"postgres_graph", "postgres"},
                available=True,
                default=default_name == "postgres_graph",
                reason=(
                    self._fallback_reason if active_name in {"postgres_graph", "postgres"} else None
                ),
                metadata={
                    "adapter_fallback": bool(self._fallback_reason)
                    if active_name in {"postgres_graph", "postgres"}
                    else False
                },
            ),
            GraphMemoryAdapterStatus(
                adapter_name="graphiti",
                active=active_name == "graphiti",
                available=graphiti_status.available,
                default=default_name == "graphiti",
                reason=graphiti_status.reason,
                metadata={
                    "status": graphiti_status.status,
                    "config_name": graphiti_status.config_name,
                    "backend_type": graphiti_status.backend_type,
                },
            ),
        ]

    def graphiti_status(
        self,
        config_name: str = "default",
        scope: list[str] | None = None,
        *,
        authorize: bool = True,
    ) -> GraphitiConfigStatus:
        """Return Graphiti status without exposing vendor objects."""
        if authorize:
            self._authorize_retrieve(
                resource_type="graph_adapter",
                resource_id=config_name,
                scope=scope or ["workspace:main"],
                context={"operation": "graphiti_status", "config_name": config_name},
            )
        adapter = self._graphiti_adapter or self._adapter
        status_method = getattr(adapter, "status", None)
        if callable(status_method):
            status = status_method(config_name)
            if status is not None:
                return cast(GraphitiConfigStatus, status)
        return _graphiti_not_configured(config_name)

    def _enter_degraded(self, component: str, reason: str, scope: list[str]) -> None:
        enter = getattr(self._degraded_mode_service, "enter", None)
        if not callable(enter):
            return
        try:
            enter(
                component=component,
                severity="medium",
                reason=reason,
                dependencies=[str(self._configured_adapter)],
                fallbacks_active=["local_baseline"] if self._fallback_reason else [],
                constraints=["graph_recall_degraded"],
                trace_id=scope[0] if scope else None,
            )
        except Exception:
            return

    def sync_graphiti(self, request: GraphitiSyncRequest) -> GraphitiSyncResponse:
        """Policy-gate and sync graph records to Graphiti."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_type="graphiti_sync",
            resource_id=request.config_name,
            risk_level="medium" if request.limit > 100000 else "low",
            scope=request.scope,
            context={
                "operation": "graphiti_sync",
                "limit": request.limit,
                "dry_run": request.dry_run,
                "force": request.force,
            },
        )
        adapter = self._graphiti_adapter or self._adapter
        sync = getattr(adapter, "sync", None)
        if not callable(sync):
            raise GraphMemoryUnavailable("graphiti_not_configured")
        try:
            return cast(GraphitiSyncResponse, sync(request))
        except RuntimeError as exc:
            raise GraphMemoryUnavailable(str(exc)) from exc

    def add_graphiti_episode(
        self,
        request: GraphitiEpisodeRequest,
    ) -> GraphitiEpisodeResponse:
        """Policy-gate and add a Graphiti episode."""
        self._ensure_allowed(
            action_type="memory.write",
            resource_type="graphiti_episode",
            resource_id=request.episode_id or request.source_id,
            risk_level="low",
            scope=request.scope,
            context={
                "operation": "graphiti_episode",
                "source_type": request.source_type,
                "source_id": request.source_id,
            },
        )
        adapter = self._graphiti_adapter or self._adapter
        add_episode = getattr(adapter, "add_episode", None)
        if not callable(add_episode):
            raise GraphMemoryUnavailable("graphiti_not_configured")
        try:
            return cast(GraphitiEpisodeResponse, add_episode(request))
        except RuntimeError as exc:
            raise GraphMemoryUnavailable(str(exc)) from exc

    @property
    def active_adapter_name(self) -> str:
        """Return selected graph adapter name."""
        return getattr(self._adapter, "adapter_name", "unknown")

    @property
    def fallback_reason(self) -> str | None:
        """Return graph adapter fallback reason."""
        return self._fallback_reason

    def _authorize_retrieve(
        self,
        *,
        resource_type: str,
        resource_id: str | None,
        scope: list[str],
        context: dict[str, object],
    ) -> None:
        self._ensure_allowed(
            action_type="memory.retrieve",
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level="low",
            scope=scope,
            context=context,
        )

    def _ensure_allowed(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        context: dict[str, object],
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_type}-{resource_id or 'root'}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )
        if not decision.allow:
            raise GraphMemoryPolicyDenied(decision)


def _risk_from_sensitivity(sensitivity: str) -> str:
    normalized = sensitivity.lower()
    if normalized in {"high", "critical"}:
        return "high"
    if normalized == "medium":
        return "medium"
    return "low"


def _normalized_adapter_name(value: str) -> str:
    return value.replace("-", "_")


def _graphiti_not_configured(config_name: str) -> GraphitiConfigStatus:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return GraphitiConfigStatus(
        graphiti_config_id=f"graphiti-{config_name}",
        config_name=config_name,
        adapter_name="graphiti",
        status="unavailable",
        backend_type="unknown",
        endpoint_ref=None,
        available=False,
        reason="graphiti_not_configured",
        metadata={},
        created_at=now,
        updated_at=now,
        last_health_check_at=None,
    )
