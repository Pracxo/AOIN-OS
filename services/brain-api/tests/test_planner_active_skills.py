"""Planner active skill metadata tests."""

from aion_brain.contracts.skills import SkillMatchResult
from aion_brain.planning.planner import Planner
from tests.test_planner import make_context
from tests.test_skill_service import make_skill


def test_planner_includes_matched_skill_ids_in_metadata() -> None:
    """Planner records matched skills without executing skill steps."""
    plan = Planner().create_plan(
        make_context("question.answer"),
        skills=[
            SkillMatchResult(
                skill=make_skill(status="active"),
                score=0.8,
                matched_patterns=["question.answer"],
                reason="deterministic_token_overlap",
            )
        ],
    )

    assert plan.metadata["matched_skill_ids"] == ["skill-1"]
    assert [step.step_id for step in plan.steps] == [
        "retrieve_context",
        "draft_response",
        "evaluate_response",
    ]
