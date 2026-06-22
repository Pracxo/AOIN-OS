"""Execution handoff service tests."""

from __future__ import annotations

from aion_brain.contracts.action_proposals import ActionProposalReviewRequest
from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from tests.action_proposal_fakes import ActionFixture, proposal_request


def test_execution_handoff_service_dry_run_creates_planned_target_request_only() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(proposal_request())

    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="dry_run",
            target_system="noop",
        )
    )

    assert handoff.status == "dry_run"
    assert handoff.result["accepted_by_target"] is False


def test_execution_handoff_service_controlled_blocks_when_disabled() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(proposal_request())
    fixture.reviews.review(
        ActionProposalReviewRequest(
            action_proposal_id=proposal.action_proposal_id,
            decision="approve_for_handoff",
            reason="approved",
            approval_present=True,
        )
    )

    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="command_dispatch",
            target_system="command_bus",
            mode="controlled",
            approval_present=True,
        )
    )

    assert handoff.status == "blocked"
    assert handoff.blocker_refs


def test_execution_handoff_service_command_bus_uses_command_dispatch_request() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(proposal_request(target_type="workflow"))

    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="command_dispatch",
            target_system="command_bus",
        )
    )

    assert handoff.handoff_payload["command_type"] == "generic"
    assert handoff.handoff_payload["idempotency_key"].startswith("action-proposal:")


def test_execution_handoff_service_workflow_uses_workflow_run_request() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(
        proposal_request(proposal_type="workflow", target_type="workflow", target_id="workflow-1")
    )

    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="workflow_run",
            target_system="workflow_engine",
        )
    )

    assert handoff.handoff_payload["workflow_id"] == "workflow-1"
    assert handoff.status == "dry_run"


def test_execution_handoff_service_capability_stays_dry_run_by_default() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(
        proposal_request(
            proposal_type="capability", target_type="capability", target_id="capability.echo"
        )
    )

    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="capability_invoke",
            target_system="capability_runtime",
        )
    )

    assert handoff.status == "dry_run"
    assert handoff.handoff_payload["capability_id"] == "capability.echo"


def test_execution_handoff_service_mcp_handoff_remains_blocked_unless_enabled() -> None:
    fixture = ActionFixture()
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
    assert handoff.blocker_refs
