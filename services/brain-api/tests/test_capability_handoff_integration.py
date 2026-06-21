"""Capability Runtime handoff integration tests."""

from __future__ import annotations

from aion_brain.contracts.execution_handoffs import ExecutionHandoffRequest
from tests.action_proposal_fakes import ActionFixture, proposal_request


class CapabilityRuntimeSpy:
    def __init__(self) -> None:
        self.called = False

    def invoke(self, request: object) -> None:
        self.called = True


def test_capability_handoff_builds_invocation_without_invoking_in_dry_run() -> None:
    fixture = ActionFixture()
    runtime = CapabilityRuntimeSpy()
    fixture.handoffs._capability_runtime = runtime  # type: ignore[attr-defined]
    proposal = fixture.proposals.create_proposal(
        proposal_request(
            proposal_type="capability",
            target_type="capability",
            target_id="capability.echo",
        )
    )

    handoff = fixture.handoffs.handoff(
        ExecutionHandoffRequest(
            action_proposal_id=proposal.action_proposal_id,
            handoff_type="capability_invoke",
            target_system="capability_runtime",
        )
    )

    assert handoff.handoff_payload["capability_id"] == "capability.echo"
    assert runtime.called is False
