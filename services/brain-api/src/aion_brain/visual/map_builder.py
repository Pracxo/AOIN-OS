"""Deterministic Brain Map projection builder."""

from collections.abc import Mapping
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Protocol, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.visual import (
    BrainMap,
    BrainMapRequest,
    BrainPulse,
    BrainVisualCluster,
    BrainVisualClusterType,
    BrainVisualEdge,
    BrainVisualEdgeType,
    BrainVisualNode,
    VisualTelemetryQuery,
)
from aion_brain.visual.intensity import (
    apply_time_decay,
    clamp_intensity,
    node_type_from_telemetry,
    status_from_event_type,
)


class TelemetryRepository(Protocol):
    """Telemetry read boundary used by the map builder."""

    def query_telemetry(self, query: VisualTelemetryQuery) -> list[VisualTelemetryEvent]:
        """Return matching telemetry events."""
        ...


SEQUENCE_EDGES: dict[tuple[str, str], BrainVisualEdgeType] = {
    ("event", "intent"): "classified_as",
    ("intent", "context"): "compiled_into",
    ("context", "retrieval"): "retrieved",
    ("context", "memory"): "retrieved",
    ("context", "evidence"): "retrieved",
    ("context", "reasoning"): "reasoned_over",
    ("reasoning", "plan"): "planned",
    ("plan", "policy"): "authorized_by",
    ("policy", "execution"): "executed_as",
    ("execution", "evaluation"): "evaluated_by",
    ("evaluation", "learning"): "learned_from",
    ("learning", "reflection"): "reflected_into",
    ("candidate", "skill"): "promoted_to",
    ("evidence", "claim"): "grounded_by",
}

CLUSTER_FAMILIES: dict[BrainVisualClusterType, set[str]] = {
    "memory": {"memory", "graph", "evidence", "chunk", "claim"},
    "reasoning": {"intent", "context", "retrieval", "reasoning", "model", "plan"},
    "execution": {
        "execution",
        "step",
        "approval",
        "capability",
        "module",
        "runtime",
        "risk",
        "guardrail",
        "governance",
        "conflict",
        "compaction",
        "retention",
        "policy",
    },
    "lifecycle": {"goal", "task", "schedule"},
    "learning": {
        "evaluation",
        "learning",
        "reflection",
        "candidate",
        "skill",
        "regression",
        "eval",
    },
    "identity": {"actor", "workspace", "permission", "scope"},
    "trace": {"trace", "telemetry", "snapshot", "replay"},
}


