from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.dialogue import DialogueFeedback
from aion_brain.contracts.responses import ResponseDraft, ResponseVerification


def test_response_draft_rejects_hidden_reasoning_content() -> None:
    with pytest.raises(ValidationError):
        ResponseDraft(
            response_id="response-1",
            status="draft",
            response_type="answer",
            content="hidden_reasoning: internal",
            content_hash="hash",
            grounded=False,
        )


def test_response_verification_validates_score() -> None:
    verification = ResponseVerification(
        verification_id="verification-1",
        response_id="response-1",
        status="passed",
        grounded=True,
        policy_ok=True,
        autonomy_ok=True,
        approval_required=False,
        score=1.0,
    )

    assert verification.score == 1.0
    with pytest.raises(ValidationError):
        ResponseVerification(
            verification_id="verification-2",
            response_id="response-1",
            status="passed",
            grounded=True,
            policy_ok=True,
            autonomy_ok=True,
            approval_required=False,
            score=1.5,
        )


def test_dialogue_feedback_validates_rating_bounds() -> None:
    feedback = DialogueFeedback(feedback_id="feedback-1", feedback_type="helpful", rating=5)

    assert feedback.rating == 5
    with pytest.raises(ValidationError):
        DialogueFeedback(feedback_id="feedback-2", feedback_type="helpful", rating=6)
