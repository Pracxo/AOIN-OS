from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.learning_synthesis import (
    LearningSynthesisRequest,
    SkillCandidateSuggestion,
)


def test_learning_synthesis_request_requires_owner_scope() -> None:
    with pytest.raises(ValidationError):
        LearningSynthesisRequest(owner_scope=[])


def test_skill_suggestion_cannot_allow_promotion() -> None:
    with pytest.raises(ValidationError):
        SkillCandidateSuggestion(
            suggestion_id="suggestion-1",
            title="Review procedure",
            description="Review only.",
            owner_scope=["workspace:main"],
            proposed_skill_type="generic",
            risk_level="low",
            confidence=0.8,
            promotion_allowed=True,
        )
