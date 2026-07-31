from __future__ import annotations

from aion_brain.model_gateway.manifests import InMemoryModelManifestRegistry


def test_capability_profiles_bind_models_and_no_effect_limits() -> None:
    profiles = InMemoryModelManifestRegistry().list_profiles()
    assert [profile.model_id for profile in profiles] == [
        "reference-json-sim-v1",
        "reference-text-sim-v1",
    ]
    for profile in profiles:
        assert profile.provider_id == "deterministic-reference-provider"
        assert profile.simulation_only is True
        assert profile.profile_fingerprint
