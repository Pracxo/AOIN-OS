"""Policy adapter audit integration tests."""

from __future__ import annotations

import httpx

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.policy.opa_adapter import OPAAdapter


class FakeAuditSink:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def record(self, audit_request: object) -> object:
        self.requests.append(audit_request)
        return audit_request


def test_policy_adapter_records_audit_entry() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "result": {
                    "allow": True,
                    "approval_required": False,
                    "reason": "allowed",
                    "constraints": [],
                    "audit_level": "standard",
                }
            },
        )

    sink = FakeAuditSink()
    adapter = OPAAdapter("http://opa.test", transport=httpx.MockTransport(handler))
    adapter.set_audit_sink(sink)

    adapter.authorize(
        PolicyRequest(
            request_id="policy-1",
            trace_id="trace-1",
            actor_id="actor-1",
            workspace_id="workspace-1",
            action_type="memory.retrieve",
            resource_type="memory",
            resource_id="memory-1",
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=["workspace:main"],
            context={},
        )
    )

    assert sink.requests[0].event_type == "policy_decision_generated"
