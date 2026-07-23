from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.research_policy import (
    redirect_method_after,
    validate_redirect_chain,
)


def test_redirect_method_remains_read_only_and_chain_is_fingerprinted():
    assert redirect_method_after(302, "GET") == "GET"
    assert redirect_method_after(308, "HEAD") == "HEAD"
    assert validate_redirect_chain(("https://research.example.invalid/next",))


def test_redirect_loop_and_limit_are_rejected():
    with pytest.raises(ValueError):
        validate_redirect_chain(("a", "a"))
    with pytest.raises(ValueError):
        validate_redirect_chain(("a", "b", "c", "d"))
