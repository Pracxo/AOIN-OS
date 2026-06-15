"""Graph memory service tests."""

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.graph import GraphNode
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.memory.graph_service import GraphMemoryPolicyDenied, GraphMemoryService
from aion_brain.memory.in_memory_graph_adapter import InMemoryGraphAdapter


class FakePolicyAdapter:
    """Policy fake for graph service tests."""

    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard",
        )


def test_graph_memory_service_calls_policy_before_write() -> None:
    """Graph writes are policy-gated."""
    policy = FakePolicyAdapter()
    adapter = InMemoryGraphAdapter()
    service = GraphMemoryService(adapter=adapter, policy_adapter=policy)

    service.upsert_node(make_node("node-1"))

    assert policy.requests[0].action_type == "memory.write"
    assert adapter.get_node("node-1", ["workspace:main"]) is not None


def test_policy_deny_blocks_graph_write() -> None:
    """Policy denial prevents graph mutation."""
    policy = FakePolicyAdapter(allow=False)
    adapter = InMemoryGraphAdapter()
    service = GraphMemoryService(adapter=adapter, policy_adapter=policy)

    with pytest.raises(GraphMemoryPolicyDenied):
        service.upsert_node(make_node("node-1"))

    assert adapter.get_node("node-1", ["workspace:main"]) is None


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