class BrainMapBuilder:
    """Convert canonical visual telemetry into a frontend-agnostic Brain Map."""

    def __init__(self, telemetry_repository: TelemetryRepository, settings: Settings) -> None:
        self._telemetry_repository = telemetry_repository
        self._settings = settings

    def build(self, request: BrainMapRequest) -> BrainMap:
        """Build nodes, edges, pulses, and clusters from telemetry."""
        query = VisualTelemetryQuery(
            trace_id=request.trace_id,
            workspace_id=request.workspace_id,
            scope=request.scope,
            node_types=request.node_types,
            event_types=request.event_types,
            since=request.since,
            until=request.until,
            limit=min(request.limit, 1000),
        )
        events = sorted(
            self._telemetry_repository.query_telemetry(query),
            key=lambda item: item.created_at,
        )
        now = datetime.now(UTC)
        nodes = self._build_nodes(events, request, now)
        edges = self._build_edges(events, nodes) if request.include_edges else []
        pulses = self._build_pulses(events, request.decay, now) if request.include_pulses else []
        clusters = self._build_clusters(nodes) if request.include_clusters else []
        return BrainMap(
            map_id=f"map-{uuid4().hex}",
            trace_id=request.trace_id,
            workspace_id=request.workspace_id,
            nodes=nodes,
            edges=edges,
            pulses=pulses,
            clusters=clusters,
            stats={
                "node_count": len(nodes),
                "edge_count": len(edges),
                "pulse_count": len(pulses),
                "cluster_count": len(clusters),
                "telemetry_event_count": len(events),
            },
            created_at=now,
        )

    def _build_nodes(
        self,
        events: list[VisualTelemetryEvent],
        request: BrainMapRequest,
        now: datetime,
    ) -> list[BrainVisualNode]:
        nodes: dict[tuple[str, str], BrainVisualNode] = {}
        for event in events:
            node_type = node_type_from_telemetry(event.node_type, event.event_type)
            intensity = (
                apply_time_decay(
                    event.intensity,
                    event.created_at,
                    now,
                    self._settings.visual_intensity_half_life_seconds,
                )
                if request.decay
                else event.intensity
            )
            status = status_from_event_type(event.event_type)
            if status == "active" and intensity < 0.1:
                status = "dormant"
            key = (event.node_id, node_type)
            existing = nodes.get(key)
            if existing is None:
                nodes[key] = BrainVisualNode(
                    node_id=event.node_id,
                    node_type=node_type,
                    label=_event_label(event),
                    status=status,
                    intensity=clamp_intensity(intensity),
                    owner_scope=_event_scope(event, request.scope),
                    trace_refs=[event.trace_id] if event.trace_id else [],
                    source_refs=_source_refs(event.payload),
                    metadata={"event_types": [event.event_type], **_safe_metadata(event.payload)},
                    first_seen_at=event.created_at,
                    last_seen_at=event.created_at,
                )
                continue
            trace_refs = _unique([*existing.trace_refs, event.trace_id])
            source_refs = _unique([*existing.source_refs, *_source_refs(event.payload)])
            event_types = _unique(
                [*cast(list[str], existing.metadata.get("event_types", [])), event.event_type]
            )
            nodes[key] = existing.model_copy(
                update={
                    "intensity": max(existing.intensity, clamp_intensity(intensity)),
                    "status": _stronger_status(existing.status, status),
                    "trace_refs": trace_refs,
                    "source_refs": source_refs,
                    "metadata": {**existing.metadata, "event_types": event_types},
                    "last_seen_at": max(
                        existing.last_seen_at or event.created_at,
                        event.created_at,
                    ),
                }
            )
        return sorted(nodes.values(), key=lambda node: (node.node_type, node.node_id))

    def _build_edges(
        self,
        events: list[VisualTelemetryEvent],
        nodes: list[BrainVisualNode],
    ) -> list[BrainVisualEdge]:
        node_types = {node.node_id: node.node_type for node in nodes}
        edges: dict[tuple[str, str, str], BrainVisualEdge] = {}
        by_trace: dict[str, list[VisualTelemetryEvent]] = {}
        for event in events:
            by_trace.setdefault(event.trace_id, []).append(event)
            if event.edge_from and event.edge_to and event.edge_from != event.edge_to:
                self._add_edge(edges, event.edge_from, event.edge_to, "linked_to", event)
        for trace_events in by_trace.values():
            ordered = sorted(trace_events, key=lambda item: item.created_at)
            for previous, current in zip(ordered, ordered[1:], strict=False):
                if previous.node_id == current.node_id:
                    continue
                self._add_edge(edges, previous.node_id, current.node_id, "triggered", current)
                edge_type = SEQUENCE_EDGES.get(
                (
                    node_types.get(previous.node_id, "unknown"),
                    node_types.get(current.node_id, "unknown"),
                )
                )
                if edge_type is not None:
                    current_status = status_from_event_type(current.event_type)
                    if current_status == "blocked":
                        edge_type = "blocked_by"
                    self._add_edge(edges, previous.node_id, current.node_id, edge_type, current)
            self._add_cognitive_sequence_edges(edges, ordered, node_types)
        return sorted(edges.values(), key=lambda edge: edge.edge_id)

    def _add_cognitive_sequence_edges(
        self,
        edges: dict[tuple[str, str, str], BrainVisualEdge],
        events: list[VisualTelemetryEvent],
        node_types: Mapping[str, str],
    ) -> None:
        by_type: dict[str, list[VisualTelemetryEvent]] = {}
        for event in events:
            by_type.setdefault(node_types.get(event.node_id, "unknown"), []).append(event)
        for (source_type, target_type), edge_type in SEQUENCE_EDGES.items():
            sources = by_type.get(source_type, [])
            targets = by_type.get(target_type, [])
            if not sources or not targets:
                continue
            source = sources[-1]
            target = targets[0]
            if source.node_id == target.node_id:
                continue
            if status_from_event_type(target.event_type) == "blocked":
                edge_type = "blocked_by"
            self._add_edge(edges, source.node_id, target.node_id, edge_type, target)

    def _add_edge(
        self,
        edges: dict[tuple[str, str, str], BrainVisualEdge],
        source: str,
        target: str,
        edge_type: BrainVisualEdgeType,
        event: VisualTelemetryEvent,
    ) -> None:
        key = (source, target, edge_type)
        existing = edges.get(key)
        if existing is None:
            edges[key] = BrainVisualEdge(
                edge_id=_stable_id("edge", *key),
                edge_type=edge_type,
                from_node_id=source,
                to_node_id=target,
                weight=event.intensity,
                status=status_from_event_type(event.event_type),
                trace_refs=[event.trace_id],
                metadata={"event_types": [event.event_type]},
                first_seen_at=event.created_at,
                last_seen_at=event.created_at,
            )
            return
        edges[key] = existing.model_copy(
            update={
                "weight": max(existing.weight, event.intensity),
                "trace_refs": _unique([*existing.trace_refs, event.trace_id]),
                    "last_seen_at": max(
                        existing.last_seen_at or event.created_at,
                        event.created_at,
                    ),
            }
        )

    def _build_pulses(
        self,
        events: list[VisualTelemetryEvent],
        decay: bool,
        now: datetime,
    ) -> list[BrainPulse]:
        pulses = []
        for event in events:
            intensity = (
                apply_time_decay(
                    event.intensity,
                    event.created_at,
                    now,
                    self._settings.visual_intensity_half_life_seconds,
                )
                if decay
                else event.intensity
            )
            pulses.append(
                BrainPulse(
                    pulse_id=f"pulse-{event.telemetry_id}",
                    trace_id=event.trace_id,
                    event_type=event.event_type,
                    node_id=event.node_id,
                    edge_id=None,
                    intensity=intensity,
                    duration_ms=max(100, min(10000, int(250 + intensity * 1750))),
                    payload=_safe_metadata(event.payload),
                    created_at=event.created_at,
                )
            )
        return pulses

    def _build_clusters(self, nodes: list[BrainVisualNode]) -> list[BrainVisualCluster]:
        clusters = []
        for cluster_type, types in CLUSTER_FAMILIES.items():
            members = [node for node in nodes if node.node_type in types]
            if not members:
                continue
            clusters.append(
                BrainVisualCluster(
                    cluster_id=f"cluster-{cluster_type}",
                    cluster_type=cluster_type,
                    label=f"{cluster_type.title()} cluster",
                    node_ids=[node.node_id for node in members],
                    intensity=sum(node.intensity for node in members) / len(members),
                    metadata={"node_types": sorted({node.node_type for node in members})},
                )
            )
        return clusters


