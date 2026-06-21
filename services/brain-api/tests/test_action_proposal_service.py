"""Action proposal service tests."""

from __future__ import annotations

import pytest

from tests.action_proposal_fakes import ActionFixture, DenyPolicy, proposal_request


def test_action_proposal_service_creates_proposal_through_policy() -> None:
    fixture = ActionFixture()

    proposal = fixture.proposals.create_proposal(proposal_request())

    assert proposal.status == "proposed"
    assert proposal.metadata["no_execution"] is True


def test_policy_deny_blocks_proposal_create() -> None:
    fixture = ActionFixture(policy=DenyPolicy())

    with pytest.raises(PermissionError):
        fixture.proposals.create_proposal(proposal_request())


def test_action_proposal_service_creates_blocker_for_external_target_disabled() -> None:
    fixture = ActionFixture()

    proposal = fixture.proposals.create_proposal(
        proposal_request(target_type="external", proposed_payload={"target_type": "external"})
    )

    assert proposal.status == "blocked"
    assert proposal.blocker_refs
