"""Policy contract tests."""

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest


def make_policy_request() -> PolicyRequest:
    """Create a valid generic policy request."""
    return PolicyRequest(
        request_id="policy-request-1",
        trace_id="trace-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        action_type="memory.retrieve",
        resource_type="memory",
        resource_id="memory-1",
        risk_level="low",
        approval_present=False,
        requested_permissions=["memory:read"],
        security_scope=["memory:read"],
        context={"purpose": "test"},
    )


def test_policy_request_serializes() -> None:
    """PolicyRequest preserves required fields during JSON serialization."""
    request = make_policy_request()

    dumped = request.model_dump(mode="json")

    assert dumped["request_id"] == "policy-request-1"
    assert dumped["action_type"] == "memory.retrieve"
    assert dumped["requested_permissions"] == ["memory:read"]


def test_policy_decision_serializes() -> None:
    """PolicyDecision preserves required fields during JSON serialization."""
    decision = PolicyDecision(
        decision_id="decision-1",
        trace_id="trace-1",
        allow=True,
        approval_required=False,
        reason="low_risk_memory_retrieval_allowed",
        constraints=[],
        audit_level="standard",
    )

    dumped = decision.model_dump(mode="json")

    assert dumped["decision_id"] == "decision-1"
    assert dumped["allow"] is True
    assert dumped["audit_level"] == "standard"
