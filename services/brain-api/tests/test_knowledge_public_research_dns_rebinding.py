from __future__ import annotations

from public_research_pilot_test_helpers import make_fixture, run_simulation


def test_peer_mismatch_blocks_rebinding_attempt() -> None:
    fixtures = {
        ("GET", "https://example.com/robots.txt"): make_fixture(
            url="https://example.com/robots.txt"
        ),
        ("GET", "https://example.com/"): make_fixture(
            url="https://example.com/", peer_address="1.1.1.1"
        ),
    }
    result = run_simulation(fixtures=fixtures)
    assert result.session.source_body_purged_count == 0
    assert result.candidate_eligibility_statuses[0] == "ineligible_for_operator_review"
