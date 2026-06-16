"""Deterministic context compiler."""

from datetime import UTC, datetime
from typing import Any, Protocol

from aion_brain.attention.context_budget import ContextBudgeter
from aion_brain.attention.controller import AttentionController
from aion_brain.config import Settings
from aion_brain.contracts.attention import (
    AttentionDecision,
    AttentionDecisionRequest,
    ContextBudgetRequest,
)
from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.retrieval import (
    ContextFusionRequest,
    RetrievalRequest,
    RetrievalResult,
    RetrievalSource,
)
from aion_brain.memory.graph_service import GraphMemoryService
from aion_brain.memory.service import PostgresMemoryService
from aion_brain.policy.base import PolicyAdapter
from aion_brain.retrieval.fusion import ContextFusionEngine
from aion_brain.retrieval.router import RetrievalRouter


class CapabilityCatalog(Protocol):
    """Capability listing boundary used by the compiler."""

    def list_manifests(self) -> list[Any]:
        """List active capability manifests."""
        ...


class EmptyCapabilityCatalog:
    """Empty capability catalog for v0.1 default runtime wiring."""

    def list_manifests(self) -> list[Any]:
        """Return no capabilities."""
        return []


class ContextCompiler:
    """Build a compact reasoning context from event, intent, and policy."""

    def __init__(
        self,
        *,
        policy_adapter: PolicyAdapter,
        memory_service: PostgresMemoryService | None = None,
        graph_service: GraphMemoryService | None = None,
        capability_catalog: CapabilityCatalog | None = None,
        retrieval_router: RetrievalRouter | None = None,
        belief_query_service: object | None = None,
        fusion_engine: ContextFusionEngine | None = None,
        attention_controller: AttentionController | None = None,
        context_budgeter: ContextBudgeter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._policy_adapter = policy_adapter
        self._memory_service = memory_service
        self._graph_service = graph_service
        self._capability_catalog = capability_catalog or EmptyCapabilityCatalog()
        self._retrieval_router = retrieval_router
        self._belief_query_service = belief_query_service
        self._fusion_engine = fusion_engine or ContextFusionEngine()
        self._attention_controller = attention_controller
        self._context_budgeter = context_budgeter
        self._settings = settings

    def compile(
        self,
        *,
        event: AIONEvent,
        intent: IntentFrame,
        scope: list[str],
    ) -> ContextPacket:
        """Compile context while recording policy constraints instead of crashing."""
        constraints: list[str] = []
        known_context: list[dict[str, Any]] = [
            {
                "source": "event",
                "event_id": event.event_id,
                "event_type": event.event_type,
                "payload_type": event.payload_type,
            },
            {
                "source": "intent",
                "intent_type": intent.intent_type,
                "risk_level": intent.risk_level,
                "confidence": intent.confidence,
            },
        ]

        compile_decision = self._authorize(
            event=event,
            scope=scope,
            action_type="context.compile",
            resource_type="context",
            resource_id=f"context-{intent.intent_id}",
            risk_level="low",
        )
        if not compile_decision.allow:
            constraints.extend(_constraints_from_decision(compile_decision))
            return _packet(event, intent, known_context, [], [], [], [], constraints)

        attention_decision: AttentionDecision | None = None
        attention_controller = self._attention_controller
        if _attention_enabled(self._settings, attention_controller) and attention_controller:
            try:
                attention_decision = attention_controller.decide(
                    AttentionDecisionRequest(
                        trace_id=event.trace_id,
                        focus_session_id=_payload_str(event.payload, "focus_session_id"),
                        actor_id=event.actor_id,
                        workspace_id=event.workspace_id,
                        goal=intent.goal,
                        intent_type=intent.intent_type,
                        scope=scope,
                        max_signals=_setting_int(
                            self._settings,
                            "attention_default_max_signals",
                            10,
                        ),
                        max_slots=_setting_int(self._settings, "attention_default_max_slots", 20),
                        metadata={"event_id": event.event_id},
                    )
                )
                known_context.append(
                    {
                        "source": "attention_decision",
                        "attention_decision_id": attention_decision.attention_decision_id,
                        "focus_session_id": attention_decision.focus_session_id,
                        "decision_type": attention_decision.decision_type,
                        "selected_slot_ids": attention_decision.selected_slot_ids,
                        "priority_score": attention_decision.priority_score,
                    }
                )
            except PermissionError as exc:
                constraints.append(f"policy:attention_decide_denied:{exc}")
                return _packet(event, intent, known_context, [], [], [], [], constraints)
            except Exception:
                constraints.append("attention_unavailable")

        try:
            retrieval_request = _retrieval_request(
                event,
                intent,
                scope,
                attention_decision,
                include_situations=_situation_context_enabled(self._settings),
            )
            retrieval_result = self._router().retrieve(retrieval_request)
            retrieval_result, budget_constraints = self._apply_context_budget(
                event=event,
                intent=intent,
                scope=scope,
                retrieval_request=retrieval_request,
                retrieval_result=retrieval_result,
                attention_decision=attention_decision,
            )
            constraints.extend(budget_constraints)
            context_bundle = self._fusion_engine.fuse(
                ContextFusionRequest(
                    retrieval_result=retrieval_result,
                    goal=intent.goal,
                    max_items=_setting_int(self._settings, "context_budget_default_max_items", 10),
                    max_chars=_setting_int(
                        self._settings,
                        "context_budget_default_max_chars",
                        12000,
                    ),
                    metadata={"context_id": f"context-{event.event_id}"},
                )
            )
        except Exception:
            constraints.append("retrieval_unavailable")
            return _packet(event, intent, known_context, [], [], [], [], constraints)

        known_context.append(
            {
                "source": "context_bundle",
                "bundle_id": context_bundle.bundle_id,
                "retrieval_id": context_bundle.retrieval_id,
                "fused_summary": context_bundle.fused_summary,
                "evidence_refs": context_bundle.evidence_refs,
            }
        )
        for item in context_bundle.items:
            if item.source == "belief_state":
                _append_belief_constraints(item.metadata, constraints)
            if item.source == "entity_registry":
                _append_entity_constraints(item.metadata, constraints)
            if item.source == "situation_model":
                _append_situation_constraints(item.metadata, constraints)
            known_context.append(
                {
                    "source": item.source,
                    "source_id": item.source_id,
                    "score": item.score,
                    "title": item.title,
                    "graph_node_ids": item.graph_node_ids,
                    "graph_edge_ids": item.graph_edge_ids,
                    "trace_refs": item.trace_refs,
                    "evidence_ref": item.evidence_ref,
                    "metadata": item.metadata,
                }
            )
        constraints.extend(context_bundle.constraints)

        return _packet(
            event,
            intent,
            known_context,
            context_bundle.memory_refs,
            context_bundle.graph_node_refs,
            context_bundle.graph_edge_refs,
            context_bundle.capability_refs,
            constraints,
        )

    def _router(self) -> RetrievalRouter:
        if self._retrieval_router is not None:
            return self._retrieval_router
        self._retrieval_router = RetrievalRouter(
            policy_adapter=self._policy_adapter,
            memory_service=self._memory_service,
            graph_memory_service=self._graph_service,
            capability_registry=self._capability_catalog,
            belief_query_service=getattr(self, "_belief_query_service", None),
        )
        return self._retrieval_router

    def _apply_context_budget(
        self,
        *,
        event: AIONEvent,
        intent: IntentFrame,
        scope: list[str],
        retrieval_request: RetrievalRequest,
        retrieval_result: RetrievalResult,
        attention_decision: AttentionDecision | None,
    ) -> tuple[RetrievalResult, list[str]]:
        if not _attention_enabled(self._settings, self._attention_controller):
            return retrieval_result, []
        if self._context_budgeter is None:
            return retrieval_result, ["context_budgeter_unavailable"]
        try:
            budget = self._context_budgeter.allocate(
                ContextBudgetRequest(
                    trace_id=event.trace_id,
                    focus_session_id=(
                        attention_decision.focus_session_id if attention_decision else None
                    ),
                    intent_id=intent.intent_id,
                    context_id=f"context-{event.event_id}",
                    scope=scope,
                    max_items=_setting_int(
                        self._settings,
                        "context_budget_default_max_items",
                        20,
                    ),
                    max_chars=_setting_int(
                        self._settings,
                        "context_budget_default_max_chars",
                        12000,
                    ),
                    requested_sources=[
                        str(source) for source in retrieval_request.requested_sources
                    ],
                    metadata={"event_id": event.event_id},
                )
            )
            selected, overflow = self._context_budgeter.apply_budget(
                retrieval_result.items,
                budget,
            )
        except PermissionError as exc:
            return retrieval_result.model_copy(update={"items": []}), [
                f"policy:context_budget_denied:{exc}"
            ]
        except Exception:
            return retrieval_result, ["context_budget_unavailable"]
        constraints = [f"context_budget:{budget.context_budget_id}"]
        if overflow:
            constraints.append(f"context_budget_overflow_count:{len(overflow)}")
        return (
            retrieval_result.model_copy(
                update={
                    "items": selected,
                    "constraints": retrieval_result.constraints + constraints,
                }
            ),
            constraints,
        )

    def _authorize(
        self,
        *,
        event: AIONEvent,
        scope: list[str],
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{event.event_id}",
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[],
                security_scope=scope,
                context={"event_id": event.event_id},
            )
        )


