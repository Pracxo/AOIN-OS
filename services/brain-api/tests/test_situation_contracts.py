from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.situations import SituationCreateRequest, SituationRecord
from tests.situation_helpers import now


def test_situation_record_validates_confidence_and_scope() -> None:
    with pytest.raises(ValidationError):
        SituationRecord(
            situation_id="situation-1",
            status="active",
            situation_type="general",
            title="Current state",
            summary="Generic state.",
            owner_scope=[],
            confidence=1.2,
        )


def test_situation_create_rejects_secret_and_domain_metadata() -> None:
    with pytest.raises(ValidationError):
        SituationCreateRequest(
            title="Current state",
            summary="Generic state.",
            owner_scope=["workspace:main"],
            metadata={"api_key": "hidden"},
        )
    with pytest.raises(ValidationError):
        SituationCreateRequest(
            title="Finance state",
            summary="Generic state.",
            owner_scope=["workspace:main"],
        )


def test_situation_create_accepts_generic_record() -> None:
    request = SituationCreateRequest(
        trace_id="trace-1",
        situation_type="general",
        title="Current state",
        summary="Generic state.",
        owner_scope=["workspace:main"],
        confidence=0.7,
        metadata={"created_at": now().isoformat()},
    )

    assert request.situation_type == "general"
