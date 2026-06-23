"""Kernel wiring tests for model provider hardening."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_provider_hardening_services() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}

    assert "model_provider_hardening_repository_present" in names
    assert "prompt_egress_guard_present" in names
    assert "model_provider_simulator_present" in names


def test_kernel_wires_provider_hardening_into_gateway_and_resource_scanner() -> None:
    container = kernel_container()

    status = container.model_gateway_service.provider_hardening_status()
    records = container.resource_scanner.scan(
        ["model_provider_profile"],
        ["model_provider_hardening"],
        ["workspace:main"],
        10,
    )

    assert status["readiness_is_not_enablement"] is True
    assert isinstance(records, list)
