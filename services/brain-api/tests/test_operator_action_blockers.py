from __future__ import annotations

from tests.operator_action_fakes import OperatorActionFixture, operator_action_request


def test_blocker_service_dismiss_does_not_enable_execution() -> None:
    fixture = OperatorActionFixture()
    request = fixture.requests.create_request(operator_action_request())
    blocker_id = request.blocker_refs[0]

    blocker = fixture.blockers.dismiss_blocker(blocker_id, actor_id="actor-1", reason="reviewed")

    assert blocker.status == "dismissed"
    assert blocker.metadata["execution_allowed"] is False
