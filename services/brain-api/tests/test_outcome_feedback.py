from __future__ import annotations

from aion_brain.contracts.outcomes import OutcomeCreateRequest, OutcomeFeedback
from tests.outcome_helpers import bundle


class SkillService:
    promoted = False

    def promote(self) -> None:
        self.promoted = True


def test_outcome_feedback_service_creates_missing_effect_feedback() -> None:
    env = bundle()
    feedback = env.feedback.create_feedback(
        OutcomeFeedback(
            outcome_feedback_id="feedback-1",
            outcome_id="outcome-1",
            source_type="outcome",
            source_id="outcome-1",
            feedback_type="missing_effect",
            status="open",
            severity="medium",
            message="A required effect is missing.",
            recommended_followup="Review expected and observed effects.",
            metadata={},
        )
    )

    assert feedback.feedback_type == "missing_effect"


def test_learning_bridge_dry_run_creates_no_learning_signal() -> None:
    env = bundle()
    outcome = env.outcomes.create_outcome(
        OutcomeCreateRequest(
            source_type="command",
            source_id="command-1",
            outcome_type="command",
            title="Outcome",
            summary="Unknown.",
            owner_scope=["workspace:main"],
        )
    )

    result = env.feedback.bridge_to_learning(outcome.outcome_id, dry_run=True)

    assert result["learning_signal_created"] is False


def test_outcome_feedback_does_not_auto_create_or_promote_skills() -> None:
    env = bundle()
    skill_service = SkillService()
    env.feedback._skill_service = skill_service  # noqa: SLF001

    env.feedback.create_feedback(
        OutcomeFeedback(
            outcome_feedback_id="feedback-1",
            source_type="outcome",
            source_id="outcome-1",
            feedback_type="skill_candidate",
            status="open",
            severity="low",
            message="Could become a skill later.",
            recommended_followup="Review manually.",
            metadata={"create_skill_candidate": True},
        )
    )

    assert skill_service.promoted is False
