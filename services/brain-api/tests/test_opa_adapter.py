"""OPA adapter tests."""

import json

import httpx

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.policy.opa_adapter import OPAAdapter


def make_policy_request(
    *,
    action_type: str = "memory.retrieve",
    risk_level: str = "low",
    approval_present: bool = False,
) -> PolicyRequest:
    """Create a generic policy request."""
    return PolicyRequest(
        request_id="policy-request-1",
        trace_id="trace-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        action_type=action_type,
        resource_type="memory",
        resource_id="memory-1",
        risk_level=risk_level,
        approval_present=approval_present,
        requested_permissions=["memory:read"],
        security_scope=["memory:read"],
        context={},
    )


def test_low_risk_memory_retrieve_can_be_allowed() -> None:
    """OPAAdapter converts an allow response into PolicyDecision."""
    adapter = OPAAdapter(
        "http://opa.test",
        transport=_transport(
            {
                "allow": True,
                "approval_required": False,
                "reason": "low_risk_memory_retrieval_allowed",
                "constraints": [],
                "audit_level": "standard",
            }
        ),
    )

    decision = adapter.authorize(make_policy_request())

    assert decision.allow is True
    assert decision.approval_required is False
    assert decision.reason == "low_risk_memory_retrieval_allowed"
    assert decision.trace_id == "trace-1"


def test_high_risk_capability_invoke_requires_approval() -> None:
    """OPAAdapter preserves approval-required deny decisions."""
    adapter = OPAAdapter(
        "http://opa.test",
        transport=_transport(
            {
                "allow": False,
                "approval_required": True,
                "reason": "elevated_risk_action_requires_approval",
                "constraints": ["approval_required"],
                "audit_level": "high",
            }
        ),
    )

    decision = adapter.authorize(
        make_policy_request(action_type="capability.invoke", risk_level="high")
    )

    assert decision.allow is False
    assert decision.approval_required is True
    assert decision.constraints == ["approval_required"]


def test_unknown_risk_is_denied() -> None:
    """OPAAdapter preserves unknown-risk deny decisions."""
    adapter = OPAAdapter(
        "http://opa.test",
        transport=_transport(
            {
                "allow": False,
                "approval_required": False,
                "reason": "unknown_risk_level",
                "constraints": ["risk_level_not_allowed"],
                "audit_level": "high",
            }
        ),
    )

    decision = adapter.authorize(make_policy_request(risk_level="mystery"))

    assert decision.allow is False
    assert decision.reason == "unknown_risk_level"
    assert decision.audit_level == "high"


def test_opa_failure_returns_fail_closed_deny() -> None:
    """OPA failures fail closed."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unavailable", request=request)

    adapter = OPAAdapter("http://opa.test", transport=httpx.MockTransport(handler))

    decision = adapter.authorize(make_policy_request())

    assert decision.allow is False
    assert decision.reason == "policy_engine_unavailable"
    assert decision.constraints == ["fail_closed"]


def test_opa_status_uses_health_endpoint_without_live_opa() -> None:
    """OPA status checks are local transport-testable."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/health"
        return httpx.Response(200, json={"status": "ok"})

    adapter = OPAAdapter("http://opa.test", transport=httpx.MockTransport(handler))

    status = adapter.status()

    assert status.available is True
    assert status.policy_loaded is True
    assert status.decision_path == "/v1/data/aion/brain/decision"


def _transport(result: dict[str, object]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        assert request.url.path == "/v1/data/aion/brain/decision"
        assert payload["input"]["request_id"] == "policy-request-1"
        return httpx.Response(200, json={"result": result})

    return httpx.MockTransport(handler)
