from __future__ import annotations

from aion_brain.contracts.learning_synthesis import LearningSynthesisRequest
from tests.learning_synthesis_helpers import bundle, create_experience_request


def test_learning_synthesis_emits_visual_telemetry_events() -> None:
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

    event_types = {event.event_type for event in items.telemetry.events}

    assert "experience_recorded" in event_types
    assert "learning_pattern_detected" in event_types
    assert "lesson_created" in event_types
    assert "skill_candidate_suggestion_created" in event_types
    assert "regression_candidate_suggestion_created" in event_types
    assert "learning_synthesis_completed" in event_types