def _packet(
    event: AIONEvent,
    intent: IntentFrame,
    known_context: list[dict[str, Any]],
    memory_ids: list[str],
    graph_node_ids: list[str],
    graph_edge_ids: list[str],
    capability_ids: list[str],
    constraints: list[str],
) -> ContextPacket:
    open_questions = []
    if intent.goal == "unknown":
        open_questions.append("A clear goal is required before planning can continue.")

    execution_limits: dict[str, Any] = {
        "no_model_calls": True,
        "no_capability_execution": True,
    }
    for item in known_context:
        metadata = item.get("metadata")
        if isinstance(metadata, dict):
            if metadata.get("decision_frame_id"):
                execution_limits["decision_frame_id"] = metadata["decision_frame_id"]
            if metadata.get("decision_record_id"):
                execution_limits["decision_record_id"] = metadata["decision_record_id"]
        if item.get("source") == "decision_journal" and item.get("source_id"):
            execution_limits.setdefault("decision_record_id", item["source_id"])

    return ContextPacket(
        context_id=f"context-{event.event_id}",
        intent_id=intent.intent_id,
        goal=intent.goal,
        known_context=known_context,
        retrieved_memory_ids=memory_ids,
        graph_node_ids=graph_node_ids,
        graph_edge_ids=graph_edge_ids,
        available_capability_ids=capability_ids,
        constraints=constraints,
        open_questions=open_questions,
        execution_limits=execution_limits,
    )


