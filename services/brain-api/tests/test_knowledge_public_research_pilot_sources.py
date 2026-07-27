from __future__ import annotations

from public_research_pilot_test_helpers import make_source


def test_source_candidate_is_explicit_credential_free_and_https() -> None:
    source = make_source()
    assert source.explicit_operator_supplied is True
    assert source.scheme == "https"
    assert source.credential_free is True
    assert source.authorization_header_free is True
