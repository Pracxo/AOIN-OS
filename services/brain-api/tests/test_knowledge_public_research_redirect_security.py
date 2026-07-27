from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.public_research_policy import evaluate_redirect_location


def test_redirect_downgrade_and_loop_reject() -> None:
    with pytest.raises(ValueError):
        evaluate_redirect_location(
            current_url="https://example.com/a",
            location="http://example.com/b",
            allowlist=("example.com",),
            seen_urls=("https://example.com/a",),
        )
    with pytest.raises(ValueError):
        evaluate_redirect_location(
            current_url="https://example.com/a",
            location="/a",
            allowlist=("example.com",),
            seen_urls=("https://example.com/a",),
        )