def _constraints_from_decision(decision: PolicyDecision) -> list[str]:
    if decision.constraints:
        return [f"policy:{decision.reason}:{constraint}" for constraint in decision.constraints]
    return [f"policy:{decision.reason}"]


def _retrieval_request(
    event: AIONEvent,
    intent: IntentFrame,
    scope: list[str],
    attention_decision: AttentionDecision | None = None,
    *,
    include_situations: bool = False,
) -> RetrievalRequest:
    requested_sources: list[RetrievalSource] = []
    if intent.requires_memory:
        requested_sources.extend(
            [
                "lexical_memory",
                "semantic_memory",
                "graph_memory",
                "evidence_vault",
                "belief_state",
            ]
        )
    if include_situations:
        requested_sources.extend(["situation_model", "temporal_state"])
    if attention_decision is not None:
        requested_sources.append("working_memory")
    requested_sources.append("capability_registry")
    requested_sources = _unique_sources(requested_sources)
    return RetrievalRequest(
        retrieval_id=f"retrieval-{event.event_id}",
        trace_id=event.trace_id,
        intent_id=intent.intent_id,
        query=_query_text(event, intent),
        scope=scope,
        requested_sources=requested_sources,
        memory_types=[],
        capability_ids=attention_decision.selected_capability_ids if attention_decision else [],
        limit=10,
        min_score=None,
        include_graph=True,
        include_capabilities=True,
        include_recent_traces=False,
        metadata={
            "context_id": f"context-{event.event_id}",
            "event_id": event.event_id,
            "created_at": datetime.now(UTC).isoformat(),
            "attention_decision_id": (
                attention_decision.attention_decision_id if attention_decision else None
            ),
            "selected_slot_ids": attention_decision.selected_slot_ids if attention_decision else [],
            "selected_memory_ids": (
                attention_decision.selected_memory_ids if attention_decision else []
            ),
            "selected_evidence_ids": (
                attention_decision.selected_evidence_ids if attention_decision else []
            ),
            "selected_skill_ids": (
                attention_decision.selected_skill_ids if attention_decision else []
            ),
            "selected_capability_ids": (
                attention_decision.selected_capability_ids if attention_decision else []
            ),
        },
    )


