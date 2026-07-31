from __future__ import annotations

import pytest

from tests.model_gateway_aion233_test_support import gateway_setup


def test_session_repository_allows_one_active_session_and_closes_cleanly() -> None:
    setup = gateway_setup()
    assert setup.session.status.value == "active"
    assert len(setup.service.session_repository.active_sessions()) == 1
    closed = setup.service.close_session(
        session_id=setup.session.session_id,
        closed_at=setup.plan.created_at,
    )
    assert closed.status.value == "closed"
    assert closed.active_request_ids == ()


def test_second_active_session_is_rejected() -> None:
    setup = gateway_setup()
    with pytest.raises(ValueError):
        setup.service.start_session(setup.plan)