def _event_label(event: VisualTelemetryEvent) -> str:
    for key in ("label", "title", "name"):
        value = event.payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return event.node_id


def _event_scope(event: VisualTelemetryEvent, fallback: list[str]) -> list[str]:
    for key in ("owner_scope", "security_scope", "resolved_security_scope"):
        value = event.payload.get(key)
        if isinstance(value, list) and value:
            return [str(item) for item in value]
    return fallback


def _source_refs(payload: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("source_ref", "evidence_ref", "source_refs", "evidence_refs"):
        value = payload.get(key)
        if isinstance(value, str):
            refs.append(value)
        elif isinstance(value, list):
            refs.extend(str(item) for item in value)
    return _unique(refs)


def _safe_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    blocked = {"password", "secret", "token", "api_key", "private_key", "authorization"}
    return {
        str(key): value
        for key, value in payload.items()
        if not any(term in str(key).lower().replace("-", "_") for term in blocked)
    }


def _stronger_status(current: str, new: str) -> str:
    rank = {"failed": 5, "blocked": 4, "active": 3, "completed": 2, "dormant": 1, "unknown": 0}
    return new if rank.get(new, 0) > rank.get(current, 0) else current


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("|".join(parts).encode()).hexdigest()[:20]
    return f"{prefix}-{digest}"
