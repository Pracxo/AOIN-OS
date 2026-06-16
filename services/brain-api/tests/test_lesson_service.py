from __future__ import annotations

from aion_brain.contracts.learning_synthesis import PatternMiningRequest
from tests.learning_synthesis_helpers import bundle, create_experience_request


def test_lesson_service_creates_generic_lesson_from_pattern() -> None:
    items = bundle()
    first = items.experiences.create_experience(create_experience_request("source-1"))
    second = items.experiences.create_experience(create_experience_request("source-2"))
    pattern = items.miner.mine(
        PatternMiningRequest(
            owner_scope=["workspace:main"],
            experience_ids=[first.experience_id, second.experience_id],
            dry_run=False,
        )
    ).patterns[0]

    lesson = items.lessons.create_lesson_from_pattern(pattern, created_by="tester")

    assert lesson.lesson_type == "planning"
    assert "no_auto_promotion" in lesson.constraints
    assert items.lessons.list_lessons(["workspace:main"])[0].lesson_id == lesson.lesson_id
