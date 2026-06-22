"""Policy API tests."""

from typing import Any

from fastapi.testclient import TestClient

from aion_brain.api.policy import get_policy_adapter
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.main import app


class FakePolicyAdapter:
    """Fake policy adapter for API tests."""

    def __init__(self, decision: PolicyDecision) -> None:
        self.decision = decision
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return self.decision


def test_policy_authorize_api_returns_policy_decision() -> None:
    """POST /brain/policy/authorize returns a PolicyDecision."""
    adapter = FakePolicyAdapter(
        PolicyDecision(
            decision_id="decision-1",
            trace_id="trace-1",
            allow=True,
            approval_required=False,
            reason="low_risk_memory_retrieval_allowed",
            constraints=[],
            audit_level="standard",
        )
    )
    app.dependency_overrides[get_policy_adapter] = lambda: adapter
    try:
        response = TestClient(app).post("/brain/policy/authorize", json=policy_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "decision_id": "decision-1",
        "trace_id": "trace-1",
        "allow": True,
        "approval_required": False,
        "reason": "low_risk_memory_retrieval_allowed",
        "constraints": [],
        "audit_level": "standard",
    }
    assert adapter.requests[0].action_type == "memory.retrieve"


def test_policy_authorize_api_validates_request() -> None:
    """Invalid policy requests return a validation error."""
    payload = policy_payload()
    del payload["action_type"]

    response = TestClient(app).post("/brain/policy/authorize", json=payload)

    assert response.status_code == 422


def policy_payload() -> dict[str, Any]:
    """Return a valid generic policy request payload."""
    return {
        "request_id": "policy-request-1",
        "trace_id": "trace-1",
        "actor_id": "actor-1",
        "workspace_id": "workspace-1",
        "action_type": "memory.retrieve",
        "resource_type": "memory",
        "resource_id": "memory-1",
        "risk_level": "low",
        "approval_present": False,
        "requested_permissions": ["memory:read"],
        "security_scope": ["memory:read"],
        "context": {},
    }
