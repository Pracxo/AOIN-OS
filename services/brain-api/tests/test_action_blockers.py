"""Action blocker service tests."""

from __future__ import annotations

from tests.action_proposal_fakes import ActionFixture


def test_action_blocker_resolve_does_not_execute() -> None:
    fixture = ActionFixture()
    blocker = fixture.blockers.create_blocker(
        blocker_type="generic",
        severity="medium",
        reason="needs_review",
    )

    resolved = fixture.blockers.resolve_blocker(
        blocker.action_blocker_id,
        actor_id="actor-1",
        reason="reviewed",
    )

    assert resolved.status == "resolved"
    assert resolved.metadata["resolution_reason"] == "reviewed"
