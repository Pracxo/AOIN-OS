from __future__ import annotations

from aion_brain.contracts.experience import ExperienceQuery
from aion_brain.contracts.learning_synthesis import LearningSynthesisRequest
from tests.learning_synthesis_helpers import bundle, create_experience_request


def test_learning_query_returns_experiences_patterns_lessons_and_suggestions() -> None:
    items = bundle()
    first = items.experiences.create_experience(create_experience_request("source-1"))
    second = items.experiences.create_experience(create_experience_request("source-2"))
    items.synthesizer.synthesize(
        LearningSynthesisRequest(
            mode="controlled",
            owner_scope=["workspace:main"],
            experience_ids=[first.experience_id, second.experience_id],
            create_skill_suggestions=True,
            create_regression_suggestions=True,
        )
    )

    result = items.query.query(ExperienceQuery(scope=["workspace:main"]))

    assert result.experiences
    assert result.patterns
    assert result.lessons
    assert result.skill_suggestions
    assert result.regression_suggestions
