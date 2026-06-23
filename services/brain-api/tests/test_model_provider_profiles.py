"""Model provider profile service tests."""

from __future__ import annotations

from aion_brain.contracts.model_provider_hardening import (
    ModelProviderProfileCreateRequest,
    ModelProviderProfileSeedRequest,
)
from tests.model_provider_hardening_helpers import SCOPE, services


def test_model_provider_profile_service_creates_metadata_only_profile() -> None:
    service = services()["profile_service"]

    profile = service.create_profile(  # type: ignore[attr-defined]
        ModelProviderProfileCreateRequest(
            provider_key="generic.metadata_only",
            name="Generic",
            description="Generic metadata profile.",
            owner_scope=SCOPE,
        )
    )

    assert profile.external_calls_allowed is False
    assert profile.metadata["provider_activation_enabled"] is False


def test_model_provider_profile_seed_defaults_are_dry_run() -> None:
    service = services()["profile_service"]

    result = service.seed_default_profiles(  # type: ignore[attr-defined]
        ModelProviderProfileSeedRequest(scope=SCOPE, dry_run=True)
    )

    assert result["dry_run"] is True
    assert result["profile_count"] == 4
    assert all(profile["external_calls_allowed"] is False for profile in result["profiles"])
