from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.experience import ExperienceCreateRequest, ExperienceQuery


def test_experience_request_rejects_secret_like_metadata() -> None:
    with pytest.raises(ValidationError):
        ExperienceCreateRequest(
            source_type="generic",
            source_id="source-1",
            experience_type="generic",
            title="Experience",
            summary="A generic experience.",
            owner_scope=["workspace:main"],
            metadata={"api_key": "hidden"},
        )


def test_experience_query_requires_scope() -> None:
    with pytest.raises(ValidationError):
        ExperienceQuery(scope=[])
