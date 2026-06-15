"""Temporal graph memory API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.audit.repository import AuditRepository
from aion_brain.config import get_settings
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
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.memory.graph_base import GraphMemoryAdapter
from aion_brain.memory.graph_service import (
    GraphMemoryPolicyDenied,
    GraphMemoryService,
    GraphMemoryUnavailable,
)
from aion_brain.memory.graphiti_adapter import GraphitiGraphMemoryAdapter
from aion_brain.memory.graphiti_compat import GraphitiCompat
from aion_brain.memory.graphiti_repository import GraphitiRepository
from aion_brain.memory.in_memory_graph_adapter import InMemoryGraphAdapter
from aion_brain.memory.postgres_graph_adapter import PostgresGraphAdapter
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.telemetry.visual import build_graph_memory_activation_event

router = APIRouter(prefix="/brain/memory/graph", tags=["graph-memory"])


class GraphNeighborsRequest(BaseModel):
    """Graph neighbors request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(min_length=1)
    max_depth: int = Field(default=2, ge=1, le=5)
    limit: int = Field(default=25, ge=1, le=100)


class GraphNodeDeleteResponse(BaseModel):
    """Graph node deletion response."""

    model_config = ConfigDict(extra="forbid")

    deleted: bool
    node_id: str


class GraphEdgeDeleteResponse(BaseModel):
    """Graph edge deletion response."""

    model_config = ConfigDict(extra="forbid")

    deleted: bool
    edge_id: str


def get_graph_memory_service() -> GraphMemoryService:
    """Create the configured graph memory service."""
    settings = get_settings()
    return get_cached_graph_memory_service(
        settings.database_url,
        settings.opa_url,
        settings.default_graph_memory_adapter,
        settings.graphiti_enabled,
        settings.graphiti_config_name,
        settings.graphiti_backend_type,
        settings.graphiti_endpoint_ref,
        settings.graphiti_fail_open_to_postgres_graph,
        settings.model_gateway_enabled,
    )


@lru_cache
def get_cached_graph_memory_service(
    database_url: str,
    opa_url: str,
    default_graph_memory_adapter: str = "postgres_graph",
    graphiti_enabled: bool = False,
    graphiti_config_name: str = "default",
    graphiti_backend_type: str = "unknown",
    graphiti_endpoint_ref: str | None = None,
    graphiti_fail_open_to_postgres_graph: bool = True,
    model_gateway_enabled: bool = False,
) -> GraphMemoryService:
    """Return a cached graph memory service."""
    policy_adapter = OPAAdapter(opa_url)
    postgres_adapter = PostgresGraphAdapter(database_url=database_url)
    graphiti_adapter = GraphitiGraphMemoryAdapter(
        graphiti_repository=GraphitiRepository(database_url),
        postgres_graph_adapter=postgres_adapter,
        telemetry_service=AuditRepository(database_url),
        compat=GraphitiCompat(),
        enabled=graphiti_enabled,
        config_name=graphiti_config_name,
        backend_type=graphiti_backend_type,
        endpoint_ref=graphiti_endpoint_ref,
        fail_open_to_postgres_graph=graphiti_fail_open_to_postgres_graph,
        model_gateway_enabled=model_gateway_enabled,
    )
    selected = default_graph_memory_adapter.replace("-", "_")
    fallback_reason: str | None = None
    adapter: GraphMemoryAdapter
    if selected == "in_memory":
        adapter = InMemoryGraphAdapter()
    elif selected == "graphiti":
        graphiti_status = graphiti_adapter.status(graphiti_config_name)
        if graphiti_status.available:
            adapter = graphiti_adapter
        elif graphiti_fail_open_to_postgres_graph:
            fallback_reason = graphiti_status.reason or "graphiti_unavailable"
            adapter = postgres_adapter
        else:
            adapter = graphiti_adapter
    else:
        adapter = postgres_adapter
    return GraphMemoryService(
        adapter=adapter,
        policy_adapter=policy_adapter,
        configured_adapter=default_graph_memory_adapter,
        fallback_reason=fallback_reason,
        graphiti_adapter=graphiti_adapter,
    )


def get_graph_telemetry_repository() -> AuditRepository:
    """Create the configured telemetry repository."""
    settings = get_settings()
    return get_cached_graph_telemetry_repository(settings.database_url)


@lru_cache
def get_cached_graph_telemetry_repository(database_url: str) -> AuditRepository:
    """Return a cached telemetry repository."""
    return AuditRepository(database_url)


