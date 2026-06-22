from __future__ import annotations

from aion_brain.contracts.decisions import (
    DecisionEvaluationRequest,
    DecisionFrameCreateRequest,
    DecisionOptionCreateRequest,
)
from tests.decision_helpers import bundle


def test_option_evaluator_scores_low_risk_above_high_risk() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
            evidence_refs=["evidence-1"],
            belief_refs=["belief-1"],
        )
    )
    low = services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="Low",
            description="Low risk option.",
            risk_level="low",
            reversibility="reversible",
        )
    )
    high = services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="High",
            description="High risk option.",
            risk_level="high",
            reversibility="reversible",
        )
    )

    result = services.evaluator.evaluate(
        DecisionEvaluationRequest(decision_frame_id=frame.decision_frame_id)
    )
    scores = {item.decision_option_id: item.score for item in result.evaluations}

    assert scores[low.decision_option_id] > scores[high.decision_option_id]


def test_option_evaluator_blocks_controlled_action_and_requires_approval() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
        )
    )
    controlled = services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            option_type="controlled_action",
            title="Controlled",
            description="Controlled generic option.",
            risk_level="high",
        )
    )

    result = services.evaluator.evaluate(
        DecisionEvaluationRequest(decision_frame_id=frame.decision_frame_id)
    )
    evaluation = next(
        item
        for item in result.evaluations
        if item.decision_option_id == controlled.decision_option_id
    )

    assert evaluation.status == "blocked"
    assert "controlled_option_not_recommended" in evaluation.constraints
    assert "approval_required" in evaluation.constraints
