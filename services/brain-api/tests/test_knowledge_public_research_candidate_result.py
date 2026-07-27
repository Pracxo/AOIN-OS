from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation


def test_candidate_remains_operator_review_item_not_truth() -> None:
    result = run_simulation()
    review = result.evidence_bundle.operator_review_items[0]
    assert review.operator_review_required is True
    assert review.candidate_is_not_factual_truth is True
    assert review.candidate_approval_authorized is False
