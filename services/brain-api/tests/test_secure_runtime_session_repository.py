from __future__ import annotations

import pytest

from aion_brain.contracts.secure_runtime import (
    InMemorySecureRuntimeSessionRepository,
    SecureRuntimeSession,
)
from tests.secure_runtime_test_support import NOW, secure_runtime_fixture


def test_repository_tracks_one_active_session_and_releases_requests_on_close() -> None:
    fixture = secure_runtime_fixture()
    repo = fixture.service.repository.with_request(fixture.request)
    assert repo.active_session_count() == 1
    assert repo.active_request_count(fixture.session.session_id) == 1
    repo = repo.complete_request(
        session_id=fixture.session.session_id, request_id=fixture.request.request_id
    )
    repo = repo.close_session(session_id=fixture.session.session_id, closed_at=NOW)
    assert repo.active_request_count(fixture.session.session_id) == 0
    assert repo.active_session_count() == 0


def test_repository_rejects_second_active_session() -> None:
    fixture = secure_runtime_fixture()
    second = SecureRuntimeSession(
        session_id="session-AION-231-B",
        session_plan=fixture.session_plan,
        created_at=NOW,
        expires_at=fixture.authorization.expires_at,
    )
    with pytest.raises(ValueError, match="only one active"):
        InMemorySecureRuntimeSessionRepository().with_session(fixture.session).with_session(second)
