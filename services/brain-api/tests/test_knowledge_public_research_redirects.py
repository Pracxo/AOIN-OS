from __future__ import annotations

from public_research_pilot_test_helpers import make_fixture, make_plan, make_source, run_simulation


def test_redirect_success_is_revalidated_and_recorded() -> None:
    source = make_source(url="https://example.com/start")
    plan = make_plan(source=source)
    fixtures = {
        ("GET", "https://example.com/robots.txt"): make_fixture(
            url="https://example.com/robots.txt"
        ),
        ("GET", "https://example.com/start"): make_fixture(
            url="https://example.com/start",
            status_code=302,
            headers=(("Location", "/final"), ("Content-Type", "text/plain")),
        ),
        ("GET", "https://example.com/final"): make_fixture(url="https://example.com/final"),
    }
    result = run_simulation(plan=plan, fixtures=fixtures)
    assert result.session.redirect_hop_fingerprints
    assert result.session.source_body_purged_count == 1
