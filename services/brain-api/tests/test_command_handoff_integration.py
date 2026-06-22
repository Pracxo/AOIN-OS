"""Command Bus handoff integration tests."""

from __future__ import annotations

from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from tests.action_proposal_fakes import ActionFixture, proposal_request


class CommandBusSpy:
    def __init__(self) -> None:
        self.called = False

    def dispatch(self, request: object) -> None:
        self.called = True


def test_command_handoff_builds_command_request_without_dispatching_in_dry_run() -> None:
    fixture = ActionFixture()
    command_bus = CommandBusSpy()
    fixture.handoffs._command_bus = command_bus  # type: ignore[attr-defined]
    proposal = fixture.proposals.create_proposal(proposal_request(target_type="workflow"))

    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="command_dispatch",
            target_system="command_bus",
        )
    )

    assert handoff.handoff_payload["command_type"] == "generic"
    assert command_bus.called is False
