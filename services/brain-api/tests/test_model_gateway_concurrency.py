from __future__ import annotations

import pytest

from tests.model_gateway_aion233_test_support import gateway_setup


def test_gateway_session_enforces_four_active_request_limit() -> None:
    setup = gateway_setup()
    session = setup.session
    for index in range(4):
        session = setup.service.session_repository.mark_request_active(
            setup.session.session_id,
            f"request-{index}",
        )
    assert len(session.active_request_ids) == 4
    with pytest.raises(ValueError):
        setup.service.session_repository.mark_request_active(
            setup.session.session_id,
            "request-4",
        )
