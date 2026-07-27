from __future__ import annotations

from public_research_pilot_test_helpers import body_keys_absent, run_simulation


def test_result_contains_no_source_body_fields() -> None:
    result = run_simulation(source_body=b"body bytes that must not be retained")
    assert result.session.source_body_purged_count == 1
    assert body_keys_absent(result.model_dump(mode="json")) is True
