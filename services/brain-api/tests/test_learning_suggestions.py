from __future__ import annotations

import pytest

from aion_brain.contracts.learning_synthesis import PatternMiningRequest
from tests.learning_synthesis_helpers import bundle, create_experience_request


def _pattern() -> tuple[object, object]:
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
    return items, pattern


def test_skill_suggestion_accept_reject_and_convert_are_review_only() -> None:
    items, pattern = _pattern()
    lesson = items.lessons.create_lesson_from_pattern(pattern, "tester")
    suggestion = items.skill_suggestions.create_suggestion_from_pattern(
        pattern,
        lesson,
        "tester",
    )

    accepted = items.skill_suggestions.accept_suggestion(
        suggestion.suggestion_id,
        "actor-1",
        "reviewed",
    )
    converted = items.skill_suggestions.convert_to_skill_candidate(
        accepted.suggestion_id,
        "actor-1",
        approval_present=True,
        reason="candidate only",
    )

    assert accepted.status == "accepted"
    assert converted.status == "converted"
    assert converted.skill_candidate_id
    assert converted.metadata["skill_record_created"] is False


def test_high_risk_skill_suggestion_conversion_requires_approval() -> None:
    items, pattern = _pattern()
    high_pattern = pattern.model_copy(update={"severity": "high"})
    suggestion = items.skill_suggestions.create_suggestion_from_pattern(
        high_pattern,
        None,
        "tester",
    )

    with pytest.raises(PermissionError):
        items.skill_suggestions.convert_to_skill_candidate(
            suggestion.suggestion_id,
            "actor-1",
            approval_present=False,
            reason="candidate only",
        )


def test_regression_suggestion_accept_reject_is_review_only() -> None:
    items, pattern = _pattern()
    suggestion = items.regression_suggestions.create_suggestion_from_failure(
        pattern,
        "outcome-1",
        "tester",
    )

    accepted = items.regression_suggestions.accept_suggestion(
        suggestion.regression_suggestion_id,
        "actor-1",
        "reviewed",
    )
    rejected = items.regression_suggestions.reject_suggestion(
        accepted.regression_suggestion_id,
        "actor-1",
        "superseded",
    )

    assert rejected.status == "rejected"
    assert rejected.regression_case_id is None
    assert rejected.metadata["regression_case_created"] is False
