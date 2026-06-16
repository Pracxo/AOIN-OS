from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from aion_brain.context.compiler import ContextCompiler
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.retrieval import RetrievalRequest, RetrievalResult, RetrievedContextItem
from aion_brain.retrieval.router import RetrievalRouter
from tests.kernel_fakes import AllowPolicy


class SituationRouter:
    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        return RetrievalResult(
            retrieval_id=request.retrieval_id,
            query=request.query,
            items=[
                RetrievedContextItem(
                    item_id="atom-1",
                    source="situation_model",
                    source_id="atom-1",
                    title="status",
                    content="state atom",
                    score=0.8,
                    confidence=0.8,
                    sensitivity="internal",
                    owner_scope=["workspace:main"],
                    memory_type=None,
                    capability_id=None,
                    graph_node_ids=[],
                    graph_edge_ids=[],
                    trace_refs=[],
                    evidence_ref=None,
                    metadata={"status": "contradicted", "situation_id": "situation-1"},
                )
            ],
            source_counts={"situation_model": 1},
            constraints=[],
            created_at=datetime.now(UTC),
        )


def test_context_compiler_adds_situation_constraints() -> None:
    compiler = ContextCompiler(
        policy_adapter=AllowPolicy(),
        retrieval_router=cast(RetrievalRouter, SituationRouter()),
    )

    packet = compiler.compile(event=_event(), intent=_intent(), scope=["workspace:main"])

    assert "state_atom_contradicted" in packet.constraints
    assert "active_situation_id:situation-1" in packet.constraints
    assert any(item["source"] == "situation_model" for item in packet.known_context)


def _event() -> AIONEvent:
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question.answer",
        payload_type="test",
        payload={"question": "what now?"},
        timestamp=datetime.now(UTC),
        trace_id="trace-1",
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
