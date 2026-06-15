"""Compatibility boundary for optional Graphiti package APIs."""

from __future__ import annotations

import importlib
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.graph import (
    GraphEdge,
    GraphitiConfigStatus,
    GraphitiEpisodeRequest,
    GraphitiEpisodeResponse,
    GraphNode,
    GraphQuery,
    GraphQueryResult,
    GraphUpsertResponse,
)


class GraphitiCompat:
    """Load and adapt optional Graphiti APIs without leaking vendor objects."""

    def __init__(self) -> None:
        self._module: Any | None = None
        self._reason: str | None = None

    def is_available(self) -> bool:
        """Return whether a graphiti module can be imported."""
        return self._load_module() is not None

    def availability_reason(self) -> str | None:
        """Return why Graphiti is unavailable, if known."""
        self._load_module()
        return self._reason

    def requires_llm(self) -> bool:
        """Return whether the loaded Graphiti API declares an LLM requirement."""
        module = self._load_module()
        if module is None:
            return False
        value = getattr(module, "REQUIRES_LLM", False)
        if bool(value):
            return True
        client_class = _first_present(module, ("Graphiti", "GraphitiClient", "Client"))
        return bool(getattr(client_class, "REQUIRES_LLM", False))

    def create_client(self, config: GraphitiConfigStatus) -> Any:
        """Create a Graphiti client through known constructor shapes."""
        module = self._require_module()
        if self.requires_llm():
            raise RuntimeError("graphiti_llm_disabled")
        client_class = _first_present(module, ("Graphiti", "GraphitiClient", "Client"))
        if client_class is None:
            raise RuntimeError("graphiti_api_incompatible:client_class_missing")
        attempts: tuple[tuple[tuple[Any, ...], dict[str, Any]], ...] = (
            (
                (),
                {
                    "backend_type": config.backend_type,
                    "endpoint": config.endpoint_ref,
                    "llm_client": None,
                },
            ),
            ((), {"backend_type": config.backend_type, "endpoint": config.endpoint_ref}),
            ((), {"endpoint": config.endpoint_ref}),
            ((config.endpoint_ref,), {}) if config.endpoint_ref else ((), {}),
            ((), {}),
        )
        for args, kwargs in attempts:
            try:
                return client_class(*args, **kwargs)
            except TypeError:
                continue
        raise RuntimeError("graphiti_api_incompatible:client_constructor")

    def add_episode(
        self,
        client: Any,
        episode: GraphitiEpisodeRequest,
    ) -> GraphitiEpisodeResponse:
        """Add an episode through known Graphiti API shapes."""
        method = _first_callable(client, ("add_episode", "add_episode_sync", "ingest_episode"))
        if method is None:
            raise RuntimeError("graphiti_api_incompatible:add_episode_missing")
        episode_id = episode.episode_id or f"episode-{uuid4().hex}"
        payload = {
            "episode_id": episode_id,
            "trace_id": episode.trace_id,
            "source_type": episode.source_type,
            "source_id": episode.source_id,
            "content": episode.content,
            "scope": episode.scope,
            "observed_at": episode.observed_at,
            "metadata": episode.metadata,
        }
        try:
            raw = method(payload)
        except TypeError:
            raw = method(episode.content, metadata=payload)
        return _episode_response(raw, episode_id)

    def upsert_node(self, client: Any, node: GraphNode) -> GraphUpsertResponse:
        """Upsert a node through known Graphiti API shapes."""
        method = _first_callable(client, ("upsert_node", "add_node", "save_node"))
        if method is None:
            raise RuntimeError("graphiti_api_incompatible:upsert_node_missing")
        raw = _call_with_model(method, node)
        return _upsert_response(raw, "node", node.node_id)

    def upsert_edge(self, client: Any, edge: GraphEdge) -> GraphUpsertResponse:
        """Upsert an edge through known Graphiti API shapes."""
        method = _first_callable(client, ("upsert_edge", "add_edge", "save_edge"))
        if method is None:
            raise RuntimeError("graphiti_api_incompatible:upsert_edge_missing")
        raw = _call_with_model(method, edge)
        return _upsert_response(raw, "edge", edge.edge_id)

    def query(self, client: Any, query: GraphQuery) -> GraphQueryResult:
        """Query Graphiti and coerce results to AION graph contracts."""
        method = _first_callable(client, ("query_graph", "search", "search_nodes", "query"))
        if method is None:
            raise RuntimeError("graphiti_api_incompatible:query_missing")
        try:
            raw = method(query.model_dump(mode="python"))
        except TypeError:
            raw = method(query.query, scope=query.scope, limit=query.limit)
        return _query_result(raw)

    def close(self, client: Any) -> None:
        """Close a Graphiti client when supported."""
        method = _first_callable(client, ("close", "disconnect"))
        if method is not None:
            method()

    def _load_module(self) -> Any | None:
        if self._module is not None:
            return self._module
        try:
            self._module = importlib.import_module("graphiti_core")
            self._reason = None
            return self._module
        except Exception:
            try:
                self._module = importlib.import_module("graphiti")
                self._reason = None
                return self._module
            except Exception:
                self._reason = "graphiti_package_unavailable"
                return None

    def _require_module(self) -> Any:
        module = self._load_module()
        if module is None:
            raise RuntimeError("graphiti_package_unavailable")
        return module


