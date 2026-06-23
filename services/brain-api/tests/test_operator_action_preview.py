from __future__ import annotations

from tests.operator_action_fakes import OperatorActionFixture, operator_action_request


def test_preview_service_creates_blocked_preview() -> None:
    fixture = OperatorActionFixture()
    request = fixture.requests.create_request(operator_action_request())
    preview = fixture.previews.create_preview(
        request.operator_action_request_id,
        request.owner_scope,
    )

    assert preview.status == "blocked"
    assert preview.would_execute is False
    assert preview.execution_allowed is False
    assert preview.blockers
