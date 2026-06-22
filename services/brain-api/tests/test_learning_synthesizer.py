from __future__ import annotations

from aion_brain.contracts.learning_synthesis import LearningSynthesisRequest
from tests.learning_synthesis_helpers import bundle, create_experience_request


def test_learning_synthesizer_dry_run_creates_review_material_without_promotion() -> None:
    items = bundle()
    first = items.experiences.create_experience(create_experience_request("source-1"))
    second = items.experiences.create_experience(create_experience_request("source-2"))

    run = items.synthesizer.synthesize(
        LearningSynthesisRequest(
            owner_scope=["workspace:main"],
            experience_ids=[first.experience_id, second.experience_id],
            create_skill_suggestions=True,
            create_regression_suggestions=True,
        )
    )

    assert run.status == "dry_run"
    assert run.lessons
    assert run.skill_candidate_suggestions
    assert run.regression_candidate_suggestions
    assert run.result["skill_promoted"] is False
    assert run.result["code_modified"] is False
    assert run.result["external_calls"] is False


def test_learning_synthesizer_controlled_persists_review_records() -> None:
    items = bundle()
    first = items.experiences.create_experience(create_experience_request("source-1"))
    second = items.experiences.create_experience(create_experience_request("source-2"))

    run = items.synthesizer.synthesize(
        LearningSynthesisRequest(
            mode="controlled",
            owner_scope=["workspace:main"],
            experience_ids=[first.experience_id, second.experience_id],
            create_skill_suggestions=True,
            create_regression_suggestions=True,
        )
    )

    assert run.status == "completed"
    assert items.lessons.list_lessons(["workspace:main"])
    assert items.skill_suggestions.list_suggestions(["workspace:main"])
    assert items.regression_suggestions.list_suggestions(["workspace:main"])
