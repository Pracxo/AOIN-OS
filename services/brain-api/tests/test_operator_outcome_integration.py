from __future__ import annotations

from aion_brain.contracts.outcomes import OutcomeCreateRequest, OutcomeFeedback
from tests.kernel_fakes import kernel_container


def test_operator_action_center_surfaces_failed_outcome_and_feedback() -> None:
    container = kernel_container()
    outcome = container.outcome_service.create_outcome(
        OutcomeCreateRequest(
            source_type="command",
            source_id="command-1",
            outcome_type="command",
            title="Failed outcome",
            summary="Required effect missing.",
            owner_scope=["workspace:main"],
            metadata={"manual": True},
        )
    )
    container.outcome_repository.save_outcome(outcome.model_copy(update={"status": "failed"}))
    container.outcome_feedback_service.create_feedback(
        OutcomeFeedback(
            outcome_feedback_id="feedback-high",
            outcome_id=outcome.outcome_id,
            source_type="outcome",
            source_id=outcome.outcome_id,
            feedback_type="failure_pattern",
            status="open",
            severity="high",
            message="Failure pattern.",
            recommended_followup="Review only.",
            metadata={},
        )
    )

    items = container.operator_action_center_service.build_action_items(["workspace:main"])
    source_types = {item.source_type for item in items}

    assert "outcome" in source_types
    assert "outcome_feedback" in source_types
