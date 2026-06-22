from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from aion_brain.context.compiler import ContextCompiler
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.retrieval import RetrievalRequest, RetrievalResult, RetrievedContextItem
from aion_brain.retrieval.router import RetrievalRouter


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class EntityRouter:
    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        return RetrievalResult(
            retrieval_id=request.retrieval_id,
            query=request.query,
            items=[
                RetrievedContextItem(
                    item_id="entity-1",
                    source="entity_registry",
                    source_id="entity-1",
                    title="generic",
                    content="Canonical reference",
                    score=0.9,
                    confidence=0.8,
                    sensitivity="internal",
                    owner_scope=["workspace:main"],
                    memory_type=None,
                    capability_id=None,
                    graph_node_ids=[],
                    graph_edge_ids=[],
                    trace_refs=[],
                    evidence_ref=None,
                    metadata={"status": "merged", "entity_type": "generic"},
                )
            ],
            source_counts={"entity_registry": 1},
            constraints=[],
            created_at=datetime.now(UTC),
        )


def test_context_compiler_adds_entity_reference_constraints() -> None:
    compiler = ContextCompiler(
        policy_adapter=AllowPolicy(),
        retrieval_router=cast(RetrievalRouter, EntityRouter()),
    )

    packet = compiler.compile(event=_event(), intent=_intent(), scope=["workspace:main"])

    assert "entity_reference_is_merged" in packet.constraints
    assert "entity_registry_items_are_references_not_raw_evidence" in packet.constraints
    assert any(item["source"] == "entity_registry" for item in packet.known_context)


def _event() -> AIONEvent:
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question.answer",
        payload_type="test",
        payload={"question": "what now?"},
        timestamp=datetime.now(UTC),
        trace_id="trace-1",
        correlation_id="corr-1",
        security_scope=["workspace:main"],
    )


def _intent() -> IntentFrame:
    return IntentFrame(
        intent_id="intent-1",
        event_id="event-1",
        intent_type="question.answer",
        goal="what now?",
        urgency="normal",
        confidence=0.8,
        risk_level="low",
        requires_memory=True,
        requires_capability=False,
        requires_approval=False,
    )
