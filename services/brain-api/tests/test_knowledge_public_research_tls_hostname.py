from __future__ import annotations

from public_research_pilot_test_helpers import make_fixture, run_simulation


def test_hostname_mismatch_blocks_source() -> None:
    fixtures = {
        ("GET", "https://example.com/robots.txt"): make_fixture(
            url="https://example.com/robots.txt"
        ),
        ("GET", "https://example.com/"): make_fixture(
            url="https://example.com/", hostname_valid=False
        ),
    }
    assert (
        run_simulation(fixtures=fixtures).candidate_eligibility_statuses[0]
        == "ineligible_for_operator_review"
    )
