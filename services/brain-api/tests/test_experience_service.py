from __future__ import annotations

import pytest

from aion_brain.contracts.experience import ExperienceQuery
from tests.learning_synthesis_helpers import DenyPolicy, bundle, create_experience_request


def test_experience_service_records_and_queries_experiences() -> None:
    items = bundle()
    record = items.experiences.create_experience(create_experience_request("source-1"))

    result = items.experiences.query(
        ExperienceQuery(scope=["workspace:main"], query="repeated", limit=10)
    )

    assert record.experience_id
    assert result.total_count == 1
    assert result.experiences[0].experience_id == record.experience_id
    assert [event.event_type for event in items.telemetry.events] == [
        "experience_recorded",
        "learning_query_completed",
    ]


def test_policy_deny_blocks_experience_write() -> None:
    items = bundle(DenyPolicy())

    with pytest.raises(PermissionError):
        items.experiences.create_experience(create_experience_request("source-1"))
