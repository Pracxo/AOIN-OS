from __future__ import annotations

import pytest

from aion_brain.contracts.dialogue import DialogueSessionCreateRequest
from tests.dialogue_helpers import DenyPolicy, service_bundle


def test_dialogue_session_service_creates_session_through_policy() -> None:
    bundle = service_bundle()

    session = bundle.session_service.create_session(
        DialogueSessionCreateRequest(title="Session", owner_scope=["workspace:main"])
    )

    assert session.status == "active"
    assert bundle.session_service.get_session(session.dialogue_session_id, ["workspace:main"])


def test_policy_deny_blocks_session_create() -> None:
    bundle = service_bundle(DenyPolicy())

    with pytest.raises(PermissionError):
        bundle.session_service.create_session(
            DialogueSessionCreateRequest(title="Session", owner_scope=["workspace:main"])
        )