def _first_present(target: Any, names: tuple[str, ...]) -> Any | None:
    for name in names:
        value = getattr(target, name, None)
        if value is not None:
            return value
    return None


def _first_callable(target: Any, names: tuple[str, ...]) -> Any | None:
    for name in names:
        value = getattr(target, name, None)
        if callable(value):
            return value
    return None


def _call_with_model(method: Any, value: GraphNode | GraphEdge) -> Any:
    try:
        return method(value)
    except TypeError:
        return method(value.model_dump(mode="python"))


def _upsert_response(raw: Any, object_type: str, object_id: str) -> GraphUpsertResponse:
    if isinstance(raw, GraphUpsertResponse):
        return raw
    if isinstance(raw, dict):
        return GraphUpsertResponse(
            upserted=bool(raw.get("upserted", raw.get("ok", True))),
            object_type=str(raw.get("object_type", object_type)),
            object_id=str(raw.get("object_id", raw.get("id", object_id))),
            reason=cast(str | None, raw.get("reason")),
        )
    return GraphUpsertResponse(
        upserted=True,
        object_type=object_type,
        object_id=object_id,
        reason=None,
    )


def _episode_response(raw: Any, episode_id: str) -> GraphitiEpisodeResponse:
    if isinstance(raw, GraphitiEpisodeResponse):
        return raw
    if isinstance(raw, dict):
        return GraphitiEpisodeResponse(
            added=bool(raw.get("added", raw.get("ok", True))),
            episode_id=str(raw.get("episode_id", raw.get("id", episode_id))),
            status=str(raw.get("status", "added")),
            reason=cast(str | None, raw.get("reason")),
            metadata=dict(raw.get("metadata", {})),
        )
    return GraphitiEpisodeResponse(
        added=True,
        episode_id=episode_id,
        status="added",
        reason=None,
        metadata={},
    )


def _query_result(raw: Any) -> GraphQueryResult:
    if isinstance(raw, GraphQueryResult):
        return raw
    if isinstance(raw, dict):
        nodes = [_coerce_node(item) for item in raw.get("nodes", [])]
        edges = [_coerce_edge(item) for item in raw.get("edges", [])]
        return GraphQueryResult(
            nodes=nodes,
            edges=edges,
            score=float(raw.get("score", 1.0 if nodes or edges else 0.0)),
            retrieval_source="graph",
            adapter_name="graphiti",
            metadata=dict(raw.get("metadata", {})),
        )
    raise RuntimeError("graphiti_api_incompatible:query_result")


def _coerce_node(value: Any) -> GraphNode:
    if isinstance(value, GraphNode):
        return value
    if isinstance(value, dict):
        payload = dict(value)
        now = datetime.now(UTC)
        payload.setdefault("node_type", "unknown")
        payload.setdefault("label", payload.get("node_id", "node"))
        payload.setdefault("owner_scope", ["workspace:main"])
        payload.setdefault("properties", {})
        payload.setdefault("source_event_id", None)
        payload.setdefault("confidence", 0.5)
        payload.setdefault("sensitivity", "low")
        payload.setdefault("valid_from", None)
        payload.setdefault("valid_to", None)
        payload.setdefault("observed_at", now)
        return GraphNode(**payload)
    raise RuntimeError("graphiti_api_incompatible:node_result")


def _coerce_edge(value: Any) -> GraphEdge:
    if isinstance(value, GraphEdge):
        return value
    if isinstance(value, dict):
        payload = dict(value)
        now = datetime.now(UTC)
        payload.setdefault("edge_type", "related_to")
        payload.setdefault("owner_scope", ["workspace:main"])
        payload.setdefault("properties", {})
        payload.setdefault("source_event_id", None)
        payload.setdefault("confidence", 0.5)
        payload.setdefault("sensitivity", "low")
        payload.setdefault("valid_from", None)
        payload.setdefault("valid_to", None)
        payload.setdefault("observed_at", now)
        return GraphEdge(**payload)
    raise RuntimeError("graphiti_api_incompatible:edge_result")
