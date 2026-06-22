"""Context compiler graph memory integration tests."""

from datetime import UTC, datetime

from aion_brain.context.compiler import ContextCompiler
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.graph import GraphEdge, GraphNode, GraphQuery, GraphQueryResult
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest


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


class FakeGraphService:
    """Graph service fake for compiler tests."""

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        return GraphQueryResult(
            nodes=[make_node("node-1")],
            edges=[make_edge("edge-1")],
            score=1.0,
            retrieval_source="graph",
            adapter_name="fake",
            metadata={"query": query.query},
        )


def test_context_compiler_includes_graph_context_when_available() -> None:
    """Compiler adds graph node and edge IDs without changing other context."""
    compiler = ContextCompiler(
        policy_adapter=FakePolicyAdapter(),
        graph_service=FakeGraphService(),
    )

    packet = compiler.compile(
        event=make_event(),
        intent=make_intent(),
        scope=["workspace:main"],
    )

    assert "node-1" in packet.graph_node_ids
    assert packet.graph_edge_ids == ["edge-1"]
    assert any(item["source"] == "graph_memory" for item in packet.known_context)


def make_event() -> AIONEvent:
    """Create a generic event."""
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question.answer",
        actor_id="actor-1",
        workspace_id="workspace-1",
        payload_type="test.payload",
        payload={"question": "what happens?"},
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
        goal="what happens?",
        urgency="normal",
        risk_level="low",
        requires_memory=True,
        requires_capability=False,
        requires_approval=False,
        confidence=0.8,
    )


def make_node(node_id: str) -> GraphNode:
    """Create a generic graph node."""
    return GraphNode(
        node_id=node_id,
        node_type="concept",
        label=node_id,
        owner_scope=["workspace:main"],
        properties={},
        source_event_id=None,
        confidence=0.8,
        sensitivity="low",
        valid_from=None,
        valid_to=None,
        observed_at=datetime.now(UTC),
    )


def make_edge(edge_id: str) -> GraphEdge:
    """Create a generic graph edge."""
    return GraphEdge(
        edge_id=edge_id,
        edge_type="related_to",
        from_node_id="node-1",
        to_node_id="node-2",
        owner_scope=["workspace:main"],
        properties={},
        source_event_id=None,
        confidence=0.7,
        sensitivity="low",
        valid_from=None,
        valid_to=None,
        observed_at=datetime.now(UTC),
    )
