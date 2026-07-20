"""AION-178 shadow operator-review item tests."""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_contracts import NOW, make_observation

from aion_brain.self_improvement.shadow_pipeline import (
    ShadowOperatorReviewItem,
    generate_shadow_hypotheses,
    generate_shadow_improvement_proposals,
    generate_shadow_regression_proposals,
    mine_shadow_failure_patterns,
    project_shadow_operator_review_items,
)


def _review_item() -> ShadowOperatorReviewItem:
    pattern = mine_shadow_failure_patterns(
        (make_observation(repeated_count=2),),
        maximum_patterns=100,
        created_at=NOW,
    )[0]
    hypothesis = generate_shadow_hypotheses((pattern,), maximum_hypotheses=50, created_at=NOW)[0]
    regression = generate_shadow_regression_proposals(
        (hypothesis,),
        maximum_proposals=25,
        created_at=NOW,
    )[0]
    proposal = generate_shadow_improvement_proposals(
        (hypothesis,),
        (regression,),
        (pattern,),
        maximum_proposals=10,
        created_at=NOW,
    )[0]
    return project_shadow_operator_review_items(
        (proposal,),
        budget_status="within_budget",
        created_at=NOW,
        expires_at=NOW + timedelta(days=1),
    )[0]


def test_operator_review_item_is_pending_and_inert() -> None:
    item = _review_item()

    assert item.review_state == "operator_review_pending"
    assert item.operator_review_required is True
    assert item.implementation_authorization_created is False
    assert item.approval_created is False
    assert item.source_modified is False
    assert item.git_mutated is False
    assert item.pull_request_created is False
    assert item.merged is False
    assert item.runtime_effect is False
    assert item.active_learning_promoted is False


def test_operator_review_item_expiry_and_states_are_enforced() -> None:
    item = _review_item()
    payload = item.model_dump(mode="python")

    with pytest.raises(ValidationError):
        ShadowOperatorReviewItem(**{**payload, "expires_at": NOW - timedelta(seconds=1)})
    with pytest.raises(ValidationError):
        ShadowOperatorReviewItem(**{**payload, "approval_created": True})
