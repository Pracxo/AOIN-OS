"""Context compiler attention integration tests."""

from datetime import UTC, datetime

from aion_brain.config import Settings
from aion_brain.context.compiler import ContextCompiler
from aion_brain.contracts.attention import (
    AttentionDecision,
    AttentionDecisionRequest,
    ContextBudgetRequest,
)
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.retrieval import RetrievalRequest, RetrievalResult, RetrievedContextItem
from tests.kernel_fakes import AllowPolicy


class FakeAttentionController:
    def __init__(self) -> None:
        self.requests: list[AttentionDecisionRequest] = []

    def decide(self, request: AttentionDecisionRequest) -> AttentionDecision:
        self.requests.append(request)
        return AttentionDecision(
            attention_decision_id="attention-decision-1",
            trace_id=request.trace_id,
            focus_session_id="focus-1",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            decision_type="focus",
            selected_signal_ids=[],
            selected_slot_ids=["slot-1"],
            selected_memory_ids=["memory-1"],
            selected_evidence_ids=[],
            selected_skill_ids=[],
            selected_capability_ids=[],
            priority_score=0.6,
            reason="selected",
            constraints=[],
            metadata={},
            created_at=datetime.now(UTC),
        )


class FakeBudgeter:
    def __init__(self) -> None:
        self.requests: list[ContextBudgetRequest] = []

    def allocate(self, request: ContextBudgetRequest):
        self.requests.append(request)
        from aion_brain.contracts.attention import ContextBudget

        return ContextBudget(
            context_budget_id="budget-1",
            trace_id=request.trace_id,
            focus_session_id=request.focus_session_id,
            intent_id=request.intent_id,
            context_id=request.context_id,
            max_items=1,
            max_chars=1000,
            allocation={"working_memory": 1, "capability_registry": 1},
            used_items=0,
            used_chars=0,
            overflow_items=[],
            constraints=[],
            created_at=datetime.now(UTC),
        )

    def apply_budget(self, items, budget):
        return items[:1], [{"item_id": "overflow"}]


class FakeRouter:
    def __init__(self) -> None:
        self.requests: list[RetrievalRequest] = []

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        self.requests.append(request)
        return RetrievalResult(
            retrieval_id=request.retrieval_id,
            query=request.query,
            items=[retrieved_item()],
            source_counts={"working_memory": 1},
            constraints=[],
            created_at=datetime.now(UTC),
        )


def test_context_compiler_calls_attention_and_applies_budget() -> None:
    """ContextCompiler consumes AttentionDecision before retrieval and fusion."""
    attention = FakeAttentionController()
    budgeter = FakeBudgeter()
    router = FakeRouter()
    compiler = ContextCompiler(
        policy_adapter=AllowPolicy(),
        retrieval_router=router,
        attention_controller=attention,
        context_budgeter=budgeter,
        settings=Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:"),
    )

    packet = compiler.compile(event=event(), intent=intent(), scope=["workspace:main"])

    assert attention.requests
    assert "working_memory" in router.requests[0].requested_sources
    assert router.requests[0].metadata["selected_slot_ids"] == ["slot-1"]
    assert "context_budget_overflow_count:1" in packet.constraints
    assert packet.known_context[2]["attention_decision_id"] == "attention-decision-1"


def event() -> AIONEvent:
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


def intent() -> IntentFrame:
    return IntentFrame(
        intent_id="intent-1",
        event_id="event-1",
        intent_type="memory.retrieve",
        goal="retrieve context",
        urgency="normal",
        confidence=0.8,
        risk_level="low",
        requires_memory=True,
        requires_capability=False,
        requires_approval=False,
    )


def retrieved_item() -> RetrievedContextItem:
    return RetrievedContextItem(
        item_id="working-memory-slot-1",
        source="working_memory",
        source_id="slot-1",
        title="slot",
        content="alpha beta",
        score=0.8,
        confidence=0.8,
        sensitivity="internal",
        owner_scope=["workspace:main"],
        memory_type="working",
        capability_id=None,
        graph_node_ids=[],
        graph_edge_ids=[],
        trace_refs=[],
        evidence_ref=None,
        metadata={},
    )
