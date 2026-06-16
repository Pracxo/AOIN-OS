from __future__ import annotations

from aion_brain.contracts.decisions import DecisionFrameCreateRequest
from tests.decision_helpers import bundle


def test_recommendation_service_proposes_evaluates_and_runs_counterfactuals() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
            constraints=["unclear_goal"],
        )
    )

    recommendation = services.recommendations.recommend(frame.decision_frame_id)

    assert recommendation.recommended_option_id is not None
    assert recommendation.evaluations
    assert recommendation.counterfactuals
    assert "not execution" in recommendation.explanation
