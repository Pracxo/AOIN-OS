from __future__ import annotations

from tests.decision_helpers import bundle


def test_utility_profile_service_seeds_generic_balanced_dry_run() -> None:
    services = bundle()

    result = services.utility_service.seed_default_profiles(
        dry_run=True,
        owner_scope=["workspace:main"],
    )

    assert result["dry_run"] is True
    assert result["profiles"][0]["name"] == "generic-balanced"
