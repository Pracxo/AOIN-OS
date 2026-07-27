from __future__ import annotations

from public_research_pilot_test_helpers import run_simulation


def test_robots_disallow_blocks_source() -> None:
    result = run_simulation(robots_body=b"User-agent: *\nDisallow: /\n")
    assert result.session.source_body_purged_count == 0
    assert result.candidate_eligibility_statuses[0] == "ineligible_for_operator_review"
