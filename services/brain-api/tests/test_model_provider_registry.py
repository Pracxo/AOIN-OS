"""Model provider registry tests."""

from aion_brain.model_gateway.provider_registry import ModelProviderRegistry
from tests.model_gateway_fakes import AllowPolicy, external_provider, repository


def test_provider_registry_registers_lists_disables_and_checks_health() -> None:
    repo = repository()
    policy = AllowPolicy()
    registry = ModelProviderRegistry(repo, policy)

    provider = registry.register_provider(external_provider())
    assert provider.provider_id == "external-provider"
    assert registry.get_provider("external-provider") == provider
    assert registry.list_providers(status="active")[0].provider_id == "external-provider"

    health = registry.health_check("external-provider")
    assert health.provider_id == "external-provider"
    disabled = registry.disable_provider("external-provider", "test")
    assert disabled.status == "disabled"
    assert [request.action_type for request in policy.requests] == [
        "model.provider.register",
        "model.provider.read",
        "model.provider.read",
        "model.provider.health_check",
        "model.provider.disable",
    ]


def test_provider_registry_bootstraps_deterministic_provider() -> None:
    registry = ModelProviderRegistry(repository(), AllowPolicy())
    registry.ensure_defaults()
    provider = registry.get_provider("deterministic")
    assert provider is not None
    assert provider.provider_type == "deterministic"
