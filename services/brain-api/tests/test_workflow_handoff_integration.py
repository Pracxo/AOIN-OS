"""Workflow Engine handoff integration tests."""

from __future__ import annotations

from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from tests.action_proposal_fakes import ActionFixture, proposal_request


class WorkflowServiceSpy:
    def __init__(self) -> None:
        self.called = False

    def run_workflow(self, request: object) -> None:
        self.called = True


def test_workflow_handoff_builds_workflow_request_without_running_in_dry_run() -> None:
    fixture = ActionFixture()
    workflow_service = WorkflowServiceSpy()
    fixture.handoffs._workflow_service = workflow_service  # type: ignore[attr-defined]
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
    assert workflow_service.called is False
