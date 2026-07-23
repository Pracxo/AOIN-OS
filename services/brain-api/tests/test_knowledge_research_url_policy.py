from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.research_policy import canonicalize_research_url


def test_https_canonicalization_normalizes_case_idna_and_fragment():
    url = canonicalize_research_url("https://Research.Example.Invalid:443/path?q=1#frag")
    assert url.canonical_url == "https://research.example.invalid/path?q=1"


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pass@research.example.invalid/",
        "https://research.example.invalid/a/../secret",
        "https://research.example.invalid/has space",
        "https://research.example.invalid/%zz",
        "file:///tmp/source",
        "ftp://research.example.invalid",
        "ws://research.example.invalid",
        "javascript:alert(1)",
        "https://93.184.216.34/source",
    ],
)
def test_url_policy_rejects_bypass_shapes(url: str):
    with pytest.raises(ValueError):
        canonicalize_research_url(url)


def test_http_is_only_allowed_for_explicit_fixture_metadata():
    with pytest.raises(ValueError):
        canonicalize_research_url("http://research.example.invalid/source")
    assert canonicalize_research_url(
        "http://research.example.invalid/source",
        allow_http_fixture=True,
    ).scheme == "http"
