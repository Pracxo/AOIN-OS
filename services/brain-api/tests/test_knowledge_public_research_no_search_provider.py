from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation


def test_boundary_flag_remains_disabled() -> None:
    review = run_simulation().evidence_bundle.operator_review_items[0]
    assert review.search_provider_authorized is False
    assert run_simulation().runtime_effect is False
