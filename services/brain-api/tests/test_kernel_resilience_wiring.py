"""Kernel wiring tests for resilience services."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_wires_resilience_services_and_diagnostics() -> None:
    container = kernel_container()
    checks = container.diagnostics.run()
    names = {check.name for check in checks}

    assert container.dependency_health_service is not None
    assert container.retry_policy_service is not None
    assert container.circuit_breaker_service is not None
    assert container.degraded_mode_service is not None
    assert container.fault_injection_service is not None
    assert container.resilience_test_runner is not None
    assert "resilience_services_present" in names
    assert "resilience_enabled" in names
