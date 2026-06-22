from __future__ import annotations

import pytest

from aion_brain.contracts.decisions import DecisionFrameCreateRequest
from tests.decision_helpers import DenyPolicy, bundle


def test_decision_frame_service_creates_frame_through_policy() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose next step",
            question="What should happen next?",
            owner_scope=["workspace:main"],
        )
    )

    assert frame.status == "open"
    assert frame.owner_scope == ["workspace:main"]


def test_policy_deny_blocks_frame_create() -> None:
    services = bundle(DenyPolicy())

    with pytest.raises(PermissionError):
        services.frame_service.create_frame(
            DecisionFrameCreateRequest(
                title="Choose next step",
                question="What should happen next?",
                owner_scope=["workspace:main"],
            )
        )
