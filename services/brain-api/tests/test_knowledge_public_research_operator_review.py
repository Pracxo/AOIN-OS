from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation


def test_operator_review_does_not_create_approval() -> None:
    review = run_simulation().evidence_bundle.operator_review_items[0]
    assert review.approval_created is False
    assert review.implementation_authorization_created is False