@router.get("/adapters", response_model=list[GraphMemoryAdapterStatus])
def list_graph_adapters(
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> list[GraphMemoryAdapterStatus]:
    """Return graph memory adapter statuses."""
    try:
        return service.adapter_statuses(actor_context.security_scope)
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/graphiti/status", response_model=GraphitiConfigStatus)
def get_graphiti_status(
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    config_name: str = "default",
) -> GraphitiConfigStatus:
    """Return Graphiti adapter config status."""
    try:
        return service.graphiti_status(config_name, actor_context.security_scope)
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/graphiti/sync", response_model=GraphitiSyncResponse)
def sync_graphiti(
    request: GraphitiSyncRequest,
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
) -> GraphitiSyncResponse:
    """Sync canonical graph memory into Graphiti."""
    try:
        return service.sync_graphiti(request)
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except GraphMemoryUnavailable as exc:
        raise _graph_unavailable(exc) from exc


@router.post("/graphiti/episodes", response_model=GraphitiEpisodeResponse)
def add_graphiti_episode(
    request: GraphitiEpisodeRequest,
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
) -> GraphitiEpisodeResponse:
    """Add a temporal Graphiti episode."""
    try:
        return service.add_graphiti_episode(request)
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except GraphMemoryUnavailable as exc:
        raise _graph_unavailable(exc) from exc


@router.post("/nodes", response_model=GraphUpsertResponse)
def upsert_graph_node(
    node: GraphNode,
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
    telemetry_repository: Annotated[
        AuditRepository,
        Depends(get_graph_telemetry_repository),
    ],
) -> GraphUpsertResponse:
    """Upsert a temporal graph node."""
    try:
        response = service.upsert_node(node)
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    _emit_activation(
        telemetry_repository,
        object_id=node.node_id,
        intensity=node.confidence,
        payload={"object_type": "node", "node_type": node.node_type},
    )
    return response


@router.post("/edges", response_model=GraphUpsertResponse)
def upsert_graph_edge(
    edge: GraphEdge,
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
    telemetry_repository: Annotated[
        AuditRepository,
        Depends(get_graph_telemetry_repository),
    ],
) -> GraphUpsertResponse:
    """Upsert a temporal graph edge."""
    try:
        response = service.upsert_edge(edge)
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    _emit_activation(
        telemetry_repository,
        object_id=edge.edge_id,
        intensity=edge.confidence,
        edge_from=edge.from_node_id,
        edge_to=edge.to_node_id,
        payload={"object_type": "edge", "edge_type": edge.edge_type},
    )
    return response


@router.get("/nodes/{node_id}", response_model=GraphNode)
def get_graph_node(
    node_id: str,
    scope: Annotated[list[str], Query()],
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
) -> GraphNode:
    """Return a graph node."""
    try:
        node = service.get_node(node_id, _parse_scope(scope))
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if node is None:
        raise HTTPException(status_code=404, detail="graph_node_not_found")
    return node


@router.get("/edges/{edge_id}", response_model=GraphEdge)
def get_graph_edge(
    edge_id: str,
    scope: Annotated[list[str], Query()],
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
) -> GraphEdge:
    """Return a graph edge."""
    try:
        edge = service.get_edge(edge_id, _parse_scope(scope))
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if edge is None:
        raise HTTPException(status_code=404, detail="graph_edge_not_found")
    return edge


@router.post("/query", response_model=GraphQueryResult)
def query_graph_memory(
    query: GraphQuery,
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
) -> GraphQueryResult:
    """Query graph memory."""
    try:
        return service.query_graph(query)
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/neighbors/{node_id}", response_model=GraphQueryResult)
def get_graph_neighbors(
    node_id: str,
    request: GraphNeighborsRequest,
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
) -> GraphQueryResult:
    """Return graph neighbors."""
    try:
        return service.neighbors(
            node_id,
            request.scope,
            max_depth=request.max_depth,
            limit=request.limit,
        )
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.delete("/nodes/{node_id}", response_model=GraphNodeDeleteResponse)
def delete_graph_node(
    node_id: str,
    scope: Annotated[list[str], Query()],
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
) -> GraphNodeDeleteResponse:
    """Soft-delete a graph node."""
    try:
        deleted = service.delete_node(node_id, _parse_scope(scope))
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="graph_node_not_found")
    return GraphNodeDeleteResponse(deleted=True, node_id=node_id)


@router.delete("/edges/{edge_id}", response_model=GraphEdgeDeleteResponse)
def delete_graph_edge(
    edge_id: str,
    scope: Annotated[list[str], Query()],
    service: Annotated[GraphMemoryService, Depends(get_graph_memory_service)],
) -> GraphEdgeDeleteResponse:
    """Soft-delete a graph edge."""
    try:
        deleted = service.delete_edge(edge_id, _parse_scope(scope))
    except GraphMemoryPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="graph_edge_not_found")
    return GraphEdgeDeleteResponse(deleted=True, edge_id=edge_id)


def _parse_scope(raw_scope: list[str]) -> list[str]:
    values: list[str] = []
    for item in raw_scope:
        values.extend(part.strip() for part in item.split(",") if part.strip())
    if not values:
        raise HTTPException(status_code=422, detail="scope_required")
    return values


def _emit_activation(
    repository: AuditRepository,
    *,
    object_id: str,
    intensity: float,
    edge_from: str | None = None,
    edge_to: str | None = None,
    payload: dict[str, object] | None = None,
) -> None:
    event = build_graph_memory_activation_event(
        object_id=object_id,
        intensity=intensity,
        edge_from=edge_from,
        edge_to=edge_to,
        payload=payload,
    )
    try:
        repository.save_visual_telemetry(event.trace_id, [event])
    except Exception:
        return


def _policy_denied(exc: GraphMemoryPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={
            "reason": exc.decision.reason,
            "decision_id": exc.decision.decision_id,
            "constraints": exc.decision.constraints,
        },
    )


def _graph_unavailable(exc: GraphMemoryUnavailable) -> HTTPException:
    return HTTPException(status_code=503, detail={"reason": exc.reason})
