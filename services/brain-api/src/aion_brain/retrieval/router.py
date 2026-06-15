"""AION Retrieval Router."""

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.contracts.evidence import EvidenceSearchRequest, EvidenceSearchResult
from aion_brain.contracts.graph import GraphQuery
from aion_brain.contracts.memory import MemoryRetrievalRequest, SemanticMemoryQuery
from aion_brain.contracts.memory_governance import MemoryGovernanceEvaluationRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.retrieval import (
    RetrievalRequest,
    RetrievalResult,
    RetrievalSource,
    RetrievedContextItem,
)
from aion_brain.contracts.skills import SkillMatchRequest, SkillMatchResult
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.contracts.working_memory import WorkingMemoryQuery, WorkingMemorySlot
from aion_brain.policy.base import PolicyAdapter
from aion_brain.retrieval.repository import RetrievalRepository
from aion_brain.retrieval.scoring import content_hash_key, rank_items


class RetrievalRouter:
    """Policy-gated router for deterministic context retrieval."""

    def __init__(
        self,
        *,
        policy_adapter: PolicyAdapter,
        memory_service: object | None = None,
        semantic_memory_service: object | None = None,
        graph_memory_service: object | None = None,
        capability_registry: object | None = None,
        skill_matcher: object | None = None,
        trace_repository: object | None = None,
        evidence_service: object | None = None,
        working_memory_service: object | None = None,
        telemetry_service: object | None = None,
        retrieval_repository: RetrievalRepository | object | None = None,
        memory_governance_engine: object | None = None,
        memory_decay_service: object | None = None,
    ) -> None:
        self._policy_adapter = policy_adapter
        self._memory_service = memory_service
        self._semantic_memory_service = semantic_memory_service
        self._graph_memory_service = graph_memory_service
        self._capability_registry = capability_registry
        self._skill_matcher = skill_matcher
        self._trace_repository = trace_repository
        self._evidence_service = evidence_service
        self._working_memory_service = working_memory_service
        self._telemetry_service = telemetry_service
        self._retrieval_repository = retrieval_repository
        self._memory_governance_engine = memory_governance_engine
        self._memory_decay_service = memory_decay_service

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """Retrieve, score, deduplicate, persist, and emit telemetry."""
        constraints: list[str] = []
        if not self._authorize_global(request):
            result = _empty_result(
                request,
                constraints=["policy:retrieval_denied", "source_blocked_by_policy:all"],
            )
            self._persist(request, result)
            return result

        candidates: list[RetrievedContextItem] = []
        for source in request.requested_sources:
            if not self._source_enabled(source, request):
                continue
            if not self._authorize_source(source, request):
                constraints.append(f"source_blocked_by_policy:{source}")
                continue
            try:
                candidates.extend(self._collect_source(source, request))
            except Exception:
                constraints.append(f"source_unavailable:{source}")

        deduped = _deduplicate(candidates)
        ranked = _apply_attention_boosts(request, rank_items(request.query, deduped))
        ranked, governance_constraints = self._apply_memory_governance(request, ranked)
        constraints.extend(governance_constraints)
        filtered = [
            item
            for item in ranked
            if request.min_score is None or item.score >= request.min_score
        ][: request.limit]
        result = RetrievalResult(
            retrieval_id=request.retrieval_id,
            query=request.query,
            items=filtered,
            source_counts=_source_counts(filtered),
            constraints=constraints,
            created_at=datetime.now(UTC),
        )
        self._persist(request, result)
        self._emit_telemetry(request, result)
        return result

    def _collect_source(
        self,
        source: RetrievalSource,
        request: RetrievalRequest,
    ) -> list[RetrievedContextItem]:
        if source == "lexical_memory":
            return self._collect_lexical_memory(request)
        if source == "semantic_memory":
            return self._collect_semantic_memory(request)
        if source == "graph_memory":
            return self._collect_graph_memory(request)
        if source == "capability_registry":
            return self._collect_capabilities(request)
        if source == "skill_registry":
            return self._collect_skills(request)
        if source == "recent_trace":
            return self._collect_recent_traces(request)
        if source == "evidence_vault":
            return self._collect_evidence(request)
        if source == "working_memory":
            return self._collect_working_memory(request)
        return []

    def _collect_lexical_memory(self, request: RetrievalRequest) -> list[RetrievedContextItem]:
        retrieve = getattr(self._memory_service, "retrieve", None)
        if not callable(retrieve):
            return []
        records = retrieve(
            MemoryRetrievalRequest(
                query=request.query,
                scope=request.scope,
                limit=request.limit,
                memory_types=cast(Any, request.memory_types),
            )
        )
        return [
            RetrievedContextItem(
                item_id=f"lexical-memory-{record.memory_id}",
                source="lexical_memory",
                source_id=record.memory_id,
                title=record.memory_type,
                content=record.summary,
                score=0.7,
                confidence=record.confidence,
                sensitivity=record.sensitivity,
                owner_scope=record.owner_scope,
                memory_type=record.memory_type,
                capability_id=None,
                graph_node_ids=[],
                graph_edge_ids=[],
                trace_refs=[],
                evidence_ref=record.content_ref,
                metadata={
                    **record.metadata,
                    "created_at": record.created_at.isoformat(),
                    "expires_at": record.expires_at.isoformat() if record.expires_at else None,
                    "source_event_id": record.source_event_id,
                    "base_relevance": 0.7,
                },
            )
            for record in records
        ]

    def _collect_semantic_memory(self, request: RetrievalRequest) -> list[RetrievedContextItem]:
        retrieve = getattr(self._semantic_memory_service, "retrieve", None)
        if not callable(retrieve):
            return []
        results = retrieve(
            SemanticMemoryQuery(
                query=request.query,
                scope=request.scope,
                limit=request.limit,
                memory_types=cast(Any, request.memory_types),
                min_score=request.min_score,
            )
        )
        return [
            RetrievedContextItem(
                item_id=f"semantic-memory-{result.memory.memory_id}",
                source="semantic_memory",
                source_id=result.memory.memory_id,
                title=result.memory.memory_type,
                content=result.memory.summary,
                score=result.score,
                confidence=result.memory.confidence,
                sensitivity=result.memory.sensitivity,
                owner_scope=result.memory.owner_scope,
                memory_type=result.memory.memory_type,
                capability_id=None,
                graph_node_ids=[],
                graph_edge_ids=[],
                trace_refs=[],
                evidence_ref=result.memory.content_ref,
                metadata={
                    **result.memory.metadata,
                    **result.metadata,
                    "adapter_name": result.adapter_name,
                    "retrieval_source": result.retrieval_source,
                    "created_at": result.memory.created_at.isoformat(),
                    "expires_at": (
                        result.memory.expires_at.isoformat()
                        if result.memory.expires_at
                        else None
                    ),
                    "matched_terms": result.matched_terms,
                    "base_relevance": result.score,
                },
            )
            for result in results
        ]

    def _collect_graph_memory(self, request: RetrievalRequest) -> list[RetrievedContextItem]:
        query_graph = getattr(self._graph_memory_service, "query_graph", None)
        if not callable(query_graph):
            return []
        result = query_graph(
            GraphQuery(
                query=request.query,
                scope=request.scope,
                limit=request.limit,
            )
        )
        items = [
            RetrievedContextItem(
                item_id=f"graph-node-{node.node_id}",
                source="graph_memory",
                source_id=node.node_id,
                title=node.label,
                content=_node_content(node.label, node.properties),
                score=0.7,
                confidence=node.confidence,
                sensitivity=node.sensitivity,
                owner_scope=node.owner_scope,
                memory_type=None,
                capability_id=None,
                graph_node_ids=[node.node_id],
                graph_edge_ids=[],
                trace_refs=[],
                evidence_ref=node.source_event_id,
                metadata={
                    **result.metadata,
                    "adapter_name": result.adapter_name,
                    "retrieval_source": result.retrieval_source,
                    "node_type": node.node_type,
                    "observed_at": node.observed_at.isoformat(),
                    "base_relevance": 0.7,
                },
            )
            for node in result.nodes
        ]
        items.extend(
            RetrievedContextItem(
                item_id=f"graph-edge-{edge.edge_id}",
                source="graph_memory",
                source_id=edge.edge_id,
                title=edge.edge_type,
                content=f"{edge.edge_type}: {edge.from_node_id} -> {edge.to_node_id}",
                score=0.65,
                confidence=edge.confidence,
                sensitivity=edge.sensitivity,
                owner_scope=edge.owner_scope,
                memory_type=None,
                capability_id=None,
                graph_node_ids=[edge.from_node_id, edge.to_node_id],
                graph_edge_ids=[edge.edge_id],
                trace_refs=[],
                evidence_ref=edge.source_event_id,
                metadata={
                    **result.metadata,
                    "adapter_name": result.adapter_name,
                    "retrieval_source": result.retrieval_source,
                    "edge_type": edge.edge_type,
                    "observed_at": edge.observed_at.isoformat(),
                    "base_relevance": 0.65,
                },
            )
            for edge in result.edges
        )
        return items

    def _collect_skills(self, request: RetrievalRequest) -> list[RetrievedContextItem]:
        match = getattr(self._skill_matcher, "match", None)
        if not callable(match):
            return []
        results = match(
            SkillMatchRequest(
                query=request.query,
                scope=request.scope,
                limit=request.limit,
                risk_levels=[],
            )
        )
        if not isinstance(results, list):
            return []
        items: list[RetrievedContextItem] = []
        for result in results:
            if not isinstance(result, SkillMatchResult):
                continue
            skill = result.skill
            items.append(
                RetrievedContextItem(
                    item_id=f"skill-{skill.skill_id}",
                    source="skill_registry",
                    source_id=skill.skill_id,
                    title=skill.name,
                    content=_skill_content(skill.description, skill.procedure_steps),
                    score=result.score,
                    confidence=result.score,
                    sensitivity="low",
                    owner_scope=skill.owner_scope,
                    memory_type="procedural",
                    capability_id=None,
                    graph_node_ids=[],
                    graph_edge_ids=[],
                    trace_refs=[],
                    evidence_ref=skill.candidate_id,
                    metadata={
                        "matched_patterns": result.matched_patterns,
                        "current_version": skill.current_version,
                        "base_relevance": result.score,
                    },
                )
            )
        return items

    def _collect_capabilities(self, request: RetrievalRequest) -> list[RetrievedContextItem]:
        list_manifests = getattr(self._capability_registry, "list_manifests", None)
        if not callable(list_manifests):
            return []
        allowed_ids = set(request.capability_ids)
        items: list[RetrievedContextItem] = []
        for manifest in list_manifests():
            for capability in getattr(manifest, "capabilities", []):
                capability_data = _capability_dict(capability)
                capability_id = capability_data.get("capability_id") or capability_data.get("id")
                if not isinstance(capability_id, str):
                    continue
                if allowed_ids and capability_id not in allowed_ids:
                    continue
                name = str(capability_data.get("name") or capability_id)
                description = str(capability_data.get("description") or name)
                items.append(
                    RetrievedContextItem(
                        item_id=f"capability-{capability_id}",
                        source="capability_registry",
                        source_id=capability_id,
                        title=name,
                        content=description,
                        score=0.6,
                        confidence=0.7,
                        sensitivity="low",
                        owner_scope=request.scope,
                        memory_type=None,
                        capability_id=capability_id,
                        graph_node_ids=[],
                        graph_edge_ids=[],
                        trace_refs=[],
                        evidence_ref=None,
                        metadata={"module_id": getattr(manifest, "module_id", None)},
                    )
                )
        return items

    def _collect_recent_traces(self, request: RetrievalRequest) -> list[RetrievedContextItem]:
        list_recent = getattr(self._trace_repository, "list_recent_traces", None)
        if not callable(list_recent):
            return []
        traces = list_recent(limit=request.limit)
        items: list[RetrievedContextItem] = []
        for trace in traces:
            trace_id = getattr(trace, "trace_id", None)
            if not isinstance(trace_id, str):
                continue
            outcome = getattr(trace, "outcome", {})
            items.append(
                RetrievedContextItem(
                    item_id=f"recent-trace-{trace_id}",
                    source="recent_trace",
                    source_id=trace_id,
                    title=trace_id,
                    content=json.dumps(outcome, sort_keys=True),
                    score=0.5,
                    confidence=0.6,
                    sensitivity="low",
                    owner_scope=request.scope,
                    memory_type=None,
                    capability_id=None,
                    graph_node_ids=[],
                    graph_edge_ids=[],
                    trace_refs=[trace_id],
                    evidence_ref=trace_id,
                    metadata={
                        "created_at": getattr(trace, "created_at", datetime.now(UTC)).isoformat(),
                        "base_relevance": 0.5,
                    },
                )
            )
        return items

    def _collect_evidence(self, request: RetrievalRequest) -> list[RetrievedContextItem]:
        search = getattr(self._evidence_service, "search", None)
        if not callable(search):
            return []
        results = search(
            EvidenceSearchRequest(
                query=request.query,
                scope=request.scope,
                source_types=[],
                limit=request.limit,
                min_score=request.min_score,
            )
        )
        if not isinstance(results, list):
            return []
        items: list[RetrievedContextItem] = []
        for result in results:
            if not isinstance(result, EvidenceSearchResult):
                continue
            chunk_id = result.chunk.chunk_id if result.chunk is not None else None
            items.append(
                RetrievedContextItem(
                    item_id=f"evidence-{chunk_id or result.evidence.evidence_id}",
                    source="evidence_vault",
                    source_id=chunk_id or result.evidence.evidence_id,
                    title=result.evidence.title,
                    content=(
                        result.chunk.text
                        if result.chunk is not None
                        else result.evidence.summary
                    ),
                    score=result.score,
                    confidence=result.evidence.confidence,
                    sensitivity=result.evidence.sensitivity,
                    owner_scope=result.evidence.owner_scope,
                    memory_type=None,
                    capability_id=None,
                    graph_node_ids=[],
                    graph_edge_ids=[],
                    trace_refs=[result.evidence.trace_id] if result.evidence.trace_id else [],
                    evidence_ref=result.evidence.evidence_id,
                    metadata={
                        **result.metadata,
                        "chunk_id": chunk_id,
                        "content_hash": result.evidence.content_hash,
                        "matched_terms": result.matched_terms,
                        "base_relevance": result.score,
                    },
                )
            )
        return items

    def _collect_working_memory(self, request: RetrievalRequest) -> list[RetrievedContextItem]:
        query_slots = getattr(self._working_memory_service, "query_slots", None)
        if not callable(query_slots):
            return []
        focus_session_id = request.metadata.get("focus_session_id")
        slots = query_slots(
            WorkingMemoryQuery(
                focus_session_id=focus_session_id if isinstance(focus_session_id, str) else None,
                scope=request.scope,
                limit=request.limit,
            )
        )
        if not isinstance(slots, list):
            return []
        items: list[RetrievedContextItem] = []
        for slot in slots:
            if not isinstance(slot, WorkingMemorySlot):
                continue
            items.append(
                RetrievedContextItem(
                    item_id=f"working-memory-{slot.slot_id}",
                    source="working_memory",
                    source_id=slot.slot_id,
                    title=slot.slot_type,
                    content=slot.summary,
                    score=slot.priority,
                    confidence=slot.confidence,
                    sensitivity="internal",
                    owner_scope=slot.owner_scope,
                    memory_type="working",
                    capability_id=None,
                    graph_node_ids=[],
                    graph_edge_ids=[],
                    trace_refs=[slot.trace_id] if slot.trace_id else [],
                    evidence_ref=slot.source_id if slot.source_type == "evidence" else None,
                    metadata={
                        **slot.metadata,
                        "source_type": slot.source_type,
                        "source_id": slot.source_id,
                        "focus_session_id": slot.focus_session_id,
                        "pinned": slot.pinned,
                        "base_relevance": slot.priority,
                    },
                )
            )
        return items

    def _authorize_global(self, request: RetrievalRequest) -> bool:
        decision = self._authorize(
            request=request,
            action_type="memory.retrieve",
            resource_type="retrieval",
            resource_id=request.retrieval_id,
            context={"operation": "retrieval_router"},
        )
        return decision.allow

    def _authorize_source(self, source: RetrievalSource, request: RetrievalRequest) -> bool:
        action_type = _action_for_source(source)
        decision = self._authorize(
            request=request,
            action_type=action_type,
            resource_type=str(source),
            resource_id=None,
            context={"source": source},
        )
        return decision.allow

    def _authorize(
        self,
        *,
        request: RetrievalRequest,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        context: dict[str, object],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{request.retrieval_id}-{resource_type}",
                trace_id=request.trace_id,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=request.scope,
                context=context,
            )
        )

    def _source_enabled(self, source: RetrievalSource, request: RetrievalRequest) -> bool:
        if source == "graph_memory":
            return request.include_graph
        if source == "capability_registry":
            return request.include_capabilities
        if source == "skill_registry":
            return True
        if source == "recent_trace":
            return request.include_recent_traces
        return True

    def _persist(self, request: RetrievalRequest, result: RetrievalResult) -> None:
        save = getattr(self._retrieval_repository, "save", None)
        if not callable(save):
            return
        try:
            save(
                result,
                trace_id=request.trace_id,
                intent_id=request.intent_id,
                context_id=str(request.metadata.get("context_id"))
                if request.metadata.get("context_id") is not None
                else None,
                scope=request.scope,
                requested_sources=list(request.requested_sources),
            )
        except Exception:
            return

    def _emit_telemetry(self, request: RetrievalRequest, result: RetrievalResult) -> None:
        if self._telemetry_service is None or not result.items:
            return
        events = [_telemetry_event(request, item) for item in result.items]
        try:
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(request.trace_id or request.retrieval_id, events)
                return
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                for event in events:
                    emit(event)
        except Exception:
            return

    def _apply_memory_governance(
        self,
        request: RetrievalRequest,
        items: list[RetrievedContextItem],
    ) -> tuple[list[RetrievedContextItem], list[str]]:
        filtered: list[RetrievedContextItem] = []
        constraints: list[str] = []
        filtered_count = 0
        for item in items:
            if item.source not in {"lexical_memory", "semantic_memory", "graph_memory"}:
                filtered.append(item)
                continue
            if _metadata_status_blocks(item.metadata) or _metadata_expired(item.metadata):
                filtered_count += 1
                constraints.append(f"memory_governance_filtered:{item.source_id}")
                continue
            governed = self._govern_retrieval_item(request, item)
            if governed is None:
                filtered_count += 1
                constraints.append(f"memory_governance_filtered:{item.source_id}")
                continue
            filtered.append(governed)
        if filtered_count:
            self._emit_governance_filtered(request, filtered_count)
            constraints.append(f"memory_governance_filtered_count:{filtered_count}")
        return filtered, constraints

    def _govern_retrieval_item(
        self,
        request: RetrievalRequest,
        item: RetrievedContextItem,
    ) -> RetrievedContextItem | None:
        get = getattr(self._memory_service, "get", None)
        evaluate = getattr(self._memory_governance_engine, "evaluate", None)
        if (
            callable(get)
            and callable(evaluate)
            and item.source in {"lexical_memory", "semantic_memory"}
        ):
            record = get(item.source_id)
            if record is not None:
                decision = evaluate(
                    MemoryGovernanceEvaluationRequest(
                        trace_id=request.trace_id,
                        memory=record,
                        action_type="memory.retrieve",
                        owner_scope=request.scope,
                        context={"retrieval_score": item.score, "retrieval_source": item.source},
                    )
                )
                decision_value = getattr(decision, "decision", "allow")
                if decision_value in {"deny", "expire", "forget"}:
                    return None
                metadata = {
                    **item.metadata,
                    "governance_decision": str(decision_value),
                    "governance_decision_id": str(
                        getattr(decision, "governance_decision_id", "")
                    ),
                }
                item = item.model_copy(update={"metadata": metadata})
        decay_score = _metadata_float(item.metadata, "governance_decay_score")
        if decay_score is None:
            compute = getattr(self._memory_decay_service, "compute_decay_score", None)
            get = getattr(self._memory_service, "get", None)
            if (
                callable(compute)
                and callable(get)
                and item.source in {"lexical_memory", "semantic_memory"}
            ):
                record = get(item.source_id)
                if record is not None:
                    computed = compute(record)
                    if (
                        isinstance(computed, tuple)
                        and len(computed) == 2
                        and isinstance(computed[0], int | float)
                    ):
                        decay_score = float(computed[0])
        if decay_score is None:
            return item
        adjusted = max(0.0, min(1.0, item.score * decay_score))
        return item.model_copy(
            update={
                "score": adjusted,
                "metadata": {
                    **item.metadata,
                    "governance_decay_score": decay_score,
                    "governance_adjusted_score": adjusted,
                },
            }
        )

    def _emit_governance_filtered(self, request: RetrievalRequest, filtered_count: int) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{request.retrieval_id}-memory-governance-filtered",
            trace_id=request.trace_id or request.retrieval_id,
            event_type=cast(Any, "memory_governance_filtered"),
            node_type=cast(Any, "governance"),
            node_id=request.retrieval_id,
            edge_from=None,
            edge_to=None,
            intensity=min(1.0, filtered_count / max(1, request.limit)),
            payload={"filtered_count": filtered_count},
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _action_for_source(source: RetrievalSource) -> str:
    if source == "capability_registry":
        return "capability.list"
    if source == "skill_registry":
        return "skill.match"
    if source == "recent_trace":
        return "trace.read"
    if source == "evidence_vault":
        return "evidence.search"
    if source == "working_memory":
        return "working_memory.read"
    return "memory.retrieve"


