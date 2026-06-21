"""Tool intent review service tests."""

from __future__ import annotations

from aion_brain.config import Settings
from aion_brain.contracts.action_proposals import ToolIntentReviewRequest
from tests.action_proposal_fakes import ActionFixture, FakeToolIntentRepository, tool_intent


def test_tool_intent_review_blocks_when_execution_disabled() -> None:
    fixture = ActionFixture(tool_intent_repository=FakeToolIntentRepository(tool_intent()))

    review = fixture.tool_reviews.review(
        ToolIntentReviewRequest(tool_intent_id="tool-intent-1", owner_scope=["workspace:main"])
    )

    assert review.decision == "block"
    assert review.blocker_refs


def test_tool_intent_review_creates_proposal_when_safe_and_requested() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_TOOL_INTENT_EXECUTION_ENABLED=True,
    )
    fixture = ActionFixture(
        settings=settings,
        tool_intent_repository=FakeToolIntentRepository(tool_intent()),
    )

    review = fixture.tool_reviews.review(
        ToolIntentReviewRequest(tool_intent_id="tool-intent-1", owner_scope=["workspace:main"])
    )

    assert review.decision == "create_proposal"
    assert review.action_proposal_id is not None
