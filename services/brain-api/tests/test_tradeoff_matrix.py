from __future__ import annotations

from aion_brain.contracts.decisions import (
    DecisionEvaluationRequest,
    DecisionFrameCreateRequest,
    DecisionOptionCreateRequest,
)
from tests.decision_helpers import bundle


def test_tradeoff_matrix_ranks_highest_non_blocked_option() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
            evidence_refs=["evidence-1"],
        )
    )
    option = services.option_service.create_option(
        DecisionOptionCreateRequest(
            decision_frame_id=frame.decision_frame_id,
            title="Reversible low",
            description="Low risk option.",
            risk_level="low",
            reversibility="reversible",
        )
    )

    result = services.evaluator.evaluate(
        DecisionEvaluationRequest(decision_frame_id=frame.decision_frame_id)
    )

    assert result.tradeoff_matrix is not None
    assert result.tradeoff_matrix.recommended_option_id == option.decision_option_id
