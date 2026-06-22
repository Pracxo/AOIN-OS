"""MCP handoff integration tests."""

from __future__ import annotations

from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from tests.action_proposal_fakes import ActionFixture, proposal_request


class MCPServiceSpy:
    def __init__(self) -> None:
        self.called = False

    def invoke(self, request: object) -> None:
        self.called = True


def test_mcp_handoff_is_blocked_and_does_not_invoke_by_default() -> None:
    fixture = ActionFixture()
    mcp_service = MCPServiceSpy()
    fixture.handoffs._mcp_service = mcp_service  # type: ignore[attr-defined]
    proposal = fixture.proposals.create_proposal(
        proposal_request(proposal_type="mcp_tool", target_type="mcp_tool")
    )

    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="mcp_tool_invoke",
            target_system="mcp_adapter",
        )
    )

    assert handoff.status == "blocked"
    assert mcp_service.called is False
