from __future__ import annotations

from public_research_pilot_test_helpers import make_source


def test_licence_status_is_explicit() -> None:
    source = make_source()
    assert source.licence_policy_status == "permitted"
