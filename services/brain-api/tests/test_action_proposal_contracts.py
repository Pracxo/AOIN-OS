"""Action proposal contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.action_proposals import (
    ActionBlocker,
    ActionProposal,
    ActionProposalCreateRequest,
    ActionProposalReview,
    ToolIntentReviewRequest,
)


def test_action_proposal_validates_proposal_type() -> None:
    with pytest.raises(ValidationError):
        ActionProposalCreateRequest(
            source_type="user_request",
            source_id="source-1",
            proposal_type="not-valid",
            title="T",
            description="D",
            action_type="generic",
            target_type="noop",
            owner_scope=["workspace:main"],
        )


def test_action_proposal_rejects_secret_like_payload() -> None:
    with pytest.raises(ValidationError):
        ActionProposal(
            action_proposal_id="proposal-1",
            source_type="user_request",
            source_id="source-1",
            status="proposed",
            proposal_type="generic",
            title="T",
            description="D",
            action_type="generic",
            target_type="noop",
            owner_scope=["workspace:main"],
            proposed_payload={"api_key": "value"},
            risk_level="low",
        )


def test_action_blocker_validates_blocker_type() -> None:
    with pytest.raises(ValidationError):
        ActionBlocker(
            action_blocker_id="blocker-1",
            blocker_type="unknown",
            severity="medium",
            status="open",
            reason="blocked",
        )


def test_action_proposal_review_validates_decision() -> None:
    with pytest.raises(ValidationError):
        ActionProposalReview(
            action_review_id="review-1",
            action_proposal_id="proposal-1",
            status="completed",
            decision="ship_it",
            reason="no",
        )


def test_tool_intent_review_request_rejects_empty_scope() -> None:
    with pytest.raises(ValidationError):
        ToolIntentReviewRequest(tool_intent_id="tool-1", owner_scope=[])
