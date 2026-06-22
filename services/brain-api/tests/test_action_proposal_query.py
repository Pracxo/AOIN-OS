"""Action proposal query tests."""

from __future__ import annotations

from aion_brain.contracts.action_proposals import ActionProposalQuery
from tests.action_proposal_fakes import ActionFixture, proposal_request


def test_action_proposal_query_service_returns_related_records() -> None:
    fixture = ActionFixture()
    fixture.proposals.create_proposal(proposal_request(trace_id="trace-1"))

    result = fixture.proposals.query(
        ActionProposalQuery(scope=["workspace:main"], trace_id="trace-1")
    )

    assert result.total_count == 1
    assert result.constraints == ["proposals_do_not_execute"]
