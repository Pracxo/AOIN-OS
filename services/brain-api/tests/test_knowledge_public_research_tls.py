from __future__ import annotations

from public_research_pilot_test_helpers import make_fixture, run_simulation


def test_certificate_failure_blocks_source() -> None:
    fixtures = {
        ("GET", "https://example.com/robots.txt"): make_fixture(
            url="https://example.com/robots.txt"
        ),
        ("GET", "https://example.com/"): make_fixture(
            url="https://example.com/", certificate_valid=False
        ),
    }
    result = run_simulation(fixtures=fixtures)
    assert result.session.source_body_purged_count == 0