def _empty_result(request: RetrievalRequest, constraints: list[str]) -> RetrievalResult:
    return RetrievalResult(
        retrieval_id=request.retrieval_id,
        query=request.query,
        items=[],
        source_counts={},
        constraints=constraints,
        created_at=datetime.now(UTC),
    )


def _deduplicate(items: list[RetrievedContextItem]) -> list[RetrievedContextItem]:
    source_ids: set[str] = set()
    content_hashes: set[str] = set()
    deduped: list[RetrievedContextItem] = []
    for item in items:
        content_key = content_hash_key(item.content)
        if item.source_id in source_ids or content_key in content_hashes:
            continue
        source_ids.add(item.source_id)
        content_hashes.add(content_key)
        deduped.append(item)
    return deduped


def _source_counts(items: list[RetrievedContextItem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item.source] = counts.get(item.source, 0) + 1
    return counts


def _telemetry_event(
    request: RetrievalRequest,
    item: RetrievedContextItem,
) -> VisualTelemetryEvent:
    return VisualTelemetryEvent(
        telemetry_id=f"telemetry-{request.retrieval_id}-{item.item_id}",
        trace_id=request.trace_id or request.retrieval_id,
        event_type=_telemetry_event_type(item.source),
        node_type=_telemetry_node_type(item.source),
        node_id=item.source_id,
        edge_from=None,
        edge_to=None,
        intensity=item.score,
        payload={"source": item.source, "retrieval_id": request.retrieval_id},
        created_at=datetime.now(UTC),
    )


def _telemetry_event_type(source: RetrievalSource) -> VisualTelemetryEventType:
    if source == "capability_registry":
        return "capability_node_seen"
    if source == "skill_registry":
        return "skill_node_seen"
    if source == "recent_trace":
        return "trace_created"
    if source == "evidence_vault":
        return "evidence_retrieved"
    return "memory_node_activated"


def _telemetry_node_type(source: RetrievalSource) -> VisualNodeType:
    if source == "capability_registry":
        return "capability"
    if source == "skill_registry":
        return "skill"
    if source == "recent_trace":
        return "trace"
    if source == "evidence_vault":
        return "evidence"
    if source == "working_memory":
        return "working_memory"
    return "memory"


def _apply_attention_boosts(
    request: RetrievalRequest,
    items: list[RetrievedContextItem],
) -> list[RetrievedContextItem]:
    selected_slots = _metadata_set(request.metadata, "selected_slot_ids")
    selected_memory = _metadata_set(request.metadata, "selected_memory_ids")
    selected_evidence = _metadata_set(request.metadata, "selected_evidence_ids")
    selected_skills = _metadata_set(request.metadata, "selected_skill_ids")
    selected_capabilities = _metadata_set(request.metadata, "selected_capability_ids")
    boosted: list[RetrievedContextItem] = []
    for item in items:
        boost = 0.0
        if item.source == "working_memory" and item.source_id in selected_slots:
            boost += 0.10
        if (
            item.source in {"lexical_memory", "semantic_memory"}
            and item.source_id in selected_memory
        ):
            boost += 0.10
        if item.source == "evidence_vault" and (
            item.source_id in selected_evidence
            or (item.evidence_ref is not None and item.evidence_ref in selected_evidence)
        ):
            boost += 0.10
        if item.source == "skill_registry" and item.source_id in selected_skills:
            boost += 0.10
        capability_id = item.capability_id or item.source_id
        if item.source == "capability_registry" and capability_id in selected_capabilities:
            boost += 0.10
        if boost:
            boosted.append(
                item.model_copy(
                    update={
                        "score": min(1.0, item.score + boost),
                        "metadata": {
                            **item.metadata,
                            "attention_boost": round(boost, 2),
                        },
                    }
                )
            )
        else:
            boosted.append(item)
    return sorted(
        boosted,
        key=lambda candidate: (-candidate.score, candidate.source, candidate.source_id),
    )


def _metadata_set(metadata: dict[str, Any], key: str) -> set[str]:
    value = metadata.get(key)
    if isinstance(value, list):
        return {str(item) for item in value if isinstance(item, str)}
    return set()


def _node_content(label: str, properties: dict[str, Any]) -> str:
    if not properties:
        return label
    return f"{label} {json.dumps(properties, sort_keys=True)}"


def _capability_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return cast(dict[str, Any], model_dump())
    return {}


def _skill_content(description: str, procedure_steps: Sequence[object]) -> str:
    summaries: list[str] = []
    for step in procedure_steps:
        action_type = getattr(step, "action_type", None)
        step_description = getattr(step, "description", None)
        if isinstance(action_type, str) and isinstance(step_description, str):
            summaries.append(f"{action_type}: {step_description}")
    if not summaries:
        return description
    return f"{description}\nProcedure steps:\n" + "\n".join(summaries)


def _metadata_status_blocks(metadata: dict[str, Any]) -> bool:
    status = metadata.get("governance_status")
    return status in {"expired", "forgotten", "deleted"}


def _metadata_expired(metadata: dict[str, Any]) -> bool:
    expires_at = metadata.get("expires_at")
    if not isinstance(expires_at, str) or not expires_at:
        return False
    try:
        parsed = datetime.fromisoformat(expires_at)
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed <= datetime.now(UTC)


def _metadata_float(metadata: dict[str, Any], key: str) -> float | None:
    value = metadata.get(key)
    if isinstance(value, int | float):
        return max(0.0, min(1.0, float(value)))
    return None
