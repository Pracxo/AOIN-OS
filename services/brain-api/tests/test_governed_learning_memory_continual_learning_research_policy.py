from __future__ import annotations

from pathlib import Path

from scripts.lib import governed_learning_memory_continual_learning_pilot_authorization as auth227

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_research_composition_requires_explicit_allowlisted_https() -> None:
    auth = auth227.load_json(
        "examples/governed-learning-memory/continual-learning-pilot-authorization.json",
        REPO_ROOT,
    )
    policy = auth["research_policy"]
    assert policy["explicit_urls_required"] is True
    assert policy["exact_domain_allowlist_required"] is True
    assert policy["https_only"] is True
    assert policy["crawler_allowed"] is False
    assert policy["search_provider_allowed"] is False
