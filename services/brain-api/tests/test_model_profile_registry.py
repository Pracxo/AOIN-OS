"""Model profile registry tests."""

from aion_brain.model_gateway.profile_registry import ModelProfileRegistry
from tests.model_gateway_fakes import AllowPolicy, external_profile, repository


def test_profile_registry_registers_lists_and_disables() -> None:
    repo = repository()
    policy = AllowPolicy()
    registry = ModelProfileRegistry(repo, policy)

    profile = registry.register_profile(external_profile())
    assert registry.get_profile("external-profile") == profile
    assert registry.list_profiles(provider_id="external-provider")[0].model_profile_id == (
        "external-profile"
    )
    disabled = registry.disable_profile("external-profile", "test")
    assert disabled.status == "disabled"
    assert [request.action_type for request in policy.requests] == [
        "model.profile.register",
        "model.profile.read",
        "model.profile.read",
        "model.profile.disable",
    ]


def test_profile_registry_bootstraps_deterministic_profile() -> None:
    registry = ModelProfileRegistry(repository(), AllowPolicy())
    registry.ensure_defaults()
    profile = registry.get_profile("aion-deterministic-v0")
    assert profile is not None
    assert profile.provider_id == "deterministic"
