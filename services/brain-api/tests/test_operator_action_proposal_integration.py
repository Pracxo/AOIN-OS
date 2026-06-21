"""Operator action proposal visibility tests."""

from __future__ import annotations

from aion_brain.contracts.action_proposals import ActionProposalReviewRequest
from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.queues import QueueSummaryBuilder
from tests.action_proposal_fakes import ActionFixture, proposal_request
from tests.operator_fakes import SCOPE, AllowPolicy, FakeTelemetry, repository


def test_operator_action_center_surfaces_high_risk_action_proposal() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(proposal_request(risk_level="high"))
    service = ActionCenterService(
        repository(),
        AllowPolicy(),
        FakeTelemetry(),
        action_proposal_service=fixture.proposals,
    )

    items = service.build_action_items(SCOPE)

    assert any(
        item.recommended_action == "review_action_proposal"
        and item.source_id == proposal.action_proposal_id
        for item in items
    )


def test_operator_action_center_surfaces_blocked_handoff() -> None:
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
    service = ActionCenterService(
        repository(),
        AllowPolicy(),
        FakeTelemetry(),
        execution_handoff_service=fixture.handoffs,
    )

    items = service.build_action_items(SCOPE)

    assert handoff.status == "blocked"
    assert any(
        item.recommended_action == "review_execution_handoff_blocker"
        and item.source_id == handoff.execution_handoff_id
        for item in items
    )


def test_operator_queue_summary_includes_action_proposals_and_handoffs() -> None:
    fixture = ActionFixture()
    proposal = fixture.proposals.create_proposal(proposal_request())
    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="dry_run",
            target_system="noop",
        )
    )
    builder = QueueSummaryBuilder(
        action_proposal_service=fixture.proposals,
        execution_handoff_service=fixture.handoffs,
    )

    queues = {item.title: item for item in builder.build_queues(SCOPE)}

    assert queues["Action Proposals"].pending_count == 1
    assert queues["Execution Handoffs"].metadata["item_count"] == 1
    assert handoff.status == "dry_run"