def _query_text(event: AIONEvent, intent: IntentFrame) -> str:
    if intent.goal and intent.goal != "unknown":
        return intent.goal
    payload_goal = event.payload.get("goal") or event.payload.get("question")
    if isinstance(payload_goal, str) and payload_goal:
        return payload_goal
    return event.event_type


def _attention_enabled(
    settings: Settings | None,
    controller: AttentionController | None,
) -> bool:
    return controller is not None and bool(getattr(settings, "attention_enabled", True))


def _setting_int(settings: Settings | None, name: str, default: int) -> int:
    return int(getattr(settings, name, default))


def _situation_context_enabled(settings: Settings | None) -> bool:
    return bool(
        settings is not None
        and getattr(settings, "situations_enabled", False)
        and getattr(settings, "situation_projection_enabled", False)
    )


def _payload_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value else None


def _unique_sources(sources: list[RetrievalSource]) -> list[RetrievalSource]:
    seen: set[RetrievalSource] = set()
    unique: list[RetrievalSource] = []
    for source in sources:
        if source in seen:
            continue
        seen.add(source)
        unique.append(source)
    return unique


def _append_belief_constraints(metadata: dict[str, Any], constraints: list[str]) -> None:
    status = str(metadata.get("status", "unknown"))
    if status in {"contradicted", "stale"}:
        constraints.append(f"belief_{status}:{metadata.get('claim_type', 'generic')}")
    constraints.append("belief_state_items_are_claims_not_absolute_truth")


def _append_entity_constraints(metadata: dict[str, Any], constraints: list[str]) -> None:
    status = str(metadata.get("status", "unknown"))
    if status == "merged":
        constraints.append("entity_reference_is_merged")
    elif status == "archived":
        constraints.append("entity_reference_is_archived")
    constraints.append("entity_registry_items_are_references_not_raw_evidence")


def _append_situation_constraints(metadata: dict[str, Any], constraints: list[str]) -> None:
    status = str(metadata.get("status") or "").lower()
    if status == "stale":
        constraints.append("situation_projection_stale")
    if status == "contradicted":
        constraints.append("state_atom_contradicted")
    situation_id = metadata.get("situation_id")
    if isinstance(situation_id, str) and situation_id:
        constraints.append(f"active_situation_id:{situation_id}")
    constraints.append("state_atoms_are_recall_not_truth")
