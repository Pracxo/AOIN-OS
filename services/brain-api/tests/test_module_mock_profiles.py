"""Module mock profile service tests."""

from __future__ import annotations

from aion_brain.contracts.module_mock_runtime import (
    ModuleMockProfileCreateRequest,
    ModuleMockProfileSeedRequest,
)
from tests.module_mock_helpers import SCOPE, services


def test_profile_service_seeds_defaults_dry_run_without_persisting() -> None:
    bundle = services()

    result = bundle["profile_service"].seed_defaults(  # type: ignore[attr-defined]
        ModuleMockProfileSeedRequest(scope=SCOPE, dry_run=True)
    )

    assert result["dry_run"] is True
    assert result["profile_count"] == 7
    assert bundle["repository"].list_profiles() == []  # type: ignore[attr-defined]


def test_profile_service_creates_profile_and_emits_telemetry() -> None:
    bundle = services()
    profile = bundle["profile_service"].create_profile(  # type: ignore[attr-defined]
        ModuleMockProfileCreateRequest(
            profile_key="generic.mock",
            name="Generic Mock",
            description="Generic mock profile.",
            owner_scope=SCOPE,
        )
    )

    assert profile.status == "active"
    assert profile.metadata["metadata_only"] is True
    assert bundle["telemetry"].events  # type: ignore[attr-defined]
