"""Kernel model gateway wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_registers_deterministic_provider_and_profile() -> None:
    container = kernel_container()
    provider = container.model_provider_registry.get_provider("deterministic")
    profile = container.model_profile_registry.get_profile("aion-deterministic-v0")
    assert provider is not None
    assert profile is not None
    assert container.model_gateway_service is not None


def test_kernel_diagnostics_include_model_gateway_checks() -> None:
    check_names = {check.name for check in kernel_container().diagnostics.run()}
    assert "model_gateway_service_present" in check_names
    assert "deterministic_provider_present" in check_names
    assert "deterministic_profile_present" in check_names
    assert "external_model_gateway_disabled_by_default" in check_names
