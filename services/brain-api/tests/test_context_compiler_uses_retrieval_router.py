"""Context compiler retrieval router integration tests."""

from datetime import UTC, datetime

from aion_brain.context.compiler import ContextCompiler
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.retrieval import (
    ContextBundle,
    ContextFusionRequest,
    RetrievalRequest,
    RetrievalResult,
    RetrievedContextItem,
)


class FakePolicyAdapter:
    """Allow-all policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class FakeRetrievalRouter:
    """Retrieval router fake."""

    def __init__(self) -> None:
        self.requests: list[RetrievalRequest] = []

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        self.requests.append(request)
        return RetrievalResult(
            retrieval_id=request.retrieval_id,
            query=request.query,
            items=[make_memory_item(), make_capability_item()],
            source_counts={"lexical_memory": 1, "capability_registry": 1},
            constraints=[],
            created_at=datetime.now(UTC),
        )


class FakeFusionEngine:
    """Fusion engine fake."""

    def fuse(self, request: ContextFusionRequest) -> ContextBundle:
        return ContextBundle(
            bundle_id="bundle-1",
            retrieval_id=request.retrieval_result.retrieval_id,
            goal=request.goal,
            items=request.retrieval_result.items,
            fused_summary="Retrieved context for goal: alpha",
            memory_refs=["memory-1"],
            capability_refs=["test.echo"],
            graph_node_refs=["node-1"],
            graph_edge_refs=["edge-1"],
            trace_refs=[],
            constraints=["constraint-1"],
            token_budget_hint=100,
            created_at=datetime.now(UTC),
        )


def test_context_compiler_uses_retrieval_router() -> None:
    """ContextCompiler delegates candidate retrieval to RetrievalRouter."""
    router = FakeRetrievalRouter()
    compiler = ContextCompiler(
        policy_adapter=FakePolicyAdapter(),
        retrieval_router=router,
        fusion_engine=FakeFusionEngine(),
    )

    packet = compiler.compile(
        event=make_event(),
        intent=make_intent(),
        scope=["workspace:main"],
    )

    assert router.requests[0].retrieval_id == "retrieval-event-1"
    assert packet.retrieved_memory_ids == ["memory-1"]
    assert packet.available_capability_ids == ["test.echo"]
    assert packet.graph_node_ids == ["node-1"]
    assert packet.graph_edge_ids == ["edge-1"]
    assert packet.constraints == ["constraint-1"]


def make_event() -> AIONEvent:
    """Create a generic event."""
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question.answer",
        actor_id="actor-1",
        workspace_id="workspace-1",
        payload_type="test.payload",
        payload={"question": "alpha"},
        timestamp=datetime.now(UTC),
        correlation_id="corr-1",
        trace_id="trace-1",
        security_scope=["workspace:main"],
    )


def make_intent() -> IntentFrame:
    """Create a generic intent."""
    return IntentFrame(
        intent_id="intent-1",
        event_id="event-1",
        intent_type="question.answer",
        goal="alpha",
        urgency="normal",
        risk_level="low",
        requires_memory=True,
        requires_capability=True,
        requires_approval=False,
        confidence=0.9,
    )


def make_memory_item() -> RetrievedContextItem:
    """Create memory retrieval item."""
    return RetrievedContextItem(
        item_id="item-memory-1",
        source="lexical_memory",
        source_id="memory-1",
        title="semantic",
        content="alpha beta",
        score=0.8,
        confidence=0.9,
        sensitivity="low",
        owner_scope=["workspace:main"],
        memory_type="semantic",
        capability_id=None,
        graph_node_ids=[],
        graph_edge_ids=[],
        trace_refs=[],
        evidence_ref=None,
        metadata={},
    )


def make_capability_item() -> RetrievedContextItem:
    """Create capability retrieval item."""
    return RetrievedContextItem(
        item_id="item-capability-1",
        source="capability_registry",
        source_id="test.echo",
        title="Echo",
        content="Echo generic input",
        score=0.7,
        confidence=0.7,
        sensitivity="low",
        owner_scope=["workspace:main"],
        memory_type=None,
        capability_id="test.echo",
        graph_node_ids=[],
        graph_edge_ids=[],
        trace_refs=[],
        evidence_ref=None,
        metadata={},
    )
