from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.decisions import (
    DecisionFrame,
    DecisionOption,
    OptionEvaluation,
    UtilityProfile,
    generic_balanced_weights,
)


def test_decision_frame_validates_frame_type_and_owner_scope() -> None:
    with pytest.raises(ValidationError):
        DecisionFrame(
            decision_frame_id="frame-1",
            frame_type="bad",
            title="Title",
            question="Question?",
            owner_scope=["workspace:main"],
        )
    with pytest.raises(ValidationError):
        DecisionFrame(
            decision_frame_id="frame-1",
            title="Title",
            question="Question?",
            owner_scope=[],
        )


def test_decision_option_validates_option_type_and_controlled_recommendation() -> None:
    with pytest.raises(ValidationError):
        DecisionOption(
            decision_option_id="option-1",
            decision_frame_id="frame-1",
            option_type="bad",
            title="Option",
            description="Generic option.",
        )
    with pytest.raises(ValidationError):
        DecisionOption(
            decision_option_id="option-1",
            decision_frame_id="frame-1",
            option_type="controlled_action",
            status="recommended",
            title="Option",
            description="Generic option.",
        )


def test_utility_profile_validates_weight_keys_and_blocks_domain_keys() -> None:
    with pytest.raises(ValidationError):
        UtilityProfile(
            utility_profile_id="profile-1",
            name="generic",
            description="Generic profile.",
            owner_scope=["workspace:main"],
            weights={"goal_alignment": 1.0},
        )
    weights = {**generic_balanced_weights(), "finance_return": 0.1}
    with pytest.raises(ValidationError):
        UtilityProfile(
            utility_profile_id="profile-1",
            name="generic",
            description="Generic profile.",
            owner_scope=["workspace:main"],
            weights=weights,
        )


def test_option_evaluation_validates_score_bounds() -> None:
    with pytest.raises(ValidationError):
        OptionEvaluation(
            option_evaluation_id="eval-1",
            decision_frame_id="frame-1",
            decision_option_id="option-1",
            status="passed",
            score=1.5,
            explanation="Generic explanation.",
        )
