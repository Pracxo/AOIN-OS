from __future__ import annotations

from public_research_pilot_test_helpers import make_source


def test_source_class_is_approved_for_pilot() -> None:
    source = make_source()
    assert source.source_class == "official_standard"
